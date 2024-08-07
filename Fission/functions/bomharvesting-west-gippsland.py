import logging, json, requests, socket
from flask import current_app

def main():
    BOM = {
        "East_Sale_Airport": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95907.json",
        "Hogan_Island": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94949.json",
        "Latrobe_Valley": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94891.json",
        "Mount_Baw_Baw": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95901.json",
        "Mount_Moornapa": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95913.json",
        "Warragul(Nilma North)": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.99806.json",
        "Yanakie": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.94911.json",
        "Yarram_Airport": "https://reg.bom.gov.au/fwo/IDV60801/IDV60801.95890.json"
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
