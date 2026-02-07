"""
Tests for IterState type
"""
import json
import pytest

from nfelodcm.nfelodcm.Engine.Types.iter_state import IterState


class TestIterState:
    def test_defaults(self):
        """Default IterState has empty season_timestamps"""
        state = IterState()
        assert state.season_timestamps == {}

    def test_get_season_timestamp_missing(self):
        """Getting a missing season returns None"""
        state = IterState()
        assert state.get_season_timestamp(2024) is None

    def test_set_and_get_season_timestamp(self):
        """Set then get returns the stored timestamp"""
        state = IterState()
        ts = '2025-01-15T12:00:00+00:00'
        state.set_season_timestamp(2024, ts)
        assert state.get_season_timestamp(2024) == ts

    def test_string_key_compatibility(self):
        """Season keys are stored as strings for JSON compat"""
        state = IterState()
        state.set_season_timestamp(2024, 'ts_value')
        ## internally stored as string key ##
        assert '2024' in state.season_timestamps
        ## int lookup still works ##
        assert state.get_season_timestamp(2024) == 'ts_value'

    def test_round_trip(self, tmp_state_dir):
        """Save and reload preserves season timestamps"""
        path = tmp_state_dir / 'iter_state.json'
        state = IterState()
        state.set_season_timestamp(2023, '2025-01-01T00:00:00+00:00')
        state.set_season_timestamp(2024, '2025-06-01T00:00:00+00:00')
        state.save(path)
        loaded = IterState.load(path)
        assert loaded.get_season_timestamp(2023) == '2025-01-01T00:00:00+00:00'
        assert loaded.get_season_timestamp(2024) == '2025-06-01T00:00:00+00:00'

    def test_missing_file_returns_defaults(self, tmp_state_dir):
        """Load from nonexistent path returns empty state"""
        path = tmp_state_dir / 'nonexistent.json'
        loaded = IterState.load(path)
        assert loaded.season_timestamps == {}

    def test_corrupt_file_returns_defaults(self, tmp_state_dir):
        """Load from corrupt JSON returns defaults"""
        path = tmp_state_dir / 'corrupt.json'
        path.write_text('{{not valid json')
        loaded = IterState.load(path)
        assert loaded.season_timestamps == {}

    def test_multiple_seasons(self):
        """Can track multiple seasons independently"""
        state = IterState()
        for season in range(1999, 2025):
            state.set_season_timestamp(season, '2025-01-01T00:00:00+00:00')
        assert len(state.season_timestamps) == 26
        assert state.get_season_timestamp(1999) == '2025-01-01T00:00:00+00:00'
        assert state.get_season_timestamp(2024) == '2025-01-01T00:00:00+00:00'
