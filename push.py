import requests
import json

MAC_URL = "http://localhost:8090/powermetrics"

def push_powermetrics(report):
    r = requests.post(MAC_URL, data=json.dumps(report))
    print(r.text)