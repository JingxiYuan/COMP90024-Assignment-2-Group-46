import logging, json, requests, socket
from flask import current_app

def main():
    BOM = {
        "Geelong_Racecourse": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94857.json",
        "Laverton": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94865.json",
        "Moorabbin Airport": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94870.json",
        "Point_Cook": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.95941.json",
        "Rhyll": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94892.json",
        "Scoresby": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.95867.json",
        "Sheoaks": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.94863.json",
        "Viewbank": "https://reg.bom.gov.au/fwo/IDV60901/IDV60901.95874.json",
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
