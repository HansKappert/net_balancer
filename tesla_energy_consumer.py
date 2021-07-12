import logging
from abc_energy_consumer import energy_consumer
from teslapy import Tesla

class tesla_energy_consumer(energy_consumer):
    def __init__(self, email,password) -> None:
        self.tesla = Tesla(email, password)
        self.tesla.fetch_token()
        vehicles = self.tesla.vehicle_list()
        self.vehicle = vehicles[0]


    def stop_charging(self):
        if self.vehicle['state'] == 'asleep':
            self.vehicle.sync_wake_up()
        self.vehicle.get_vehicle_data()
        if self.vehicle['charge_state']['charging_state'].lower() == 'charging':
            self.vehicle.command('STOP_CHARGE')


    def start_charging(self):
        try:
            self.vehicle.command('START_CHARGE')
        except Exception as e:
            print(e)
