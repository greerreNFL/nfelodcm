import json
import pathlib

## reads global variables and returns values ##

def current_season(type="last_full_week"):
    """ 
    Returns the current season
    """
    global_variables = None
    with open('{0}/global_variables.json'.format(pathlib.Path(__file__).parent.resolve()), 'r') as fp:
        ## load config ##
        global_variables = json.load(fp)
    
    ## return ##
    if type in global_variables['season_states']:
        return global_variables['season_states'][type]['season']
    else:
        raise ValueError('Invalid season type: {0}'.format(type))
