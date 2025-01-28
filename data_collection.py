import requests
import json
import datetime
import os

# Collect data from backpack.tf API if most recent file is >1 day old, store out to local file.

# NOTE: This storage method maintains visual structure, which means a ton more spaces
# stored out than the previously-stored json objects I've added for history reference.
# If we were paying more attention to storage capacity, could trim that out, but for
# a little project like this I like the added clarity.

# Load in all prices:

# TODO OPTIONAL: Move filename format to a config file
nameformat='Backpack_spreadsheet_'

# Look at all relevantly-named files, pick the most recent
fnames = os.listdir('Data')
fnames = [name for name in fnames if name[:len(nameformat)] == nameformat]
mostrecent = max(fnames)

# If the most recent file is more than a day old, refresh=True
mostrecent_datetime = datetime.datetime.strptime(mostrecent[-18:-5], '%Y%m%d_%H%M')
current_datetime = datetime.datetime.now()
refresh = current_datetime - mostrecent_datetime > datetime.timedelta(days=1)

if refresh:
    # Load personal backpack.tf API key (set up as separate file for hypothetical security)
    with open('api_key.txt') as f:
        api_key = f.read()

    # Query the backpack.tf pricing API using the stored key
    response = requests.get(f'https://backpack.tf/api/IGetPrices/v4/?key={api_key}&appid=440')
    response_parsed = json.loads(response.text)  # keeping a lot of process variables

    # Store out the response
    query_datetime = datetime.datetime.fromtimestamp(response_parsed['response']['current_time'])
    dt_str = query_datetime.strftime("%Y%m%d_%H%M")
    filepath = os.path.join('Data', f'{nameformat}{dt_str}.json')
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(response_parsed, f)

    print('Refreshed file')
else:
    print('Most recent file is fresh')

