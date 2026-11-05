from .load_maps import load_maps

def validate_table_request(tables):
    '''
    Reject an empty list, duplicate names, and names with no map.
    '''
    if len(tables) == 0:
        raise Exception('MAP ERROR: No tables were given.')
    seen = []
    duplicates = []
    for table in tables:
        if table in seen and table not in duplicates:
            duplicates.append(table)
        if table not in seen:
            seen.append(table)
    if len(duplicates) > 0:
        raise Exception('MAP ERROR: Duplicate table names: {0}'.format(
            ', '.join(duplicates)
        ))
    ## check that all passed tables have maps ##
    map_data = load_maps()
    maps = list(map_data.keys()) if len(map_data) > 0 else []
    missing_maps = [t for t in tables if t not in maps]
    if len(missing_maps) > 0:
        raise Exception('MAP ERROR: The following tables do not have maps: {0}'.format(
            '\n     '.join(missing_maps)
        ))
