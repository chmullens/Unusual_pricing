import json
import datetime
import os

import numpy as np
import pandas as pd

# I am going to do a little bit of layering multiple ages of data here. This isn't strictly
# necessary: we could just use the most recent datapoint for each item, it would be simpler,
# but this way I can test whether we get better predictive power for the holdout set with or
# without any added history. This will only impact items repriced within the last six months,
# so we can do segmentation to verify whether it's helping with the full dataset or with the
# repriced subset.

# Steps:
#  - Import most recent stored file
#  - Parse out individual pricing events (i.e. item, effect, price, date)
#  - Repeat for each prior file, add unique events

# Detect files
fnames = os.listdir('Data')

# TODO OPTIONAL: Move filename format below to a config file
rawnameformat = 'Backpack_spreadsheet_'
fnames = [name for name in fnames if name[:len(rawnameformat)] == rawnameformat]


def price_parser(pricedict):
    """
    Function to select out item type, unusual effect, pricing date, currency and value
    for any unusual cosmetic items found in the backpack.tf price object. This function
    is purpose-specific. It's much easier than trying to generalize here, since the
    object structure is complicated.

    What does it find? For any item, the "prices" subsection is separated into different
    qualities, indicated by a number. '5' is the shorthand for unusual quality. Within
    that subsection, it checks whether the tradeable, craftable subsection contains any
    different effects, which are again indicated with a number. If so, then the item has
    unusual effects, and it steps through those effects and adds the price for each to
    the existing structure.

    Possible point of failure: Type check for dictionary in second conditional, looks
    like it works fine for now but may not be future-proof.

    Input: Pricing object
    Output: List of pricing events
        (Each event contains: item, effect, update time, currency type, value)
    """

    # Initialize storage
    unusualprices = []
    # Step through all items
    for item in pricedict:
        # Does the item come in unusual quality? (Unusual quality items are item type '5')
        if '5' in pricedict[item]['prices']:
            # If so, grab the reference
            unusual_ids = pricedict[item]['prices']['5']['Tradable']['Craftable']
            # Is it unusual with effect numbers? (Items w/o effects store list, not dictionary of effects)
            if type(unusual_ids) == dict:
                # If it has effect numbers, step through the effect numbers and store key variables
                for effectnum in unusual_ids:
                    unusualprices.append([item,
                                          effectnum,
                                          unusual_ids[effectnum]['last_update'],
                                          unusual_ids[effectnum]['currency'],
                                          unusual_ids[effectnum]['value']])
    return unusualprices


# Load in example file TODO: CONVERT TO LOOP AFTER DEDUPLICATION
with open(os.path.join('Data', fnames[0]), 'r') as f:
    response_parsed = json.loads(f.read())

# Parse our example case:
allprices = response_parsed['response']['items']
price_events = price_parser(allprices)
