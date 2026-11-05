## built-in ##
from typing import List, Dict
## external ##
import pandas as pd
import numpy

## local ##
from .Engine import DCMTable
import nfelodcm.nfelodcm.Utilities as utils
from .Engine.Storage.DCMStorage import DCMStorage

## wrappers and classes to interact with the package ##
def get_df(table: str) -> pd.DataFrame:
    """
    Load a single dataframe

    Parameters:
    * table: str - the name of the table to load

    Returns:
    * pd.DataFrame - the dataframe loaded from the table
    """
    engine = DCMTable(table)
    return engine.tableIO.df

def load(tables: List[str]) -> Dict[str, pd.DataFrame]:
    """
    loads an array of tables and returns a dictionary

    Parameters:
    * tables: List[str] - a list of table names to load

    Returns:
    * Dict[str, pd.DataFrame] - a dictionary of table names and their corresponding dataframes
    """
    ## init db structure ##
    db = {}
    utils.validate_table_request(tables)
    ## add tables ##
    for table in tables:
        db[table] = get_df(table)
    ## return db struc ##
    return db

def check(tables: List[str]) -> Dict:
    '''
    Return the freshness metadata init already computed.
    Does not pull and does not download a CSV.

    Parameters:
    * tables: List[str] - a list of table names to check

    Returns:
    * Dict - one result, with a tables list in input order
    '''
    utils.validate_table_request(tables)
    reported = []
    for table in tables:
        engine = DCMTable(table, load=False)
        reported.append(engine.report())
    return {'tables': reported}

def refresh(tables: List[str]) -> Dict:
    '''
    Run the existing load for each table, then return report().

    Parameters:
    * tables: List[str] - a list of table names to refresh

    Returns:
    * Dict - one result, with a tables list in input order
    '''
    utils.validate_table_request(tables)
    reported = []
    for table in tables:
        engine = DCMTable(table)
        reported.append(engine.report())
    return {'tables': reported}

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

def configure(storage):
    '''
    Prepare storage and make it the active backend.

    Parameters:
    * storage: StorageBackend - the backend to use for this process
    '''
    DCMStorage.configure(storage)

def get_season_state(state_type='last_full_week') -> tuple:
    '''
    Returns the season and week of the specified state type:
       'last_full_week' (default): the last week in which no games are still unplayed
       'last_partual_week': the last week where any game has been played
       'next_week': the first week with no games played
    '''
    state_dict = DCMStorage.get_season_state().week_states()
    ## check input ##
    if state_type not in state_dict:
        raise Exception('UTILITY ERROR: {0} is not an available state_type. Available types: {1}'.format(
            state_type, '\n     '.join(list(state_dict.keys()))
        ))
    ## if state valid, return ##
    return state_dict[state_type]['season'], state_dict[state_type]['week']

def list_tables() -> None:
    '''
    Lists all tables available to the package

    Parameters:
    * None

    Returns:
    * None (prints list of tables)
    '''
    ## get maps ##
    maps = utils.load_maps()
    ## print ##
    print('Available tables:')
    for table, table_map in maps.items():
        print('     {0} - {1}'.format(table, table_map['description']))
