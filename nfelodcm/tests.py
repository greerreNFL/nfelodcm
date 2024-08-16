import pandas as pd
import pathlib
import time

from .nfelodcm import get_df

def test_all_maps():
    '''
    Attempts to load all maps
    '''
    print('Testing all available maps')
    map_loc = '{0}/Maps'.format(
        pathlib.Path(__file__).parent.resolve()
    )
    maps = []
    for f in pathlib.Path(map_loc).iterdir():
        if f.is_file() and f.suffix == ".json":
            maps.append(f.stem)
    print('     Found {0} maps'.format(len(maps)))
    if len(maps) > 0:
        for table_map in maps:
            print('     Loading {0}'.format(table_map))
            ## first load ##
            l1_start = time.time()
            get_df(table_map)
            l1_end = time.time()
            print('          1st load completed in {0} seconds'.format(round(
                l1_end-l1_start,3
            )))
            ## second load
            l2_start = time.time()
            get_df(table_map)
            l2_end = time.time()
            print('          2nd load completed in {0} seconds'.format(round(
                l2_end-l2_start,3
            )))


