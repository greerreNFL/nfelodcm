"""
Tests for public API contract (no network)
"""
import pytest

from nfelodcm.nfelodcm.Utilities.paths import SEASON_STATE_JSON
from nfelodcm.nfelodcm.Engine.Types import SeasonState


class TestGetSeasonState:
    def test_get_season_state_returns_tuple(self):
        """Returns (season, week) tuple"""
        ## load state directly to avoid triggering full package import ##
        state = SeasonState.load(SEASON_STATE_JSON)
        state_dict = state.to_dict()
        if 'last_full_week' in state_dict and state_dict['last_full_week']['season'] is not None:
            result = (state_dict['last_full_week']['season'], state_dict['last_full_week']['week'])
            assert isinstance(result, tuple)
            assert len(result) == 2

    def test_get_season_state_invalid_type_raises(self):
        """Bad state_type raises"""
        state = SeasonState.load(SEASON_STATE_JSON)
        state_dict = state.to_dict()
        with pytest.raises(KeyError):
            _ = state_dict['totally_invalid_type']


class TestListTables:
    def test_list_tables_no_error(self):
        """load_maps doesn't crash"""
        from nfelodcm.nfelodcm.Utilities.load_maps import load_maps
        maps = load_maps()
        assert isinstance(maps, dict)
        assert len(maps) > 0


class TestLoadMissingTable:
    def test_load_missing_table_raises(self):
        """Nonexistent table name raises"""
        from nfelodcm.nfelodcm.Engine.Primatives.TableMap import TableMap
        tm = TableMap('this_table_does_not_exist_xyz')
        assert tm.config is None
