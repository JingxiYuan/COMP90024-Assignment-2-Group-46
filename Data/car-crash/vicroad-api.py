import requests
import pandas as pd
import json

api_url = ('https://services2.arcgis.com/18ajPSI0b3ppsmMt/arcgis/rest/services/Victorian_Road_Crash_Data/FeatureServer'
           '/0/query?where=1%3D1&outFields=*&outSR=4326&f=json')

response = requests.get(api_url)

tmp = json.loads(response.text)

print(tmp["features"][0])


