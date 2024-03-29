from datetime import datetime, timedelta
import math
import logging
from service.abc_energy_consumer        import energy_consumer
from teslapy                            import Tesla
from teslapy                            import VehicleError
from teslapy                            import RequestException
from common.persistence                 import persistence
from common.database_logging_handler    import database_logging_handler

class tesla_energy_consumer(energy_consumer):
    def __init__(self, db:persistence, logger=None) -> None:
        self._last_vehicle_data_update = datetime.now()
        self.persistence = db
        self.is_consuming = False
        self._consumption = 0
        self._name = "Tesla"
        self.voltage = 230
        self._consumption_amps_now = 0
        self._max_power_consumption  = self.persistence.get_consumer_consumption_max(self._name)
        self._max_current_consumption = self.power_to_current(self._max_power_consumption)
        self.charge_state = {}
        self.drive_state = {}
        self.email = ""
        self._is_at_home = False
        self._is_disconnected = False
        self._est_battery_range = 0
        self._battery_range = '0 '
        self._price_percentage = db.get_tesla_price_percentage()
        self._status = ""
        self._old_status = ""
        self._block_status_publishing  = False # while doing logic, we don't want to see the status changing in the web frontend
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)
            log_handler = logging.StreamHandler()
            log_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(log_handler)

            log_handler = database_logging_handler(self.persistence)
            log_handler.setLevel(logging.INFO)
            self.logger.addHandler(log_handler)

        self.vehicle = None
        
        
        

    def initialize(self, **kwargs):
        if kwargs and kwargs['email']:
            self.email = kwargs['email']
        if self.email:
            try:
                self.tesla = Tesla(self.email)
                self.tesla.captcha_solver = self.solve_captcha
                self.tesla.fetch_token()
                vehicles = self.tesla.vehicle_list()
                if len(vehicles) > 0:
                    self.vehicle = vehicles[0]
                    self.logger.info("Initialization succesful. NR of vehicles = {}. We're using the first".format(len(vehicles)))
                    return True
            except (Exception) as e:
                self.logger.info(f"Error during initializing Tesla energy consumer: {e}")            
        return False

    def solve_captcha(self, svg) -> str:
        with open('captcha.svg', 'wb') as f:
            f.write(svg)
        return input('Captcha: ')

    def __update_vehicle_data(self) -> None:
        diff = datetime.now() - self._last_vehicle_data_update
        if diff.total_seconds() < 8 and len(self.drive_state) > 0: 
            return
        
        try:
            if self.vehicle is None:
                self.initialize()
        except:
            self.logger.exception("Error during vehicle data update")
            self.initialize()
        try:
            if not self.vehicle:
                self.logger.warning("No known vehicle")
                return
            if self.vehicle.get('state') == 'asleep':
                self.vehicle.sync_wake_up()
        
            self.vehicle.get_vehicle_data()
            self._last_vehicle_data_update = datetime.now()
            self.charge_state     = self.vehicle.get('charge_state')
            self.drive_state      = self.vehicle.get('drive_state')
            self.is_consuming     = self.charge_state.get('charging_state') == 'Charging'
            self._is_disconnected = self.charge_state.get('charging_state') == "Disconnected"

            self.est_battery_range = self.dist_units(self.charge_state['est_battery_range'])
            self._battery_range = self.dist_units(self.charge_state['battery_range'])
            
            if 'latitude' in self.drive_state and 'longitude' in self.drive_state:
                self.latitude_current = float(self.drive_state['latitude'])
                self.longitude_current = float(self.drive_state['longitude'])

                (lat,lon) = self.persistence.get_tesla_home_coords()

                
                self._is_at_home = abs(self.longitude_current - lon) < 0.000100 and \
                                   abs(self.latitude_current  - lat) < 0.000100

                self.persistence.set_tesla_current_coords(self.latitude_current, self.longitude_current)            
            
            if self.is_at_home:
                self._consumption_amps_now = self.charge_state['charger_actual_current']
            else: 
                self._consumption_amps_now = 0

            self.persistence.set_consumer_consumption_now(self._name, self.consumption_amps_now)

            self._max_power_consumption  = self.persistence.get_consumer_consumption_max(self._name)
            self._max_current_consumption = self.power_to_current(self._max_power_consumption)
        
        except Exception as e:
            self.logger.error("Error during getting vehicle data: " + str(e))
            return        


    # def consumer_is_consuming(self):
    #     return self.is_consuming
        
    def stop_consuming(self) -> bool:
        if not self._may_stop_consuming:
            return

        if self.is_consuming:
            self.logger.info("Giving stop_charging command")    
            res = self.vehicle.command('STOP_CHARGE')
            self.logger.debug("Stop command result: " + str(res))
            self.__update_vehicle_data()
            return self.is_consuming
        else:
            self.logger.info("Stop charging command is not needed. Vehicle wasn't charging")   
            
    def start_consuming(self, surplus_power) -> bool:
        """
        Tell the consumer to start consumer the given amout of power.
        Make sure beofrehand that the consumer is capable and willing
        to consume this. Use that function can_consume_this_surplus.
        """
        try:
            
            old_charging_current = self.charge_state.get('charger_actual_current',0)
            # calculate what the new charging current needs to be. 
            new_charging_current = self.calc_new_charge_current(old_charging_current, surplus_power)
            self.logger.info("Actual charging current: {}, New charging current: {}".format(old_charging_current,new_charging_current))
            try:
                self.__set_charge_current(new_charging_current)
            except Exception as e:
                self.logger.info("Exception during setting of the current:".format(e))
            
            res = True
            if  not self.is_consuming:
                try:
                    res = self.vehicle.command('START_CHARGE')
                    self.logger.debug("Start command result: " + str(res))
                except Exception as e:
                    self.logger.info("Exception when giving the START_CHARGE command:{}".format(e))
                    return False
            self.__update_vehicle_data()
            return res
        except Exception as e:
            self.logger.error(e)
            return False


    def get_forecasted_battery_level(self) -> dict:
        self.__update_vehicle_data()
        estimation_dict = {}
        if 'charge_rate' in self.charge_state:
            charge_rate = self.dist_units(self.charge_state.get('charge_rate',0))
            self.logger.info(f"Charge rate is {charge_rate}/h")
            charge_rate = float(charge_rate.split(' ')[0])
            now = datetime.now()
            
            # under which percentage of the average price should we charge at full speed?
            price_percentage = self.price_percentage

            # calculate for the rest of today
            datum = datetime.strptime(datetime.today().strftime("%Y-%m-%d"),"%Y-%m-%d")
            prices = self.persistence.get_day_prices(datum)
            total = 0
            for row in prices:
                total += row[1]  # price
            average_price = round(total/24,2) 
            current_surplus = self.persistence.get_surplus()

            consumption_amps_now = self.persistence.get_consumer_consumption_now(self._name)
            
            for row in prices:
                dt = datetime.fromtimestamp(int(row[0]))
                hour = dt.hour  
                hours_price = row[1]
                    
                if hour == datetime.now().hour:  
                    this_hour = datetime(now.year, now.month, now.day, now.hour, 0,0)
                    estimation_dict[this_hour] = self.battery_range
                    time_in_1_hour = now + timedelta(hours=1)
                    next_hour = datetime(time_in_1_hour.year, time_in_1_hour.month, time_in_1_hour.day, time_in_1_hour.hour, 0,0)
                    timedelta_to_next_hour = next_hour - now

                    if hours_price < self.charge_below_price(average_price, price_percentage):
                        battery_range_at_next_hour = self.battery_range + round(charge_rate * timedelta_to_next_hour.seconds/3600,2)
                    else:
                        if self.battery_level < self.balance_above:
                            battery_range_at_next_hour = math.min(self.battery_range + round(charge_rate * timedelta_to_next_hour.seconds/3600,2), self.balance_above)
                        else:
                            battery_range_at_next_hour = self.battery_range + round(charge_rate,2)
                    
                    estimation_dict[next_hour] = battery_range_at_next_hour
                if hour > datetime.now().hour:
                    next_hour = datetime(time_in_1_hour.year, time_in_1_hour.month, time_in_1_hour.day, hour, 0,0) + timedelta(hours=1)
                    if hours_price < self.charge_below_price(average_price, price_percentage):
                        # We assume 1 hours of full speed loading, which is 25 km/h. How to calc this 25?
                        self.logger.debug(f"Addition: 25km for {next_hour.hour}h")
                        battery_range_at_next_hour = battery_range_at_next_hour + 25
                    else:
                        # use current charging power as the basis for estimation                    
                        self.logger.debug(f"Addition: {charge_rate}km for {next_hour.hour}h")
                        battery_range_at_next_hour = battery_range_at_next_hour + charge_rate
                    
                    estimation_dict[next_hour] = battery_range_at_next_hour
        return estimation_dict

    def charge_below_price(self, average_price, price_percentage) -> float:
        return round(average_price - ((100-price_percentage)/100 * abs(average_price)),2)

    def balance(self, current_hour_price,average_price, average_surplus) -> bool:
        """
        Balances the energy consumption based on the current hour price, average price, and average surplus.

        Parameters:
            current_hour_price (float): The price of the current hour.
            average_price (float): The average price of today.
            average_surplus (float): The average surplus power taken the last few minutes.

        Returns:
            bool: True if surplus has been taken, False otherwise.
        """

        self.block_status_publishing = True
        has_taken_surplus = False
        self.__update_vehicle_data() 
        if not 'battery_level' in self.charge_state:
            self.logger.info("Charge state unknown, cannot balance")
            return False
        
        # Charge at full speed until battery level exceeds 'balance_above' setting
        curr_level = int(self.charge_state.get('battery_level',0))
        if curr_level < self.balance_above:
            self.status = f"Snelladen tot {self.balance_above}%. Nu ({curr_level}%)"
            self.logger.info("Tesla opladen op maximale snelheid tot {}%. Huidig batterij perc. is {}%".format(self.balance_above, curr_level))
            self._consume_at_maximum()
            return True # this will disqualify this consumer for consuming the given (possibly small amount of) surplus power.


        price_percentage = self.price_percentage
        charge_below_price = self.charge_below_price(average_price, price_percentage)
        if current_hour_price < charge_below_price:
            self.logger.info(f"Price this hour ({current_hour_price}) is below {charge_below_price} ({average_price} - ({price_percentage}/100 * abs({average_price}))), so consume at maximum")
            self.status = f"Uurprijs ({current_hour_price}) is lager dan {price_percentage}% van daggemiddelde ({average_price}), dus maximaal consumeren" 
            max_consumption_power = self.max_consumption_power
            if self.can_consume_this_surplus(max_consumption_power):
                self.start_consuming(max_consumption_power)
            else:
                self.logger.debug("Tesla could not start consuming, so no surplus has been taken")
        else:
            self.logger.info(f"Price this hour ({current_hour_price}) is above {charge_below_price} ({average_price} - ({price_percentage}/100 * abs({average_price}))), so balance ")
            self.status = f"Uurprijs ({current_hour_price}) is hoger dan {price_percentage}% van daggemiddelde ({average_price}), dus alleen overtollige energie consumeren" 
            self.logger.info(f"Average surplus: {average_surplus}")
            if average_surplus: # if there is some plus or minus surplus
                # potential improvement is to lower the av_surplus with the amount given to the consumer, and try to give the remainder to other consumers
                
                if self.can_consume_this_surplus(average_surplus):
                    if self.start_consuming(average_surplus): # returns true if something has changed in energy consumption
                        has_taken_surplus = True
                    else:
                        self.logger.debug("Tesla could not start consuming, so no surplus has been taken")
            else:
                self.stop_consuming()
        self.block_status_publishing = False
        return has_taken_surplus
    
    def can_consume_this_surplus(self, surplus_power) -> bool:
        """
        Function that returs true if the consumer is able to serve (consume the given)
        surpplus energy. This allows for multiple consumers and a mediator to choose
        the most appropriate consumer, with algorithms yet to be developed.
        """
        # if self.balance_activated == False:
        #     self.logger.info("Het balanceren voor de gebruiker Tesla is uitgeschakeld")
        #     self.status = "Balanceren is uitgeschakeld"
        #     return False

        if not self._can_start_consuming: # property will call self.__update_vehicle_data()
            self.logger.debug("Cannot start consuming")
            return False

        battery_level = int(self.charge_state.get('battery_level',0))
        charge_limit_soc = int(self.charge_state.get('charge_limit_soc',0))

        if not charge_limit_soc or not battery_level:
            self.logger.info("Charge state or battery level unknown; cannot balance")
            return False

        if battery_level >= charge_limit_soc:
            self.logger.info(f"Tesla is opgeladen tot het opgegeven maximum ({charge_limit_soc}%)")
            self.status = f"Tot max ({charge_limit_soc})% opgeladen"
            return False
        
        # old_charging_current = 0 if self.charge_state['charger_actual_current'] is None else self.charge_state['charger_actual_current']

        
        self.__update_vehicle_data() 

        # # Charge at full speed until battery level exceeds 'balance_above' setting
        # curr_level = int(self.charge_state['battery_level'])
        # if curr_level < self.balance_above:
        #     self.status = f"Snelladen tot {self.balance_above}%. Nu ({curr_level}%)"
        #     self.logger.info("Tesla opladen op maximale snelheid tot {}%. Huidig batterij perc. is {}%".format(self.balance_above, curr_level))
        #     self._consume_at_maximum()
        #     return False # this will disqualify this consumer for consuming the given (possibly small amount of) surplus power.
    
        if surplus_power and surplus_power <= self._max_power_consumption:
            return True
        self.logger.info(f"Surplus_power {surplus_power} exceeds max_power_consumption: {self._max_power_consumption}")
        return False

    def _consume_at_maximum(self):
        max_consumption_power = self.max_consumption_power
        if self.can_consume_this_surplus(max_consumption_power):
            self.logger.info("Calling start_consuming with {max_consumption_power}")
            self.start_consuming(max_consumption_power)
        else:
            self.logger.info("Tesla could not consume this surplus")

            
    def power_to_current(self, power) -> int:
        """
        Function that returns a rounded number indicating how much current will 
        flow for given power and set voltage. The formula is P=VI, so fof this
        function I=P/V
        """
        return int(power / self.voltage)

    def calc_new_charge_current(self, charger_actual_current:int, surplus_power:int) -> int:
        """
        This function returns a number between and including 0 and some maximum.
        It uses the current power consumption and the given surplus to calculate
        a new current that it should consume
        """
        amps_new = charger_actual_current + self.power_to_current(surplus_power)
        amps_new = max(0, amps_new)
        amps_new = min(self.power_to_current(self.max_consumption_power),amps_new)
        return amps_new

    def __set_charge_current(self, amps) -> None:
        if amps >= 0:
            res = self.vehicle.command("CHARGING_AMPS",charging_amps=amps)
            self.logger.debug("Set charge current result: " + str(res))
            self.__update_vehicle_data()

    def dist_units(self, miles, speed=False) -> str:
            """ Format and convert distance or speed to GUI setting units """
            if miles is None:
                return None
            if 'gui_settings' not in self.vehicle:
                self.__update_vehicle_data()
            # Lookup GUI settings of the vehicle
            if 'km' in self.vehicle['gui_settings']['gui_distance_units']:
                return '%.1f %s' % (miles * 1.609344, 'km/h' if speed else 'km')
            return '%.1f %s' % (miles, 'mph' if speed else 'mi')
    
    @property 
    def name(self) -> str:
        return self._name
    
    #propery for blocking the status publishing
    @property
    def block_status_publishing(self) -> bool:
        return self._block_status_publishing
    @block_status_publishing.setter
    def block_status_publishing(self,value) -> None:
        if value == False:
            self.persistence.set_consumer_status(self._name, self.status)
        self._block_status_publishing = value

    @property
    def status(self) -> str:
        if self.block_status_publishing:
            return self._status
        else:
            return self.persistence.get_consumer_status(self._name)
    @status.setter
    def status(self,value)  -> None:
        self._status = value

    @property
    def battery_range(self) -> float:
        self.__update_vehicle_data()
        return float(self._battery_range.split(' ')[0])
        
    @property
    def max_consumption_power(self) -> int:
        self._consumption = self.persistence.get_consumer_consumption_max(self._name)
        return self._consumption
    @max_consumption_power.setter
    def max_consumption_power(self,value) -> None:
        self._consumption = value
        self.persistence.set_consumer_consumption_max(self._name, value)

    @property
    def balance_above(self) -> int:
        self._balance_above = self.persistence.get_tesla_balance_above()
        return self._balance_above
    @balance_above.setter
    def balance_above(self,value) -> None:
        self._balance_above = value
        self.persistence.set_tesla_balance_above(value)

    @property
    def price_percentage(self) -> int:
        self._price_percentage = self.persistence.get_tesla_price_percentage()
        return self._price_percentage
    @price_percentage.setter
    def price_percentage(self,value) -> None:
        self._price_percentage = value
        self.persistence.set_tesla_price_percentage(value)


    @property
    def charge_until(self) -> int:
        self._charge_until = self.persistence.get_tesla_charge_until()
        return self._charge_until
    @charge_until.setter
    def charge_until(self,value) -> None:
        self._charge_until = value
        self.persistence.set_tesla_charge_until(value)
        try:
            self.vehicle.command('CHANGE_CHARGE_LIMIT', percent=value)
        except (VehicleError) as e:
            self.logger.debug(e)
        except (RequestException) as e:
            self.logger.exception(e)


    @property
    def isConsuming(self) -> bool:
        return self.is_consuming
    
    @property
    def consumption_amps_now(self) -> int:
        self.__update_vehicle_data()
        return self._consumption_amps_now
    
    @property
    def consumption_power_now(self) -> float:
        self.__update_vehicle_data()
        # if self.consumption_amps_now is none, return 0
        if self.consumption_amps_now is None:
            return 0
        return self.consumption_amps_now * self.voltage
    
    @property
    def balance_activated(self) -> bool:
        is_activated = self.persistence.get_consumer_balance(self._name) 
        if not is_activated:
            self.status = "Balanceren is uitgeschakeld"
        return is_activated
    
    @balance_activated.setter
    def balance_activated(self,value) -> None:
        """
        Bij het uitschakelen van balaceren, moeten we zorgen dat de tesla of volle sterkte gaat laden.
        Het daadwerkelijk starten en stoppen moeten we niet forceren, maar overlaten aan
        bijv. Jedlix, of de gebruiker (via zijn Tesla app).
        """
        self.block_status_publishing = True
        self.persistence.set_consumer_balance(self._name,value)
        if value == False:
            curr_level = self.charge_state.get('battery_level','onbekend')
            self.logger.info("Tesla opladen op maximale snelheid. Huidig batterij perc. is {}%".format(curr_level))
            max_level = self.charge_state.get('charge_limit_soc',100)
            self.status = f"Tot maximum ({max_level})% opladen"
            self._consume_at_maximum()
        self.block_status_publishing = False
            

    @property
    def _can_start_consuming(self) -> bool:
        self.__update_vehicle_data()
        
        if not self.is_at_home:
            self.logger.info("Kan niet laden want de Tesla is niet op de thuislokatie")
            self.status = "Niet thuis"
            return False 

        if  self.is_disconnected:
            self.logger.info("Kan niet laden want de Tesla is niet aangesloten")
            self.status = "Niet aangesloten"
            return False

        return True

    
    @property
    def is_disconnected(self) -> bool:
        self.__update_vehicle_data()  

        self.logger.debug(f"Charge state is {self.vehicle.get('charge_state')}")         
        if self.charge_state and self.charge_state.get('charging_state') == "Disconnected":
            _is_disconnected = True
            return _is_disconnected
        _is_disconnected = False
        return _is_disconnected

    @property
    def is_at_home(self) -> bool:
        self.__update_vehicle_data()  
        return self._is_at_home


    @property
    def _may_stop_consuming(self) -> bool:
        """
        Checks if the vehicle may stop consuming.
        
        Returns:
            bool: True if the vehicle may stop consuming, False otherwise.
        """
        self.__update_vehicle_data()
        
        if not self.is_at_home:
            self.logger.info("Will not stop because car is not at home")
            self.status = "Niet thuis"
            return False
        return True

    @property
    def battery_level(self) -> int:
        self.__update_vehicle_data()
        return int(self.charge_state.get('battery_level',0))

    @property
    def est_battery_range(self) -> float:
        self.__update_vehicle_data()
        return self._est_battery_range
    @est_battery_range.setter
    def est_battery_range(self, value) -> None:
        self._est_battery_range = value

        