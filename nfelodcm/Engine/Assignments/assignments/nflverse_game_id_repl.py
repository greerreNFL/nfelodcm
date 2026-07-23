from ..resources.team_id_map import FASTR_TO_LEGACY_TEAM


def nflverse_game_id_repl(df):
    """
    Remap team tokens inside nflverse_game_id to legacy nfelo ids.

    Parses season_week_away_home, replaces away/home via the shared
    fastr->legacy map, and reconstitutes the id. Fully vectorized.
    """
    if 'nflverse_game_id' not in df.columns:
        return df
    gid = df['nflverse_game_id']
    parts = gid.str.split('_', n=3, expand=True)
    rebuilt = (
        parts[0] + '_' +
        parts[1] + '_' +
        parts[2].replace(FASTR_TO_LEGACY_TEAM) + '_' +
        parts[3].replace(FASTR_TO_LEGACY_TEAM)
    )
    df['nflverse_game_id'] = rebuilt.where(gid.notna(), gid)
    return df
