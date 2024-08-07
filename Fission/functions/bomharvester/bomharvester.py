import logging, json, requests, socket, warnings
from flask import current_app
from elasticsearch import Elasticsearch
from string import Template
from elasticsearch.exceptions import BadRequestError

warnings.filterwarnings("ignore")


def check_index(client):
    # the index's mappings we want to use
    BOM_mappings = {
        "settings": {
            "index": {
                "number_of_shards": 3,
                "number_of_replicas": 1
            }
        },
        "mappings": {
            "properties": {
                "STATION": {
                    "type": "keyword"
                },
                "STATE": {
                    "type": "keyword"
                },
                "DATE": {
                    "type": "date"
                },
                "Location": {
                    "type": "geo_point"
                },
                "wmo": {
                    "type": "integer"
                },
                "air_temp": {
                    "type": "double"
                },
                "apparent_t": {
                    "type": "double",
                },
                "dewpt": {
                    "type": "double"
                },
                "rel_hum": {
                    "type": "integer"
                },
                "delta_t": {
                    "type": "double",
                },
                "wind_dir": {
                    "type": "keyword"
                },
                "wind_spd_kmh": {
                    "type": "integer"
                },
                "wind_spd_kt": {
                    "type": "integer"
                },
                "gust_kmh": {
                    "type": "integer"
                },
                "gust_kt": {
                    "type": "integer"
                },
                "press": {
                    "type": "double"
                },
                "rain_trace": {
                    "type": "double"
                }
            }
        }
    }
    index_name = "bom_weather-000001"
    try:
        client.indices.create(index=index_name, body=BOM_mappings)
    except BadRequestError as e:
        print("The index has been already in Elastic Search")


def parse_time(obj: str):
    yy = obj[0:4]
    mm = obj[4:6]
    dd = obj[6:8]
    hh = obj[8:10]
    mm2= obj[10:12]
    ss = obj[-2:]

    return f"{yy}-{mm}-{dd}T{hh}:{mm2}:{ss}"


def para2dict(row, station_name, state):
    f = {idx: row[idx] for idx in row.keys()}
    for k in f.keys():
        if f[k] == None or f[k] == '-':
            f[k] = "null"
    s = {"station":station_name, "state":state}
    return {**f,**s}


def insert(client, record, station_name, state):
    query_template = Template('''
    {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "DATE": "$DATE"
                        }
                    },
                    {
                        "match_phrase": {
                            "STATION": "$STATION"
                        }
                    }
                ]
            }
        }
    }
    ''')
    doc_template = Template('''{
                "STATION": "$station",
                "STATE": "$state",
                "DATE": "$local_date_time_full",
                "Location":{"lat":$lat, "lon":$lon},
                "wmo": $wmo,
                "air_temp": $air_temp,
                "apparent_t": $apparent_t,
                "dewpt": $dewpt,
                "rel_hum": $rel_hum,
                "delta_t": $delta_t,
                "wind_dir": "$wind_dir",
                "wind_spd_kmh": $wind_spd_kmh,
                "wind_spd_kt": $wind_spd_kt,
                "gust_kmh": $gust_kmh,
                "gust_kt": $gust_kt,
                "press": $press,
                "rain_trace": $rain_trace
            }''')
    date = record["local_date_time_full"]
    expr = query_template.substitute({"STATION":station_name, "DATE": date})
    query_body = json.loads(expr)
    res = client.search(index="bom_weather", body=query_body)
    if res["hits"]["total"]["value"] == 0:
        expr = doc_template.substitute(para2dict(record, station_name, state))
        doc_body = json.loads(expr)
        client.index(index="bom_weather", body=doc_body)
        return True

    return False

def config(k):
    with open(f'/configs/default/shared-data/{k}', 'r') as f:
        return f.read()


