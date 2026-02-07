import pandas as pd

import nfelodcm.nfelodcm.Utilities as utils
import nfelodcm.nfelodcm.Engine.Assignments as assignments
from .DataPull import DataPull

class PullManager():
    """
    Orchestrates the full pull flow for a table. Handles iteration strategy,
    per-file caching, concatenation, and assignment application.
    """

    def __init__(self, config, iter_state=None):
        self.config = config
        self.iter_state = iter_state
        self.dataPull = DataPull(config)
        self.pulled_df = None
        ## resolve parts directory for caching ##
        self.parts_dir = utils.parts_data_dir(config.name)

    def pull_and_cache_part(self, season):
        """
        Pulls a single season file, writes it to the parts cache, and
        updates iter_state with the current timestamp.
        """
        ## form download url ##
        url = self.config.download_url.format(season)
        ## pull data ##
        df = self.dataPull.pull(url)
        ## ensure parts directory exists ##
        self.parts_dir.mkdir(parents=True, exist_ok=True)
        ## write to parts cache (raw, pre-assignment) ##
        cache_path = self.parts_dir / '{0}.csv'.format(season)
        df.to_csv(cache_path)
        return df

    def read_cached_part(self, season):
        """
        Reads a cached season file from the parts directory.
        Returns the dataframe or None if the cache does not exist.
        """
        cache_path = self.parts_dir / '{0}.csv'.format(season)
        if not cache_path.exists():
            return None
        try:
            df = pd.read_csv(
                cache_path,
                index_col=0,
                usecols=self.dataPull.columns,
                dtype=self.dataPull.dtypes,
                engine=self.config.engine
            )
            return df
        except Exception as e:
            print('WARN: Failed to read cached part for season {0}: {1}'.format(season, e))
            return None

    def handle_single_pull(self):
        """
        Handles a non-iter table: single URL download.
        """
        self.pulled_df = self.dataPull.pull(self.config.download_url)

    def handle_iter_pull(self, stale_parts=None):
        """
        Handles an iter table pull. If stale_parts is a list of season ints,
        only those seasons are re-downloaded (others read from cache).
        If stale_parts is None, all seasons are re-downloaded (full pull).
        """
        accepts_partial = self.config.iter.accept_partial
        current_season = utils.current_season()
        missing_parts = []
        frames = []
        ## loop through seasons ##
        for season in range(self.config.iter.start, current_season + 1):
            ## determine whether to pull or read from cache ##
            should_pull = (stale_parts is None) or (season in stale_parts)
            df = None
            if should_pull:
                ## pull fresh data for this season ##
                try:
                    df = self.pull_and_cache_part(season)
                except Exception as e:
                    if accepts_partial:
                        missing_parts.append(season)
                        print('WARN: Failed to pull season {0}, but partial iter data is accepted.'.format(season))
                    else:
                        raise e
            else:
                ## read from cache ##
                df = self.read_cached_part(season)
                if df is None:
                    ## cache miss - fall back to fresh pull ##
                    try:
                        df = self.pull_and_cache_part(season)
                    except Exception as e:
                        if accepts_partial:
                            missing_parts.append(season)
                            print('WARN: Cache miss and pull failed for season {0}, but partial iter data is accepted.'.format(season))
                        else:
                            raise e
            ## add to frames ##
            if df is not None:
                frames.append(df)
        ## validate that at least some data was pulled ##
        if accepts_partial:
            if len(frames) == 0:
                raise ValueError('ERROR: Partial iter data is accepted, but no data was pulled')
            elif len(missing_parts) > 0:
                print('WARN: Partial iter data is accepted, but the following seasons were missing: {0}'.format(missing_parts))
        ## concat all frames ##
        if len(frames) == 0:
            raise ValueError('ERROR: A data request was made, but no data was pulled.')
        elif len(frames) == 1:
            self.pulled_df = frames[0]
        else:
            self.pulled_df = pd.concat(frames).reset_index(drop=True)
        ## save iter_state if present ##
        if self.iter_state is not None:
            iter_state_path = utils.iter_state_path(self.config.name)
            self.iter_state.save(iter_state_path)

    def apply_assignments(self):
        """
        Applies any assignments to the pulled data
        """
        if len(self.config.assignments) > 0:
            for assignment in self.config.assignments:
                self.pulled_df = assignments.assign(
                    self.pulled_df,
                    assignment
                )

    def update_data(self, stale_parts=None):
        """
        Main entry point. Routes to single or iter pull based on config,
        then applies assignments.
        """
        ## route to appropriate pull handler ##
        if self.config.iter.type is None:
            self.handle_single_pull()
        elif self.config.iter.type == 'season':
            self.handle_iter_pull(stale_parts)
        else:
            raise ValueError('ERROR: Iter type not recognized.')
        ## apply assignments ##
        self.apply_assignments()
