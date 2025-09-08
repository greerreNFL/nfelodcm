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
    for col in ['qb1', 'qb2', 'name_id', 'display_name']:
        if col in df.columns:
            df[col] = df[col].replace(qb_name_repl)
    ## return ##
    return df