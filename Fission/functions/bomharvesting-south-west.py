import logging, json, requests, socket
from flask import current_app

def main():
    BOM = {
        "Ben_Nevis": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94835.json",
        "Cape_Nelson": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94826.json",
        "Cape_Otway": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94842.json",
        "Casterton": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95825.json",
        "Dartmoor": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95822.json",
        "Hamilton": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94829.json"
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
