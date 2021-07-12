import logging
import threading
import time
import energy_producer
import logging
from abc_energy_consumer import energy_consumer
from model import model

class mediator:

    def mediate(consumer : energy_consumer, producer : energy_producer, data_model : model):
        th = threading.Thread(target=producer.start_reading, daemon=True)
        th.start()

        while True:
            if data_model.surplus > 1000:
                logging.info("Giving start_charging command")
                try:
                    consumer.start_charging()
                except Exception as e:
                    logging.error(e)
            if data_model.surplus < -1000:
                logging.info("Giving stop_charging command")
                try:
                    consumer.stop_charging()
                except Exception as e:
                    logging.error(e)

            
            time.sleep(10)
