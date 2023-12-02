import unittest
import os
from service.tesla_energy_consumer   import tesla_energy_consumer
from unittest.mock import Mock, patch
from common.model import model
from common.persistence import persistence

TESLA_ENERGY_CONSUMER_CLASS = 'service.tesla_energy_consumer.tesla_energy_consumer'

class TestBalance(unittest.TestCase):

    def setUp(self) -> None:
        self.db = persistence()
        self.tesla_consumer = tesla_energy_consumer(self.db)
        from dotenv import find_dotenv, load_dotenv

        success = load_dotenv(dotenv_path="src/unittests/.env", verbose=True)

        print(success)
        tesla_user = os.environ["TESLA_USER"]
        #tesla_user = 'hans.kappert@hetconsultancyhuis.nl'
        self.tesla_consumer.initialize(email=tesla_user)
        

    def test_balance_below_threshold(self):
        """
        Test the case where the current battery level is below the balance threshold.
        It should then charge at full speed until battery level exceeds 'balance_above' setting
        """
        self.tesla_consumer.balance_above = 80
        self.tesla_consumer.max_consumption_power = 3600
        result = self.tesla_consumer.balance(0.10, 0.20, -250) 
        self.assertEqual(result, True)

    def test_balance_above_threshold(self):
        """
        Test the case where the current battery level is below the balance threshold.
        It should then charge at full speed until battery level exceeds 'balance_above' setting
        """
        # Mock the necessary attributes and methods
        self.tesla_consumer.balance_above = 20
        self.tesla_consumer.max_consumption_power = 3600
        result = self.tesla_consumer.balance(10, 20, -250)
        self.assertEqual(result, True)


if __name__ == '__main__':
    unittest.main()