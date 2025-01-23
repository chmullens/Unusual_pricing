import requests
import json
import datetime
import os

import numpy as np
import pandas as pd


def store_parsed_response(parseresponse):
    # Store out the resulting json object in a file with the time on it
    current_datetime = datetime.datetime.fromtimestamp(parseresponse['response']['current_time'])
    dt_str = current_datetime.strftime("%Y%m%d_%H%M")
    filepath = os.path.join('Data', f'Backpack_spreadsheet_{dt_str}.json')
    with open(filepath, 'w', encoding='utf-8') as fname:
        json.dump(parseresponse, fname, indent=4)

    return 'Stored to Data directory'


def get_priceresponse(refresh=True):
    # Pull in a fresh API query
    if refresh:
        # Load personal backpack.tf API key (set up as separate file for hypothetical security)
        with open('api_key.txt') as f:
            api_key = f.read()

        # Query the backpack.tf pricing API using the key
        response = requests.get(f'https://backpack.tf/api/IGetPrices/v4/?key={api_key}&appid=440')
        response_parsed = json.loads(response.text)  # keeping a lot of process variables

        store_parsed_response(response_parsed)

    # Load json from most recent file
    else:
        # Find most recent file:
        with open(os.path.join('Data', max(os.listdir('Data'))), 'r') as f:
            response_parsed = json.loads(f.read())

    return response_parsed


# Load in all prices:
refreshcond = False  # TODO OPTIONAL: Add check to grab existing file if within past day

response_parsed = get_priceresponse(refresh=refreshcond)
allprices = response_parsed['response']['items']

