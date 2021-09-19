from logging import StreamHandler
from persistence import persistence

class database_logging_handler(StreamHandler):

    def __init__(self, db:persistence):
        StreamHandler.__init__(self)
        self._db = db
        

    def emit(self, record):
        msg = self.format(record)
        self._db.log_event(record.levelname, record.module, msg)