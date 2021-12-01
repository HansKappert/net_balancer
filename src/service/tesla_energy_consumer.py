import logging
from typing import Tuple
from abc_energy_consumer import energy_consumer
from teslapy import Tesla
from teslapy import VehicleError
from teslapy import RequestException
from persistence import persistence
from database_Logging_handler import database_logging_handler

class tesla_energy_consumer(energy_consumer):
    def __init__(self, db:persistence) -> None:
        self.persistence = db
        self.is_consuming = False
        self._consumption = 0
        self._name = "Tesla"
        self.voltage = 230
        self._consumption_amps_now = 0
        self.charge_state = {}
        self.drive_state = {}
        
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
        if self.vehicle['state'] == 'asleep':
            self.vehicle.sync_wake_up()
        self.vehicle.get_vehicle_data()
        self.charge_state = self.vehicle['charge_state']
        self.drive_state = self.vehicle['drive_state']
        self.is_consuming = self.charge_state['charging_state'].lower() == 'charging'
        self._consumption_amps_now = self.charge_state['charger_actual_current']
        self.latitude_current = float(self.drive_state['latitude'])
        self.longitude_current = float(self.drive_state['longitude'])
        self.persistence.set_tesla_current_coords(self.latitude_current, self.longitude_current)            
        self.persistence.set_consumer_consumption_now(self._name, self.consumption_amps_now)


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
            
    def start_consuming(self, surplus_power, at_maximum):

        try:
            
            old_charging_current = 0 if self.charge_state['charger_actual_current'] is None else self.charge_state['charger_actual_current']
            # calculate what the new charging current needs to be. 
            power_max = self.persistence.get_consumer_consumption_max(self._name) 
            if at_maximum:                
                new_charging_current = self.calc_new_charge_current(0, power_max, power_max)
            else:
                new_charging_current = self.calc_new_charge_current(old_charging_current, power_max, surplus_power)
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

        
    def can_consume_this_surplus(self, surplus_power, at_maximum):
        if (self.persistence.get_consumer_disabled('Tesla') == 1):
            return False

        self.__update_vehicle_data()
        if not self.can_start_consuming: # property will call self.__update_vehicle_data()
            return False

        if int(self.charge_state['battery_level']) >= int(self.charge_state['charge_limit_soc']):
            return False

        old_charging_current = 0 if self.charge_state['charger_actual_current'] is None else self.charge_state['charger_actual_current']

        max_power_consumption = self.persistence.get_consumer_consumption_max(self._name)
        if surplus_power < max_power_consumption or at_maximum == True:
            return True
        return False

    def calc_new_charge_current(self, charger_actual_current, power_max, surplus_power):
            surplus_amp = int(surplus_power / self.voltage)
            amps_new = charger_actual_current + surplus_amp
            if amps_new * self.voltage > power_max:
                amps_new = int(power_max / self.voltage)
            if amps_new < 0:
                amps_new = 0
            return amps_new

    def __set_charge_current(self, amps):
        if amps >= 0:
            self.vehicle.command("CHARGING_AMPS",charging_amps=amps)
            self.__update_vehicle_data()

    @property
    def consumption(self):
        self._consumption = self.persistence.get_consumer_consumption_max(self._name)
        return self._consumption
    @consumption.setter
    def consumption(self,value):
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
        return self._consumption_amps_now
    
    @property
    def consumption_power_now(self):
        return self.consumption_amps_now * self.voltage
    
    @property
    def override_activated(self):
        return self.persistence.get_consumer_override(self._name)

    @property
    def can_start_consuming(self):
        self.__update_vehicle_data()
        
        if not self.is_at_home:
            self.logger.info("Cannot start because car is not at home")
            return False 

        if  self.is_disconnected:
            self.logger.info("Cannot start because car is not connected")
            return False

        #if  self.is_consuming:
        #    self.logger.info("Cannot start because the vehicle is already charging")
        #    return False
            
        return True, ""

    # make sure you've done self.__update_vehicle_data() before using this property
    @property
    def is_disconnected(self):
        if self.charge_state['charging_state'] == "Disconnected":
            self.logger.debug("Charging state is {}".format(self.vehicle['charge_state']['charging_state']))   
            return True
        return False

    # make sure you've done self.__update_vehicle_data() before using this property
    @property
    def is_at_home(self):
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