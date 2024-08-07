import logging, json, requests, socket
from flask import current_app

def main():
    BOM = {
        "Mel_Olympic_Park": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.95936.json",
        "Melbourne_Airport": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94866.json",
        "Avalon": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94854.json",
        "Cerberus": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94898.json",
        "Essendon_Airport": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.95866.json",
        "Ferny_Creek": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94872.json",
        "Frankston(Ballam Park)": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94876.json"
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
