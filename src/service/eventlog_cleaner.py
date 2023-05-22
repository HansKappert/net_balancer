import time
from common.persistence import persistence

class eventlog_cleaner:
    def __init__(self, database) -> None:
        self.persistence = database
        pass

    def start(self):
        while True:
            # sleep for 30 seconds
            time.sleep(30) # don't start immediately. Give other processes some time to do more urgent stuff
            self.persistence.remove_old_log_lines()
