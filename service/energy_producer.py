import service.P1data_interpreter
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
        data = service.P1data_interpreter.raw_to_dictionary(raw_data_array)

        meter=0
        # Often the data list does not contain then needed entries, so put it in a try/except block
        try:
            data_model.current_consumption = int(data['1-0:1.7.0'])
        except: 
            pass
        try:   
            data_model.current_production  = int(data['1-0:2.7.0'])
        except:
            pass

        logging.info("Smart meter data: Consuming {}W, Producing {}W. Surplus is {}".format(data_model.current_consumption,data_model.current_production,data_model.surplus))



    def start_reading(self):
        self.state = "running"
        while self.state == "running":
            self.read_once(self.data_model)
            logging.debug("Next reading is in {} seconds".format(self.sleep_time))
            time.sleep(self.sleep_time)

    def stop_reading(self):
        self.state = "stopped"

