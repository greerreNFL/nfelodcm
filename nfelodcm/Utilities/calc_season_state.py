import pandas as pd
import numpy
import datetime

from .paths import map_path
from .extract_map import extract_map
from nfelodcm.nfelodcm.Engine.Types import SeasonState, TableConfig

## calculates season state from nflgamedata games ##
##      last partial week is the last week with any played game ##
##      last full week is the last week with no unplayed games ##
##      next week is the first week with no played games ##
## Storage and caching are handled by DCMStorage.get_season_state ##

def calc_season_state(games=None):
    '''
    Calculates season state and returns it with a UTC last_updated timestamp.
    Downloads games with the games map unless a games df is passed.
    Raises if games cannot be downloaded or the state cannot be calculated.
    '''
    ## download games when a df is not passed ##
    if games is None:
        config = TableConfig.load(map_path('games'))
        columns, dtypes = extract_map(config.map)
        games = pd.read_csv(
            config.download_url,
            usecols=columns,
            dtype=dtypes,
            engine=config.engine
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

    ## build state ##
    return SeasonState(
        last_full_week={
            "season": int(full.iloc[-1]['season']),
            "week": int(full.iloc[-1]['week'])
        },
        last_partial_week={
            "season": int(partial.iloc[-1]['season']),
            "week": int(partial.iloc[-1]['week'])
        },
        next_week=next_week,
        last_updated=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

def infer_season_state():
    '''
    Infers season state from the current month. Used only when season
    state cannot be calculated. last_updated is None, so it is never
    treated as current or stored.
    '''
    today = datetime.datetime.today()
    ## infer season from current month ##
    if today.month < 9:
        inferred_season = today.year - 1
    else:
        inferred_season = today.year
    return SeasonState(
        last_full_week={"season": inferred_season, "week": None},
        last_partial_week={"season": None, "week": None},
        next_week={"season": None, "week": None}
    )
