import logging, json, requests, socket
from flask import current_app

def main():
    BOM = {
        "Albury": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95896.json",
        "Falls_Creek": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94903.json",
        "Hunters_Hill": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94878.json",
        "Mount_Buller": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94894.json",
        "Mount_Hotham_Airport": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94905.json",
        "Mount_Hotham": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94906.json",
        "Rutherglen": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95837.json",
        "Wangaratta": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94889.json"
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
