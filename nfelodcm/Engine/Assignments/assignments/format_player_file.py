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
    "Phillip Walker": "P.J. Walker"
}


def fix_fastr_qb_names(df):
    '''
    Standardizes QB names to match elo
    '''
    ## fix player names ##
    df['full_name'] = df['full_name'].replace(qb_name_repl)
    ## return ##
    return df