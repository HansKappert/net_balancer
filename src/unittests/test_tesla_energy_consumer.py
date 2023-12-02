import unittest
import os
from common.persistence              import persistence
from service.tesla_energy_consumer   import tesla_energy_consumer

from unittest.mock import Mock, patch
from common.model import model
from common.persistence import persistence

TESLA_ENERGY_CONSUMER_CLASS = 'service.tesla_energy_consumer.tesla_energy_consumer'

class TestBalance(unittest.TestCase):

    def setUp(self) -> None:
        self.db = persistence()
        
        self.tesla_consumer = tesla_energy_consumer(self.db)
        self.tesla_consumer.logger = Mock()

    def test_balance_below_threshold(self):
        """
        Test the case where the current battery level is below the balance threshold.
        It should then charge at full speed until battery level exceeds 'balance_above' setting
        """
        # Mock the necessary attributes and methods
        self.tesla_consumer.balance_above = 80
        self.tesla_consumer.max_consumption_power = 3600
        self.tesla_consumer._is_at_home = True
        self.tesla_consumer._is_disconnected = False
        self.tesla_consumer.charge_state = {'battery_level': '50',
                                            'charge_limit_soc': '90',
                                            'charging_state':'Connected'}
        self.tesla_consumer.vehicle = Mock()
        self.tesla_consumer.vehicle.get.return_value = {'battery_level': '50',
                                            'charge_limit_soc': '90',
                                            'charging_state':'Connected'}
        with patch('service.tesla_energy_consumer.tesla_energy_consumer._consume_at_maximum') as mock_method:
            mock_method.return_value = True
            result = self.tesla_consumer.balance(10, 20, -250)
            mock_method.assert_called_once()
        
        self.assertEqual(result, True)

    def test_balance_above_threshold(self):
        """
        Test the case where the current battery level is below the balance threshold.
        It should then charge at full speed until battery level exceeds 'balance_above' setting
        """
        # Mock the necessary attributes and methods
        self.tesla_consumer.balance_above = 20
        self.tesla_consumer.max_consumption_power = 3600
        self.tesla_consumer._is_at_home = True
        self.tesla_consumer._is_disconnected = False
        self.tesla_consumer.charge_state = {'battery_level': '50',
                                            'charge_limit_soc': '90',
                                            'charging_state':'Connected'}
        self.tesla_consumer.vehicle = Mock()
        self.tesla_consumer.vehicle.get.return_value = {'battery_level': '50',
                                            'charge_limit_soc': '90',
                                            'charging_state':'Connected'}
        # Call the balance method
        

        with patch(f'{TESLA_ENERGY_CONSUMER_CLASS}.can_consume_this_surplus') as mocked_method_can_consume_this_surplus:
            mocked_method_can_consume_this_surplus.return_value = True
            with patch(f'{TESLA_ENERGY_CONSUMER_CLASS}.start_consuming') as mocked_method_start_consuming:
                result = self.tesla_consumer.balance(10, 20, -250)
                mocked_method_can_consume_this_surplus.assert_called_once()
                mocked_method_start_consuming.assert_called_once()
                self.assertEqual(result, True)

class TestChargeBelowPrice(unittest.TestCase):
    
    def setUp(self):
        # Set up your environment variables here
        os.environ['TESLA_USER'] = 'hans.kappert@hetconsultancyhuis.nl'

    def tearDown(self):
        # Clean up any changes made to the environment variables
        del os.environ['TESLA_USER']

    def test_charge_below_price(self):
        db = persistence()
        tesla = tesla_energy_consumer(db)
        tesla_user = os.environ["TESLA_USER"]

        try:
            tesla.initialize(email=tesla_user)
        except Exception as e:
            print(e)            
        # Testing when price percentage is 0
        self.assertEqual(tesla.charge_below_price(100, 1), 1)
        
        # Testing when price percentage is 100
        self.assertEqual(tesla.charge_below_price(100, 50), 50)
        
        # Testing when average price is 0
        self.assertEqual(tesla.charge_below_price(0, 50), 0)
        
        # Testing when average price is negative
        self.assertEqual(tesla.charge_below_price(-100, 50), -150)
        
        # Testing with different average prices and price percentages
        self.assertEqual(tesla.charge_below_price(200, 25), 50)
        self.assertEqual(tesla.charge_below_price(50, 75), 37.5)
        self.assertEqual(tesla.charge_below_price(75.5, 90), 67.95)
        self.assertEqual(tesla.charge_below_price(0.09, 80), 0.07)

if __name__ == '__main__':
    unittest.main()