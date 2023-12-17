import pandas as pd
import numpy
import pathlib
import json
import datetime

## script that runs on package import to set season states ##
##      last partial week is the last week with any played game ##
##      last full week is the last week with no unplayed games ##
##      next week is the first week with no played games ##
## This script leverages nflgamedata to determine states ##

def set_season_state():
    ## Try to set the state with data, but as a backup, infer from month ##
    try:
        games = pd.read_csv(
            "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
        )
        ## demarcate played games ##
        games['played'] = numpy.where(
            ~pd.isnull(games['result']),
            1,
            0
        )
        
        ## get weekly pct played ##
        weeks = games.groupby(['season', 'week']).agg(
            pct_played = ('played', 'mean')
        ).reset_index()
        weeks = weeks.sort_values(
            by=['season', 'week'],
            ascending=[True, True]
        ).reset_index(drop=True)
        
        ## cut data by pct played ##
        partial = weeks[weeks['pct_played'] > 0].copy()
        full = weeks[weeks['pct_played'] == 1].copy()
        next = weeks[weeks['pct_played'] == 0].copy()
        
        ## open global variables json and write values ##
        global_variables = None
        with open('{0}/global_variables.json'.format(pathlib.Path(__file__).parent.resolve()), 'r') as fp:
            ## load config ##
            global_variables = json.load(fp)
        
        ## set values ##
        global_variables['season_states']['last_full_week']['week'] = int(full.iloc[-1]['week'])
        global_variables['season_states']['last_full_week']['season'] = int(partial.iloc[-1]['season'])
        global_variables['season_states']['last_partial_week']['week'] = int(partial.iloc[-1]['week'])
        global_variables['season_states']['last_partial_week']['season'] = int(partial.iloc[-1]['season'])
        try:
            global_variables['season_states']['next_week']['week'] = int(next.iloc[0]['week'])
            global_variables['season_states']['next_week']['season'] = int(next.iloc[0]['season'])
        except:
            global_variables['season_states']['next_week']['week'] = numpy.nan
            global_variables['season_states']['next_week']['season'] = numpy.nan
        ## write ##
        with open('{0}/global_variables.json'.format(pathlib.Path(__file__).parent.resolve()), 'w') as fp:
            json.dump(global_variables, fp, indent=4)
        
    except Exception as e:
        print('WARN: Could not set season states with nflgamedata. Inferring from date instead.')
        print('       {0}'.format(e))
        today = datetime.datetime.today()
        
        ## open global variables json and write values ##
        global_variables = None
        with open('{0}/global_variables.json'.format(pathlib.Path(__file__).parent.resolve), 'r') as fp:
            ## load config ##
            global_variables = json.load(fp)
        
        ## set values ##
        global_variables['season_states']['last_full_week']['week'] = numpy.nan
        global_variables['season_states']['last_partial_week']['week'] = numpy.nan
        global_variables['season_states']['last_partial_week']['season'] = numpy.nan
        global_variables['season_states']['next_week']['week'] = numpy.nan
        global_variables['season_states']['next_week']['season'] = numpy.nan
        if today.month < 9:
            global_variables['season_states']['last_full_week']['season'] = today.year - 1
        else:
            global_variables['season_states']['last_full_week']['season'] = today.year
