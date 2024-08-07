from elasticsearch8 import Elasticsearch
from elasticsearch8.helpers import bulk
from string import Template
import json

import warnings
warnings.filterwarnings("ignore")

def config(k):
    with open(f'/configs/default/shared-data/{k}', 'r') as f:
        return f.read()
    
def es_download_specific_crash_fields(es, index):
    query = {
        "query": {
            "match_all": {}  
        },
        "_source": ["id", "created_at", "content", "sentiment"]
    }

    result = es.search(index=index, body=query, scroll="1m", size=1000)
    sources = []
    scroll_id = result['_scroll_id']
    hits = result['hits']['hits']

    while hits:
        for hit in hits:
            sources.append(hit["_source"])
        
        result = es.scroll(scroll_id=scroll_id, scroll="1m")
        scroll_id = result['_scroll_id']
        hits = result['hits']['hits']

    if scroll_id:
        es.clear_scroll(scroll_id=scroll_id)

    return sources

def main():
    es = Elasticsearch('https://elasticsearch-master.elastic.svc.cluster.local:9200',
                       verify_certs = False,
                       basic_auth=(config('ES_USERNAME'), config('ES_PASSWORD')),
                       request_timeout=300)
    # get all indices begin with "epa_air-"
    indices_info = es.indices.get_alias(name="mastodon_crash*")
    indices = [index for index in indices_info]

    all_crash_data = []
    for index in indices:
        data = es_download_specific_crash_fields(es, index)
        all_crash_data.extend(data)
    
    # Convert combined_data to a JSON string
    json_string = json.dumps(all_crash_data)
    print("Total number of records retrieved:", len(all_crash_data))
    print("done")
    return json_string