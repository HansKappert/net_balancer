import argparse
import logging
from unittests.P1reader_fake import P1reader
from energy_producer import energy_producer
from tesla_energy_consumer import tesla_energy_consumer
from energy_mediator import mediator
from model import model

if __name__ == "__main__":
        
    ap = argparse.ArgumentParser()
    ap.add_argument("-u", "--user_email", type=str,
                    help="Tesla account user name (e-mail address)")
    ap.add_argument("-p", "--password", type=str,
                    help="Password of the Tesla account")
    ap.add_argument("-d", "--device_name", type=str,
                    help="tty device name as listed by ls /dev/tt*")
    args = ap.parse_args()

    default_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    # loging level can be parameterized if needed. Fixed seting to DEBUG for now
    logging.basicConfig(level=logging.DEBUG, format=default_format)
    
    if (args.user_email == "" or args.password == ""):
        print("Please specify your Tesla account credentials")
        quit()

    data_model = model()
    current_data_supplier = P1reader(port=args.device_name)
    producer = energy_producer(current_reader=current_data_supplier, data_model = data_model)
    consumer = tesla_energy_consumer(args.user_email, args.password)
    mediator.mediate(consumer, producer, data_model)
