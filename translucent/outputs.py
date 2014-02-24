# -*- coding: utf-8 -*-

from ._compat import OrderedDict
import warnings

PANDAS = False

try:
    import pandas as pd
    PANDAS = True
except:
    warnings.warn('pandas not installed, skipping related components')

if PANDAS:
    def dataframe(df):
        if not isinstance(df, pd.DataFrame):
            raise Exception('pandas DataFrame expected, got %s' % type(df))
        return {'json': OrderedDict((k, v.tolist()) for k, v in df.iterrows()),
            'columns': list(df.columns)}
