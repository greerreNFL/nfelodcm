"""
Tests for the storage layer: adapters, DCMStorage, TableIO, and season state (no network)
"""
import json
import datetime
import pytest
import pandas as pd
import requests
from unittest.mock import patch, MagicMock

from nfelodcm.nfelodcm.Engine.Storage import (
    DCMStorage, LocalStorage, SupabaseStorage, StorageBackend,
    StorageError, MissingObjectError
)
from nfelodcm.nfelodcm.Engine.Primatives.TableIO import TableIO
from nfelodcm.nfelodcm.Engine.Types import SeasonState


@pytest.fixture
def local_storage(tmp_path, monkeypatch):
    """LocalStorage in a temp dir, with DCMStorage reset and restored after the test"""
    monkeypatch.setattr(DCMStorage, 'backend', None)
    monkeypatch.setattr(DCMStorage, 'season_state', None)
    monkeypatch.setattr(DCMStorage, 'stored_season_state', None)
    return LocalStorage(tmp_path)


def _season_state(season, seconds_old=0):
    """Helper to build a calculated SeasonState with a last_updated seconds_old in the past"""
    updated = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=seconds_old)
    return SeasonState(
        last_full_week={'season': season, 'week': 1},
        last_updated=updated.isoformat()
    )


def _response(status_code, body=None):
    """Helper to build a mocked requests response"""
    response = MagicMock()
    response.status_code = status_code
    response.content = b''
    if body is None:
        response.json.side_effect = ValueError('no json')
    else:
        response.json.return_value = body
    return response


class TestLocalStorage:
    def test_round_trip(self, local_storage):
        """Written bytes read back unchanged"""
        local_storage.write('Data/a.csv', b'a,b\n1,2\n', 'text/csv')
        assert local_storage.read('Data/a.csv') == b'a,b\n1,2\n'
        assert local_storage.exists('Data/a.csv')

    def test_missing_key(self, local_storage):
        """A missing key is not found and raises MissingObjectError on read"""
        assert not local_storage.exists('Data/missing.csv')
        with pytest.raises(MissingObjectError):
            local_storage.read('Data/missing.csv')

    @pytest.mark.parametrize('key', ['', '/Data/a.csv', '../a.csv', 'Data//a.csv', 'Data\\a.csv', 'Data/./a.csv'])
    def test_invalid_key_raises(self, local_storage, key):
        """Keys outside the tree are rejected"""
        with pytest.raises(StorageError):
            local_storage.read(key)

    def test_atomic_write(self, local_storage, tmp_path):
        """File exists after write, no .tmp left behind"""
        local_storage.write('State/Tables/a.json', b'{}', 'application/json')
        assert (tmp_path / 'State/Tables/a.json').exists()
        assert len(list((tmp_path / 'State/Tables').glob('.storage_*.tmp'))) == 0


