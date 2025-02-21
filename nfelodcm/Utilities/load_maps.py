## built-in ##
import pathlib
import json
from typing import Dict

def load_maps() -> Dict[str, Dict]:
    '''
    Loads all maps from the Maps folder

    Parameters:
    * None

    Returns:
    * Dict[str, Dict] - a dictionary of table names and their corresponding maps
    '''
    ## container for maps ##
    maps = {}
    ## get maps ##
    maps_dir = pathlib.Path(__file__).parent.parent.resolve() / 'Maps'
    existing_maps = list(maps_dir.glob('*.json'))
    ## check that maps were found ##
    if len(existing_maps) > 0:
        for map_path in existing_maps:
            ## parse the name ##
            table = map_path.stem
            ## load the map ##
            with open(map_path, 'r') as map_json:
                maps[table] = json.load(map_json)
    ## return ##
    return maps
