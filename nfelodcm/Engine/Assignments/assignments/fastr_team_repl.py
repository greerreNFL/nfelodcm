import pandas as pd

## assignment functions that replaces fastr team names with legacy team names ##
repl = {
    'LV' : 'OAK',
    'SD' : 'LAC',
    'STL' : 'LAR',
    'LA' : 'LAR',
}

def team_id_repl(df):
    """
    Replaces fastr team ids with a legacy nfelo ids.
    """
    ## if a col with team names exists, replace it ##
    for col in [
        'home_team', 'away_team', 'team_abbr',
        'posteam', 'defteam', 'penalty_team',
        'side_of_field', 'timeout_team', 'td_team',
        'return_team', 'possession_team',
        'recent_team', 'opponent_team'
    ]:
        if col in df.columns:
            df[col] = df[col].replace(repl)
    ## if game if is also in the DF, replace it
    if 'game_id' in df.columns:
        ## id col ##
        df['game_id'] = (
            df['season'].astype('str') + '_' +
            df['week'].astype('str').str.zfill(2) + '_' +
            df['away_team'] + '_' +
            df['home_team']
        )
    return df
