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
    
def es_download_specific_fields(es, index):
   
    query = {
        "query": {
            "match_all": {}
        },
        "_source": ["healthParameter", "location"]  
    }

    result = es.search(index=index, body=query, scroll="1m", size=1000)
    sources = []
    
    hits = result["hits"]["hits"]
    print("Sample data from Elasticsearch query:")
    if hits: 
        print("Sample hit:", hits[0]) 
    
    while hits:
        scroll_id = result['_scroll_id']
        for hit in hits:
            source_data = hit["_source"] 
            source_data['_id'] = hit['_id'] 
            sources.append(source_data)  

        result = es.scroll(scroll_id=scroll_id, scroll="1m")
        hits = result["hits"]["hits"]

    es.clear_scroll(scroll_id=scroll_id)

    return sources

def main():
    es = Elasticsearch('https://elasticsearch-master.elastic.svc.cluster.local:9200',
                       verify_certs = False,
                       basic_auth=(config('ES_USERNAME'), config('ES_PASSWORD')),
                       request_timeout=300)
    # get all indices begin with "epa_air-"
    indices = es.cat.indices(format="json")
    epa_air_indices = [i["index"] for i in indices if i["index"].startswith("epa_air-")]

    all_epa_data = []
    for idx in epa_air_indices:
        data = es_download_specific_fields(es, idx)
        all_epa_data.extend(data)

    print("Total number of entries retrieved:", len(all_epa_data))
    
    # Convert combined_data to a JSON string
    json_string = json.dumps(all_epa_data)
    print("Total number of records retrieved:", len(all_epa_data))
    print("done")
    return json_string