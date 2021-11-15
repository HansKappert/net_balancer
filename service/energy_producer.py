import time
import logging
from model import model
from service.P1datagram import P1datagram

class energy_producer:
    def __init__(self,current_reader, data_model : model, sleep_time=1) -> None:
        self.current_reader = current_reader
        self.state = 'stopped'
        self.sleep_time = sleep_time
        self.data_model = data_model

    def read_once(self, data_model : model):
        raw_data_array, errortxt = self.current_reader.read_data()
        
        datagram = P1datagram()
        datagram.fill(raw_data_array)
        if datagram.actual_electricity_power_delivered is not None:
            data_model.current_production = datagram.actual_electricity_power_delivered
        if datagram.actual_electricity_power_received is not None:
            data_model.current_consumption = datagram.actual_electricity_power_received

        logging.info("Smart meter data: Consuming {}W, Producing {}W. Surplus is {}".format(data_model.current_consumption,data_model.current_production,data_model.surplus))



    def start_reading(self):
        self.state = "running"
        while self.state == "running":
            self.read_once(self.data_model)
            logging.debug("Next reading is in {} seconds".format(self.sleep_time))
            time.sleep(self.sleep_time)

    def stop_reading(self):
        self.state = "stopped"

