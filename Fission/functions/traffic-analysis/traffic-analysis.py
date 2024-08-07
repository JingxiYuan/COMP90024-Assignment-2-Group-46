from flask import request, current_app
import requests, logging,json,warnings
from elasticsearch import Elasticsearch
from string import Template
import pandas as pd
warnings.filterwarnings("ignore")

def es_download(es, query, index):
    result = es.search(
        index= index,
        body= query,
        scroll="1m"
    )
    source = []
    cnt = 0
    hits = result["hits"]["hits"]
    for hit in hits:
        source.append(hit["_source"])
        cnt+=1
    current_app.logger.info(f'{cnt}')

    old = []
    while len(hits) > 0:
        scroll_id = result["_scroll_id"]
        if scroll_id not in old:
            old.append(scroll_id)
        result = es.scroll(scroll_id=scroll_id, scroll="1m")
        hits = result["hits"]["hits"]
        for hit in hits:
            source.append(hit["_source"])
            cnt +=1
        current_app.logger.info(f'{cnt}')
    for id in old:
        es.clear_scroll(scroll_id=id)
    return source

def config(k):
    with open(f'/configs/default/shared-data/{k}', 'r') as f:
        return f.read()

def main():
    location = {
        "Melbourne": {"lat": -37.81, "lon": 144.96},
        "Geelong": {"lat": -38.15, "lon": 144.36},
        "Ballarat": {"lat": -37.56, "lon": 143.85},
        "Bendigo": {"lat": -36.76, "lon": 144.28}
    }

    try:
        index_name = request.headers['X-Fission-Params-Index']
    except KeyError:
        index_name = None

    try:
        city = request.headers['X-Fission-Params-City']
    except KeyError:
        city = None


    current_app.logger.info(f'Processing {city}')

    roads_template = Template('''
        {"query": {
        "bool": {
            "filter": {
                "geo_distance": {
                    "distance": "10km",
                    "coordinates": {
                        "lat": $lat,
                        "lon": $lon
                    }
                }
            }
        }
    },
        "size": 2000
    }
        ''')

    crash_template = Template('''
    {
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "DATE": {
                                "gte": "2018-01-04T00:00:00",
                                "lte": "2020-05-31T23:59:59"
                            }
                        }
                    },
                    {
                        "range": {
                            "SERIOUSINJURY": {
                                "gte": 2
                            }
                        }
                    },
                    {
                        "geo_distance": {
                            "distance": "10km",
                            "Location": {
                                "lat": $lat,
                                "lon": $lon
                            }
                        }
                    }
                ]
            }
        }, "size": 3000
    }
    ''')

    client = Elasticsearch(
        'https://elasticsearch-master.elastic.svc.cluster.local:9200',
        verify_certs=False,
        basic_auth=(config('ES_USERNAME'), config('ES_PASSWORD')),
        request_timeout=600
    )

    if city is not None:
        if index_name == "traffic_volume":
            roads_param = location[city]
            expr = roads_template.substitute(roads_param)
            roads_body = json.loads(expr)

            road_source = es_download(client, roads_body, index_name)
            #road_source = json.dumps(road_source)
            current_app.logger.info(f'Done in {index_name}')

            roads_df1 = pd.DataFrame(road_source[0])
            roads_df1 = roads_df1.loc[['coordinates']]
            for i in road_source[1:]:
                roads_df2 = pd.DataFrame(i)
                roads_df2 = roads_df2.loc[['coordinates']]
                roads_df1 = pd.concat([roads_df1, roads_df2])
                roads_df1.reset_index(drop=True, inplace=True)

            roads_json = roads_df1.to_json()
            return roads_json
        if index_name == "vic_roads_crash":
            crash_param = location[city]
            expr = crash_template.substitute(crash_param)
            crash_body = json.loads(expr)

            crash_source = es_download(client, crash_body, index_name)
            #crash_source = json.dumps(road_source)
            current_app.logger.info(f'Done in {index_name}')

            crash_df1 = pd.DataFrame(crash_source[0])
            crash_df1.reset_index(drop=True, inplace=True)
            crash_df1['Location'] = crash_df1['Location'].apply(lambda x: [x])
            crash_df1.at[0, 'Location'] = [crash_df1.loc[1, 'Location'][0], crash_df1.loc[0, 'Location'][0]]
            crash_df1 = crash_df1.iloc[[0]]
            for i in crash_source[1:]:
                crash_df2 = pd.DataFrame(i)
                crash_df2.reset_index(drop=True, inplace=True)
                crash_df2['Location'] = crash_df2['Location'].apply(lambda x: [x])
                crash_df2.at[0, 'Location'] = [crash_df2.loc[1, 'Location'][0], crash_df2.loc[0, 'Location'][0]]
                crash_df2 = crash_df2.iloc[[0]]
                crash_df1 = pd.concat([crash_df1, crash_df2])
                crash_df1.reset_index(drop=True, inplace=True)
            crash_json = crash_df1.to_json()

            return crash_json

        return json.dumps({"error": "Don't have the index you want", "status": 404})
    else:
        return json.dumps({"error": "Don't determine the City you want", "status": 404})
