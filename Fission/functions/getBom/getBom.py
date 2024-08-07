from elasticsearch8 import Elasticsearch
from elasticsearch8.helpers import bulk
from string import Template
from datetime import datetime, timedelta
import json

import warnings
warnings.filterwarnings("ignore")

def config(k):
    with open(f'/configs/default/shared-data/{k}', 'r') as f:
        return f.read()
    
def es_download_specific_weather_fields(es, index, start_date, end_date):
    query = {
        "query": {
            "bool": {
                "must": [
                    {"range": {"DATE": {"gte": start_date, "lte": end_date}}}
                ]
            }
        },
        "_source": ["DATE", "air_temp", "wind_spd_kmh", "rain_trace", "wind_dir", "Location","rel_hum","press"]
    }

    result = es.search(index=index, body=query, scroll="1m", size=1000)
    sources = []
    
    hits = result["hits"]["hits"]
    scroll_id = None  
    try:
        while hits:
            scroll_id = result['_scroll_id']
            for hit in hits:
                sources.append(hit["_source"])

            result = es.scroll(scroll_id=scroll_id, scroll="1m")
            hits = result["hits"]["hits"]
    finally:
        if scroll_id: 
            es.clear_scroll(scroll_id=scroll_id)

    return sources


def main():
    es = Elasticsearch('https://elasticsearch-master.elastic.svc.cluster.local:9200',
                       verify_certs = False,
                       basic_auth=(config('ES_USERNAME'), config('ES_PASSWORD')),
                       request_timeout=300)
    
    indices = es.cat.indices(format="json")
    bom_weather_indices = [i["index"] for i in indices if i["index"].startswith("bom_weather-")]

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    all_bom_data = []
    for idx in bom_weather_indices:
        data = es_download_specific_weather_fields(es, idx, start_date, end_date)
        all_bom_data.extend(data)
    
    # Convert combined_data to a JSON string
    json_string = json.dumps(all_bom_data)
    print("Total number of records retrieved:", len(all_bom_data))
    print("done")
    return json_string