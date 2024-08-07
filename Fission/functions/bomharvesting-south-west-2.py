import logging, json, requests, socket
from flask import current_app

def main():
    BOM = {
        'Mount_Gellibrand': "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95845.json",
        "Mount_William": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94833.json",
        "Port_Fairy": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94830.json",
        "Portland_Airport": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94828.json",
        "Warrnambool": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94837.json",
        "Westmere": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95840.json",
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
