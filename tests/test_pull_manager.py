"""
Tests for PullManager with mocked HTTP
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from nfelodcm.nfelodcm.Engine.Primatives.PullManager import PullManager
from nfelodcm.nfelodcm.Engine.Types.table_config import (
    TableConfig, FreshnessConfig, IterConfig
)
from nfelodcm.nfelodcm.Engine.Types.iter_state import IterState


def _make_config(name='test', iter_type=None, iter_start=None, accept_partial=False, assignments=None):
    """Helper to build a minimal TableConfig for PullManager tests"""
    return TableConfig(
        name=name,
        description='test',
        download_url='https://example.com/{0}.csv' if iter_type else 'https://example.com/data.csv',
        iter=IterConfig(type=iter_type, start=iter_start, accept_partial=accept_partial),
        freshness=FreshnessConfig(
            type='gh_commit',
            sla_seconds=900,
            gh_api_endpoint='https://api.github.com/repos/test/commits'
        ),
        assignments=assignments or [],
        map={'col_a': 'object', 'col_b': 'int32'}
    )


def _mock_df(rows=3):
    """Helper to create a small test DataFrame"""
    return pd.DataFrame({
        'col_a': ['a', 'b', 'c'][:rows],
        'col_b': [1, 2, 3][:rows]
    })


class TestPullManagerSinglePull:
    @patch.object(PullManager, '__init__', lambda self, *a, **kw: None)
    def test_handle_single_pull(self):
        """Non-iter table: single URL pulled, df set"""
        pm = PullManager.__new__(PullManager)
        pm.config = _make_config()
        pm.iter_state = None
        pm.pulled_df = None
        ## mock DataPull ##
        mock_dp = MagicMock()
        mock_dp.pull.return_value = _mock_df()
        pm.dataPull = mock_dp
        pm.handle_single_pull()
        assert pm.pulled_df is not None
        assert len(pm.pulled_df) == 3
        mock_dp.pull.assert_called_once_with('https://example.com/data.csv')


class TestPullManagerIterPull:
    @patch('nfelodcm.nfelodcm.Engine.Primatives.PullManager.utils.current_season', return_value=2001)
    @patch.object(PullManager, '__init__', lambda self, *a, **kw: None)
    def test_handle_iter_pull_full(self, mock_season):
        """Iter table with stale_parts=None pulls all seasons"""
        pm = PullManager.__new__(PullManager)
        pm.config = _make_config(iter_type='season', iter_start=1999)
        pm.iter_state = None
        pm.pulled_df = None
        pm.parts_dir = MagicMock()
        pm.parts_dir.mkdir = MagicMock()
        pm.parts_dir.__truediv__ = lambda self, x: MagicMock()
        ## mock DataPull ##
        mock_dp = MagicMock()
        mock_dp.pull.return_value = _mock_df(1)
        mock_dp.columns = ['col_a', 'col_b']
        mock_dp.dtypes = {'col_a': 'object', 'col_b': 'int32'}
        pm.dataPull = mock_dp
        pm.handle_iter_pull(stale_parts=None)
        ## should pull 3 seasons: 1999, 2000, 2001 ##
        assert mock_dp.pull.call_count == 3
        assert pm.pulled_df is not None
        assert len(pm.pulled_df) == 3

    @patch('nfelodcm.nfelodcm.Engine.Primatives.PullManager.utils.current_season', return_value=2001)
    @patch.object(PullManager, '__init__', lambda self, *a, **kw: None)
    def test_handle_iter_pull_selective(self, mock_season):
        """Iter table with stale_parts=[2001] only pulls that season, reads cache for others"""
        pm = PullManager.__new__(PullManager)
        pm.config = _make_config(iter_type='season', iter_start=1999)
        pm.iter_state = IterState()
        pm.pulled_df = None
        pm.parts_dir = MagicMock()
        pm.parts_dir.mkdir = MagicMock()
        pm.parts_dir.__truediv__ = lambda self, x: MagicMock()
        ## mock DataPull ##
        mock_dp = MagicMock()
        mock_dp.pull.return_value = _mock_df(1)
        mock_dp.columns = ['col_a', 'col_b']
        mock_dp.dtypes = {'col_a': 'object', 'col_b': 'int32'}
        pm.dataPull = mock_dp
        ## mock read_cached_part for non-stale seasons ##
        pm.read_cached_part = MagicMock(return_value=_mock_df(1))
        ## mock pull_and_cache_part for stale season ##
        pm.pull_and_cache_part = MagicMock(return_value=_mock_df(1))
        ## mock iter_state.save ##
        pm.iter_state.save = MagicMock()
        pm.handle_iter_pull(stale_parts=[2001])
        ## should read cache for 1999, 2000 and pull for 2001 ##
        assert pm.read_cached_part.call_count == 2
        assert pm.pull_and_cache_part.call_count == 1
        pm.pull_and_cache_part.assert_called_with(2001)


class TestPullManagerUpdateData:
    @patch.object(PullManager, '__init__', lambda self, *a, **kw: None)
    def test_update_data_routes_single(self):
        """update_data routes to handle_single_pull for non-iter config"""
        pm = PullManager.__new__(PullManager)
        pm.config = _make_config()
        pm.iter_state = None
        pm.pulled_df = None
        pm.handle_single_pull = MagicMock()
        pm.apply_assignments = MagicMock()
        pm.update_data()
        pm.handle_single_pull.assert_called_once()
        pm.apply_assignments.assert_called_once()

    @patch.object(PullManager, '__init__', lambda self, *a, **kw: None)
    def test_update_data_routes_iter(self):
        """update_data routes to handle_iter_pull for season iter config"""
        pm = PullManager.__new__(PullManager)
        pm.config = _make_config(iter_type='season', iter_start=1999)
        pm.iter_state = None
        pm.pulled_df = None
        pm.handle_iter_pull = MagicMock()
        pm.apply_assignments = MagicMock()
        pm.update_data(stale_parts=[2024])
        pm.handle_iter_pull.assert_called_once_with([2024])
        pm.apply_assignments.assert_called_once()

    @patch.object(PullManager, '__init__', lambda self, *a, **kw: None)
    def test_update_data_invalid_iter_type(self):
        """update_data raises on unrecognized iter type"""
        pm = PullManager.__new__(PullManager)
        pm.config = _make_config()
        pm.config.iter = IterConfig(type='unknown')
        pm.iter_state = None
        pm.pulled_df = None
        pm.apply_assignments = MagicMock()
        with pytest.raises(ValueError, match='Iter type not recognized'):
            pm.update_data()
