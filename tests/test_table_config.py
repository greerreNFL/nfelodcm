"""
Tests for TableConfig validation and construction
"""
import copy
import pytest

from nfelodcm.nfelodcm.Engine.Types.table_config import (
    TableConfig, FreshnessConfig, IterConfig
)


class TestTableConfigValidation:
    def test_valid_config_passes(self, sample_table_config):
        """A correctly formed config passes validate()"""
        passing, errors = sample_table_config.validate()
        assert passing is True
        assert len(errors) == 0

    def test_missing_required_field_fails(self, sample_config_dict):
        """Omitting name (empty string) still passes, but None fails"""
        config = TableConfig.from_dict(sample_config_dict)
        config.name = None
        passing, errors = config.validate()
        assert passing is False
        assert any('name' in e['error_msg'] for e in errors)

    def test_nullable_field_allows_none(self, sample_config_dict):
        """compression=None passes validation"""
        data = copy.deepcopy(sample_config_dict)
        data['compression'] = None
        config = TableConfig.from_dict(data)
        passing, errors = config.validate()
        assert passing is True

    def test_non_nullable_field_rejects_none(self, sample_config_dict):
        """name=None fails validation"""
        config = TableConfig.from_dict(sample_config_dict)
        config.name = None
        passing, errors = config.validate()
        assert passing is False
        assert any('name' in e['error_msg'] for e in errors)

    def test_wrong_type_fails(self, sample_config_dict):
        """name=123 fails validation"""
        config = TableConfig.from_dict(sample_config_dict)
        config.name = 123
        passing, errors = config.validate()
        assert passing is False
        assert any('name' in e['error_msg'] for e in errors)

    def test_invalid_dtype_fails(self, sample_config_dict):
        """Map with dtype 'badtype' fails"""
        data = copy.deepcopy(sample_config_dict)
        data['map']['bad_col'] = 'badtype'
        config = TableConfig.from_dict(data)
        passing, errors = config.validate()
        assert passing is False
        assert any('badtype' in e['error_msg'] for e in errors)

    def test_valid_dtypes_pass(self, sample_config_dict):
        """All allowed dtypes pass"""
        data = copy.deepcopy(sample_config_dict)
        data['map'] = {}
        for i, dtype in enumerate(TableConfig.ALLOWED_DTYPES):
            data['map']['col_{0}'.format(i)] = dtype
        config = TableConfig.from_dict(data)
        passing, errors = config.validate()
        assert passing is True
        assert len(errors) == 0


class TestTableConfigConstruction:
    def test_from_dict_nested(self, sample_config_dict):
        """from_dict correctly constructs IterConfig and FreshnessConfig"""
        config = TableConfig.from_dict(sample_config_dict)
        assert isinstance(config.iter, IterConfig)
        assert isinstance(config.freshness, FreshnessConfig)
        assert config.iter.type is None
        assert config.freshness.type == 'gh_commit'
        assert config.freshness.sla_seconds == 900

    def test_from_dict_unknown_keys(self, sample_config_dict):
        """Extra keys in JSON are ignored"""
        data = copy.deepcopy(sample_config_dict)
        data['unknown_top_level'] = 'should be ignored'
        data['freshness']['unknown_nested'] = 'also ignored'
        config = TableConfig.from_dict(data)
        assert not hasattr(config, 'unknown_top_level')
        assert config.freshness.type == 'gh_commit'

    def test_to_dict_round_trip(self, sample_config_dict):
        """to_dict produces dict that from_dict can reconstruct"""
        config = TableConfig.from_dict(sample_config_dict)
        d = config.to_dict()
        config2 = TableConfig.from_dict(d)
        assert config.name == config2.name
        assert config.download_url == config2.download_url
        assert config.iter.type == config2.iter.type
        assert config.iter.start == config2.iter.start
        assert config.freshness.type == config2.freshness.type
        assert config.freshness.sla_seconds == config2.freshness.sla_seconds
        assert config.map == config2.map
        assert config.assignments == config2.assignments