class TestDCMStorage:
    def test_configure_prepares_and_publishes(self, local_storage, tmp_path):
        """configure creates the layout and makes the backend active"""
        DCMStorage.configure(local_storage)
        assert DCMStorage.backend is local_storage
        for folder in DCMStorage.FOLDERS:
            assert (tmp_path / folder).is_dir()

    def test_configure_reconciles_missing_csvs(self, local_storage):
        """Missing CSVs reset table and iter state. Present CSVs keep their state."""
        ## pbp has iter state but no csv, games has a csv and state ##
        local_storage.write('State/Parts/pbp.json', json.dumps({'season_timestamps': {'2024': 'ts'}}).encode(), 'application/json')
        local_storage.write('Data/games.csv', b'a\n1\n', 'text/csv')
        local_storage.write('State/Tables/games.json', json.dumps({'last_local_update': 'ts'}).encode(), 'application/json')
        DCMStorage.configure(local_storage)
        assert json.loads(local_storage.read('State/Parts/pbp.json')) == {'season_timestamps': {}}
        assert json.loads(local_storage.read('State/Tables/pbp.json'))['last_local_update'] is None
        assert json.loads(local_storage.read('State/Tables/games.json'))['last_local_update'] == 'ts'

    def test_configure_failure_keeps_previous_backend(self, local_storage):
        """A storage error during reconcile raises, writes nothing, and keeps the previous backend"""
        DCMStorage.configure(local_storage)

        class FailingStorage(StorageBackend):
            def __init__(self):
                self.writes = []
            def prepare(self, folders):
                pass
            def exists(self, key):
                raise StorageError('STORAGE ERROR: down')
            def read(self, key):
                raise StorageError('STORAGE ERROR: down')
            def write(self, key, data, content_type):
                self.writes.append(key)

        failing = FailingStorage()
        with pytest.raises(StorageError):
            DCMStorage.configure(failing)
        assert DCMStorage.backend is local_storage
        assert failing.writes == []

    def test_configure_rejects_non_backend(self, local_storage):
        """configure only accepts a StorageBackend"""
        with pytest.raises(StorageError):
            DCMStorage.configure(object())

    def test_read_json_missing_and_invalid(self, local_storage):
        """Missing and invalid JSON read as {}"""
        DCMStorage.configure(local_storage)
        local_storage.write('State/Global/bad.json', b'{{not json', 'application/json')
        assert DCMStorage.read_json('State/Global/missing.json') == {}
        assert DCMStorage.read_json('State/Global/bad.json') == {}


class TestTableIO:
    def test_read_missing_returns_false(self, local_storage, sample_table_config):
        """A missing CSV is not loadable"""
        DCMStorage.configure(local_storage)
        io = TableIO(sample_table_config, 'Data/test_table.csv')
        assert io.read() is False

    def test_read_missing_column_returns_false(self, local_storage, sample_table_config):
        """A CSV without every mapped column is not loadable"""
        DCMStorage.configure(local_storage)
        local_storage.write('Data/test_table.csv', b'col_a,col_b\nx,1\n', 'text/csv')
        io = TableIO(sample_table_config, 'Data/test_table.csv')
        assert io.read() is False

    def test_write_and_read(self, local_storage, sample_table_config):
        """A written CSV reads back with mapped columns only"""
        DCMStorage.configure(local_storage)
        io = TableIO(sample_table_config, 'Data/test_table.csv')
        io.df = pd.DataFrame({'col_a': ['x'], 'col_b': [1], 'col_c': [1.5], 'col_old': [0]})
        io.write()
        assert io.read() is True
        assert list(io.df.columns) == ['col_a', 'col_b', 'col_c']


class TestSupabaseStorage:
    def _storage(self):
        return SupabaseStorage('https://abc.supabase.co/storage/v1/', 'secret-key', 'data')

    def test_url_normalized(self):
        """A /storage/v1 URL normalizes to the project origin"""
        assert self._storage().base == 'https://abc.supabase.co'

    @patch('nfelodcm.nfelodcm.Engine.Storage.Adapters.SupabaseStorage.requests.request')
    def test_exists_missing(self, mock_request):
        """NoSuchKey and a 404 with no code are missing"""
        mock_request.return_value = _response(400, {'code': 'NoSuchKey'})
        assert self._storage().exists('Data/a.csv') is False
        mock_request.return_value = _response(404)
        assert self._storage().exists('Data/a.csv') is False

    @patch('nfelodcm.nfelodcm.Engine.Storage.Adapters.SupabaseStorage.requests.request')
    def test_auth_error_raises_without_key(self, mock_request):
        """InvalidJWT is a failure, not a missing object, and the key is not in the message"""
        mock_request.return_value = _response(400, {'code': 'InvalidJWT', 'message': 'bad jwt'})
        with pytest.raises(StorageError) as e:
            self._storage().exists('Data/a.csv')
        assert not isinstance(e.value, MissingObjectError)
        assert 'secret-key' not in str(e.value)

    @patch('nfelodcm.nfelodcm.Engine.Storage.Adapters.SupabaseStorage.requests.request')
    def test_read_missing_raises(self, mock_request):
        """A missing object raises MissingObjectError"""
        mock_request.return_value = _response(400, {'code': 'NoSuchKey'})
        with pytest.raises(MissingObjectError):
            self._storage().read('Data/a.csv')

    @patch('nfelodcm.nfelodcm.Engine.Storage.Adapters.SupabaseStorage.requests.request')
    def test_connection_error_not_chained(self, mock_request):
        """A connection failure raises StorageError without the requests exception attached"""
        mock_request.side_effect = requests.exceptions.ConnectionError('boom')
        with pytest.raises(StorageError) as e:
            self._storage().read('Data/a.csv')
        assert e.value.__suppress_context__ is True
        assert e.value.__cause__ is None

    def test_invalid_key_raises(self):
        """Keys outside the tree are rejected before a request is made"""
        with pytest.raises(StorageError):
            self._storage().object_url('object', 'Data/../a.csv')


