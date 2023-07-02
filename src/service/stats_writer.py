from datetime import datetime
import time
import logging

from common.model       import model
from common.persistence import persistence
from common.database_logging_handler  import database_logging_handler


class stats_writer:

    def __init__(self, data_model : model, persistence : persistence) -> None:
        self.data_model = data_model
        self.persistence = persistence
        self.state = "stopped"        
        self.logger = logging.getLogger(__name__)

        log_handler = logging.StreamHandler()
        log_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(log_handler)

        log_handler = database_logging_handler(self.persistence)
        log_handler.setLevel(logging.INFO)
        self.logger.addHandler(log_handler)


        

    def write_stats(self):
        when = datetime.now()
        current_price_kwh                            = self.persistence.get_price_at_datetime(when)
        if current_price_kwh is not None:
            current_price_kwm                        = current_price_kwh / 60   # price in euro
            current_price_kw10s                      = current_price_kwm / 6
            current_price_w10s                       = current_price_kw10s / 1000
            tesla_consumption                        = self.data_model.get_consumer("Tesla").consumption_power_now
            tesla_cost                               = tesla_consumption * current_price_w10s
            consumption                              = self.data_model.current_consumption
            tesla_consumption                        = self.data_model.get_consumer("Tesla").consumption_power_now
            production                               = self.data_model.current_production
            gas_reading                              = self.data_model.current_gas_reading
            meter_reading_delivered_to_client_low    = self.data_model.meter_reading_delivered_to_client_low
            meter_reading_delivered_to_client_normal = self.data_model.meter_reading_delivered_to_client_normal
            meter_reading_delivered_by_client_low    = self.data_model.meter_reading_delivered_by_client_low
            meter_reading_delivered_by_client_normal = self.data_model.meter_reading_delivered_by_client_normal
            
            self.logger.debug(f"KWh price={current_price_kwh}, consumption={consumption} tesla_cost={tesla_cost} gas_reading={gas_reading} el_low={meter_reading_delivered_to_client_low} el_normal={meter_reading_delivered_to_client_normal} el_delivered_low={meter_reading_delivered_by_client_low} el_delivered_normal={meter_reading_delivered_by_client_normal}")
            self.persistence.write_statistics(
                                    when,
                                    production,
                                    consumption,
                                    tesla_consumption,                                    
                                    current_price_kwh,                                    
                                    tesla_cost,
                                    gas_reading,
                                    meter_reading_delivered_to_client_low,
                                    meter_reading_delivered_to_client_normal,
                                    meter_reading_delivered_by_client_low,
                                    meter_reading_delivered_by_client_normal
                                    )
        else:
            self.logger.info("Geen prijsinformatie bekend voor dit tijdstip.")

    def start(self):
        self.state = "running"
        while self.state == "running":
            self.logger.debug("Writing statistics...")
            self.write_stats()
            time.sleep(10)
        self.logger.debug("Statistics writer ended.")

    def stop(self):
        self.logger.debug("Stopping statistics writer.")
        self.state = "stopped"

