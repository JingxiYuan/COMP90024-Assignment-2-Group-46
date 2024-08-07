import logging, json, requests, socket
from flask import current_app

def main():
    BOM = {
        "Bendigo": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94855.json",
        "Kyabram": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95833.json",
        "Mangalore": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94874.json",
        "Redesdale": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94859.json",
        "Shepparton": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94875.json",
        "Tatura": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95836.json",
        "Yarrawonga": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94862.json"
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