CALC = 'nfelodcm.nfelodcm.Engine.Storage.DCMStorage.calc_season_state'


class TestGetSeasonState:
    @patch(CALC)
    def test_calculated_then_held(self, mock_calc, local_storage):
        """With nothing stored, the first call calculates and stores. Later calls use memory."""
        mock_calc.return_value = _season_state(2024)
        DCMStorage.configure(local_storage)
        assert DCMStorage.get_season_state().last_full_week['season'] == 2024
        DCMStorage.get_season_state()
        assert mock_calc.call_count == 1
        assert json.loads(local_storage.read('State/Global/season_state.json'))['last_full_week']['season'] == 2024

    @patch(CALC)
    def test_valid_stored_state_used(self, mock_calc, local_storage):
        """A new process uses a valid stored state without calculating"""
        local_storage.write('State/Global/season_state.json', json.dumps(_season_state(2023, 60).to_dict()).encode(), 'application/json')
        DCMStorage.configure(local_storage)
        assert DCMStorage.get_season_state().last_full_week['season'] == 2023
        assert mock_calc.call_count == 0

    @patch(CALC)
    def test_stale_stored_state_recalculated(self, mock_calc, local_storage):
        """A stored state older than the SLA is recalculated"""
        local_storage.write('State/Global/season_state.json', json.dumps(_season_state(2023, 3600).to_dict()).encode(), 'application/json')
        mock_calc.return_value = _season_state(2024)
        DCMStorage.configure(local_storage)
        assert DCMStorage.get_season_state().last_full_week['season'] == 2024
        assert mock_calc.call_count == 1

    @patch(CALC)
    def test_memory_written_to_new_backend(self, mock_calc, local_storage, tmp_path):
        """After a backend change, a valid state in memory is written to the new backend"""
        mock_calc.return_value = _season_state(2024)
        DCMStorage.configure(local_storage)
        DCMStorage.get_season_state()
        new_storage = LocalStorage(tmp_path / 'new')
        DCMStorage.configure(new_storage)
        assert DCMStorage.get_season_state().last_full_week['season'] == 2024
        assert mock_calc.call_count == 1
        assert json.loads(new_storage.read('State/Global/season_state.json'))['last_full_week']['season'] == 2024

    @patch(CALC, side_effect=Exception('download failed'))
    def test_failed_calc_uses_stale_state(self, mock_calc, local_storage):
        """A failed calculation falls back to the stale stored state"""
        local_storage.write('State/Global/season_state.json', json.dumps(_season_state(2023, 3600).to_dict()).encode(), 'application/json')
        DCMStorage.configure(local_storage)
        assert DCMStorage.get_season_state().last_full_week['season'] == 2023

    @patch(CALC, side_effect=Exception('download failed'))
    def test_failed_calc_infers_without_storing(self, mock_calc, local_storage):
        """With no state at all, a failed calculation infers from the month and stores nothing"""
        DCMStorage.configure(local_storage)
        state = DCMStorage.get_season_state()
        assert state.last_updated is None
        assert state.last_full_week['season'] is not None
        assert not local_storage.exists('State/Global/season_state.json')
