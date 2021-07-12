import unittest   # The test framework
import threading
import time
from energy_producer import energy_producer
from unittests.P1reader_fake import P1reader
from model import model

class Test_energy_producer(unittest.TestCase):
    def test_surplus(self):
        current_data_supplier = P1reader(port="")
        data_model = model()
        producer = energy_producer(current_reader=current_data_supplier, data_model = data_model, sleep_time = 0.1)

        th = threading.Thread(target=producer.start_reading, daemon=True)
        th.start()
        time.sleep(0.2)
        self.assertEqual(data_model.surplus, 1200)


if __name__ == '__main__':
    unittest.main()