import pandas as pd
import numpy

def desc_based_plays(df):
    '''
    Infers play types from description that may show up
    differently in the standard columns, especially when 
    there is a penalty
    '''
    ## infer pass play ##
    df['desc_based_dropback'] = numpy.where(
        (
            (df['desc'].str.contains(' pass ', regex=False)) |
            (df['desc'].str.contains(' sacked', regex=False)) |
            (df['desc'].str.contains(' scramble', regex=False))
        ),
        1,
        0
    )
    ## infer run ##
    df['desc_based_run'] = numpy.where(
        (
            (~df['desc'].str.contains(' pass ', regex=False, na=False)) &
            (~df['desc'].str.contains(' sacked', regex=False, na=False)) &
            (~df['desc'].str.contains(' scramble', regex=False, na=False)) &
            (~df['desc'].str.contains(' kicks ', regex=False, na=False)) &
            (~df['desc'].str.contains(' punts ', regex=False, na=False)) &
            (~df['desc'].str.contains(' field goal ', regex=False, na=False)) &
            (df['desc'].str.contains(' to ', regex=False)) &
            (df['desc'].str.contains(' for ', regex=False))
        ),
        1,
        0
    )
    ## add new cols ##
    df['qb_dropback_all'] = df[[
        'qb_dropback', 'desc_based_dropback'
    ]].max(axis=1)
    df['rush_attempt_all'] = df[[
        'rush_attempt', 'desc_based_run'
    ]].max(axis=1)
    ## create a specific play call field ##
    df['play_call'] = numpy.where(
        df['qb_dropback_all'] == 1,
        'Pass',
        numpy.where(
            df['rush_attempt_all'] == 1,
            'Run',
            numpy.nan
        )
    )
    ## clean up ##
    df = df.drop(columns=[
        'desc_based_dropback', 'desc_based_run'
    ]).copy()
    ## return ##
    return df