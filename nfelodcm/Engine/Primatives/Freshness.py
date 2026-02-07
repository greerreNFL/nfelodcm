import requests
import datetime

from nfelodcm.nfelodcm.Utilities.paths import SEASON_STATE_JSON
from nfelodcm.nfelodcm.Utilities.env import get_github_headers
from nfelodcm.nfelodcm.Engine.Types import SeasonState
from .Retry import with_retry

class Freshness():
    """
    Determines whether or not a data update is required
    """

    def __init__(self, config, last_freshness_check=None, last_local_update=None, iter_state=None):
        self.config = config
        self.last_freshness_check = last_freshness_check
        self.last_local_update = last_local_update
        self.iter_state = iter_state
        self.needs_update = False
        self.stale_parts = None
        self.freshness_check_time = None
        self.check_freshness()

    ## helpers ##
    def determine_current_season(self):
        """
        Loads the current season from season state
        """
        state = SeasonState.load(SEASON_STATE_JSON)
        if state.last_full_week is not None:
            return state.last_full_week.get('season')
        return None

    def form_season_iter_download_url(self, download_url):
        """
        If the dataset is a season iter, formulate the dl link based on current seaosn
        get current season
        """
        year = self.determine_current_season()
        if year is None:
            raise ValueError('ERROR: Could not determine current season.')
        return download_url.format(year)

    ## primary SLA check ##
    def sla_check(self):
        """
        Checks SLA seconds and the last update timestamp from state, to determine if
        a freshness check is needed, or if the data is still within its SLA
        """
        ## fails SLA if null ##
        if self.last_freshness_check is None or self.config.freshness.sla_seconds is None:
            ## either freshness was never previously established or there is no SLA and freshness should be checked ##
            return False
        else:
            ## get seconds since last freshness check ##
            last_freshness_check = datetime.datetime.fromisoformat(
                self.last_freshness_check
            ).astimezone(datetime.timezone.utc)
            seconds_since_last_check = (
                datetime.datetime.now(datetime.timezone.utc) -
                last_freshness_check
            ).total_seconds()
            ## compare to sla ##
            if seconds_since_last_check > self.config.freshness.sla_seconds:
                ## if freshness state breaches SLA, update freshness
                return False
            else:
                ## if the time since the last check is less than the SLA, then it passes
                return True

    ## shared API helpers ##
    def fetch_gh_release_data(self, github_endpoint, tag):
        """
        Fetches the release API response with retry, returns parsed json.
        Returns None on failure (prints warning).
        """
        try:
            def _fetch():
                r = requests.get(
                    '{0}/{1}'.format(github_endpoint, tag),
                    headers=get_github_headers()
                )
                r.raise_for_status()
                return r.json()
            return with_retry(
                _fetch,
                max_retries=3,
                context='gh_release/{0}'.format(tag)
            )
        except Exception as e:
            print('WARN: Request to github releases failed for {0}: {1}'.format(tag, e))
            return None

    def get_release_assets(self, github_endpoint, tag):
        """
        Fetches release data and extracts the assets list.
        Returns the assets list or None on failure.
        """
        data = self.fetch_gh_release_data(github_endpoint, tag)
        if data is None:
            return None
        assets = data.get('assets')
        if assets is None:
            print('WARN: Release assets did not come with response json from github for {0}.'.format(tag))
            return None
        if len(assets) == 0:
            print('WARN: No release assets included in response json from github for {0}.'.format(tag))
            return None
        return assets

    ## config types ##
    def check_gh_release_freshness(self):
        """
        Checks the freshness of a map with a github release source.
        For iter tables with iter_state, computes per-season stale_parts.
        For non-iter tables, compares a single URL.
        """
        ## helpers ##
        def get_asset_timestamp(assets, download_url):
            ## Finds matching asset and returns its updated_at timestamp ##
            for asset in assets:
                if asset['browser_download_url'] == download_url:
                    try:
                        return datetime.datetime.fromisoformat(
                            asset['updated_at']
                        ).astimezone(datetime.timezone.utc)
                    except:
                        print('WARN: Could not parse last update string for {0}.'.format(download_url))
                        return None
            return None

        def is_newer_than_local(remote_ts, local_ts_str):
            ## Compares a remote timestamp to a local ISO string ##
            if remote_ts is None:
                return False
            if local_ts_str is None:
                return True
            local_ts = datetime.datetime.fromisoformat(
                local_ts_str
            ).astimezone(datetime.timezone.utc)
            return remote_ts > local_ts

        ## validate config ##
        github_endpoint = self.config.freshness.gh_api_endpoint
        tag = self.config.freshness.gh_release_tag
        download_url = self.config.download_url
        if not tag or not download_url or not github_endpoint:
            raise ValueError('ERROR: Tag, Endpoint, and Download URL must be included in a Github Release Map')
        ## fetch assets (single API call) ##
        assets = self.get_release_assets(github_endpoint, tag)
        if assets is None:
            ## API failed - don't flag update ##
            return
        ## determine if this is an iter table with per-part tracking ##
        is_iter = self.config.iter.type is not None and self.config.iter.type == 'season'
        if is_iter and self.iter_state is not None:
            ## per-part freshness: compare each season's asset against iter_state ##
            from nfelodcm.nfelodcm.Utilities.retrieve_season_state import current_season
            stale = []
            for season in range(self.config.iter.start, current_season() + 1):
                ## form the download url for this season ##
                season_url = download_url.format(season)
                ## get the remote timestamp for this season's asset ##
                remote_ts = get_asset_timestamp(assets, season_url)
                ## get the local timestamp from iter_state ##
                local_ts = self.iter_state.get_season_timestamp(season)
                ## compare ##
                if is_newer_than_local(remote_ts, local_ts):
                    stale.append(season)
                ## update iter_state with the remote timestamp ##
                if remote_ts is not None:
                    self.iter_state.set_season_timestamp(
                        season,
                        remote_ts.isoformat()
                    )
            self.stale_parts = stale
            self.needs_update = len(stale) > 0
        else:
            ## non-iter or no iter_state: compare single URL ##
            if is_iter:
                download_url = self.form_season_iter_download_url(download_url)
            remote_ts = get_asset_timestamp(assets, download_url)
            self.needs_update = is_newer_than_local(remote_ts, self.last_local_update)

    def check_gh_commit_freshness(self):
        """
        Checks the freshness of a map with a github commit source.
        No per-file granularity - stale_parts stays None (full pull).
        """
        ## helpers ##
        def get_gh_commit_date(endpoint):
            ## retrieves the last time a commit was pushed to a repo ##
            ## note, this does not necessarily mean the data itself was updated, but ##
            ## its the safest way to ensure fresh data w/o a release ##
            try:
                def _fetch():
                    r = requests.get(endpoint, headers=get_github_headers())
                    r.raise_for_status()
                    return r.json()
                data = with_retry(
                    _fetch,
                    max_retries=3,
                    context='gh_commit'
                )
            except Exception as e:
                print('WARN: Request to github commits failed: {0}'.format(e))
                return
            if len(data) == 0:
                print('WARN: No commits returned from github.')
                return
            ## parse results ##
            commits = []
            for commit in data:
                commits.append(
                    datetime.datetime.fromisoformat(
                        commit['commit']['committer']['date']
                    ).astimezone(datetime.timezone.utc)
                )
            ## return ##
            return max(commits)

        def check_for_new_gh_data(last_local_update, endpoint):
            ## Compares the last update of the local file to the last update of the
            ## commit on github to determine if new data is available.
            ## get last update ##
            last_gh_update = get_gh_commit_date(endpoint)
            ## compare ##
            if last_gh_update is None:
                return False
            if last_local_update is None:
                ## if no local update, return True signal download ##
                return True
            if last_gh_update > datetime.datetime.fromisoformat(
                last_local_update
            ).astimezone(datetime.timezone.utc):
                ## if gh update is newer, return True signal download ##
                return True
            return False

        ## handle request for GH Commit freshness ##
        github_endpoint = self.config.freshness.gh_api_endpoint
        if not github_endpoint:
            raise ValueError('ERROR: Endpoint must be included in a Github Commit Map')
        last_local_update = self.last_local_update
        ## check last GH update ##
        self.needs_update = check_for_new_gh_data(
            last_local_update,
            github_endpoint
        )
        ## stale_parts stays None for gh_commit (no per-file granularity) ##

    def check_freshness(self):
        """
        Wrapper function that checks data freshness for a map given a freshness config.
        """
        ## check the freshness sla ##
        sla_passing = self.sla_check()
        ## update if it is not passing ##
        if not sla_passing:
            ## check the data type and route to appropriate function ##
            if self.config.freshness.type == 'gh_release':
                self.check_gh_release_freshness()
            elif self.config.freshness.type == 'gh_commit':
                self.check_gh_commit_freshness()
            else:
                raise ValueError('ERROR: Freshness type not recognized.')
            ## update last check property with the current time since freshness was checked ##
            self.freshness_check_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
