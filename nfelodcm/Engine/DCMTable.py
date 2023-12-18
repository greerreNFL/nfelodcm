import pandas as pd
import numpy
import pathlib
import datetime

from .Primatives import TableMap, Freshness, DataPull, LocalIO
import nfelodcm.nfelodcm.Utilities as utils

class DCMTable():
    """
    Takes a table name and handles all backend loading and pulling of data.
    """
    def __init__(self, table):
        self.table = table
        ## init table map ##
        self.tableMap = TableMap(self.table)
        self.check_table_map()
        ## init freshness ##
        self.freshness = Freshness(self.tableMap.config)
        ## init data pull ##
        self.dataPull = DataPull(self.tableMap.config)
        ## init local io ##
        self.localIO = LocalIO(self.tableMap.config, self.tableMap.table_data_location)
        ## handle load ##
        self.handle_load()

    def check_table_map(self):
        """
        Checks to ensure the structure of the table map config and data types 
        are valid
        """
        ##
        config_passes, config_errors = utils.check_struc(self.tableMap.config)
        if not config_passes:
            raise ValueError(
                "Config structure is not valid. Errors: \n     -> " +
                '\n     -> '.join([err['error_msg'] for err in config_errors])
            )
        ## check map ##
        map_passes, map_errors = utils.check_map_type(self.tableMap.config['map'])
        if not map_passes:
            raise ValueError(
                "Map had data type errors. Errors: \n     -> " +
                '\n     -> '.join([err['error_msg'] for err in map_errors])
            )


    def handle_load(self):
        """
        Handles loading of the table based on freshness status.
        """
        if self.freshness.freshness_check_time is not None:
            ## if freshness was checked, update the time in the config ##
            self.tableMap.config['freshness']['last_freshness_check'] = self.freshness.freshness_check_time
            self.tableMap.update_map(
                self.tableMap.config
            )
        ## reference freshness to determine where to pull data from ##
        if self.freshness.needs_update:
            ## pull new data ##
            self.dataPull.update_data()
            ## load into local io ##
            self.localIO.df = self.dataPull.pulled_df
            ## write ##
            self.localIO.write()
            ## update config timestamp with a UTC iso timestamp ##
            self.tableMap.config['last_local_update'] = datetime.datetime.utcnow().isoformat()
            self.tableMap.update_map(
                self.tableMap.config
            )
        else:
            self.localIO.read()
