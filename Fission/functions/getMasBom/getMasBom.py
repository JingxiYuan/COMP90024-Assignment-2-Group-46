from elasticsearch8 import Elasticsearch
from elasticsearch8.helpers import bulk
from string import Template
from datetime import datetime,timedelta
import json

import warnings
warnings.filterwarnings("ignore")

def config(k):
    with open(f'/configs/default/shared-data/{k}', 'r') as f:
        return f.read()
    
def es_download_specific_mastodon_fields(es, index, start_date, end_date):
    
    query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "created_at": {
                                "gte": start_date,
                                "lte": end_date
                            }
                        }
                    }
                ]
            }
        },
        "_source": ["id", "created_at", "content", "sentiment"]
    }

    result = es.search(index=index, body=query, scroll="1m", size=1000)
    sources = []
    scroll_id = None  

    hits = result["hits"]["hits"]
    while hits:
        scroll_id = result.get('_scroll_id')  
        for hit in hits:
            sources.append(hit["_source"])

        result = es.scroll(scroll_id=scroll_id, scroll="1m")
        hits = result["hits"]["hits"]

    if scroll_id:  
        es.clear_scroll(scroll_id=scroll_id)

    return sources

def main():
    es = Elasticsearch('https://elasticsearch-master.elastic.svc.cluster.local:9200',
                       verify_certs = False,
                       basic_auth=(config('ES_USERNAME'), config('ES_PASSWORD')),
                       request_timeout=300)
    
    # get all indices
    indices = es.cat.indices(format="json")

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    mastodon_indices = [i["index"] for i in indices if i["index"].startswith("mastodon_au-")]

    all_mastodon_data = []
    for idx in mastodon_indices:
        data = es_download_specific_mastodon_fields(es, idx, start_date, end_date)
        all_mastodon_data.extend(data)
    
    # Convert combined_data to a JSON string
    json_string = json.dumps(all_mastodon_data)
    print("Total number of records retrieved:", len(all_mastodon_data))
    print("done")
    return json_string