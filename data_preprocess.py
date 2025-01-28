import json
import datetime
import os

import numpy as np
import pandas as pd

# Matplotlib bug to track down: Errors as using 'macosx' as the gui rather than the valid 'osx'
# import matplotlib.pyplot as plt

# I am going to do a little bit of layering multiple ages of data here. This isn't strictly
# necessary: we could just use the most recent datapoint for each item, it would be simpler,
# but this way I can test whether we get better predictive power for the holdout set with or
# without any added history. This will only impact items repriced within the last six months.
# TODO OPTIONAL: Use segmentation to verify whether the added data helps with the full
#  dataset, only with the repriced subset, or neither

# Steps:
#  - Import most recent stored file
#  - Parse out individual pricing events (i.e. item, effect, price, date)
#  - Repeat for each prior file, add unique events


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

    Possible point of failure: Type check for dictionary in second conditional works
    fine for now, but may not be future-proof.

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


def price_loader(filename):
    with open(os.path.join('Data', filename), 'r') as f:
        response_parsed = json.loads(f.read())

    # Parse prices from our example case:
    allprice = response_parsed['response']['items']

    price_events = price_parser(allprice)

    priceframe = pd.DataFrame(price_events,
                              columns=['Itemname', 'Effectnum', 'Unixtime', 'Currency', 'Value'])

    return priceframe, allprice


def convert_values(priceframe, allprice):
    """
    Some prices are defined in "keys", a standard in-game currency, while others are in "usd",
    standard US dollars. To convert all prices to USD, I'll be using the value of keys in
    refined metal, and the value of refined metal in USD, both from the full allprice object.

    Note: Price suggestions are typically "accepted" on backpack.tf in number of keys, but
    since I am prioritizing ease of interpretation, I'm converting to USD. This will mean
    mild added complexity on the deduplication step.

    :param priceframe: Unusual price dataframe, must have columns "Currency" and "Value"
    :param allprice: Full unprocessed price object
    :return: USD-converted unusual price dataframe
    """

    # avoid overwriting existing frame
    priceframe = priceframe.copy()

    # metal per key:
    keyprice = allprice['Mann Co. Supply Crate Key']['prices']['6']['Tradable']['Craftable'][0]['value']
    # dollars per metal:
    metalprice = allprice['Refined Metal']['prices']['6']['Tradable']['Craftable'][0]['value']

    keyinds = priceframe['Currency'] == 'keys'
    priceframe.loc[keyinds, 'Value'] = priceframe.loc[keyinds, 'Value'] * (keyprice * metalprice)

    return priceframe


# Detect stored price files (starts from most recent, don't need to flip)
fnames = os.listdir('Data')
# TODO OPTIONAL: Move filename format below to a config file
rawdataname = 'Backpack_spreadsheet_'
# Keep filenames that match the raw file storage format
fnames = [name for name in fnames if name[:len(rawdataname)] == rawdataname]
# Sort from most to least recent (largest to smallest)
fnames.sort(reverse=True)

# Initialize dataframe
orig_pricedf = pd.DataFrame()

# Loop through files:
for fname in fnames:
    # Load in example file.
    pricedf, allprices = price_loader(fname)
    pricedf = convert_values(pricedf, allprices)

    # Data filter: Drop all items that start with "Taunt:", their pricing is fundamentally
    # different from the pricing for other permanently-active unusuals. There's no overlap
    # since item names and effect numbers do not match between the two, but they do have a
    # different price distribution.
    nontauntinds = pricedf['Itemname'].transform(lambda x: 'Taunt:' not in x)
    pricedf = pricedf[nontauntinds]

    # Note: Values are not identical between files, even when item has not been repriced,
    # because changing key and metal values cause variation in USD price estimates.

    # Tack on new prices to the end of the dataframe
    pricedf = pd.concat([orig_pricedf, pricedf])
    # Remove duplicate pricing events, keeping most recent (uses current key -> dollar conversion)
    pricedf = pricedf.drop_duplicates(subset=['Itemname', 'Effectnum', 'Unixtime'], keep='first')

    # reinitialize
    orig_pricedf = pricedf.copy()

# Note: File will error out if no saved files exist, this is fine.

# MANUAL FILTER: Looks like at least one taunt is not labeled, "Shred Alert". Going to
# trim manually based on unusual effect, since taunt effects are numbered 3000+
pricedf = pricedf[pricedf['Effectnum'].astype(int) < 3000]

# Store the resulting dataframe
pricedf.to_csv(os.path.join('Data', 'Price_event_dataframe.csv'), index=False)
