import logging
from abc_energy_consumer import energy_consumer
from teslapy import Tesla

class tesla_energy_consumer(energy_consumer):
    def __init__(self, email,password) -> None:
        self.tesla = Tesla(email, password)
        self.tesla.captcha_solver = self.solve_captcha
        self.tesla.fetch_token()
        vehicles = self.tesla.vehicle_list()
        self.vehicle = vehicles[0]


    def solve_captcha(self, svg):
        with open('captcha.svg', 'wb') as f:
            f.write(svg)
        return input('Captcha: ')

    def stop_charging(self):
        if self.vehicle['state'] == 'asleep':
            self.vehicle.sync_wake_up()
        self.vehicle.get_vehicle_data()
        if self.vehicle['charge_state']['charging_state'].lower() == 'charging':
            logging.info("Giving stop_charging command")    
            self.vehicle.command('STOP_CHARGE')
        else:
            logging.info("Stop charging command is not needed. Vehicle wasn't chargin")   
            


    def start_charging(self):
        try:
            logging.debug("Fetching vehicle data")
            self.vehicle.get_vehicle_data()     
            if self.vehicle['charge_state']['charging_state'].lower() != 'charging':
                logging.debug("Charging state is", self.vehicle['charge_state']['charging_state'])   
                logging.info("Giving start_charging command")
                self.vehicle.command('START_CHARGE')
            else:
                logging.info("Charging command is not needed. Vehicle already charging")
        except Exception as e:
            print(e)
