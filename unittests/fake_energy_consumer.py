import logging
from abc_energy_consumer import energy_consumer

class fake_energy_consumer(energy_consumer):
    def __init__(self) -> None:
        pass

    def stop_charging(self):
        pass

    def start_charging(self):
        pass