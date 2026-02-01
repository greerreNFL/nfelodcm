"""
Tests for Maps/*.json integrity
"""
import json
import pytest

from nfelodcm.nfelodcm.Utilities.paths import MAPS_DIR
from nfelodcm.nfelodcm.Engine.Types.table_config import TableConfig
from nfelodcm.nfelodcm.Engine.Assignments.assignment import assignments as assignment_registry


## collect all map files ##
MAP_FILES = sorted(MAPS_DIR.glob('*.json'))
MAP_IDS = [f.stem for f in MAP_FILES]


class TestMapsValidJSON:
    @pytest.mark.parametrize('map_file', MAP_FILES, ids=MAP_IDS)
    def test_all_maps_are_valid_json(self, map_file):
        """Every .json in Maps/ parses without error"""
        with open(map_file, 'r') as fp:
            data = json.load(fp)
        assert isinstance(data, dict)

    @pytest.mark.parametrize('map_file', MAP_FILES, ids=MAP_IDS)
    def test_all_maps_pass_config_validation(self, map_file):
        """Every map passes TableConfig.validate()"""
        with open(map_file, 'r') as fp:
            data = json.load(fp)
        config = TableConfig.from_dict(data)
        passing, errors = config.validate()
        assert passing, 'Validation failed for {0}: {1}'.format(
            map_file.stem,
            errors
        )

    @pytest.mark.parametrize('map_file', MAP_FILES, ids=MAP_IDS)
    def test_all_maps_load_as_table_config(self, map_file):
        """Every map loads into TableConfig.from_dict()"""
        with open(map_file, 'r') as fp:
            data = json.load(fp)
        config = TableConfig.from_dict(data)
        assert isinstance(config, TableConfig)
        assert config.name != ''

    @pytest.mark.parametrize('map_file', MAP_FILES, ids=MAP_IDS)
    def test_no_mutable_fields_in_maps(self, map_file):
        """No map has last_local_update or last_freshness_check"""
        with open(map_file, 'r') as fp:
            data = json.load(fp)
        assert 'last_local_update' not in data
        assert 'last_freshness_check' not in data


class TestMapAssignments:
    @pytest.mark.parametrize('map_file', MAP_FILES, ids=MAP_IDS)
    def test_all_assignments_registered(self, map_file):
        """Every assignment name in every map exists in the assignments registry"""
        with open(map_file, 'r') as fp:
            data = json.load(fp)
        for assignment_name in data.get('assignments', []):
            assert assignment_name in assignment_registry, (
                '{0} references assignment "{1}" which is not in the registry'.format(
                    map_file.stem, assignment_name
                )
            )
