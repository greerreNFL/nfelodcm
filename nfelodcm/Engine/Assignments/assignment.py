from .assignments import (
    game_id_repl, penalty_formatting, desc_based_plays
)

## a dictionary that holds assignments and the columns they add ##
assignments = {
    'game_id_repl' : {
        'func' : game_id_repl,
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
