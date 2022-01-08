import logging
import os 

from flask import Flask

from common.model import model
from common.persistence import persistence
from common.database_logging_handler import database_logging_handler

from service.tesla_energy_consumer import tesla_energy_consumer


app = Flask(__name__)
app.config['SECRET_KEY'] = 'HeelLekkerbeLangrijk'

db = persistence()
data_model = model(db)
tesla = tesla_energy_consumer(db)

tesla_user = os.environ["TESLA_USER"]
try:
    tesla.initialize(email=tesla_user)
except Exception as e:
    logging.exception(e)
data_model.add_consumer(tesla)

logger = logging.getLogger(__name__)

log_handler = logging.StreamHandler()
log_handler.setLevel(logging.DEBUG)
logger.addHandler(log_handler)

log_handler = database_logging_handler(db)
log_handler.setLevel(logging.INFO)
logger.addHandler(log_handler)

import web_pages
import web_api

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=8081,debug=True)
    # app.run(host='0.0.0.0',port=8081,debug=True, use_debugger=False, use_reloader=False, passthrough_errors=True)
