import unittest   # The test framework
import time
from unittests.fake_energy_consumer import fake_energy_consumer
from unittests.P1reader_fake import P1reader
from model import model
from persistence import persistence
from energy_mediator import mediator

class Test_energy_producer(unittest.TestCase):
    def test_mediate_start_charging(self):
        db = persistence()
        data_model = model(db)     
        data_model.surplus = 2000
        data_model.surplus_delay_theshold = 0
        consumer = fake_energy_consumer()
        energy_mediator = mediator()
        command = energy_mediator.mediate_once(consumer, data_model)
        self.assertEqual(command, "start_charging")

    def test_mediate_stop_charging(self):
        db = persistence()
        data_model = model(db)     
        data_model.surplus = -2000
        data_model._deficient_delay_theshold = 0
        consumer = fake_energy_consumer()
        energy_mediator = mediator()
        command = energy_mediator.mediate_once(consumer, data_model)
        self.assertEqual(command, "stop_charging")

if __name__ == '__main__':
    unittest.main()