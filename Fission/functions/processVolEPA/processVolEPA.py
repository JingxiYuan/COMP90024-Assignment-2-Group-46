from elasticsearch8 import Elasticsearch
from elasticsearch8.helpers import bulk
from string import Template
import requests

import warnings
warnings.filterwarnings("ignore")


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
    # (config('ES_USERNAME'), config('ES_PASSWORD'))
    es = Elasticsearch('https://elasticsearch-master.elastic.svc.cluster.local:9200',
                       verify_certs = False,
                       basic_auth=(config('ES_USERNAME'), config('ES_PASSWORD')),
                       request_timeout=300)

    # Get the data for volume and crash 
    #http://router.fission/traffic/
    url_endpoint="http://router.fission/data/traffic/"
    epa_url = url_endpoint+"epa"
    volume_url = url_endpoint+"volume"
    # Send a GET request to the URL
    response_epa = requests.get(epa_url)
    response_volume = requests.get(volume_url)

    if response_epa.status_code == 200 and response_volume.status_code == 200:
        # Parse the JSON response
        all_epa_data = response_epa.json()
        all_traffic_data = response_volume.json()
    else:
        print("Error:", response_epa.status_code)
        print("Error:", response_volume.status_code)
        return
    
    print("get data from url")
  
    counted_ids = set()
    pollutant_counts = {}
    # pollutant_counts = {pollutant: {} for pollutant in target_pollutants}
   
   
    for road in all_traffic_data:
        coords = road['_source']['coordinates']['coordinates']
        volume = road['_source']['ALLVEHS_MMW']
        min_lon, max_lon, min_lat, max_lat = get_min_max_coordinates(coords)

        for data in all_epa_data:
            
            if 'location' in data:
                
                pollutant = data['healthParameter']
                incident_id = data['_id']
                if is_within_bounds(data['location'], min_lon, max_lon, min_lat, max_lat):
                    
                    if incident_id not in counted_ids:
                        
                        if pollutant not in pollutant_counts:
                            pollutant_counts[pollutant]={}
                            pollutant_counts[pollutant][volume] = 0
                        else:
                            if volume not in pollutant_counts[pollutant]:
                                pollutant_counts[pollutant][volume] = 0 
                        pollutant_counts[pollutant][volume]+=1
                        counted_ids.add(incident_id)

    index_settings = {
        "settings": {
            "number_of_shards": 3,
            "number_of_replicas": 1
        },
        "mappings": {
            "properties": {
                "pollutant_type": {
                    "type": "text"
                },
                "count": {
                    "type": "integer"
                },
                "traffic_volume": {
                    "type": "integer"
                }
            }
        }
    }
    # create index
    index_name="vol_vs_epa"
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name, ignore=[400, 404])

    es.indices.create(index=index_name, body=index_settings)
    print("index created")

    #Store the data 
    for pollutant_type, volume_counts in pollutant_counts.items():
        # Loop through each volume and its count for the current accident type
        for volume, count in volume_counts.items():
            document_data = {
                        "pollutant_type": pollutant_type,
                        "traffic_volume": volume,
                        "count":count
                    }
            es.index(index=index_name, body=document_data)
        print('data inserted!')
        
    