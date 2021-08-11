import argparse
import logging
# from unittests.P1reader_fake import P1reader
from P1reader import P1reader
from energy_producer import energy_producer
from tesla_energy_consumer import tesla_energy_consumer
from energy_mediator import mediator
from model import model
from persistence import persistence

if __name__ == "__main__":
        
    
    ap = argparse.ArgumentParser()
    ap.add_argument("-u", "--user_email", type=str,
                    help="Tesla account user name (e-mail address)")
    ap.add_argument("-p", "--password", type=str,
                    help="Password of the Tesla account")
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
        
    if (args.user_email == None or args.password == None):
        print("Please specify your Tesla account credentials")
        quit()

    if (args.device_name == None):
        print("Please specify the Smart Meter device name")
        quit()

    logging.debug ("User name    : " + args.user_email)
    logging.debug ("User password is secret, remember")
    logging.debug ("Device name  : " + args.device_name)
    db = persistence()
    data_model = model(db)
    logging.debug ("Data model created")
    current_data_supplier = P1reader(port=args.device_name)
    logging.debug ("Data supplier reader is setup")
    producer = energy_producer(current_reader=current_data_supplier, data_model = data_model, sleep_time = 10)
    logging.debug ("Energy producer is setup")
    consumer = tesla_energy_consumer(args.user_email, args.password)
    logging.debug ("Energy consumer is setup")
    energy_mediator = mediator()
    logging.debug ("Mediator is created. Starting mediation")
    energy_mediator.mediate(consumer=consumer, producer=producer)
