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
    df = df.rename(columns={'draftround': 'draft_round'})
    return df