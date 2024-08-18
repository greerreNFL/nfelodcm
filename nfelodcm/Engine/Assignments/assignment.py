from .assignments import (
    fastr_team_id_repl, penalty_formatting, desc_based_plays,
    score_clean, fix_elo_qb_names, fix_fastr_qb_names
)

## a dictionary that holds assignments and the columns they add ##
assignments = {
    'fastr_team_id_repl' : {
        'func' : fastr_team_id_repl,
        'new_columns' : []
    },
    'penalty_formatting' : {
        'func' : penalty_formatting,
        'new_columns' : []
    },
    'desc_based_plays' : {
        'func' : desc_based_plays,
        'new_columns' : [
            ('qb_dropback_all', 'float32'),
            ('rush_attempt_all', 'float32'),
            ('play_call', 'str'),
        ]
    },
    'score_clean' : {
        'func' : score_clean,
        'new_columns' : []
    },
    'fix_elo_qb_names' : {
        'func' : fix_elo_qb_names,
        'new_columns' : []
    },
    'fix_fastr_qb_names' : {
        'func' : fix_fastr_qb_names,
        'new_columns' : []
    }
}

def assign(df, assignment):
    """
    An extension on the pandas assign() function which allows the dcm to add non-standard fields
    to the CSVs it downloads.
    """
    ## get the function ##
    func = assignments[assignment]['func']
    ## return the assignment ##
    return func(df)


def assignment_columns_added(assignment):
    """
    When an assignment is used and adds columns to a dataframe not in the map,
    assignment_columns_added() will returns a list of the columns added, so they can
    be passed when reading from cache
    """
    return assignments[assignment]['new_columns']
