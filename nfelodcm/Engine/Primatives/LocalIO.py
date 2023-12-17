import pandas as pd
import numpy
import json

import nfelodcm.nfelodcm.Utilities as utils
import nfelodcm.nfelodcm.Engine.Assignments as assignments

class LocalIO():
    """
    Reads and writes local CSVs provided a map that contains fields and assignments
    """
    
    def __init__(self, config, data_location):
        self.config = config
        self.columns, self.dtypes = utils.extract_map(config['map'])
        self.data_location = data_location
        self.df = None
        self.add_assignment_cols()
    
    def add_assignment_cols(self):
        """
        Add columns to the dataframe based on the assignments in the config
        """
        for assignment in self.config['assignments']:
            cols_added = assignments.assignment_columns_added(assignment)
            for col in cols_added:
                if col[0] not in self.columns:
                    self.columns.append(col[0])
                    self.dtypes[col[0]] = col[1]
      
    def read(self):
        """
        Read the data from local CSV
        """
        self.df = pd.read_csv(
            self.data_location,
            usecols=self.columns,
            dtype=self.dtypes,
            engine=self.config['engine']
        )
        
    def write(self):
        """
        Write the data to local CSV
        """
        if self.df is None:
            raise Exception('Dataframe is None. Cannot write. Please load a DF into the LocalIO object first.')
        self.df.to_csv(
            self.data_location
        )
