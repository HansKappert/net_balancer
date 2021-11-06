import argparse
import logging
import threading
# from unittests.P1reader_fake import P1reader
from service.P1reader_stub import P1reader_stub
from service.P1reader import P1reader
from service.energy_producer import energy_producer
from service.tesla_energy_consumer import tesla_energy_consumer
from service.energy_mediator import mediator
from model import model
from persistence import persistence
from service.eventlog_cleaner import eventlog_cleaner

if __name__ == "__main__":
        
    
    ap = argparse.ArgumentParser()
    ap.add_argument("-u", "--user_email", type=str,
                    help="Tesla account user name (e-mail address)")
    ap.add_argument("-d", "--device_name", type=str,
                    help="tty device name as listed by ls /dev/tt*")
    ap.add_argument("-l", "--loglevel", type=str,
                    help="logging level: d=debug, i=info, w=warning, e=error")
    args = ap.parse_args()

    default_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    if args.loglevel == None or args.loglevel == 'i':
        logging.basicConfig(level=logging.INFO, format=default_format)
    elif args.loglevel == 'd':
        logging.basicConfig(level=logging.DEBUG, format=default_format)
    elif args.loglevel == 'w':
        logging.basicConfig(level=logging.WARN, format=default_format)
    elif args.loglevel == 'e':
        logging.basicConfig(level=logging.ERROR, format=default_format)
    
    if (args.user_email == None):
        print("Please specify your Tesla account credentials")
        quit()

    if (args.device_name == None):
        print("Please specify the Smart Meter device name")
        quit()

    logging.debug ("User name    : " + args.user_email)
    logging.debug ("Device name  : " + args.device_name)
    db = persistence()
    data_model = model(db)

    if args.device_name == "stub":
        current_data_supplier = P1reader_stub("none")
    else:
        current_data_supplier = P1reader(port=args.device_name)
    logging.debug ("Data supplier reader is setup")
    producer = energy_producer(current_reader=current_data_supplier, data_model = data_model, sleep_time = 10)
    logging.debug ("Energy producer is setup")

    consumer = tesla_energy_consumer(db)
    try:
        consumer.initialize(email=args.user_email)
    except Exception as e:
        logging.exception(e)
    data_model.add_consumer(consumer)
    logging.debug ("Data model created")

    logging.debug ("Energy consumer is setup")
    energy_mediator = mediator()
    logging.debug ("Mediator is created. Starting mediation")

    cleaner = eventlog_cleaner()
    th = threading.Thread(target=cleaner.start, daemon=True)
    th.start()
    energy_mediator.mediate(consumer=consumer, producer=producer)

