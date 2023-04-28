from datetime import datetime
import logging
from service.abc_energy_consumer        import energy_consumer
from teslapy                            import Tesla
from teslapy                            import VehicleError
from teslapy                            import RequestException
from common.persistence                 import persistence
from common.database_logging_handler    import database_logging_handler

class tesla_energy_consumer(energy_consumer):
    def __init__(self, db:persistence) -> None:
        self._last_vehicle_data_update = datetime.now()
        self.persistence = db
        self.is_consuming = False
        self._consumption = 0
        self._name = "Tesla"
        self.voltage = 230
        self._consumption_amps_now = 0
        self.charge_state = {}
        self.drive_state = {}
        self.email = ""
        self._est_battery_range = 0
        self._price_percentage = db.get_tesla_price_percentage()
        self._status = ""
        self.logger = logging.getLogger(__name__)
        
        log_handler = logging.StreamHandler()
        log_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(log_handler)
        
        log_handler = database_logging_handler(self.persistence)
        log_handler.setLevel(logging.INFO)
        self.logger.addHandler(log_handler)

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
                    self.logger.debug("Initialization succesful. NR of vehicles = {}.".format(vehicles.count))
                    return True
            except (Exception) as e:
                self.logger.debug(f"Error during initializing Tesla energy consumer: {e}")            
        return False

    def solve_captcha(self, svg):
        with open('captcha.svg', 'wb') as f:
            f.write(svg)
        return input('Captcha: ')

    def __update_vehicle_data(self):
        diff = datetime.now() - self._last_vehicle_data_update
        if diff.total_seconds() < 5 and len(self.drive_state) > 0: 
            return
        
        try:
            if self.vehicle is None:
                self.initialize()
        except:
            self.initialize()
        try:
            if self.vehicle['state'] == 'asleep':
                self.vehicle.sync_wake_up()
        
            self.vehicle.get_vehicle_data()
            self._last_vehicle_data_update = datetime.now()
            self.charge_state = self.vehicle['charge_state']
            self.drive_state = self.vehicle['drive_state']
            self.is_consuming = self.charge_state['charging_state'].lower() == 'charging'
            if self.is_at_home:
                self._consumption_amps_now = self.charge_state['charger_actual_current']
            else: 
                self._consumption_amps_now = 0
            self._est_battery_range = self.dist_units(self.charge_state['est_battery_range'])
            self.latitude_current = float(self.drive_state['latitude'])
            self.longitude_current = float(self.drive_state['longitude'])

            self.persistence.set_tesla_current_coords(self.latitude_current, self.longitude_current)            
            self.persistence.set_consumer_consumption_now(self._name, self.consumption_amps_now)
        except Exception as e:
            self.logger.error("Error during getting vehicle data: " + str(e))
            return        


    # def consumer_is_consuming(self):
    #     return self.is_consuming
        
    def stop_consuming(self):
        if not self.may_stop_consuming():
            return

        if self.is_consuming:
            self.logger.info("Giving stop_charging command")    
            res = self.vehicle.command('STOP_CHARGE')
            self.logger.debug("Stop command result: " + str(res))
            self.__update_vehicle_data()
            return self.is_consuming
        else:
            self.logger.info("Stop charging command is not needed. Vehicle wasn't charging")   
            
    def start_consuming(self, surplus_power):
        """
        Tell the consumer to start consumer the given amout of power.
        Make sure beofrehand that the consumer is capable and willing
        to consume this. Use that function can_consume_this_surplus.
        """
        try:
            
            old_charging_current = 0 if self.charge_state['charger_actual_current'] is None else self.charge_state['charger_actual_current']
            # calculate what the new charging current needs to be. 
            new_charging_current = self.calc_new_charge_current(old_charging_current, surplus_power)
            self.logger.info("Actual charging current: {}, New charging current: {}".format(old_charging_current,new_charging_current))
            try:
                self.__set_charge_current(new_charging_current)
            except Exception as e:
                self.logger.exception("Exception during setting of the current:".format(e))
            
            if  not self.is_consuming:
                try:
                    res = self.vehicle.command('START_CHARGE')
                    self.logger.debug("Start command result: " + str(res))
                except Exception as e:
                    self.logger.exception("Exception when giving the START_CHARGE command:{}".format(e))
            
            self.__update_vehicle_data()
            return old_charging_current != new_charging_current
        except Exception as e:
            self.logger.error(e)

    def balance(self, current_hour_price,average_price, average_surplus):

        price_percentage = self.price_percentage
        if current_hour_price < average_price * (price_percentage/100):
            self.logger.info(f"Price this hour ({current_hour_price}) is below {price_percentage}% of today's average ({average_price}), so consume at maximum")
            self.status = f"Uurprijs ({current_hour_price}) is lager dan {price_percentage}% van daggemiddelde ({average_price}), dus maximaal consumeren" 
            max_consumption_power = self.max_consumption_power
            if self.can_consume_this_surplus(max_consumption_power):
                self.start_consuming(max_consumption_power)
        else:
            self.logger.info(f"Price this hour ({current_hour_price}) is above {price_percentage}% of today's average ({average_price}), so balance ")
            self.status = f"Uurprijs ({current_hour_price}) is hoger dan {price_percentage}% van daggemiddelde ({average_price}), dus alleen overtollige energie consumeren" 
            if average_surplus: # if there is some plus or minus surplus
                # potential improvement is to lower the av_surplus with the amount given to the consumer, and try to give the remainder to other consumers
                # self.logger.info("Average surplus: " + str(av_surplus))
                if self.can_consume_this_surplus(average_surplus):
                    if self.start_consuming(average_surplus): # returns true if something has changed in energy consumption
                        self.data_model.reset_average_surplus()
    def can_consume_this_surplus(self, surplus_power):
        """
        Function that returs true if the consumer is able to serve (consume the given)
        surpplus energy. This allows for multiple consumers and a mediator to choose
        the most appropriate consumer, with algorithms yet to be developed.
        """
        if self.balance_activated == False:
            self.logger.info("Het balanceren voor de gebruiker Tesla is uitgeschakeld")
            return False

        if not self.can_start_consuming: # property will call self.__update_vehicle_data()
            return False

        if int(self.charge_state['battery_level']) >= int(self.charge_state['charge_limit_soc']):
            self.logger.info(f"Tesla is opgeladen tot het opgegeven maximum ({self.charge_state['charge_limit_soc']})")
            self.status = f"Tot max ({self.charge_state['charge_limit_soc']})% opgeladen"
            return False
        
        # old_charging_current = 0 if self.charge_state['charger_actual_current'] is None else self.charge_state['charger_actual_current']

        max_power_consumption = self.persistence.get_consumer_consumption_max(self._name)
        
        self.__update_vehicle_data() 

        # Charge at full speed until battery level exceeds 'balance_above' setting
        curr_level = int(self.charge_state['battery_level'])
        if curr_level < self.balance_above:
            max_current_consumption = self.power_to_current(max_power_consumption)
            self.__set_charge_current(max_current_consumption)
            self.logger.info("Tesla opladen op maximale snelheid tot {}%. Huidig batterij perc. is {}%".format(self.balance_above, curr_level))
            self.status = f"Snelladen tot {self.balance_above}%. Nu {curr_level}%)"
            return False # this will disqualify this consumer for consuming the given (possibly small amount of) surplus power.
    
        if surplus_power and surplus_power <= max_power_consumption:
            return True
        return False

    def power_to_current(self, power):
        """
        Function that returns a rounded number indicating how much current will 
        flow for given power and set voltage. The formula is P=VI, so fof this
        function I=P/V
        """
        return int(power / self.voltage)

    def calc_new_charge_current(self, charger_actual_current, surplus_power):
        """
        This function returns a number between and including 0 and some maximum.
        It uses the current power consumption and the given surplus to calculate
        a new current that it should consume
        """
        amps_new = charger_actual_current + self.power_to_current(surplus_power)
        amps_new = max(0, amps_new)
        amps_new = min(self.power_to_current(self.max_consumption_power),amps_new)
        return amps_new

    def __set_charge_current(self, amps):
        if amps >= 0:
            self.vehicle.command("CHARGING_AMPS",charging_amps=amps)
            self.__update_vehicle_data()

    def dist_units(self, miles, speed=False):
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
    def name(self):
        return self._name
    
    @property
    def status(self):
        self._status = self.persistence.get_consumer_status(self._name)
        return self._status
    @status.setter
    def status(self,value):
        self._status = value
        self.persistence.set_consumer_status(self._name, value)
        
    @property
    def max_consumption_power(self):
        self._consumption = self.persistence.get_consumer_consumption_max(self._name)
        return self._consumption
    @max_consumption_power.setter
    def max_consumption_power(self,value):
        self._consumption = value
        self.persistence.set_consumer_consumption_max(self._name, value)

    @property
    def balance_above(self):
        self._balance_above = self.persistence.get_tesla_balance_above()
        return self._balance_above
    @balance_above.setter
    def balance_above(self,value):
        self._balance_above = value
        self.persistence.set_tesla_balance_above(value)

    @property
    def price_percentage(self):
        self._price_percentage = self.persistence.get_tesla_price_percentage()
        return self._price_percentage
    @price_percentage.setter
    def price_percentage(self,value):
        self._price_percentage = value
        self.persistence.set_tesla_price_percentage(value)


    @property
    def charge_until(self):
        self._charge_until = self.persistence.get_tesla_charge_until()
        return self._charge_until
    @charge_until.setter
    def charge_until(self,value):
        self._charge_until = value
        self.persistence.set_tesla_charge_until(value)
        try:
            self.vehicle.command('CHANGE_CHARGE_LIMIT', percent=value)
        except (VehicleError) as e:
            self.logger.debug(e)
        except (RequestException) as e:
            self.logger.exception(e)


    @property
    def isConsuming(self):
        return self.is_consuming
    
    @property
    def consumption_amps_now(self):
        self.__update_vehicle_data()
        return self._consumption_amps_now
    
    @property
    def consumption_power_now(self):
        self.__update_vehicle_data()
        return self.consumption_amps_now * self.voltage
    
    @property
    def balance_activated(self):
        return self.persistence.get_consumer_balance(self._name) 
    @balance_activated.setter
    def balance_activated(self,value):
        """
        Bij het uitschakelen van balaceren, moeten we zorgen dat de tesla of volle sterkte gaat laden.
        Het daadwerkelijk starten en stoppen moeten we niet forceren, maar overlaten aan
        bijv. Jedlix, of de gebruiker (via zijn Tesla app).
        """
        if value == False:
            max_power_consumption = self.persistence.get_consumer_consumption_max(self._name)
            max_current_consumption = self.power_to_current(max_power_consumption)
            self.__set_charge_current(max_current_consumption)
            self.logger.info("Balanceren werd uitgeschakeld. Laadstroom op {}A gezet".format(max_current_consumption))
            

    @property
    def can_start_consuming(self):
        self.__update_vehicle_data()
        
        if not self.is_at_home:
            self.logger.info("Kan niet laden want de Tesla is niet op de thuislokatie")
            self.status = "Niet thuis"
            return False 

        if  self.is_disconnected:
            self.logger.info("Kan niet laden want de Tesla is niet aangesloten")
            self.status = "Niet aangesloten"
            return False

        return True, ""

    
    @property
    def is_disconnected(self):
        self.__update_vehicle_data()  
        if self.charge_state['charging_state'] == "Disconnected":
            self.logger.debug(f"Charging state is {self.vehicle['charge_state']['charging_state']}")   
            return True
        return False

    @property
    def is_at_home(self):
        self.__update_vehicle_data()  
        (lat,lon) = self.persistence.get_tesla_home_coords()
        if 'longitude' in self.drive_state and 'latitude' in self.drive_state:
            if abs(float(self.drive_state['longitude']) - lon) < 0.000100 and abs(float(self.drive_state['latitude'])  - lat) < 0.000100: 
                return True
        return False

    @property
    def may_stop_consuming(self):
        self.__update_vehicle_data()
        
        if not self.is_at_home:
            self.logger.info("Will not stop because car is not at home")
            self.status = "Niet thuis"
            return True
        return False

    @property
    def battery_level(self):
        self.__update_vehicle_data()
        if 'battery_level' in self.charge_state:
            return int(self.charge_state['battery_level'])
        else:
            return 0

    @property
    def est_battery_range(self):
        self.__update_vehicle_data()
        return self._est_battery_range

        