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
        ## logic for retries ##
        retries_remaining = 3
        pull_error = None
        while retries_remaining > 0:
            try:
                ## pull data ##
                df = pd.read_csv(
                    url,
                    usecols=self.columns,
                    dtype=self.dtypes,
                    engine=self.config['engine']
                )
                ## add pulled data to container ##
                self.pulled_data.append(df)
                ## end if successful ##
                break
            except Exception as e:
                print('ERROR: Failed to pull data from {0}. Retrying...'.format(
                    url
                ))
                pull_error = e
                retries_remaining -= 1
        ## if retries are exhausted, raise an error ##
        if retries_remaining == 0:
            raise ValueError(
                'ERROR: Failed to pull data from {0} after 3 retries: {1}'.format(
                    url,
                    pull_error
                )
            )
        
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
            ## determine if config accepts partials ##
            accepts_partial = False
            missing_parts = []
            if 'accept_partial' in self.config['iter']:
                accepts_partial = self.config['iter']['accept_partial']
            ## if season iter, loop through seasons ##
            for season in range(
                self.config['iter']['start'],
                utils.current_season() + 1
            ):
                ## form download url ##
                url = self.config['download_url'].format(season)
                ## pull data ##
                try:
                    self.pull_data(url)
                except Exception as e:
                    if accepts_partial:
                        missing_parts.append(season)
                        print('WARN: Failed to pull data, but partial iter data is accepted.')
                    else:
                        raise e
            ## if partials accepted, ensure at least one frame was pulled ##
            if accepts_partial:
                if len(self.pulled_data) == 0:
                    raise ValueError('ERROR: Partial iter data is accepted, but no data was pulled')
                elif len(missing_parts) > 0:
                    print('WARN: Partial iter data is accepted, but the following seasons were missing: {0}'.format(missing_parts))
                else:
                    ## if partials are accepted, but no missing parts, do not flag ##
                    pass
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
