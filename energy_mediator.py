import logging
import threading
import time
import energy_producer
import logging
from abc_energy_consumer import energy_consumer
from model import model

class mediator:
    def __init__(self) -> None:
        pass

    def mediate_once(self, consumer : energy_consumer, data_model : model):
        command = ''
        if data_model.surplus >= 1000:
            data_model.surplus_delay_count += 1
        if data_model.surplus <= -1000:
            data_model.deficient_delay_count += 1

        if data_model.surplus_delay_count > data_model.surplus_delay_theshold:
            data_model.surplus_delay_count = 0
            try:
                consumer.start_charging()
                command = 'start_charging'
            except Exception as e:
                logging.error(e)

        if data_model.deficient_delay_count > data_model.deficient_delay_theshold:
            data_model.deficient_delay_count = 0
            try:
                consumer.stop_charging()
                command = 'stop_charging'
            except Exception as e:
                logging.error(e)
        return command

    def mediate(self, consumer : energy_consumer, producer : energy_producer, data_model : model):
        th = threading.Thread(target=producer.start_reading, daemon=True)
        th.start()

        while True:
            self.mediate_once(consumer, data_model)
            time.sleep(10)
