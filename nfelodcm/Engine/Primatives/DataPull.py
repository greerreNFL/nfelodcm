import pandas as pd
import numpy

import nfelodcm.nfelodcm.Utilities as utils
import nfelodcm.nfelodcm.Engine.Assignments as assignments

class DataPull():
    """
    Downloads CSVs provided a map that contains url, fields, and iter details
    """
    
    def __init__(self, config):
        self.config = config
        self.columns, self.dtypes = utils.extract_map(config['map'])
        self.pulled_data = []
        self.pulled_df = None
    
    def pull_data(self, url):
        """
        Pulls data from the url and returns a pandas dataframe
        """
        ## pull data ##
        df = pd.read_csv(
            url,
            usecols=self.columns,
            dtype=self.dtypes,
            engine=self.config['engine']
        )
        ## add pulled data to container ##
        self.pulled_data.append(df)
        
    def handle_pull(self):
        """
        Handles the pull based on the iter type. If the iter is a loop, it will form download urls and loop,
        otherwise it will pull simply pull the download url
        """
        ## handle pull ##
        if self.config['iter']['type'] is None:
            ## if not iter type, assume single download url ##
            self.pull_data(self.config['download_url'])
        elif self.config['iter']['type'] == 'season':
            ## if season iter, loop through seasons ##
            for season in range(
                self.config['iter']['start'],
                utils.current_season() + 1
            ):
                ## form download url ##
                url = self.config['download_url'].format(season)
                ## pull data ##
                self.pull_data(url)
        else:
            raise ValueError('ERROR: Iter type not recognized.')
    
    def concat_data(self):
        """
        Once data is pulled, it will handle any necessary concatenation
        """
        if len(self.pulled_data) == 0:
            raise ValueError('ERROR: A data request was made, but no data was pulled.')
        elif len(self.pulled_data) == 1:
            self.pulled_df = self.pulled_data[0]
        else:
            df = pd.concat(self.pulled_data)
            self.pulled_df = df.reset_index(drop=True)
    
    def apply_assignments(self):
        """
        Applies any assignments to the pulled data
        """
        ## apply assignments ##
        if len(self.config['assignments']) > 0:
            for assignment in self.config['assignments']:
                ## apply assignment ##
                self.pulled_df = assignments.assign(
                    self.pulled_df,
                    assignment
                )
    
    def update_data(self):
        """
        Wrrapper to handle the pull if called
        """
        ## handle pull ##
        self.handle_pull()
        ## concat data ##
        self.concat_data()
        ## apply assignments ##
        self.apply_assignments()
