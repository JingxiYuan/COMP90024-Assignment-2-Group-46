import json, requests, warnings, logging, socket
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import BadRequestError
from flask import current_app
from datetime import datetime,timedelta
warnings.filterwarnings("ignore")
from string import Template


def config(k):
    with open(f'/configs/default/shared-data/{k}', 'r') as f:
        return f.read()


def check_index(client):
    # the index's mappings we want to use
    index_name = "epa_air"
    body = {
        "aliases": {
            "epa_air": {
                "is_write_index": "true"
            }
        }
    }
    try:
        client.indices.create(index=f"{index_name}-000001", body=body)
    except BadRequestError as e:
        print("The index has been already in Elastic Search")


def parse_time(time):
    time_format = '%Y-%m-%dT%H:%M:%SZ'
    time = datetime.strptime(time, time_format)
    au_time = time + timedelta(hours=10)
    return au_time.strftime('%Y-%m-%dT%H:%M:%S')


def extract_features(record: dict, useful_features):
    all_features = set(record.keys())
    feature_removed = all_features - set(useful_features)
    [record.pop(k) for k in feature_removed]
    lat = lon = since = until = healthAdvice = averageValue = healthParameter = None
    for k in record.keys():
        if k == "geometry":
            lat = record["geometry"]["coordinates"][0]
            lon = record["geometry"]["coordinates"][1]
        if k== "siteHealthAdvices":
            if "siteHealthAdvices" not in record.keys():
                continue
            siteHealthAdvices = record["siteHealthAdvices"][0]
            since = parse_time(siteHealthAdvices["since"])
            until = parse_time(siteHealthAdvices["until"])
            if "healthParameter" not in siteHealthAdvices.keys():
                continue
            healthParameter = siteHealthAdvices["healthParameter"]
            averageValue = siteHealthAdvices["averageValue"]
            healthAdvice = siteHealthAdvices["healthAdvice"]

    record["lat"] = lat
    record["lon"] = lon
    record["since"] = since
    record["until"] = until
    record["healthAdvice"] = healthAdvice
    record["averageValue"] = averageValue
    record["healthParameter"] = healthParameter
    record.pop("geometry")
    if "siteHealthAdvices" in record.keys():
        record.pop("siteHealthAdvices")
    return record


def insert(client, record):
    doc_template = Template('''{
                "siteName": "$siteName",
                "siteType": "$siteType",
                "location":{"lat":$lat, "lon":$lon},
                "since": "$since",
                "until": "$until",
                "healthAdvice": "$healthAdvice",
                "healthParameter": "$healthParameter",
                "averageValue": $averageValue
            }''')

    query_template = Template('''
    {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "since": "$since"
                        }
                    },
                    {
                        "match": {
                            "until": "$until"
                        }
                    },
                    {
                        "match": {
                            "siteName": "$siteName"
                        }
                    }
                ]
            }
        }
    }
    ''')

    query_parm = ["siteName", "since", "until"]
    index_name = "epa_air"

    parm = {k: record[k] for k in query_parm}
    if parm["since"] == None:
        return False
    expr = query_template.substitute(parm)
    query_body = json.loads(expr)
    res = client.search(index=index_name, body=query_body)
    if res["hits"]["total"]["value"] == 0:
        for k in record.keys():
            if record[k] == None or record[k] == '-':
                record[k] = "null"
        expr = doc_template.substitute(record)
        doc_body = json.loads(expr)
        '_'.join(record["siteName"].split(" "))
        id = f'{"_".join(record["siteName"].split(" "))}-{record["since"]}'
        client.index(index=index_name, body=doc_body, id=id)
        return True

    return False


def main():
    client = Elasticsearch(
        'https://elasticsearch-master.elastic.svc.cluster.local:9200',
        verify_certs=False,
        basic_auth=(config('ES_USERNAME'), config('ES_PASSWORD')),
        request_timeout=600
    )

    url = "https://gateway.api.epa.vic.gov.au/environmentMonitoring/v1/sites"
    params = {"environmentalSegment": "air"}
    headers = {
        'User-Agent': 'curl/8.4.0',
        'Cache-Control': 'no-cache',
        'X-API-Key': '0c205e70de6741258e305303f789f2a1',
    }

    # check whether the index exists. if not, create it
    check_index(client)
    useful_features = ["siteName", "siteType", "geometry", "siteHealthAdvices"]

    response = requests.get(url, params=params, headers=headers)
    result = response.json()["records"]

    cnt = 0
    for record in result:
        data = extract_features(record, useful_features)
        if insert(client ,record):
            cnt += 1
            #print(cnt)

    current_app.logger.info(f'Harvested {cnt} eqa observations!')

    return f'Harvested {cnt} epa observations!'

