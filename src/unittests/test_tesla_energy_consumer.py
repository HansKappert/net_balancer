import unittest
import os
from common.persistence              import persistence
from service.tesla_energy_consumer   import tesla_energy_consumer

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
        self.assertEqual(tesla.charge_below_price(100, 0), 100)
        
        # Testing when price percentage is 100
        self.assertEqual(tesla.charge_below_price(100, 50), 50)
        
        # Testing when average price is 0
        self.assertEqual(tesla.charge_below_price(0, 50), 0)
        
        # Testing when average price is negative
        self.assertEqual(tesla.charge_below_price(-100, 50), -150)
        
        # Testing with different average prices and price percentages
        self.assertEqual(tesla.charge_below_price(200, 25), 150)
        self.assertEqual(tesla.charge_below_price(50, 75), 12.5)
        self.assertEqual(tesla.charge_below_price(75.5, 10), 67.95)

if __name__ == '__main__':
    unittest.main()