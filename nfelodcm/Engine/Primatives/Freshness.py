import requests
import datetime
import pathlib
import json

class Freshness():
    """
    Determines whether or not a data update is required
    """
    
    def __init__(self, config):
        self.config = config
        self.needs_update = False
        self.freshness_check_time = None
        self.check_freshness()
        
    ## helpers ##  
    def determine_current_season(self):
        """
        Loads the current season from global variables
        """
        ## container for current seaosn ##
        season = None
        ## load global_variables.json ##
        with open('{0}/Utilities/global_variables.json'.format(pathlib.Path(__file__).parent.parent.parent.resolve()), 'r') as fp:
            global_variables = json.load(fp)
            season = global_variables['season_states']['last_full_week']['season']
        ## return ##
        return season
        
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
        Checks SLA seconds and the last update timestamp from the config, to determine if
        a freshness check is needed, or if the data is still within its SLA
        """
        ## fails SLA if null ##
        if self.config['freshness']['last_freshness_check'] is None or self.config['freshness']['sla_seconds'] is None:
            ## either freshness was never previously established or there is no SLA and freshness should be checked ##
            return False
        else:
            ## get seconds since last freshness check ##
            last_freshness_check = datetime.datetime.fromisoformat(
                self.config['freshness']['last_freshness_check']
            ).astimezone(datetime.timezone.utc)
            seconds_since_last_check = (
                datetime.datetime.now(datetime.timezone.utc) -
                last_freshness_check
            ).total_seconds()
            ## compare to sla ##
            if seconds_since_last_check > self.config['freshness']['sla_seconds']:
                ## if freshness state breaches SLA, update freshness
                return False
            else:
                ## if the time since the last check is less than the SLA, then it passes
                return True
    
    ## config types ##
    def check_gh_release_freshness(self):
        """
        Checks the freshness of a map with a github release source.
        """
        ## helpers ##
        def get_gh_release_date(github_endpoint, tag, public_download_url):
            ## Retrieves releases for a tag, matches last update on dl url, and returns
            ## the timestampe of the last update.
            ## get release ##
            r = requests.get(
                '{0}/{1}'.format(
                    github_endpoint,
                    tag
                )
            )
            ## hand response ##
            if r.status_code != 200:
                print('WARN: Request to github releases failed for {0}.'.format(tag))
                return
            ## load json ##
            r = r.json()
            ## get assets ##
            assets = r.get('assets')
            if assets is None:
                print('WARN: Release assets did not come with response json from github for {0}.'.format(tag))
                return
            if len(assets) == 0:
                print('WARN: No release assets included in response json from github for {0}.'.format(tag))
                return
            ## iter through assets until url matches ##
            last_update = None
            for asset in assets:
                if asset['browser_download_url'] == public_download_url:
                    try:
                        return datetime.datetime.fromisoformat(
                            asset['updated_at']
                        ).astimezone(datetime.timezone.utc)
                    except:
                        print('WARN: Could not parse last update string for {0}.'.format(public_download_url))
                        return
            ## if nothing has been returned, return None ##
            print('WARN: No asset matched {0}.'.format(public_download_url))
        
        def check_for_new_gh_data(last_local_update, github_endpoint, tag, public_download_url):
            ## Compares the last update of the local file to the last update of the
            ## release asset on github to determine if new data is available.
            ## get last update ##
            last_gh_update = get_gh_release_date(github_endpoint, tag, public_download_url)
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
            
        ## handle request for GH Release freshness ##
        github_endpoint = self.config['freshness'].get('gh_api_endpoint')
        tag = self.config['freshness'].get('gh_release_tag')
        download_url = self.config.get('download_url')
        if tag is None or download_url is None or github_endpoint is None:
            raise ValueError('ERROR: Tag, Endpoint, and Download URL must be included in a Github Release Map')
        ## get url of most recent season file if iter ##
        if self.config['iter']['type'] is not None:
            if self.config['iter']['type'] == 'season':
                download_url = self.form_season_iter_download_url(download_url)
        last_local_update = self.config.get('last_local_update')
        ## check last GH update ##
        self.needs_update = check_for_new_gh_data(
            last_local_update,
            github_endpoint,
            tag,
            download_url
        )
        
    def check_gh_commit_freshness(self):
        """
        Checks the freshness of a map with a github commit source.
        """
        ## helpers ##
        def get_gh_commit_date(endpoint):
            ## retrieves the last time a commit was pushed to a repo ##
            ## note, this does not necessarily mean the data itself was updated, but ##
            ## its the safest way to ensure fresh data w/o a release ##
            r = requests.get(endpoint)
            ## handle response ##
            if r.status_code != 200:
                print('WARN: Request to github commits failed.')
                return
            r = r.json()
            if len(r) == 0:
                print('WARN: No commits returned from github.')
                return
            ## parse results ##
            commits = []
            for commit in r:
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
        github_endpoint = self.config['freshness'].get('gh_api_endpoint')
        if github_endpoint is None:
            raise ValueError('ERROR: Endpoint must be included in a Github Commit Map')
        last_local_update = self.config.get('last_local_update')
        ## check last GH update ##
        self.needs_update = check_for_new_gh_data(
            last_local_update,
            github_endpoint
        )
    
    def check_freshness(self):
        """
        Wrapper function that checks data freshness for a map given a freshness config.
        """
        ## check the freshness sla ##
        sla_passing = self.sla_check()
        ## update if it is not passing ##
        if not sla_passing:
            ## check the data type and route to appropriate function ##
            if self.config['freshness']['type'] == 'gh_release':
                self.check_gh_release_freshness()
            elif self.config['freshness']['type'] == 'gh_commit':
                self.check_gh_commit_freshness()
            else:
                raise ValueError('ERROR: Freshness type not recognized.')
            ## update last check property with the current time since freshness was checked ##
            self.freshness_check_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
