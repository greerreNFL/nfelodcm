import pytest
import tempfile
import pathlib

from nfelodcm.nfelodcm.Engine.Types import TableState
from nfelodcm.nfelodcm.Engine.Types.table_config import (
    TableConfig, FreshnessConfig, IterConfig
)


@pytest.fixture
def tmp_state_dir(tmp_path):
    """Temp directory for state file tests"""
    return tmp_path


@pytest.fixture
def sample_config_dict():
    """Valid config as raw dict (mirrors Maps/*.json shape)"""
    return {
        'name': 'test_table',
        'description': 'A test table',
        'download_url': 'https://example.com/data.csv',
        'compression': None,
        'engine': 'c',
        'freshness': {
            'type': 'gh_commit',
            'sla_seconds': 900,
            'gh_api_endpoint': 'https://api.github.com/repos/test/commits',
            'gh_release_tag': None
        },
        'iter': {
            'type': None,
            'start': None
        },
        'assignments': [],
        'map': {
            'col_a': 'object',
            'col_b': 'int32',
            'col_c': 'float32'
        }
    }


@pytest.fixture
def sample_table_config(sample_config_dict):
    """Valid TableConfig instance"""
    return TableConfig.from_dict(sample_config_dict)


@pytest.fixture
def sample_table_state():
    """TableState with populated timestamps"""
    return TableState(
        last_local_update='2025-01-01T00:00:00+00:00',
        last_freshness_check='2025-01-01T00:00:00+00:00'
    )
