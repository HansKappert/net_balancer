import logging
import threading
import time
import energy_producer
import logging
from abc_energy_consumer import energy_consumer
from model import model
from persistence import persistence

class mediator:
    def __init__(self) -> None:
        pass

    def mediate_once(self, consumer : energy_consumer, data_model : model):
        command = ''
        
        if data_model.surplus >= 1500:
            data_model.surplus_delay_count += 1
            logging.info("data_model.surplus_delay_count is now {}".format(data_model.surplus_delay_count))
        #elif consumer.consumer_is_consuming() and data_model.surplus <= -1500:
        elif data_model.surplus <= -1500:
            data_model.deficient_delay_count += 1
            logging.info("data_model.deficient_delay_count is now {}".format(data_model.deficient_delay_count))
        elif data_model.surplus <= 800:
            data_model.deficient_delay_count = 0
            data_model.surplus_delay_count = 0

        if data_model.surplus_delay_count > data_model.surplus_delay_theshold:
            logging.debug("data_model.surplus_delay_theshold of {} exceeded".format(data_model.surplus_delay_theshold))
            data_model.surplus_delay_count = 0
            try:
                consumer.start_charging()
                command = 'start_charging'
            except Exception as e:
                logging.error(e)

        if data_model.deficient_delay_count > data_model.deficient_delay_theshold:
            logging.debug("data_model.deficient_delay_theshold of {} exceeded".format(data_model.deficient_delay_theshold))
            data_model.deficient_delay_count = 0
            try:
                consumer.stop_charging()
                command = 'stop_charging'
            except Exception as e:
                logging.error(e)
        return command

    def mediate(self, consumer : energy_consumer, producer : energy_producer):
        db = persistence()
        data_model = model(db)
        data_model.surplus_delay_theshold = 4
        data_model.deficient_delay_theshold = 4
        logging.debug ("Data model created")

        th = threading.Thread(target=producer.start_reading, daemon=True)
        th.start()

        while True:
            self.mediate_once(consumer, data_model)
            time.sleep(10)
