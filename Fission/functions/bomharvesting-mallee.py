import logging, json, requests, socket
from flask import current_app

def main():
    BOM = {
        "Charlton":"https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94839.json",
        "Hopetoun_Airport": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94838.json",
        "Mildura": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94693.json",
        "Swan_Hill": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94843.json",
        "Walpeup": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95831.json"
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