import unittest   # The test framework
import time
from unittests.fake_energy_consumer import fake_energy_consumer
from unittests.P1reader_fake import P1reader
from model import model
from energy_mediator import mediator

class Test_energy_producer(unittest.TestCase):
    def test_mediate_start_charging(self):
        data_model = model()
        data_model.surplus = 1000
        consumer = fake_energy_consumer()
        command = mediator.mediate_once(consumer, data_model)
        self.assertEqual(command, "start_charging")

    def test_mediate_stop_charging(self):
        data_model = model()
        data_model.surplus = -1000
        consumer = fake_energy_consumer()
        command = mediator.mediate_once(consumer, data_model)
        self.assertEqual(command, "stop_charging")

if __name__ == '__main__':
    unittest.main()