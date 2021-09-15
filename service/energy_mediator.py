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

        self.logger.info("Test")
        pass

    def mediate_once(self, consumer : energy_consumer, data_model : model):
        command = ''
        
        if data_model.surplus >= 0.6 * consumer.consumption:
            data_model.surplus_delay_count += self.mediation_delay
            self.logger.info("current surplus exceeds 0.6*power consumption (0.6*{}={})".format(consumer.consumption,0.6 * consumer.consumption))
            self.logger.info("data_model.surplus_delay_count is now {}".format(data_model.surplus_delay_count))
        #elif consumer.consumer_is_consuming() and data_model.surplus <= -1500:
        elif data_model.surplus <= -0.6*consumer.consumption:
            self.logger.info("current deficient exceeds -0.6*power consumption (-0.6*{}={})".format(consumer.consumption,-0.6 * consumer.consumption))
            data_model.deficient_delay_count += self.mediation_delay
            self.logger.info("data_model.deficient_delay_count is now {}".format(data_model.deficient_delay_count))
        elif data_model.surplus <= 800:
            data_model.deficient_delay_count = 0
            data_model.surplus_delay_count = 0

        if data_model.surplus_delay_count > data_model.surplus_delay_theshold:
            self.logger.debug("data_model.surplus_delay_theshold of {} exceeded".format(data_model.surplus_delay_theshold))
            data_model.surplus_delay_count = 0
            try:
                consumer.start_consuming()
                command = 'start_consuming'
            except Exception as e:
                self.logger.error(e)

        if data_model.deficient_delay_count > data_model.deficient_delay_theshold:
            self.logger.debug("data_model.deficient_delay_theshold of {} exceeded".format(data_model.deficient_delay_theshold))
            data_model.deficient_delay_count = 0
            try:
                consumer.stop_consuming()
                command = 'stop_consuming'
            except Exception as e:
                self.logger.error(e)
        
        if consumer.isConsuming == False and data_model.override == True:
            consumer.start_consuming()
            command = 'start_consuming'

        return command

    def mediate(self, consumer : energy_consumer, producer : service.energy_producer):
        data_model = model(self.persistence)

        th = threading.Thread(target=producer.start_reading, daemon=True)
        th.start()

        while True:
            self.mediate_once(consumer, data_model)
            time.sleep(self.mediation_delay)
