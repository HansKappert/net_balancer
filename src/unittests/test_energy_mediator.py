import unittest   # The test framework
import time
from unittests.fake_energy_consumer import fake_energy_consumer
from unittests.P1reader_fake import P1reader
from common.model import model
from persistence import persistence
from service.energy_mediator import mediator

class test_energy_producer(unittest.TestCase):

    # Als er meer dan 60% van het verbruik over is, dan verhoog je de surplus teller
    # Als de teller boven de grens komt, start je het laden

    def test_mediate_start_consuming(self):
        db = persistence()
        data_model = model(db)     
        data_model.surplus = 600
        data_model.log_retention = 0
        data_model.surplus_delay_count = 0
        consumer = fake_energy_consumer(db)
        consumer.consumption = 1000
        energy_mediator = mediator()
        command = energy_mediator.mediate_once(consumer, data_model)
        self.assertEqual(command, "start_consuming")
        self.assertEqual(data_model.surplus_delay_count, 0)

    def test_mediate_dont_start_consuming(self):
        db = persistence()
        data_model = model(db)     
        data_model.surplus = 599
        data_model.log_retention = 0
        data_model.surplus_delay_count = 0
        consumer = fake_energy_consumer(db)
        consumer.consumption = 1000
        energy_mediator = mediator()
        command = energy_mediator.mediate_once(consumer, data_model)
        self.assertEqual(command, "")
        self.assertEqual(data_model.surplus_delay_count, 0)

    def test_mediate_increase_surplus_delay_count_1(self):
        db = persistence()
        data_model = model(db)     
        data_model.surplus = 2000
        data_model.log_retention = 10
        data_model.surplus_delay_count = 0
        consumer = fake_energy_consumer(db)
        consumer.consumption = 2000
        energy_mediator = mediator()
        command = energy_mediator.mediate_once(consumer, data_model)
        self.assertEqual(data_model.surplus_delay_count, 10)
        

    def test_mediate_stop_consuming(self):
        db = persistence()
        data_model = model(db)     
        data_model.surplus = -600
        data_model.deficient_delay_theshold = 0
        data_model.deficient_delay_count = 0
        consumer = fake_energy_consumer(db)
        consumer.consumption = 1000
        consumer.is_consuming = True
        energy_mediator = mediator()
        command = energy_mediator.mediate_once(consumer, data_model)
        self.assertEqual(command, "stop_consuming")

    def test_mediate_dont_stop_consuming(self):
        db = persistence()
        data_model = model(db)     
        data_model.surplus = -599
        data_model.deficient_delay_theshold = 0
        data_model.deficient_delay_count = 0
        consumer = fake_energy_consumer(db)
        consumer.consumption = 1000
        consumer.is_consuming = True
        energy_mediator = mediator()
        command = energy_mediator.mediate_once(consumer, data_model)
        self.assertEqual(command, "")

if __name__ == '__main__':
    unittest.main()