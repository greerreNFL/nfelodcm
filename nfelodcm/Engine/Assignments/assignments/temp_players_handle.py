import pandas as pd
import numpy

def temp_players_handle(df):
    """
    Renames the the players.csv columns (draftround) to match
    the old naming. This is a temporary fix as nflfastR is updating
    pipelines and does not plan to address this bug

    When the new pipelines are officially released, players will point
    to the new file
    """
    ## rename ##
    df = df.rename(columns={
        'latest_team': 'team_abbr',
        'rookie_season': 'rookie_year', 
        'draft_team': 'draft_club',
        'draft_pick': 'draft_number',
        'draft_year': 'entry_year',
        'ngs_status' : 'status_description_abbr',
        'ngs_status_short_description': 'status_short_description'
    })
    
    ## add missing columns that were lost in migration ##
    df['team_seq'] = None  # Lost - was chronological team sequence
    df['current_team_id'] = None  # Lost - was numeric team ID
    df['gsis_it_id'] = None  # Lost - was GSIS IT identifier
    df['uniform_number'] = None  # Lost - was uniform number field
    
    return df