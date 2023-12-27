import unittest
from unittest.mock import MagicMock
from service.energy_mediator import mediator
from common.model import model
from common.persistence import persistence

class Test_mediator(unittest.TestCase):
    def setUp(self):
        self.db = persistence()
        self.mymodel = model(self.db)
        self.mediator = mediator(self.mymodel)


    def test_mediate_once_active_consumer_take_surplus(self):
        consumer = MagicMock()
        consumer.balance_activated = True
        consumer.balance.return_value = True
        self.mediator.data_model.add_consumer(consumer)
        self.mediator.data_model = MagicMock()
        self.mediator.data_model.consumers = [consumer]
        self.mediator.data_model.get_current_and_average_price.return_value = (10, 20)
        self.mediator.data_model.average_surplus.return_value = 500
        self.mediator.mediate_once()
        consumer.balance.assert_called()