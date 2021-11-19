import time
import os
import logging
from model import model
from service.P1datagram import P1datagram

class energy_producer:
    DATA_DUMP_FOLDER_NAME = "output"
    DATA_DUMP_FILE_NAME = DATA_DUMP_FOLDER_NAME + "/measurements.csv"

    def __init__(self,current_reader, data_model : model, sleep_time=1) -> None:
        self.current_reader = current_reader
        self.state = 'stopped'
        self.sleep_time = sleep_time
        self.data_model = data_model
        if not os.path.isdir(self.DATA_DUMP_FOLDER_NAME):
            os.makedirs(self.DATA_DUMP_FOLDER_NAME)
        if not os.path.exists(self.DATA_DUMP_FILE_NAME):
            with open(self.DATA_DUMP_FILE_NAME,"w") as f:
                self.write_datagram_to_file(dg = None,header = True)

    def read_once(self, data_model : model):
        raw_data_array, errortxt = self.current_reader.read_data()
        
        datagram = P1datagram()
        datagram.fill(raw_data_array)
        if datagram.actual_electricity_power_received is not None:
            data_model.current_production = datagram.actual_electricity_power_received
        if datagram.actual_electricity_power_delivered is not None:
            data_model.current_consumption =  datagram.actual_electricity_power_delivered

        logging.info("Smart meter data: Consuming {}W, Producing {}W. Surplus is {}".format(data_model.current_consumption,data_model.current_production,data_model.surplus))
        self.write_datagram_to_file(datagram, False)

    def write_datagram_to_file(self, dg : P1datagram, header : bool):
        line = \
            self.write_datagram_field(dg, "datetime_stamp"                          , header) + ";" + \
            self.write_datagram_field(dg, "nr_of_power_failures_any_phase"          , header) + ";" + \
            self.write_datagram_field(dg, "nr_of_long_power_failures_any_phase"     , header) + ";" + \
            self.write_datagram_field(dg, "actual_electricity_power_delivered"      , header) + ";" + \
            self.write_datagram_field(dg, "actual_electricity_power_received"       , header) + ";" + \
            self.write_datagram_field(dg, "meter_reading_delivered_by_client_low"   , header) + ";" + \
            self.write_datagram_field(dg, "meter_reading_delivered_by_client_normal", header) + ";" + \
            self.write_datagram_field(dg, "meter_reading_delivered_to_client_normal", header) + ";" + \
            self.write_datagram_field(dg, "meter_reading_delivered_to_client_low"   , header) + ";" + \
            self.write_datagram_field(dg, "power_failure_event_log"                 , header) + ";" + \
            self.write_datagram_field(dg, "nr_of_voltage_sags_in_phase_L1"          , header) + ";" + \
            self.write_datagram_field(dg, "nr_of_voltage_sags_in_phase_L2"          , header) + ";" + \
            self.write_datagram_field(dg, "nr_of_voltage_sags_in_phase_L3"          , header) + ";" + \
            self.write_datagram_field(dg, "nr_of_voltage_swells_in_phase_L1"        , header) + ";" + \
            self.write_datagram_field(dg, "nr_of_voltage_swells_in_phase_L2"        , header) + ";" + \
            self.write_datagram_field(dg, "nr_of_voltage_swells_in_phase_L3"        , header)
        with open(self.DATA_DUMP_FILE_NAME, 'a') as f:
            f.write(line + "\n")
            f.close()

    def write_datagram_field(self, dg : P1datagram, field_name : str, header : bool):
        if header:
            return field_name
        else:
            return str(eval("dg." + field_name))

    def start_reading(self):
        self.state = "running"
        while self.state == "running":
            self.read_once(self.data_model)
            logging.debug("Next reading is in {} seconds".format(self.sleep_time))
            time.sleep(self.sleep_time)

    def stop_reading(self):
        self.state = "stopped"

