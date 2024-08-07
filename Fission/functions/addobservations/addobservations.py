import logging, json,warnings
from flask import current_app, request
from elasticsearch import Elasticsearch
from string import Template
from elasticsearch.exceptions import BadRequestError, NotFoundError
warnings.filterwarnings("ignore")

def main():
    client = Elasticsearch (
        'https://elasticsearch-master.elastic.svc.cluster.local:9200',
        verify_certs= False,
        basic_auth=('elastic', 'elastic')
    )

    current_app.logger.info(f'Observations to add')

    for obs in request.get_json(force=True):
        current_app.logger.info(f'{obs}')
        if obs['type'] == "bom":
            current_app.logger.info(f'Observations to BOM')
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
            temp ={}
            for k in obs.keys():
                if k=="type":
                    continue

                if k=="Location":
                    temp[k] = {"lat":obs[k][1], "lon":obs[k][0]}
                else:
                    temp[k]=obs[k]

            date = obs["DATE"]
            expr = query_template.substitute({"STATION": obs['STATION'], "DATE": date})
            query_body = json.loads(expr)
            res = client.search(index="bom_weather", body=query_body)
            if res["hits"]["total"]["value"] == 0:
                client.index(
                    index='bom_weather',
                    body=temp
                )
                current_app.logger.info(f'Indexed observation {obs["type"]}-{obs["STATION"]}-{obs["DATE"]}')

        elif obs['type'] == "epa":
            current_app.logger.info(f'Observations to EPA')
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

            parm = {k: obs[k] for k in query_parm}
            if parm["since"] == "null":
                continue
            expr = query_template.substitute(parm)
            query_body = json.loads(expr)
            #current_app.logger.info(obs)
            res = client.search(index=index_name, body=query_body)
            if res["hits"]["total"]["value"] == 0:
                for k in obs.keys():
                    if obs[k] == None or obs[k] == '-':
                        obs[k] = "null"
                    if obs['averageValue'] =='null':
                        obs['averageValue'] = 0

                id = f'{"_".join(obs["siteName"].split(" "))}-{obs["since"]}'

                client.index(index=index_name, body=obs, id=id)
                current_app.logger.info(f'Indexed observation {obs["type"]}-{obs["siteName"]}-{obs["since"]}')

        elif obs['type'] == 'mastodon_au':
            index_name = "mastodon_au"
            client.index(index=index_name, body=obs)
            current_app.logger.info(f'Indexed mastodon_au {obs}')
        elif obs['type'] == 'mastodon_social':
            index_name = 'mastodon_social'
            client.index(index=index_name, body=obs)
            current_app.logger.info(f'Indexed mastodon_social {obs}')
        elif obs['type'] == 'mastodon_crime':
            index_name = 'mastodon_crime'
            try:
                client.get(index=index_name, id=obs['id'])
            except NotFoundError as e:
                client.index(index=index_name, body=obs, id=obs['id'])
                current_app.logger.info(f'Indexed mastodon_crime {obs}')
        elif obs['type'] == 'mastodon_crash':
            index_name = 'mastodon_crash'
            try:
                client.get(index=index_name, id=obs['id'])
            except NotFoundError as e:
                client.index(index=index_name, body=obs, id=obs['id'])
                current_app.logger.info(f'Indexed mastodon_crash {obs}')

    return 'ok'
