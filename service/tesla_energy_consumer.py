import logging
from typing import Tuple
from abc_energy_consumer import energy_consumer
from teslapy import Tesla
from persistence import persistence
from database_Logging_handler import database_logging_handler

class tesla_energy_consumer(energy_consumer):
    def __init__(self, db:persistence) -> None:
        self.persistence = db
        self.is_consuming = False
        self._consumption = 0
        self._name = "Tesla"
        
        self.logger = logging.getLogger(__name__)
        
        log_handler = logging.StreamHandler()
        log_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(log_handler)
        
        log_handler = database_logging_handler(self.persistence)
        log_handler.setLevel(logging.INFO)
        self.logger.addHandler(log_handler)

    def initialize(self, **kwargs):
        self.tesla = Tesla(kwargs['email'], kwargs['password'])
        self.tesla.captcha_solver = self.solve_captcha
        self.tesla.fetch_token()
        vehicles = self.tesla.vehicle_list()
        self.vehicle = vehicles[0]

    def solve_captcha(self, svg):
        with open('captcha.svg', 'wb') as f:
            f.write(svg)
        return input('Captcha: ')

    def __update_charging_state(self):
        if self.vehicle['state'] == 'asleep':
            self.vehicle.sync_wake_up()
        self.vehicle.get_vehicle_data()
        self.is_consuming = self.vehicle['charge_state']['charging_state'].lower() == 'charging'
        
    def consumer_is_consuming(self):
        return self.is_consuming
        
    def stop_consuming(self):
        if not self.may_stop_consuming():
            return

        if self.is_consuming:
            logging.info("Giving stop_charging command")    
            res = self.vehicle.command('STOP_CHARGE')
            logging.info(res)
            self.__update_charging_state()
            return self.is_consuming
        else:
            logging.info("Stop charging command is not needed. Vehicle wasn't charging")   
            
    def start_consuming(self):
        try:
            if not self.can_start_consuming():
                return
            self.logger.info("Giving start_charging command")
            res = self.vehicle.command('START_CHARGE')
            self.logger.info(res)
            self.__update_charging_state()
            return self.is_consuming
        except Exception as e:
            self.logger.error(e)

    def set_home_location(self):
        if self.vehicle['state'] == 'asleep':
            self.vehicle.sync_wake_up()
        self.vehicle.get_vehicle_data()
        #self.vehicle['driving_state']

    @property
    def consumption(self):
        self._consumption = self.persistence.get_consumer_consumption(self._name)
        return self._consumption
    @consumption.setter
    def consumption(self,value):
        self._consumption = value
        self.persistence.set_consumer_consumption(self._name, value)

    @property
    def start_above(self):
        self._start_above = self.persistence.get_consumer_start_above(self._name)
        return self._start_above
    @start_above.setter
    def start_above(self,value):
        self._start_above = value
        self.persistence.set_consumer_start_above(self._name, value)

    @property
    def stop_under(self):
        self._stop_under = self.persistence.get_consumer_stop_under(self._name)
        return self._stop_under
    @stop_under.setter
    def stop_under(self,value):
        self._stop_under = value
        self.persistence.set_consumer_stop_under(self._name, value)

    @property
    def isConsuming(self):
        return self.is_consuming
    
    @property
    def can_start_consuming(self):
        if self.vehicle['state'] == 'asleep':
            self.vehicle.sync_wake_up()
        self.vehicle.get_vehicle_data()
        
        if not self.is_at_home:
            self.logger.info("Cannot start because car is not at home")
            return False 

        if  self.is_disconnected:
            self.logger.info("Cannot start because car is not connected")
            return False

        if  self.is_consuming:
            self.logger.info("Cannot start because the vehicle is already charging")
            return False
            
        return True, ""

    @property
    def is_disconnected(self):
        if self.vehicle['charge_state']['charging_state'] == "Disconnected":
            self.logger.debug("Charging state is {}".format(self.vehicle['charge_state']['charging_state']))   
            return True
        return False

    @property
    def is_at_home(self):
        if abs(float(self.vehicle['driving_state']['longitude']) -  4.232935) < 0.000100 and abs(float(self.vehicle['driving_state']['latitude'])  - 51.936002) < 0.000100: 
            return True

    @property
    def may_stop_consuming(self):
        if self.vehicle['state'] == 'asleep':
            self.vehicle.sync_wake_up()
        self.vehicle.get_vehicle_data()

        if self.is_at_home:
            self.logger.info("Will not stop because car is not at home")
            return True
        return False