def main():
    # connect to es clusters
    client = Elasticsearch(
        'https://elasticsearch-master.elastic.svc.cluster.local:9200',
        verify_certs=False,
        basic_auth=(config('ES_USERNAME'), config('ES_PASSWORD')),
        request_timeout=600
    )

    BOM = {
        "Mel_Olympic_Park": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.95936.json",
        "Melbourne_Airport": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94866.json",
        "Avalon": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94854.json",
        "Cerberus": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94898.json",
        "Essendon_Airport": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.95866.json",
        "Fawkner_Beacon": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.95872.json",
        "Ferny_Creek": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94872.json",
        "Frankston(Ballam Park)": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94876.json",
        "Frankston_Beach": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94871.json",
        "Geelong_Racecourse": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94857.json",
        "Laverton": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94865.json",
        "Moorabbin Airport": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94870.json",
        "Point_Cook": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.95941.json",
        "Point_Wilson": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94847.json",
        "Rhyll": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94892.json",
        "Scoresby": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.95867.json",
        "Sheoaks": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94863.json",
        "South_Channel_Island": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94853.json",
        "St Kilda Harbour RMYS": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.95864.json",
        "Viewbank": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.95874.json",
        #SOUTH WEST
        "Ben_Nevis": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94835.json",
        "Cape_Nelson":"https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94826.json",
        "Cape_Otway": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94842.json",
        "Casterton": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95825.json",
        "Dartmoor":"https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95822.json",
        "Hamilton":"https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94829.json",
        "Mortlake":"https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94840.json",
        'Mount_Gellibrand': "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95845.json",
        "Mount_William":"https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94833.json",
        "Port_Fairy": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94830.json",
        "Portland_Airport":"https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94828.json",
        "Warrnambool": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94837.json",
        "Westmere": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95840.json",
        #WIMMERA
        "Edenhope": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95832.json",
        "Horsham":"https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95839.json",
        "Kanagulk": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95827.json",
        "Longerenong":"https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95835.json",
        "Nhill_Aerodrome": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94827.json",
        "Stawell": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94836.json",
        "Warracknabeal_Airport": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94920.json",
        #MALLEE
        "Charlton":"https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94839.json",
        "Hopetoun_Airport": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94838.json",
        "Mildura": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94693.json",
        "Swan_Hill": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94843.json",
        "Walpeup": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95831.json",
        #NORTHERN COUNTRY
        "Bendigo": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94855.json",
        "Kyabram": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95833.json",
        "Mangalore": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94874.json",
        "Redesdale": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94859.json",
        "Shepparton": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94875.json",
        "Tatura": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95836.json",
        "Yarrawonga": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94862.json",
        #NORTH EAST
        "Albury": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95896.json",
        "Falls_Creek": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94903.json",
        "Hunters_Hill": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94878.json",
        "Mount_Buller": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94894.json",
        "Mount_Hotham_Airport": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94905.json",
        "Mount_Hotham": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94906.json",
        "Rutherglen": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95837.json",
        "Wangaratta": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94889.json",
        #NORTH CENTRAL
        "Eildon_Fire_Tower": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94881.json",
        "Kilmore Gap":"https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94860.json",
        "Puckapunyal-Lyon_Hill(Defence)":"https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94858.json",
        "Puckapunyal_West(Defence)": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94856.json",
        #WEST AND SOUTH GIPPSLAND
        "East_Sale_Airport":"https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95907.json",
        "Hogan_Island":"https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94949.json",
        "Latrobe_Valley":"https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94891.json",
        "Mount_Baw_Baw": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95901.json",
        "Mount_Moornapa": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95913.json",
        "Warragul(Nilma North)": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.99806.json",
        "Yanakie": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94911.json",
        "Yarram_Airport": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95890.json",
        #EAST GIPPSLAND
        "Bairnsdale": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94912.json",
        "Combienbar": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94914.json",
        "Gabo_Island": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94933.json",
        "Gelantipy": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94913.json",
        "Mallacoota": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94935.json",
        "Mount_Nowa_Nowa": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94930.json",
        "Omeo": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94908.json",
        "Orbost": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95918.json"
    }

    # the features we are interested in
    useful_feature = ["wmo", "local_date_time_full", "lat", "lon", "apparent_t", "delta_t", "gust_kmh", "gust_kt",
                      "air_temp", "dewpt", "press", "rain_trace", "rel_hum", "wind_spd_kmh", "wind_spd_kt", "wind_dir"]

    # check whether the index exists. if not, create it
    check_index(client)

    # return data of 'json format' from each station
    # parse each json for each station
    cnt = 0
    for station in BOM.keys():
        data = requests.get(BOM[station]).json()
        result = data["observations"]
        # extract station's name and state which it belongs to
        header = result["header"][0]
        station_name = header["name"]
        state = header["state"]
        # start to handle each record from the station
        records = result["data"]

        processed_records = []
        temp_cnt = 0
        for row in records:
            feature_removed = set(list(row.keys())) - set(useful_feature)
            [row.pop(k) for k in feature_removed]
            row["local_date_time_full"] = parse_time(row["local_date_time_full"])
            processed_records.append(row)

        for record in processed_records:
            if insert(client, record, station_name, state):
                cnt +=1
                temp_cnt +=1

        current_app.logger.info(f"{temp_cnt} records are Saved in {station_name}!")

    return_str = f"{len(BOM)} Stations Harvested! \n {cnt} records have been saved!"
    return return_str

