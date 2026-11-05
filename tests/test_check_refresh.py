'''
Tests for validate_table_request, check, and report.
'''
import datetime
import json

import pytest
import requests

from nfelodcm import check, load
from nfelodcm.nfelodcm.Engine.Primatives.DataPull import DataPull
from nfelodcm.nfelodcm.Engine.Storage import DCMStorage, LocalStorage


@pytest.fixture
def storage(tmp_path, monkeypatch):
    '''Temp LocalStorage, active for one test, then restored'''
    monkeypatch.setattr(DCMStorage, 'backend', None)
    monkeypatch.setattr(DCMStorage, 'season_state', None)
    monkeypatch.setattr(DCMStorage, 'stored_season_state', None)
    backend = LocalStorage(tmp_path)
    DCMStorage.configure(backend)
    return backend


def test_empty_list_raises():
    '''An empty list is a MAP ERROR for check and load'''
    with pytest.raises(Exception, match='MAP ERROR: No tables were given.'):
        check([])
    with pytest.raises(Exception, match='MAP ERROR: No tables were given.'):
        load([])


def test_duplicate_names_raise():
    '''A repeated name is a MAP ERROR for check and load'''
    with pytest.raises(Exception, match='MAP ERROR: Duplicate table names: hfa'):
        check(['hfa', 'hfa'])
    with pytest.raises(Exception, match='MAP ERROR: Duplicate table names: hfa'):
        load(['hfa', 'games', 'hfa'])


def test_missing_map_raises():
    '''A name with no map is the same MAP ERROR load used'''
    message = 'MAP ERROR: The following tables do not have maps: missing_table'
    with pytest.raises(Exception, match=message):
        check(['missing_table'])
    with pytest.raises(Exception, match=message):
        load(['missing_table'])


def test_check_reports_init_metadata(storage, monkeypatch):
    '''Inside the SLA, report is the metadata init already has, and nothing is pulled'''
    fresh = datetime.datetime.now(datetime.timezone.utc).isoformat()
    local = '2024-06-01T00:00:00+00:00'
    storage.write(
        'State/Tables/hfa.json',
        json.dumps({
            'last_local_update': local,
            'last_freshness_check': fresh,
        }).encode(),
        'application/json'
    )

    def pull(self, url):
        raise AssertionError(url)

    def get(*args, **kwargs):
        raise AssertionError('github')

    monkeypatch.setattr(DataPull, 'pull', pull)
    monkeypatch.setattr(requests, 'get', get)
    assert check(['hfa']) == {
        'tables': [{
            'table': 'hfa',
            'needs_update': False,
            'stale_parts': None,
            'freshness_check_time': None,
            'last_freshness_check': fresh,
            'last_local_update': local,
        }]
    }
