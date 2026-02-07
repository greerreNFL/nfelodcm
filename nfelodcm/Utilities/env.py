import os

from dotenv import load_dotenv

## load .env from cwd on module import ##
load_dotenv()


def get_github_token():
    """
    Returns the GITHUB_TOKEN from environment, or None if not set
    """
    return os.environ.get('GITHUB_TOKEN')

def get_github_headers():
    """
    Returns auth headers dict if GITHUB_TOKEN is set, else empty dict
    """
    token = get_github_token()
    if token:
        return {'Authorization': 'token {0}'.format(token)}
    return {}
