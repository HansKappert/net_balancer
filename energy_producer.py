import P1data_interpreter
import time
import logging
from model import model

class energy_producer:
    def __init__(self,current_reader, data_model : model, sleep_time=1) -> None:
        self.current_reader = current_reader
        self.state = 'stopped'
        self.sleep_time = sleep_time
        self.data_model = data_model

    def read_once(self, data_model : model):
        raw_data_array, errortxt = self.current_reader.read_data()
        data = P1data_interpreter.raw_to_dictionary(raw_data_array)

        meter=0
        try:
            current_consumption      = int(data['1-0:1.7.0'])
            current_production = int(data['1-0:2.7.0'])
            self.data_model.surplus = current_production - current_consumption
            logging.info("Smart meter data: Consuming {}W, Producing {}W. Surplus is {}".format(current_consumption,current_production,self.data_model.surplus))
        except:
            self.data_model.surplus = 0


    def start_reading(self):
        self.state = "running"
        while self.state == "running":
            self.read_once(self.data_model)
            logging.debug("Next reading is in {} seconds".format(self.sleep_time))
            time.sleep(self.sleep_time)

    def stop_reading(self):
        self.state = "stopped"

