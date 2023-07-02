import time
import logging
from common.persistence import persistence
from common.database_logging_handler import database_logging_handler

class eventlog_cleaner:
    def __init__(self, database) -> None:
        self.persistence = database
        self.logger = logging.getLogger(__name__)
        
        log_handler = logging.StreamHandler()
        log_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(log_handler)

        log_handler = database_logging_handler(self.persistence)
        log_handler.setLevel(logging.INFO)
        self.logger.addHandler(log_handler)


        pass

    def start(self):
        while True:
            # sleep for 5 minutes
            time.sleep(300) # don't start immediately. Give other processes some time to do more urgent stuff
            result = self.persistence.remove_old_log_lines()
            if result and result.rowcount:
                self.logger.info(f"Removed {result.rowcount} lines from eventlog")
            else:
                self.logger.info(f"Nothing removed from eventlog")

