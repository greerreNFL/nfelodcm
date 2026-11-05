import pandas as pd
import numpy
import datetime

from .Primatives import TableMap, Freshness, PullManager, TableIO
from nfelodcm.nfelodcm.Utilities.paths import table_state_path, iter_state_path, data_path
from nfelodcm.nfelodcm.Engine.Types import TableState, IterState
from nfelodcm.nfelodcm.Engine.Storage.DCMStorage import DCMStorage

class DCMTable():
    """
    Takes a table name and handles all backend loading and pulling of data.
    """
    def __init__(self, table, load=True):
        self.table = table
        ## init table map (read-only config) ##
        self.tableMap = TableMap(self.table)
        self.check_table_map()
        ## init table state (mutable) ##
        self.state_path = table_state_path(self.table)
        self.tableState = DCMStorage.read_model(TableState, self.state_path)
        ## init iter state for iter tables ##
        self.iter_state = None
        if self.tableMap.config.iter.type is not None:
            self.iter_state = DCMStorage.read_model(IterState, iter_state_path(self.table))
        ## init freshness, passing state values and iter_state ##
        self.freshness = Freshness(
            self.tableMap.config,
            last_freshness_check=self.tableState.last_freshness_check,
            last_local_update=self.tableState.last_local_update,
            iter_state=self.iter_state
        )
        ## init pull manager (replaces DataPull for orchestration) ##
        self.pullManager = PullManager(self.tableMap.config, iter_state=self.iter_state)
        ## init table io ##
        self.tableIO = TableIO(self.tableMap.config, data_path(self.table))
        ## handle load ##
        if load:
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
        ## if no update is needed, read the stored file. If a CSV is deleted
        ## or a write fails, timestamps, and therefore freshness, may
        ## incorrectly assume we have a current file to read
        if not self.freshness.needs_update and not self.tableIO.read():
            ## if the csv cannot be read, flag the update flag ##
            self.freshness.needs_update=True
        if self.freshness.freshness_check_time is not None:
            ## if freshness was checked, update the time in state ##
            self.tableState.last_freshness_check = self.freshness.freshness_check_time
            DCMStorage.write_json(self.state_path, self.tableState.to_dict())
        ## reference freshness to determine where to pull data from ##
        if self.freshness.needs_update:
            ## pull new data, passing stale_parts for selective iter pulls ##
            self.pullManager.update_data(stale_parts=self.freshness.stale_parts)
            ## load into table io ##
            self.tableIO.df = self.pullManager.pulled_df
            ## write ##
            self.tableIO.write()
            ## update state timestamp with a UTC iso timestamp ##
            ## use datetime.now(datetime.timezone.utc) to ensure we also write the timezone offset, so
            ## operations that use the timestamp are not ambiguous (ie read it as local time b/c there is no offset)
            self.tableState.last_local_update = datetime.datetime.now(datetime.timezone.utc).isoformat()
            DCMStorage.write_json(self.state_path, self.tableState.to_dict())

    def report(self):
        '''
        Return the freshness metadata init already computed.
        '''
        return {
            'table': self.table,
            'needs_update': self.freshness.needs_update,
            'stale_parts': self.freshness.stale_parts,
            'freshness_check_time': self.freshness.freshness_check_time,
            'last_freshness_check': self.tableState.last_freshness_check,
            'last_local_update': self.tableState.last_local_update,
        }
