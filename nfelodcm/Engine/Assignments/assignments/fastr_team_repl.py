import pandas as pd

## assignment functions that replaces fastr team names with legacy team names ##
repl = {
    'LV' : 'OAK',
    'SD' : 'LAC',
    'STL' : 'LAR',
    'LA' : 'LAR',
}

def game_id_repl(df):
    """
    Replaces fastr game_ids with a legacy game id.
    """
    df['game_id'] = (
        df['season'].astype('str') + '_' +
        df['week'].astype('str').str.zfill(2) + '_' +
        df['away_team'].replace(repl) + '_' +
        df['home_team'].replace(repl)
    )
    return df
