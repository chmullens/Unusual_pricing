import os
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_squared_error

# Import generated dataframe:
# Note: Defaults to importing our columns in the correct datatypes:
#     Itemname      object
#     Effectnum      int64
#     Unixtime       int64
#     Currency      object
#     Value        float64
# TODO OPTIONAL: Verify datatypes, would help catch any improper inputs
# Why have I not? Mainly because the data seems to be pretty darn reliable, and I have
# not run into any problems with it so far.
data = pd.read_csv(os.path.join('Data', 'Price_event_dataframe.csv'))

# Pre-pipeline processing:

# Generate target value (log price)
data['Value_ln'] = np.log(data['Value'])

# Generate time-weighting variable: Any prices established within the past six months
# should be treated as fully relevant, but any before that should be increasingly less
# relevant for the current price. I'm using approximations here, but for business cases
# where the specific year/month cutoffs are relevant, it's easy to do this more cleanly
# using datetime objects.
oneyear_s = 365.25 * 24*60*60

def time_transform(timevals, currentday=data['Unixtime'].max(),
                   currentenough=0.5*oneyear_s, halflife=2*oneyear_s):
    # Calculate seconds before most recent update, offset by time we count as current
    timevalout = currentday - timevals - currentenough
    # Clip at zero and 20 years
    timevalout = np.clip(timevalout, a_min=0, a_max=20*oneyear_s)
    # Attenuate weight over time using half-life, with 2 years in seconds as the default
    timevalout = 0.5 ** (timevalout / halflife)

    return timevalout

data['Time_weight'] = time_transform(data['Unixtime'])

# Let's functionalize our fitting here, for easy retests on differently-filtered sets.
# This is the point where going object-oriented would be much easier, since I'd have to
# pass many variables in here if I wanted to treat these notably differently.

# TODO OPTIONAL: Switch to fixed train/test assignment. This will mean that the train/test
#  mix isn't identical for the alternative models, where some data is dropped, but it will
#  be randomly distributed and makes the comparison between them more straightforward

def generate_fit(dataset):
    """ Simple model fit using sklearn pipelines """
    # Data split:
    # I'm using a default 80/20 train/test split here, but if we were optimizing model design
    # this would be a great spot for train/test/validation using an out-of-time validation
    # set or a validation set disproportionately sampled from our most recent data
    X_tr, X_test, y_tr, y_test = train_test_split(dataset[['Itemname','Effectnum','Time_weight']],
                                                  dataset['Value_ln'],
                                                  random_state=100)

    # Establish pipeline:
    pipe = Pipeline([
        ('onehot', OneHotEncoder(handle_unknown='ignore')),
        ('LinReg', LinearRegression())
    ])

    modelcols = ['Itemname','Effectnum']
    # Fit:
    pipe.fit(X_tr[modelcols], y_tr,
             LinReg__sample_weight=X_tr['Time_weight'])
    # Make stored predictions:
    y_tr_pred = pipe.predict(X_tr[modelcols])
    y_tr_pred = pd.Series(y_tr_pred, index=X_tr.index, name='Value_ln_pred')
    y_test_pred = pipe.predict(X_test[modelcols])
    y_test_pred = pd.Series(y_test_pred, index=X_test.index, name='Value_ln_pred')

    # Output convenient version of test set for comparison:
    y_tester_frame = pd.DataFrame(zip(y_test, y_test_pred),
                                  columns=['Actual','Pred'],
                                  index=X_test.index)
    testeyeball_df = pd.concat([X_test, y_tester_frame], axis=1)

    # Display some base metrics:
    rsquared_tr = r2_score(y_tr, y_tr_pred)
    rsquared_test = r2_score(y_test, y_test_pred)
    print(f'\nModel r^2: {rsquared_tr:.3f} train, {rsquared_test:.3f} test')
    mse_tr = mean_squared_error(y_tr, y_tr_pred)
    mse_test = mean_squared_error(y_test, y_test_pred)
    print(f'Model MSE: {mse_tr:.3f} train, {mse_test:.3f} test')

    # For these items, RELATIVE price is the most crucial. Is this hat worth more than
    # the other one? Because head-to-head comparisons are common, One good metric I could
    # add here would be an Elo-based ranking, where I compare each item against each other
    # item in the predicted set and the actual set, and look at the items for which the
    # difference is largest. Where does it miss?

    # Stick dataset back together, with ID flags
    df_tr = pd.concat([X_tr, y_tr, y_tr_pred], axis=1)
    df_tr['TrTest'] = 'tr'
    df_test = pd.concat([X_test, y_test, y_test_pred], axis=1)
    df_test['TrTest'] = 'test'
    outdf = pd.concat([df_tr, df_test], axis=0)

    return testeyeball_df, pipe, outdf

# TODO OPTIONAL: Convert fits to a loop, storing outputs in lists to start with, then for
#  the metrics just step through the list rather than use manual naming like below. If I
#  were doing more estimates on this, I'd switch, but for three it's reasonable.

# Basic fit: Use all data
test_df1, pipe1, outdf1 = generate_fit(data)

# Fit 2: Exclude our older prices! We talked about this earlier; does including more info
# about historical prices for these items actually help it predict values, or are current
# prices the most important?
data_v2 = (data
           .sort_values('Unixtime', ascending=False)
           .drop_duplicates(['Itemname','Effectnum'], keep='first')
           )
test_df2, pipe2, outdf2 = generate_fit(data_v2)

# Fit 3: There's an effective floor on unusual prices around $9, where many items sort of
# cluster up. Why? There's a perceived value in having *any* unusual cosmetic that isn't
# directly due to the specific properties of the item. The default linear regression has
# an intercept term, so we don't need to offset the floor or anything, but what if the
# data we have from those low grade items just isn't very informative? Filter low value
# items out, then see how the model does:
data_v3 = data[data['Value'] > 15]
test_df3, pipe3, outdf3 = generate_fit(data_v3)


# But wait, what do we actually care about with our data? For performance that is this
# close, you need to have matched-item comparisons.

# Generate a dataframe with all train/test assignments and predictions by model:
outdf_all = pd.merge(outdf1, outdf2[['Value_ln_pred','TrTest']],
                     how='left', left_index=True, right_index=True, suffixes=('','_v2'))
outdf_all = pd.merge(outdf_all, outdf3[['Value_ln_pred','TrTest']],
                     how='left', left_index=True, right_index=True, suffixes=('','_v3'))

matched_data = outdf_all[
    (outdf_all['TrTest'] == 'test') &
    (outdf_all['TrTest'] == outdf_all['TrTest_v2']) &
    (outdf_all['TrTest_v2']== outdf_all['TrTest_v3'])
]

rsquared_v1 = r2_score(matched_data['Value_ln'], matched_data['Value_ln_pred'])
rsquared_v2 = r2_score(matched_data['Value_ln'], matched_data['Value_ln_pred_v2'])
rsquared_v3 = r2_score(matched_data['Value_ln'], matched_data['Value_ln_pred_v3'])
mse_v1 = mean_squared_error(matched_data['Value_ln'], matched_data['Value_ln_pred'])
mse_v2 = mean_squared_error(matched_data['Value_ln'], matched_data['Value_ln_pred_v2'])
mse_v3 = mean_squared_error(matched_data['Value_ln'], matched_data['Value_ln_pred_v3'])

print('\nItems assigned to "test" on all models:', len(matched_data))
print(f'Matched test items, r^2: {rsquared_v1:.3f}, {rsquared_v2:.3f}, {rsquared_v3:.3f}')
print(f'Matched test items, MSE: {mse_v1:.3f}, {mse_v2:.3f}, {mse_v3:.3f}')
