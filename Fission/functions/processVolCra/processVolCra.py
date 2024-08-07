from elasticsearch8 import Elasticsearch
from elasticsearch8.helpers import bulk
from string import Template
import requests

import warnings
warnings.filterwarnings("ignore")
from flask import request


# function that calculate the max and min log and lat of the road. 
def get_min_max_coordinates(coords):
    min_lon = min(point[0] for point in coords)
    max_lon = max(point[0] for point in coords)
    min_lat = min(point[1] for point in coords)
    max_lat = max(point[1] for point in coords)
    return min_lon, max_lon, min_lat, max_lat

# check if the crash is happen with the range of a location. 
def is_within_bounds(location, min_lon, max_lon, min_lat, max_lat, tolerance=0.02):
    return (
        (min_lon - tolerance) <= location['lon'] <= (max_lon + tolerance) and
        (min_lat - tolerance) <= location['lat'] <= (max_lat + tolerance)
    )

def config(k):
    with open(f'/configs/default/shared-data/{k}', 'r') as f:
        return f.read()


def main():
    
    # 'https://elasticsearch-master.elastic.svc.cluster.local:9200'
    es = Elasticsearch('https://elasticsearch-master.elastic.svc.cluster.local:9200',
                       verify_certs = False,
                       basic_auth=(config('ES_USERNAME'), config('ES_PASSWORD')),
                       request_timeout=300)

    # Get the data for volume and crash 
    url_endpoint="http://router.fission/data/traffic/"
    crash_url = url_endpoint+"crash"
    volume_url = url_endpoint+"volume"
    # Send a GET request to the URL
    response_crash = requests.get(crash_url)
    response_volume = requests.get(volume_url)

    if response_crash.status_code == 200 and response_volume.status_code == 200:
        # Parse the JSON response
        all_crash_data = response_crash.json()
        all_traffic_data = response_volume.json()
    else:
        print("Error:", response_crash.status_code)
        print("Error:", response_volume.status_code)
    

    counted_accidents = set()

    road_accident_counts = {}

    #Data processing 
    for road in all_traffic_data:
        coords = road['_source']['coordinates']['coordinates']
        volume = road['_source']['ALLVEHS_MMW']
        min_lon, max_lon, min_lat, max_lat = get_min_max_coordinates(coords)

        for accident in all_crash_data:
            accident_id = accident['_id']
            if accident_id not in counted_accidents:  # check if it is already counted 
                location = {'lon': accident['_source']['Location']['lon'], 'lat': accident['_source']['Location']['lat']}
                
                if is_within_bounds(location, min_lon, max_lon, min_lat, max_lat):
                    ## if it is within the boundary --> record the type and also the volume 
                    accident_type = accident['_source']['ACCIDENT_TYPE']
                    if accident_type not in road_accident_counts:
                        road_accident_counts[accident_type]={}
                        road_accident_counts[accident_type][volume]=0
                    else:
                        if volume not in road_accident_counts[accident_type]:
                            road_accident_counts[accident_type][volume]=0

                    road_accident_counts[accident_type][volume] += 1
                    counted_accidents.add(accident_id)

                    

    print("Data process done")

    index_settings = {
        "settings": {
            "number_of_shards": 3,
            "number_of_replicas": 1
        },
        "mappings": {
            "properties": {
                "accident_type": {
                    "type": "text"
                },
                "collision_count": {
                    "type": "integer"
                },
                "traffic_volume": {
                    "type": "integer"
                }
            }
        }
    }

    # create index
    index_name="vol_vs_crash"
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name, ignore=[400, 404])

    es.indices.create(index=index_name, body=index_settings)
    print("index created")

    #Store the data 
    for accident_type, volume_counts in road_accident_counts.items():
        # Loop through each volume and its count for the current accident type
        for volume, count in volume_counts.items():
            document_data = {
                        "accident_type": accident_type,
                        "traffic_volume": volume,
                        "collision_count":count
                    }
            es.index(index=index_name, body=document_data)
        
        print('data inserted!')
        
    