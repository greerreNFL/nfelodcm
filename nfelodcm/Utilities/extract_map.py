import numpy

def extract_map(map):
    """
    Extracts the map from a set of cols, and returns a col list and dtypes
    """
    ## init containers ##
    columns = []
    dtypes = {}
    ## init a dict of dtypes ##
    ## The json config can only have strings and numbers, so in instances ##
    ## where a string alias can't be passed to dtypes (ie if you wanted to specify numpy.int32)
    ## then this dict will handle the conversion ##
    ## This is effectively custom aliasing for dtypes ##
    dtype_conversion ={
        'str' : 'string',
    }
    ## iter map ##
    for k, v in map.items():
        ## add field to cols ##
        columns.append(k)
        ## parse cast type ##
        if v is None:
            v = 'infer'
        ## if cast requires a conversion, then convert ##
        if v in dtype_conversion:
            v = dtype_conversion[v]
        ## add to the dtypes dict ##
        dtypes[k] = v
    ## return ##
    return columns, dtypes
