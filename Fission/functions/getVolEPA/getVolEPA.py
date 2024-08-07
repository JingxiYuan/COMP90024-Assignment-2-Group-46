from elasticsearch8 import Elasticsearch
from elasticsearch8.helpers import bulk
from string import Template
import json

import warnings
warnings.filterwarnings("ignore")
from flask import request

def config(k):
    with open(f'/configs/default/shared-data/{k}', 'r') as f:
        return f.read()
    
target_pollutants = [
    "PM2.5",
    "Particles",
    "PM10",
    "O3",
    "SO2",
    "NO2"
]
type_message="Different pollutants are PM2.5, Particles, PM10, O3, SO2 and NO2"
def main():
    #https://localhost:9200
    #https://elasticsearch-master.elastic.svc.cluster.local:9200
    #config('ES_USERNAME'), config('ES_PASSWORD')
    es = Elasticsearch('https://elasticsearch-master.elastic.svc.cluster.local:9200',
                       verify_certs = False,
                       basic_auth=(config('ES_USERNAME'), config('ES_PASSWORD')),
                       request_timeout=300)
    

    
    target_pollutant = request.headers.get('X-Fission-Params-Type', '')  # Using .get() method to handle missing header case

    if target_pollutant == '':
        return json.dumps({"error": "Empty type! No accident type specified.\n" + type_message})

    # Check if the target accident type is in the list of valid accident types
    if target_pollutant not in target_pollutants:
        message = {"error": "Invalid type! \n" + type_message}
        return json.dumps(message)

    try:
        # Your existing code for Elasticsearch search
        scroll = es.search(
            index="vol_vs_epa",
            scroll='2m',
            size=200,
            body={
                "query": {
                    "bool": {
                        "must": [
                            { "match_phrase": { "pollutant_type": target_pollutant } }  # Match documents with the specified accident type using match_phrase
                        ]
                    }
                },
                "_source": ["pollutant_type", "count", "traffic_volume"]
            }
        )


        all_data = []
        
        while True:
            scroll_id = scroll['_scroll_id']
            hits = scroll['hits']['hits']
            if not hits:
                break
            all_data.extend(hits)
            scroll = es.scroll(scroll_id=scroll_id, scroll='2m')

        es.clear_scroll(scroll_id=scroll_id)

        # Calculate the coord range of each road
        volume = []
        counts = []
        for data in all_data:
            volume.append(data['_source']['traffic_volume'])
            counts.append(data['_source']['count'])

        combined_data = {}

        print(volume)
        print(counts)
        # Add the contents of vic_roads_crash to combined_data
        combined_data['volume'] = volume

        # Add the contents of traffic_volume to combined_data
        combined_data['counts'] = counts

        json_string = json.dumps(combined_data)
        print("done")
        return json_string

    except KeyError:
        error_message = {"error": "Invalid URL! require accident type"}
        return json.dumps(error_message)


main()