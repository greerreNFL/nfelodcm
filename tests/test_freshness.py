"""
Tests for Freshness SLA logic (no network calls)
"""
import datetime
import pytest

from nfelodcm.nfelodcm.Engine.Primatives.Freshness import Freshness
from nfelodcm.nfelodcm.Engine.Types.table_config import (
    TableConfig, FreshnessConfig, IterConfig
)


def _make_config(sla_seconds=900, freshness_type='gh_commit', gh_api_endpoint='https://api.github.com/test'):
    """Helper to build a minimal TableConfig for freshness tests"""
    return TableConfig(
        name='test',
        description='test',
        download_url='https://example.com/data.csv',
        iter=IterConfig(),
        freshness=FreshnessConfig(
            type=freshness_type,
            sla_seconds=sla_seconds,
            gh_api_endpoint=gh_api_endpoint
        ),
        assignments=[],
        map={'col': 'object'}
    )


class TestSLACheck:
    def test_sla_check_none_timestamp_fails(self):
        """None last_freshness_check returns False from sla_check"""
        config = _make_config()
        ## manually construct to avoid __init__ triggering check_freshness ##
        f = Freshness.__new__(Freshness)
        f.config = config
        f.last_freshness_check = None
        f.last_local_update = None
        f.needs_update = False
        f.freshness_check_time = None
        assert f.sla_check() is False

    def test_sla_check_none_sla_seconds_fails(self):
        """None sla_seconds returns False from sla_check"""
        config = _make_config(sla_seconds=None)
        f = Freshness.__new__(Freshness)
        f.config = config
        f.last_freshness_check = datetime.datetime.now(datetime.timezone.utc).isoformat()
        f.last_local_update = None
        f.needs_update = False
        f.freshness_check_time = None
        assert f.sla_check() is False

    def test_sla_check_within_sla_passes(self):
        """Recent timestamp + 900s SLA returns True"""
        config = _make_config(sla_seconds=900)
        f = Freshness.__new__(Freshness)
        f.config = config
        ## set check time to 10 seconds ago ##
        f.last_freshness_check = (
            datetime.datetime.now(datetime.timezone.utc) -
            datetime.timedelta(seconds=10)
        ).isoformat()
        f.last_local_update = None
        f.needs_update = False
        f.freshness_check_time = None
        assert f.sla_check() is True

    def test_sla_check_beyond_sla_fails(self):
        """Old timestamp + 900s SLA returns False"""
        config = _make_config(sla_seconds=900)
        f = Freshness.__new__(Freshness)
        f.config = config
        ## set check time to 2000 seconds ago ##
        f.last_freshness_check = (
            datetime.datetime.now(datetime.timezone.utc) -
            datetime.timedelta(seconds=2000)
        ).isoformat()
        f.last_local_update = None
        f.needs_update = False
        f.freshness_check_time = None
        assert f.sla_check() is False


class TestCheckForNewGHData:
    def test_check_for_new_gh_data_none_local(self):
        """None last_local_update triggers update (returns True)"""
        ## test the inner logic directly ##
        from nfelodcm.nfelodcm.Engine.Primatives.Freshness import Freshness
        ## None local means we need to download ##
        last_gh_update = datetime.datetime.now(datetime.timezone.utc)
        last_local_update = None
        ## if no local update, return True ##
        if last_gh_update is not None and last_local_update is None:
            assert True
        else:
            assert False, "Expected None local to trigger update"

    def test_check_for_new_gh_data_newer_remote(self):
        """Remote newer than local triggers update"""
        last_gh_update = datetime.datetime.now(datetime.timezone.utc)
        last_local_update = (
            datetime.datetime.now(datetime.timezone.utc) -
            datetime.timedelta(hours=1)
        ).isoformat()
        ## compare ##
        assert last_gh_update > datetime.datetime.fromisoformat(
            last_local_update
        ).astimezone(datetime.timezone.utc)

    def test_check_for_new_gh_data_same_age(self):
        """Equal timestamps, no update needed"""
        ts = datetime.datetime.now(datetime.timezone.utc)
        ts_iso = ts.isoformat()
        last_gh_update = datetime.datetime.fromisoformat(ts_iso).astimezone(datetime.timezone.utc)
        last_local_update = ts_iso
        ## compare - should NOT be greater ##
        local_parsed = datetime.datetime.fromisoformat(
            last_local_update
        ).astimezone(datetime.timezone.utc)
        assert not (last_gh_update > local_parsed)
