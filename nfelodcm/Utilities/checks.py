import pandas as pd

from .paths import MAPS_DIR, DATA_DIR, table_state_path, iter_state_path, ensure_dirs
from nfelodcm.nfelodcm.Engine.Types import TableState, IterState


def check_data_folder():
    '''
    Runs on load and checks that the data folder exists. If it does not, it creates it
    '''
    ensure_dirs()

def check_data():
    '''
    Runs on load and checks for the existence of local data for each map. If data does not exist,
    freshness meta data in the state is reset
    '''
    ## get maps ##
    maps = list(MAPS_DIR.glob('*.json'))
    ## check that maps were found ##
    if len(maps) == 0:
        return
    ## for each map, parse name, check for csv, and make updates as needed ##
    for map_path in maps:
        ## parse the name ##
        table = map_path.stem
        ## check for the csv ##
        csv_path = DATA_DIR / '{0}.csv'.format(table)
        if not csv_path.exists():
            ## if the csv does not exist, reset table state ##
            state = TableState()
            state.save(table_state_path(table))
            ## also reset iter state if it exists ##
            isp = iter_state_path(table)
            if isp.exists():
                iter_state = IterState()
                iter_state.save(isp)
