from abc import ABC, abstractmethod

class P1data_reader(ABC):
    @abstractmethod
    def __init__(self, port):
        pass

    @abstractmethod
    def read_data(self):
        pass

