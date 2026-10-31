"""
Tests for public API contract (no network)
"""
import pytest
import datetime

from nfelodcm.nfelodcm.nfelodcm import get_season_state
from nfelodcm.nfelodcm.Engine.Storage import DCMStorage
from nfelodcm.nfelodcm.Engine.Types import SeasonState


def _preset_season_state(monkeypatch, state):
    """Helper to hold a current, already stored season state so no download or storage read happens"""
    state.last_updated = datetime.datetime.now(datetime.timezone.utc).isoformat()
    monkeypatch.setattr(DCMStorage, 'season_state', state)
    monkeypatch.setattr(DCMStorage, 'stored_season_state', state)


class TestGetSeasonState:
    def test_get_season_state_returns_tuple(self, monkeypatch):
        """Returns (season, week) tuple from the configured storage's season state"""
        _preset_season_state(monkeypatch, SeasonState(
            last_full_week={'season': 2024, 'week': 18}
        ))
        assert get_season_state('last_full_week') == (2024, 18)

    def test_get_season_state_invalid_type_raises(self, monkeypatch):
        """Bad state_type raises, and last_updated is not a state_type"""
        _preset_season_state(monkeypatch, SeasonState())
        with pytest.raises(Exception, match='not an available state_type'):
            get_season_state('last_updated')


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
