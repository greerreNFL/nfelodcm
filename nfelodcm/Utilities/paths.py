import pathlib

## Package root: the nfelodcm/nfelodcm/ directory ##
## This module lives at nfelodcm/nfelodcm/Utilities/paths.py ##
## so .parent.parent gets us to nfelodcm/nfelodcm/ ##
PACKAGE_ROOT = pathlib.Path(__file__).parent.parent.resolve()

## top-level directories ##
MAPS_DIR = PACKAGE_ROOT / 'Maps'
DATA_DIR = PACKAGE_ROOT / 'Data'
STATE_DIR = PACKAGE_ROOT / 'State'
UTILS_DIR = PACKAGE_ROOT / 'Utilities'

## state subdirectories ##
TABLE_STATE_DIR = STATE_DIR / 'Tables'
GLOBAL_STATE_DIR = STATE_DIR / 'Global'

## parts directories (per-season caches) ##
PARTS_DATA_DIR = DATA_DIR / 'Parts'
PARTS_STATE_DIR = STATE_DIR / 'Parts'

## specific files ##
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
    Path to a table's state JSON in State/tables/
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


def ensure_dirs() -> None:
    '''
    Ensure runtime directories exist. Called once on import.
    '''
    DATA_DIR.mkdir(exist_ok=True)
    TABLE_STATE_DIR.mkdir(parents=True, exist_ok=True)
    GLOBAL_STATE_DIR.mkdir(parents=True, exist_ok=True)
    PARTS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PARTS_STATE_DIR.mkdir(parents=True, exist_ok=True)
