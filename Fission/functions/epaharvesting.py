import logging, json, requests, socket
from flask import current_app
from datetime import datetime,timedelta

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

def main():

    url = "https://gateway.api.epa.vic.gov.au/environmentMonitoring/v1/sites"
    params = {"environmentalSegment": "air"}
    headers = {
        'User-Agent': 'curl/8.4.0',
        'Cache-Control': 'no-cache',
        'X-API-Key': '0c205e70de6741258e305303f789f2a1',
    }
    response = requests.get(url, params=params, headers=headers)
    result = response.json()

    result = result["records"]
    cnt = 0
    data = []
    useful_features = ["siteName", "siteType", "geometry", "siteHealthAdvices"]
    for record in result:
        temp = extract_features(record, useful_features)
        for k in temp.keys():
            if temp[k] == None or temp[k] == '-':
                temp[k] = "null"
        data.append(temp)

    current_app.logger.info(f'Harvested EPA observation')
    requests.post(url='http://router.fission/enqueue/epa',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({"records":data})
    )
    return json.dumps({"records":data})