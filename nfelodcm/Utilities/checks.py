import pandas as pd
import numpy
import pathlib
import json
import datetime

## script that runs on package import to check format of config file, existance of csvs, and columns ##
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

