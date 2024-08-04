from abc import ABC, abstractmethod
import requests
import os

class push_message_type:
    info    = "info"
    error   = "error"
    warning = "warning"
    success = "success"
class push_service(ABC):
    @abstractmethod
    def __init__(self):
        self.api_key = os.environ.get("PUSH_SERVICE_API_KEY")
        pass

    @abstractmethod
    def send_message(self, message="", description="", type:push_message_type=None, **kwargs):
        pass
