# -*- coding: utf-8 -*-

from collections import OrderedDict
import pandas as pd


def dataframe(df):
    if not isinstance(df, pd.DataFrame):
        raise Exception('pandas DataFrame expected, got %s' % type(df))
    return {'json': OrderedDict((k, v.tolist()) for k, v in df.iterrows()),
        'columns': list(df.columns)}
