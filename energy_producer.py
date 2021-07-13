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
            huidig_afname      = int(data['1-0:1.7.0'])
            huidige_teruglever = int(data['1-0:2.7.0'])
            self.data_model.surplus = huidige_teruglever - huidig_afname
        except:
            self.data_model.surplus = 0


    def start_reading(self):
        self.state = "running"
        while self.state == "running":
            self.read_once(self.data_model)
            time.sleep(self.sleep_time)

    def stop_reading(self):
        self.state = "stopped"

