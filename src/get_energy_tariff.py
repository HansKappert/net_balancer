import requests
import urllib.parse
import json

from datetime import datetime, timedelta
from_date  = datetime(2022,10,31,0,0,0,0) # price van 31 okt.
end_date   = from_date + timedelta(hours=23)
base_url   = "https://api.energyzero.nl/v1/energyprices"
url_params = "?fromDate={}&tillDate={}&interval=4&usageType=1&inclBtw=true"
url        = base_url + url_params.format(urllib.parse.quote(from_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")), 
                                          urllib.parse.quote( end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")))
response = requests.get(url)
if response.status_code != 200:
    print("HTTP status code: {} {}".format(response.status_code, response.reason) )
else: 
    json_response = json.loads(response.text)
    for idx, p in enumerate(json_response["Prices"]):
        print (p["readingDate"], p["price"])
