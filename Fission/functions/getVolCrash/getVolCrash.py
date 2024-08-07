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

accident_type_list=[
    "No collision and no object struck", 
    "Collision with vehicle", 
    "Vehicle overturned (no collision)", 
    "collision with some other object", 
    "Struck Pedestrian", 
    "Struck animal", 
    "Collision with a fixed object",
    "Other accident",
    "Fall from or in moving vehicle"]

type_message="Different accident types: No collision and no object struck, Collision with vehicle, Vehicle overturned (no collision), collision with some other object, Struck Pedestrian, Struck animal, Collision with a fixed object."

def main():
    #https://localhost:9200
    #https://elasticsearch-master.elastic.svc.cluster.local:9200
    es = Elasticsearch('https://elasticsearch-master.elastic.svc.cluster.local:9200',
                       verify_certs = False,
                       basic_auth=(config('ES_USERNAME'), config('ES_PASSWORD')),
                       request_timeout=300)
    
    target_accident_type = request.headers.get('X-Fission-Params-Type', '')  # Using .get() method to handle missing header case

    if target_accident_type == '':
        return json.dumps({"error": "Empty type! No accident type specified.\n" + type_message})

    # Check if the target accident type is in the list of valid accident types
    if target_accident_type not in accident_type_list:
        message = {"error": "Invalid type! \n" + type_message}
        return json.dumps(message)

    try:
        # Your existing code for Elasticsearch search
        scroll = es.search(
            index="vol_vs_crash",
            scroll='2m',
            size=200,
            body={
                "query": {
                    "bool": {
                        "must": [
                            { "match_phrase": { "accident_type": target_accident_type } }  # Match documents with the specified accident type using match_phrase
                        ]
                    }
                },
                "_source": ["accident_type", "collision_count", "traffic_volume"]
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
            counts.append(data['_source']['collision_count'])

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


