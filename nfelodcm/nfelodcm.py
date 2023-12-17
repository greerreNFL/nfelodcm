import pandas as pd
import numpy

from .Engine import DCMTable
import nfelodcm.nfelodcm.Utilities as utils

## init season state on load ##
utils.set_season_state()

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