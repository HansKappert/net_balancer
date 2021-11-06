import logging
import threading
import time
import service.energy_producer
import logging
from abc_energy_consumer import energy_consumer
from model import model
from persistence import persistence
from database_Logging_handler import database_logging_handler

class mediator:
    def __init__(self) -> None:
        self.persistence = persistence()
        self.mediation_delay = 10
        self.logger = logging.getLogger(__name__)
        
        log_handler = logging.StreamHandler()
        log_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(log_handler)
        
        log_handler = database_logging_handler(self.persistence)
        log_handler.setLevel(logging.INFO)
        self.logger.addHandler(log_handler)

        pass

    def mediate_once(self, consumer : energy_consumer, data_model : model):
        # only one consumer now. Direct all surplus energy to that consumer
        if consumer.can_consume_this_surplus(data_model.surplus) or data_model.override == True:
            consumer.start_consuming(data_model.surplus)
        
        

    def mediate(self, consumer : energy_consumer, producer : service.energy_producer):
        data_model = model(self.persistence)

        th = threading.Thread(target=producer.start_reading, daemon=True)
        th.start()

        while True:
            self.mediate_once(consumer, data_model)
            time.sleep(self.mediation_delay)
