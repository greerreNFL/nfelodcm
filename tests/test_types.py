"""
Tests for JsonModel, TableState, and SeasonState
"""
import json
import pytest

from nfelodcm.nfelodcm.Engine.Types import TableState, SeasonState
from nfelodcm.nfelodcm.Engine.Types.json_model import JsonModel


class TestTableState:
    def test_table_state_defaults(self):
        """Default TableState has None fields"""
        state = TableState()
        assert state.last_local_update is None
        assert state.last_freshness_check is None

    def test_table_state_round_trip(self, tmp_state_dir):
        """Save to file, load back, values match"""
        path = tmp_state_dir / 'test_state.json'
        state = TableState(
            last_local_update='2025-06-01T00:00:00+00:00',
            last_freshness_check='2025-06-01T01:00:00+00:00'
        )
        state.save(path)
        loaded = TableState.load(path)
        assert loaded.last_local_update == state.last_local_update
        assert loaded.last_freshness_check == state.last_freshness_check

    def test_table_state_missing_file(self, tmp_state_dir):
        """Load from nonexistent path returns defaults"""
        path = tmp_state_dir / 'nonexistent.json'
        loaded = TableState.load(path)
        assert loaded.last_local_update is None
        assert loaded.last_freshness_check is None

    def test_table_state_corrupt_file(self, tmp_state_dir):
        """Load from corrupt JSON returns defaults"""
        path = tmp_state_dir / 'corrupt.json'
        path.write_text('{{not valid json')
        loaded = TableState.load(path)
        assert loaded.last_local_update is None
        assert loaded.last_freshness_check is None

    def test_table_state_extra_keys_ignored(self, tmp_state_dir):
        """Unknown keys in JSON don't cause errors"""
        path = tmp_state_dir / 'extra.json'
        path.write_text(json.dumps({
            'last_local_update': '2025-01-01T00:00:00+00:00',
            'last_freshness_check': None,
            'unknown_field': 'should be ignored'
        }))
        loaded = TableState.load(path)
        assert loaded.last_local_update == '2025-01-01T00:00:00+00:00'
        assert not hasattr(loaded, 'unknown_field')

    def test_table_state_atomic_write(self, tmp_state_dir):
        """File exists after save, no .tmp left behind"""
        path = tmp_state_dir / 'atomic.json'
        state = TableState(last_local_update='2025-01-01T00:00:00+00:00')
        state.save(path)
        assert path.exists()
        ## check no .tmp files remain ##
        tmp_files = list(tmp_state_dir.glob('.state_*.tmp'))
        assert len(tmp_files) == 0


class TestSeasonState:
    def test_season_state_defaults(self):
        """Default SeasonState has None season/week"""
        state = SeasonState()
        assert state.last_full_week['season'] is None
        assert state.last_full_week['week'] is None

    def test_season_state_round_trip(self, tmp_state_dir):
        """Save and reload preserves values"""
        path = tmp_state_dir / 'season.json'
        state = SeasonState(
            last_full_week={'season': 2024, 'week': 18},
            last_partial_week={'season': 2025, 'week': 1},
            next_week={'season': 2025, 'week': 2}
        )
        state.save(path)
        loaded = SeasonState.load(path)
        assert loaded.last_full_week == {'season': 2024, 'week': 18}
        assert loaded.last_partial_week == {'season': 2025, 'week': 1}
        assert loaded.next_week == {'season': 2025, 'week': 2}
