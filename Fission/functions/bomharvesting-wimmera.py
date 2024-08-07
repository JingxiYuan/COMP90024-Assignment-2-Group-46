import logging, json, requests, socket
from flask import current_app

def main():
    BOM = {
        "Edenhope": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95832.json",
        "Horsham": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95839.json",
        "Kanagulk": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95827.json",
        "Longerenong": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95835.json",
        "Nhill_Aerodrome": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94827.json",
        "Stawell": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94836.json",
        "Warracknabeal_Airport": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94920.json"
    }

    temp = []
    for stat in BOM.keys():
        response = requests.get(BOM[stat]).json()
        data = response['observations']['data']
        temp = temp + data

    current_app.logger.info(f'Harvested {len(BOM)} stations')

    requests.post(url='http://router.fission/enqueue/bom',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({"allstation": temp})
    )
    return json.dumps({"allstation": temp})
