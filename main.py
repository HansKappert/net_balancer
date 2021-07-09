import time
import argparse
import threading
from P1reader import P1reader
from energy_producer import energy_producer
from tesla_energy_consumer import energy_consumer

def main(consumer, producer):
    th = threading.Thread(target=producer.start_reading)
    th.start()

    while True:
        energy_surplus = producer.surpluss()
        if energy_surplus > 1000:
            consumer.start_charging()
        if energy_surplus < -1000:
            consumer.stop_charging()
        
        time.sleep(10000)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-u", "--user_email", type=str,
                    help="Tesla account user name (e-mail address)")
    ap.add_argument("-p", "--password", type=str,
                    help="Password of the Tesla account")
    ap.add_argument("-d", "--device_name", type=str,
                    help="tty device name as listed by ls /dev/tt*")
    args = ap.parse_args()

    if (args.user_email == "" or args.password == ""):
        print("Please specify your Tesla account credentials")
        quit()
    current_data_supplier = P1reader.P1reader(port=args.device_name)
    producer = energy_producer(current_data_supplier)
    consumer = energy_consumer(args.user_email, args.password)
    
    main(consumer, producer)
