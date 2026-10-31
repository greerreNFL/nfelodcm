import pathlib

## Package root: the nfelodcm/nfelodcm/ directory ##
## This module lives at nfelodcm/nfelodcm/Utilities/paths.py ##
## so .parent.parent gets us to nfelodcm/nfelodcm/ ##
PACKAGE_ROOT = pathlib.Path(__file__).parent.parent.resolve()

## package files ##
MAPS_DIR = PACKAGE_ROOT / 'Maps'
UTILS_DIR = PACKAGE_ROOT / 'Utilities'

## storage locations, relative to the active backend ##
DATA_DIR = pathlib.Path('Data')
STATE_DIR = pathlib.Path('State')
TABLE_STATE_DIR = STATE_DIR / 'Tables'
GLOBAL_STATE_DIR = STATE_DIR / 'Global'
PARTS_DATA_DIR = DATA_DIR / 'Parts'
PARTS_STATE_DIR = STATE_DIR / 'Parts'
SEASON_STATE_JSON = GLOBAL_STATE_DIR / 'season_state.json'


def map_path(table: str) -> pathlib.Path:
    '''
    Path to a table's config JSON in Maps/
    '''
    return MAPS_DIR / f'{table}.json'


def data_path(table: str) -> pathlib.Path:
    '''
    Path to a table's CSV data file in Data/
    '''
    return DATA_DIR / f'{table}.csv'


def table_state_path(table: str) -> pathlib.Path:
    '''
    Path to a table's state JSON in State/Tables/
    '''
    return TABLE_STATE_DIR / f'{table}.json'


def parts_data_dir(table: str) -> pathlib.Path:
    '''
    Path to a table's per-season cache directory in Data/Parts/{table}/
    '''
    return PARTS_DATA_DIR / table


def iter_state_path(table: str) -> pathlib.Path:
    '''
    Path to a table's per-season state JSON in State/Parts/{table}.json
    '''
    return PARTS_STATE_DIR / f'{table}.json'
