import pandas as pd

import nfelodcm.nfelodcm.Utilities as utils
from .Retry import with_retry

class DataPull():
    """
    Downloads a single CSV from a URL and returns a DataFrame.
    Iteration, concatenation, and assignments are handled by PullManager.
    """

    def __init__(self, config):
        self.config = config
        self.columns, self.dtypes = utils.extract_map(config.map)

    def pull(self, url):
        """
        Pulls data from a single url and returns a pandas dataframe.
        Uses shared retry utility for transient error handling.
        """
        ## use shared retry utility ##
        df = with_retry(
            lambda: pd.read_csv(
                url,
                usecols=self.columns,
                dtype=self.dtypes,
                engine=self.config.engine
            ),
            max_retries=3,
            context=url
        )
        return df
