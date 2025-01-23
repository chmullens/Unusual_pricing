import os
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, roc_auc_score

# Import generated dataframe:
# Note: Defaults to importing our columns in the correct datatypes:
#     Itemname      object
#     Effectnum      int64
#     Unixtime       int64
#     Value        float64
# TODO OPTIONAL: Verify datatypes, this would help catch any improper inputs
data = pd.read_csv(os.path.join('Data', 'Price_event_dataframe.csv'))

