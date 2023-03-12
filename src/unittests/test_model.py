import unittest   # The test framework
import threading
import time
from service.energy_producer import energy_producer
from unittests.P1reader_fake import P1reader
from common.model import model
from common.persistence import persistence

class Test_model(unittest.TestCase):
    def test_surplus1(self):
        db = persistence()
        data_model = model(db)
        data_model._past_surplusses = [-2000,-2000,-2000,-2000,-2000]
        av_surplus = data_model.average_surplus(5)
        self.assertEqual(av_surplus, -2000)


    def test_surplus2(self):
        db = persistence()
        data_model = model(db)
        data_model._past_surplusses = [-2000,-2000,-2000,-2000,10]
        av_surplus = data_model.average_surplus(5)
        self.assertEqual(av_surplus, None)

    

if __name__ == '__main__':
    unittest.main()