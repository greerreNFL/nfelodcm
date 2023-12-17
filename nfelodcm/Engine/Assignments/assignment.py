from .assignments import game_id_repl

## a dictionary that holds assignments and the columns they add ##
assignments = {
    'game_id_repl' : {
        'func' : game_id_repl,
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
