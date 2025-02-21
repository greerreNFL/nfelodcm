## built-in ##
import pathlib
import json
from typing import List, Dict
## external ##
import pandas as pd
import numpy

## local ##
from .Engine import DCMTable
import nfelodcm.nfelodcm.Utilities as utils

## ensure local data folder exists ##
utils.check_data_folder()
## init season state on load ##
utils.set_season_state()
## update local data freshness meta as needed ##
utils.check_data()

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
    return engine.localIO.df

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
    ## check that all passed tables have maps ##
    map_data = utils.load_maps()
    maps = list(map_data.keys()) if len(map_data) > 0 else []
    missing_maps = [t for t in tables if t not in maps]
    if len(missing_maps) > 0:
        raise Exception('MAP ERROR: The following tables do not have maps: {0}'.format(
            '\n     '.join(missing_maps)
        ))
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

def get_season_state(state_type='last_full_week') -> tuple:
    '''
    Returns the season and week of the specified state type:
       'last_full_week' (default): the last week in which no games are still unplayed
       'last_partual_week': the last week where any game has been played
       'next_week': the first week with no games played
    '''
    ## open global variables json ##
    global_variables = None
    with open('{0}/Utilities/global_variables.json'.format(pathlib.Path(__file__).parent.resolve()), 'r') as fp:
        ## load config ##
        global_variables = json.load(fp)
    ## check input ##
    if state_type not in list(global_variables['season_states'].keys()):
        raise Exception('UTILITY ERROR: {0} is not an available state_type. Available types: {1}'.format(
            state_type, '\n     '.join(list(global_variables['season_states'].keys()))
        ))
    ## if state valid, return ##
    return global_variables['season_states'][state_type]['season'], global_variables['season_states'][state_type]['week']

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
