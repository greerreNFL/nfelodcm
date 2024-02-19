import pandas as pd
import numpy

def penalty_formatting(df):
    """
    Adds additional context to penalties
    """
    ## offensive and defensive penalties ##
    df['off_penalty'] = numpy.where(
        df['penalty_team'] == df['posteam'],
        1,
        0
    )
    df['def_penalty'] = numpy.where(
        df['penalty_team'] == df['defteam'],
        1,
        0
    )
    ## remove nans from penalties to enable groupings ##
    df['penalty_type'] = df['penalty_type'].fillna('No Penalty')
    return df
