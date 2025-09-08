import pandas as pd

def player_stats_repl(df):
    """
    Replaces new stats_player to match old player_stats
    """
    ## cols renames##
    potential_changes = {
        'passing_interceptions': 'interceptions',
        'sacks_suffered' : 'sacks',
        'sack_yards_lost': 'sack_yards',
        'team' : 'recent_team',
    }
    ## get repl dict ##
    repls = {k: v for k, v in potential_changes.items() if k in df.columns}
    ## replace columns ##
    df = df.rename(columns=repls)
    ## return ##
    return df
    
