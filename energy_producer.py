import P1data_interpreter
import time
import logging

class energy_producer:
    def __init__(self,current_reader) -> None:
        default_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(level=logging.DEBUG, format=default_format)
        self.current_reader = current_reader
        self.surplus = 0
        self.state = 'stopped'

    
    def start_reading(self):
        self.state = "running"
        while self.state == "running":
            raw_data_array, errortxt = self.current_reader.read_data()
            data = P1data_interpreter.raw_to_dictionary(raw_data_array)

            meter=0
            try:
                huidig_afname      = data['1-0:1.7.0']
                huidige_teruglever = data['1-0:2.7.0']
                self.surplus = huidig_afname + huidige_teruglever
                time.sleep(1000)
            except:
                self.surplus = 0

    def stop_reading(self):
        self.state = "stopped"

    def surplus(self):
        return self.surplus
    