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

def main():
    es = Elasticsearch('https://elasticsearch-master.elastic.svc.cluster.local:9200',
                       verify_certs = False,
                       basic_auth=(config('ES_USERNAME'), config('ES_PASSWORD')),
                       request_timeout=300)
    
    #traffic_volume
    scroll = es.search(
        index="traffic_volume",
        scroll='2m',
        size=200,
        body={
            "query": {"match_all": {}},
            "_source": ["ALLVEHS_MMW", "coordinates", "OBJECTID"]
        }
    )

    all_traffic_data = []

    while True:
        scroll_id = scroll['_scroll_id']
        hits = scroll['hits']['hits']
        if not hits:
            break
        all_traffic_data.extend(hits)
        scroll = es.scroll(scroll_id=scroll_id, scroll='2m')

    es.clear_scroll(scroll_id=scroll_id)

    # Convert combined_data to a JSON string
    json_string = json.dumps(all_traffic_data)
    print("Total number of records retrieved:", len(all_traffic_data))
    print("volume done")
    return json_string