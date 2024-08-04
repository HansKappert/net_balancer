import push_services.abc_push_service as abc_push_service
import requests
from  push_services.abc_push_service import push_message_type

class push_service(abc_push_service.push_service):

    def __init__(self):
        super().__init__()
        pass   

    def send_message(self, message="", description="", type:push_message_type=None, **kwargs):
        type = str(type)
        res = requests.post('https://api.mynotifier.app', {
            "apiKey": self.api_key,
            "message": message,
            "description": description,
            "type": str(type),
        })
        print(res)
        