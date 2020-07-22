import urequests as requests
import ujson as json

with open('config.json','r+') as f:
    config = json.loads(f.read())
    f.close()
