import pandas as pd
import numpy
import datetime

from .Primatives import TableMap, Freshness, DataPull, LocalIO
from nfelodcm.nfelodcm.Utilities.paths import table_state_path
from nfelodcm.nfelodcm.Engine.Types import TableState

class DCMTable():
    """
    Takes a table name and handles all backend loading and pulling of data.
    """
    def __init__(self, table):
        self.table = table
        ## init table map (read-only config) ##
        self.tableMap = TableMap(self.table)
        self.check_table_map()
        ## init table state (mutable) ##
        self.state_path = table_state_path(self.table)
        self.tableState = TableState.load(self.state_path)
        ## init freshness, passing state values ##
        self.freshness = Freshness(
            self.tableMap.config,
            last_freshness_check=self.tableState.last_freshness_check,
            last_local_update=self.tableState.last_local_update
        )
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
        passing, errors = self.tableMap.config.validate()
        if not passing:
            raise ValueError(
                "Config validation failed. Errors: \n     -> " +
                '\n     -> '.join([err['error_msg'] for err in errors])
            )


    def handle_load(self):
        """
        Handles loading of the table based on freshness status.
        """
        ## add a check to always make sure there is a local file in the DB.
        ## If a CSV is deleted or a write fails, timestamps, and therefore
        ## freshness, may incorrectly assume we have a current file to read
        if not self.localIO.loadable():
            ## if the csv does not exist, flag the update flag ##
            self.freshness.needs_update=True
        if self.freshness.freshness_check_time is not None:
            ## if freshness was checked, update the time in state ##
            self.tableState.last_freshness_check = self.freshness.freshness_check_time
            self.tableState.save(self.state_path)
        ## reference freshness to determine where to pull data from ##
        if self.freshness.needs_update:
            ## pull new data ##
            self.dataPull.update_data()
            ## load into local io ##
            self.localIO.df = self.dataPull.pulled_df
            ## write ##
            self.localIO.write()
            ## update state timestamp with a UTC iso timestamp ##
            ## use datetime.now(datetime.timezone.utc) to ensure we also write the timezone offset, so
            ## operations that use the timestamp are not ambiguous (ie read it as local time b/c there is no offset)
            self.tableState.last_local_update = datetime.datetime.now(datetime.timezone.utc).isoformat()
            self.tableState.save(self.state_path)
        else:
            self.localIO.read()
