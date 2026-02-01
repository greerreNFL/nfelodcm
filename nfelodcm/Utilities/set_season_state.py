import pandas as pd
import numpy
import datetime

from .paths import SEASON_STATE_JSON
from nfelodcm.nfelodcm.Engine.Types import SeasonState

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

        ## build next week values ##
        try:
            next_week = {
                "season": int(next.iloc[0]['season']),
                "week": int(next.iloc[0]['week'])
            }
        except (IndexError, ValueError):
            next_week = {"season": None, "week": None}

        ## build and save state ##
        state = SeasonState(
            last_full_week={
                "season": int(full.iloc[-1]['season']),
                "week": int(full.iloc[-1]['week'])
            },
            last_partial_week={
                "season": int(partial.iloc[-1]['season']),
                "week": int(partial.iloc[-1]['week'])
            },
            next_week=next_week
        )
        state.save(SEASON_STATE_JSON)

    except Exception as e:
        print('WARN: Could not set season states with nflgamedata. Inferring from date instead.')
        print('       {0}'.format(e))
        today = datetime.datetime.today()

        ## infer season from current month ##
        if today.month < 9:
            inferred_season = today.year - 1
        else:
            inferred_season = today.year

        state = SeasonState(
            last_full_week={"season": inferred_season, "week": None},
            last_partial_week={"season": None, "week": None},
            next_week={"season": None, "week": None}
        )
        state.save(SEASON_STATE_JSON)
