import pandas as pd
import numpy
import pathlib
import json
import datetime


def check_struc(config):
    """
    Checks to ensure the config structure is valid
    """
    ## config requirements ##
    config_requiremnets = {
        'name' : {'type':str, 'nullable' : False},
        'description' : {'type':str, 'nullable' : False},
        'last_local_update' : {'type':str, 'nullable' : True},
        'download_url' : {'type':str, 'nullable' : False},
        'compression' : {'type':str, 'nullable' : True},
        'engine' : {'type':str, 'nullable' : True},
        'iter' : {'type':dict, 'nullable' : False},
        'assignments' : {'type':list, 'nullable' : False},
        'map' : {'type':dict, 'nullable' : False},
    }
    ## containers ##
    passing = True
    errors = []
    for k, v in config_requiremnets.items():
        if k not in config:
            ## check that config has the prop ##
            passing = False
            errors.append({
                'type' : 'config_structure',
                'error_msg' : '{0} is a required property, but was not found in the map config'.format(
                    k
                )
            })
        else:
            ## make sure its of the right type ##
            if config[k] is None and not v['nullable']:
                passing = False
                errors.append({
                    'type' : 'config_structure',
                    'error_msg' : '{0} is cannot be null'.format(
                        k
                    )
                })
            elif config[k] is not None:
                if not isinstance(config[k], v['type']):
                    errors.append({
                        'type' : 'config_structure',
                        'error_msg' : '{0} must be a {1}'.format(
                            k, v['type']
                        )
                    })
    ## return ##            
    return passing, errors

def check_map_type(map):
    """
    Iterates through map keys value pairs and ensures values are an allowed type
    """
    allowed_types = [
        'object', 'int32', 'int64', 'float32', 'float64',
        'boolean', 'interval', 'category', 'datetime64[ns, <tz>]',
        'bool'
    ]
    ## containers ##
    passing = True
    errors = []
    for k, v in map.items():
        if v not in allowed_types:
            passing = False
            errors.append({
                'error_type' : 'dtype',
                'error_msg' : '{0} type provided for {1} is not an accepted datatype'.format(
                    v, k 
                )
            })
    ## return ##
    return passing, errors

def check_data():
    '''
    Runs on load and checks for the existence of local data for each map. If data does not exist,
    freshness meta data in the map is reset
    '''
    ## get maps ##
    maps_dir = pathlib.Path(__file__).parent.parent.resolve() / 'Maps'
    maps = list(maps_dir.glob('*.json'))
    ## check that maps were found ##
    if len(maps) == 0:
        return
    ## for each map, parse name, check for csv, and make updates as needed ##
    for map_path in maps:
        ## parse the name ##
        table = map_path.stem
        ## check for the csv ##
        csv_path = pathlib.Path(
            pathlib.Path(__file__).parent.parent.resolve() / 'Data' / '{0}.csv'.format(table)
        )
        csv_path.exists()
        if not csv_path.exists():
            ## if the csv does not exist, update the map file ##
            with open(map_path, 'r+') as config_file:
                data = json.load(config_file)
                data['last_local_update'] = None
                data['freshness']['last_freshness_check'] = None
                config_file.seek(0)  # reset file position to the beginning
                json.dump(data, config_file, indent=2)
                config_file.truncate()  # remove remaining part```
