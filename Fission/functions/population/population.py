from flask import request, current_app
import requests, logging,json,warnings
import pandas as pd
from elasticsearch import Elasticsearch
from string import Template
warnings.filterwarnings("ignore")

def config(k):
    with open(f'/configs/default/shared-data/{k}', 'r') as f:
        return f.read()

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

def main():

    location = {
        "Melbourne": {"lat":-37.81, "lon": 144.96},
        "Geelong": {"lat":-38.15, "lon":144.36},
        "Ballarat": {"lat": -37.56, "lon": 143.85},
        "Bendigo": {"lat":-36.76, "lon":144.28}
    }

    try:
        pop = request.headers['X-Fission-Params-Pop']
    except KeyError:
        pop = None

    try:
        crime = request.headers['X-Fission-Params-Crime']
    except KeyError:
        crime = None

    try:
        city = request.headers['X-Fission-Params-City']
    except KeyError:
        city = None

    query_pop = Template('''
    {
  "query": {
    "bool": {
      "should": [
        {"match": {
          "age_group": "all_males"
        }},
        {
          "match": {
            "age_group": "all_females"
          }
        }
      ],
      "filter": {
        "geo_distance": {
          "distance": "10km",
          "geometry": {
            "lat": $lat,
            "lon": $lon
          }
        }
  },
  "minimum_should_match": 1
    }
  }
}
    ''')


    client = Elasticsearch(
        'https://elasticsearch-master.elastic.svc.cluster.local:9200',
        verify_certs=False,
        basic_auth=(config('ES_USERNAME'), config('ES_PASSWORD')),
        request_timeout=600
    )

    if city is not None:
        pop_param = location[city]
        expr = query_pop.substitute(pop_param)
        pop_body = json.loads(expr)

        pop_source = es_download(client, pop_body, "population_fis")
        pop_df1 = pd.DataFrame(pop_source[0])
        pop_df1 = pop_df1.loc[['coordinates']]
        for i in pop_source[1:]:
            pop_df2 = pd.DataFrame(i)
            pop_df2 = pop_df2.loc[['coordinates']]
            pop_df1 = pd.concat([pop_df1, pop_df2])
        pop_df1['LGA_name'] = pop_df1['LGA_name'].str[:-4]
        pop_df1.reset_index(drop=True, inplace=True)
        pop_json = pop_df1.to_json()
        current_app.logger.info(f'Done in "population_fis"')

        lga_list = []
        for pop in pop_source:
            lga_list.append(pop['LGA_name'])
        match_list = list(set(lga_list))
        should_clause = []
        for lga in match_list:
            should_clause.append({"match": {"LGA_name": lga[:-4]}})
        query_crime = {"query": {
            "bool": {
                "should": should_clause
            }
        }, "size":3000
        }

        crime_source = es_download(client, query_crime, "offence_record_fis")
        crime_df1 = pd.DataFrame([crime_source[0]])
        crime_df1.reset_index(drop=True, inplace=True)
        for i in crime_source[1:]:
            crime_df2 = pd.DataFrame([i])
            crime_df2.reset_index(drop=True, inplace=True)
            crime_df1 = pd.concat([crime_df1, crime_df2])
        crime_df1 = crime_df1.reset_index(drop=True)
        crime_df1 = crime_df1.drop(crime_df1[crime_df1['LGA_name'] == 'Melbourne'].index)
        crime_df1 = crime_df1.drop(crime_df1[crime_df1['LGA_name'] == 'Greater Geelong'].index)
        crime_df1 = crime_df1.drop(crime_df1[crime_df1['LGA_name'] == 'Ballarat'].index)
        crime_df1 = crime_df1.drop(crime_df1[crime_df1['LGA_name'] == 'Greater Dandenong'].index)
        crime_df1 = crime_df1.drop(crime_df1[crime_df1['LGA_name'] == 'Greater Bendigo'].index)

        crime_json = crime_df1.to_json()

        current_app.logger.info(f'Done in "offence_record_fis"')

        selected_rows = pop_df1[['LGA_name', 'population', 'age_group']].groupby("LGA_name").agg({'population': 'sum'})
        selected_rows = selected_rows.reset_index(drop=False)
        type_crime = pd.merge(selected_rows[['LGA_name', 'population']],
                              crime_df1[['LGA_name', 'offence_count', 'offence_subdiv']], on=['LGA_name'], how='inner')
        type_crime = type_crime.drop_duplicates()
        type_crime = type_crime.groupby(['LGA_name', 'offence_subdiv']).agg(
            {'population': 'first', 'offence_count': 'sum'}).reset_index()
        pop_cr = type_crime.groupby('LGA_name').agg({'population': 'first', 'offence_count': 'sum'})
        pop_cr_json = pop_cr.to_json()

        selected_rows = pop_df1[(pop_df1['age_group'] == 'all_males') | (pop_df1['age_group'] == 'all_females')]
        selected_rows = selected_rows.groupby("LGA_name").agg({'population': 'sum', 'geometry': 'first'})
        selected_rows = selected_rows.reset_index(drop=False)
        selected_rows_json = selected_rows.to_json()

        crime_geo = pd.merge(pop_cr, selected_rows, how='inner')
        crime_geo_json = crime_geo.to_json()

        return json.dumps({"population":pop_json, "crime":crime_json,"pop_cr":pop_cr_json,"selected_rows":selected_rows_json,"crime_geo":crime_geo_json})
    else:
        return json.dumps({"error":"cannot found index", "status":404})
