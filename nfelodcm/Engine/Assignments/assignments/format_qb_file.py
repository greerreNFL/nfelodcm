import pandas as pd

qb_name_repl = {
    "Robert Griffin": "Robert Griffin III",
    "A.J. McCarron": "AJ McCarron",
    "Mitch Trubisky": "Mitchell Trubisky",
    "Joe Milton": "Joe Milton III",
    "Michael Penix" : "Michael Penix Jr.",
    "P.J. Walker" : "PJ Walker",
    "Phillip Walker" : "PJ Walker"
}

def fix_elo_qb_names(df):
    '''
    Standardizes QB names to match fastr
    '''
    ## fix player names ##
    df['qb1'] = df['qb1'].replace(qb_name_repl)
    df['qb2'] = df['qb2'].replace(qb_name_repl)
    ## return ##
    return df