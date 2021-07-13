import unittest   # The test framework
import threading
import time
from energy_producer import energy_producer
from unittests.P1reader_fake import P1reader
from model import model

class Test_energy_producer(unittest.TestCase):
    def test_surplus1(self):
        current_data_supplier = P1reader(port="",huidig_afname=0, huidige_teruglever=1200)
        data_model = model()
        producer = energy_producer(current_reader=current_data_supplier, data_model = data_model, sleep_time = 0.1)

        th = threading.Thread(target=producer.start_reading, daemon=True)
        th.start()
        time.sleep(0.2)
        self.assertEqual(data_model.surplus, 1200)


    def test_surplus2(self):
        current_data_supplier = P1reader(port="",huidig_afname=1000, huidige_teruglever=100)
        data_model = model()
        producer = energy_producer(current_reader=current_data_supplier, data_model = data_model, sleep_time = 0.1)

        th = threading.Thread(target=producer.start_reading, daemon=True)
        th.start()
        time.sleep(0.2)
        self.assertEqual(data_model.surplus, -900)

    def test_surplus3(self):
        current_data_supplier = P1reader(port="",huidig_afname=1000, huidige_teruglever=0)
        data_model = model()
        producer = energy_producer(current_reader=current_data_supplier, data_model = data_model, sleep_time = 0.1)

        th = threading.Thread(target=producer.start_reading, daemon=True)
        th.start()
        time.sleep(0.2)
        self.assertEqual(data_model.surplus, -1000)

if __name__ == '__main__':
    unittest.main()