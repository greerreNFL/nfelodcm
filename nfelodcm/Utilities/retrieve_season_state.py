from .paths import SEASON_STATE_JSON
from nfelodcm.nfelodcm.Engine.Types import SeasonState

## reads season state and returns values ##

def current_season(type="last_full_week"):
    """
    Returns the current season
    """
    state = SeasonState.load(SEASON_STATE_JSON)
    state_dict = state.to_dict()
    ## return ##
    if type in state_dict:
        return state_dict[type]['season']
    else:
        raise ValueError('Invalid season type: {0}'.format(type))
