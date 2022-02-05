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
        self._est_battery_range = 0
        
        self.logger = logging.getLogger(__name__)
        
        log_handler = logging.StreamHandler()
        log_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(log_handler)
        
        log_handler = database_logging_handler(self.persistence)
        log_handler.setLevel(logging.INFO)
        self.logger.addHandler(log_handler)

    def initialize(self, **kwargs):
        self.tesla = Tesla(kwargs['email'])
        self.tesla.captcha_solver = self.solve_captcha
        self.tesla.fetch_token()
        vehicles = self.tesla.vehicle_list()
        self.vehicle = vehicles[0]

    def solve_captcha(self, svg):
        with open('captcha.svg', 'wb') as f:
            f.write(svg)
        return input('Captcha: ')

    def __update_vehicle_data(self):
        diff = datetime.now() - self._last_vehicle_data_update
        if diff.total_seconds() < 5 and len(self.drive_state) > 0: 
            return
        if self.vehicle['state'] == 'asleep':
            self.vehicle.sync_wake_up()
        
        self._last_vehicle_data_update = datetime.now()
        
        try:
            self.vehicle.get_vehicle_data()
            self.charge_state = self.vehicle['charge_state']
            self.drive_state = self.vehicle['drive_state']
            self.is_consuming = self.charge_state['charging_state'].lower() == 'charging'
            self._consumption_amps_now = self.charge_state['charger_actual_current']
            self._est_battery_range = self.dist_units(self.charge_state['est_battery_range'])
            self.latitude_current = float(self.drive_state['latitude'])
            self.longitude_current = float(self.drive_state['longitude'])

            self.persistence.set_tesla_current_coords(self.latitude_current, self.longitude_current)            
            self.persistence.set_consumer_consumption_now(self._name, self.consumption_amps_now)
        except Exception as e:
            self.logger.debug("Error during getting vehicle data: " + str(e))
            return        


    def consumer_is_consuming(self):
        return self.is_consuming
        
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
            return self.is_consuming
        except Exception as e:
            self.logger.error(e)

    def set_home_location(self):
        self.__update_vehicle_data()
        
    def can_consume_this_surplus(self, surplus_power, is_activated):

        if is_activated == False:
            self.logger.info("Het balanceren voor de gebruiker Tesla is uitgeschakeld")
            return False

        if not self.can_start_consuming: # property will call self.__update_vehicle_data()
            return False

        if int(self.charge_state['battery_level']) >= int(self.charge_state['charge_limit_soc']):
            self.logger.info("Tesla is opgeladen tot het opgegeven maximum")
            return False

        old_charging_current = 0 if self.charge_state['charger_actual_current'] is None else self.charge_state['charger_actual_current']

        max_power_consumption = self.persistence.get_consumer_consumption_max(self._name)
        
        if surplus_power < max_power_consumption:
            return True
        return False

    def get_current(self, power):
        return int(power / self.voltage)


    def calc_new_charge_current(self, charger_actual_current, surplus_power):
        amps_new = charger_actual_current + self.get_current(surplus_power)
        amps_new = max(0, amps_new)
        amps_new = min(self.get_current(self.max_consumption_power),amps_new)
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
    def max_consumption_power(self):
        self._consumption = self.persistence.get_consumer_consumption_max(self._name)
        return self._consumption
    @max_consumption_power.setter
    def max_consumption_power(self,value):
        self._consumption = value
        self.persistence.set_consumer_consumption_max(self._name, value)


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
        if value == 0:
            max_power_consumption = self.persistence.get_consumer_consumption_max(self._name)
            max_current_consumption = self.get_current(max_power_consumption)
            self.__set_charge_current(max_current_consumption)

    @property
    def can_start_consuming(self):
        self.__update_vehicle_data()
        
        if not self.is_at_home:
            self.logger.info("Kan niet laden want de Tesla is niet op de thuislokatie")
            return False 

        if  self.is_disconnected:
            self.logger.info("Kan niet laden want de Tesla is niet aangesloten")
            return False

        return True, ""

    
    @property
    def is_disconnected(self):
        self.__update_vehicle_data()  
        if self.charge_state['charging_state'] == "Disconnected":
            self.logger.debug("Charging state is {}".format(self.vehicle['charge_state']['charging_state']))   
            return True
        return False

    @property
    def is_at_home(self):
        self.__update_vehicle_data()  
        (lat,lon) = self.persistence.get_tesla_home_coords()
        if abs(float(self.drive_state['longitude']) - lon) < 0.000100 and abs(float(self.drive_state['latitude'])  - lat) < 0.000100: 
            return True
        return False

    @property
    def may_stop_consuming(self):
        self.__update_vehicle_data()
        
        if not self.is_at_home:
            self.logger.info("Will not stop because car is not at home")
            return True
        return False

    @property
    def battery_level(self):
        self.__update_vehicle_data()
        return int(self.charge_state['battery_level'])

    @property
    def est_battery_range(self):
        self.__update_vehicle_data()
        return self._est_battery_range

        