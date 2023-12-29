import pandas as pd
import numpy

from .Engine import DCMTable
import nfelodcm.nfelodcm.Utilities as utils

## init season state on load ##
utils.set_season_state()
## update local data freshness meta as needed ##
utils.check_data()

## wrappers and classes to interact with the package ##
def get_df(table):
    """
    gets a single table
    """
    engine = DCMTable(table)
    return engine.localIO.df

def load(tables):
    """
    loads an array of tables and returns a dictionary
    """
    ## init db structure ##
    db = {}
    ## add tables ##
    for table in tables:
        db[table] = get_df(table)
    ## return db struc ##
    return db

def get_map(url):
    '''
    reads a web based csv and returns a column map
    with 64 to 32 downcasting
    '''
    df = pd.read_csv(url)
    for col in df.columns.tolist():
        dtype = df[col].dtype.name
        ## downcast ##
        if '64' in dtype:
            dtype = dtype.replace('64', '32')
        ## print ##
        print('"{0}": "{1}",'.format(
            col, dtype
        ))
        