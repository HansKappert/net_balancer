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
        self.__update_charging_state()
        if self.is_consuming:
            logging.info("Giving stop_charging command")    
            res = self.vehicle.command('STOP_CHARGE')
            logging.info(res)
            self.__update_charging_state()
            return self.is_consuming
        else:
            logging.info("Stop charging command is not needed. Vehicle wasn't chargin")   
            
    def start_consuming(self):
        try:
            self.logger.debug("Fetching vehicle data")
            self.__update_charging_state()
            if  self.is_consuming:
                self.logger.info("Charging command is not needed. Vehicle already charging")
            else:
                self.logger.debug("Charging state is {}".format(self.vehicle['charge_state']['charging_state']))   
                self.logger.info("Giving start_charging command")
                res = self.vehicle.command('START_CHARGE')
                self.logger.info(res)
                self.__update_charging_state()
                return self.is_consuming
        except Exception as e:
            self.logger.error(e)

    @property
    def consumption(self):
        self._consumption = self.persistence.get_consumer_consumption(self._name)
        return self._consumption
    @consumption.setter
    def consumption(self,value):
        self._consumption = value
        self.persistence.set_consumer_consumption(self._name, value)

    @property
    def isConsuming(self):
        return self.is_consuming
    
