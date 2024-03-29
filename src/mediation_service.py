import argparse
import logging
import threading
import os

from service.P1reader_stub           import P1reader_stub
from service.P1reader                import P1reader
from service.energy_producer         import energy_producer
from service.tesla_energy_consumer   import tesla_energy_consumer
from service.eventlog_cleaner        import eventlog_cleaner
from service.energy_mediator         import mediator
from service.stats_writer            import stats_writer
from service.cum_stats_writer        import cum_stats_writer
from service.prices_writer           import prices_writer
from common.model                    import model
from common.persistence              import persistence
from common.database_logging_handler import database_logging_handler

if __name__ == "__main__":
        
    logger = logging.getLogger(__name__)
        
    ap = argparse.ArgumentParser()
    
    ap.add_argument("-d", "--device_name", type=str,
                    help="tty device name as listed by ls /dev/tt*")
    ap.add_argument("-l", "--loglevel", type=str,
                    help="logging level: d=debug, i=info, w=warning, e=error")
    args = ap.parse_args()


    db = persistence()
    data_model = model(db)

    level_translator = {
        'd': logging.DEBUG,
        'i': logging.INFO,
        'w': logging.WARN,
        'e': logging.ERROR
    }
    default_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=default_format)

    log_handler = logging.StreamHandler()
    log_handler.setLevel(level_translator[args.loglevel])
    logging.getLogger().addHandler(log_handler)
    
    log_handler = database_logging_handler(db)
    log_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(log_handler)

    
    if (args.device_name == None):
        logger.error("Please specify the Smart Meter device name")
        quit()


    logger.info ("Device name  : " + args.device_name)

    if args.device_name == "stub":
        current_data_supplier = P1reader_stub("none")
    else:
        current_data_supplier = P1reader(port=args.device_name)
    logger.info ("Data supplier reader is setup")
    
    producer = energy_producer(current_reader=current_data_supplier, data_model = data_model, sleep_time = 10)
    logger.info ("Energy producer is setup")

    if "TESLA_USER" in os.environ:
        tesla = tesla_energy_consumer(db)
        tesla_user = os.environ["TESLA_USER"]

        try:
            tesla.initialize(email=tesla_user)
        except Exception as e:
            print(e)
            logger.exception(e)
        data_model.add_consumer(tesla)
    else:
        logger.warning("Please set TESLA_USER environment variable")
    logger.debug ("Data model created")

    # Start some background processes
    cleaner = eventlog_cleaner(db)
    th = threading.Thread(target=cleaner.start, daemon=True)
    th.start()
    logger.info ("Eventlog table cleaner is setup")

    priceswriter = prices_writer(db)
    th = threading.Thread(target=priceswriter.start, daemon=True)
    th.start()
    logger.info ("Prices writer is setup")

    statswriter = stats_writer(data_model,db)
    th = threading.Thread(target=statswriter.start, daemon=True)
    th.start()
    logger.info ("Stats writer is setup")

    cum_statswriter = cum_stats_writer(db)
    th = threading.Thread(target=cum_statswriter.start, daemon=True)
    th.start()
    logger.info ("Cum_stats writer is setup")

    logger.info ("Energy consumer is setup")
    energy_mediator = mediator(data_model) # a list of consumers is part of this data model
    logger.info ("Mediator is created. Starting mediation")
    energy_mediator.mediate(producer=producer)

