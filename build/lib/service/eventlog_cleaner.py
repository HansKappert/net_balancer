import time
from common.persistence import persistence

class eventlog_cleaner:
    def __init__(self, database) -> None:
        self.persistence = database
        pass

    def start(self):
        while True:
            self.persistence.remove_old_log_lines()
            time.sleep(1000000)
