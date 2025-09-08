import pandas as pd

qb_name_repl = {
    "Jacob Dolegala": "Jake Dolegala",
    "Robert Griffin": "Robert Griffin III",
    "Thad Lewis": "Thaddeus Lewis",
    "E.J. Manuel": "EJ Manuel",
    "A.J. McCarron": "AJ McCarron",
    "Matthew McGloin": "Matt McGloin",
    "Vincent Testaverde": "Vinny Testaverde",
    "Mike Vick": "Michael Vick",
    "Phillip Walker": "PJ Walker",
    "P.J. Walker": "PJ Walker"
}


def fix_fastr_qb_names(df):
    '''
    Standardizes QB names to match elo
    '''
    ## fix player names ##
    for col in ['full_name', 'display_name']:
        if col in df.columns:
            df[col] = df[col].replace(qb_name_repl)
    ## return ##
    return df