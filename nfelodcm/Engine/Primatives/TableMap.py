import json
from pathlib import Path

from nfelodcm.nfelodcm.Utilities.paths import map_path, data_path
from nfelodcm.nfelodcm.Engine.Types import TableConfig

class TableMap():
    """ load table maps (read-only at runtime) """

    def __init__(self, table):
        self.table = table
        self.table_map_location = str(map_path(table))
        self.table_data_location = str(data_path(table))
        self.config = self.load_map()

    def load_map(self):
        """
        Loads the configuration json for a given table and returns
        a TableConfig instance.
        """
        p = Path(self.table_map_location)
        if not p.exists():
            print('ERROR: Could not load map for {0}'.format(self.table))
            print('       Use create_map from this class instance to create a new map')
            return None
        try:
            return TableConfig.load(p)
        except Exception as e:
            print('ERROR: Could not load map for {0}'.format(self.table))
            print('       Use create_map from this class instance to create a new map')
            return None

    def create_map(self, new_config):
        """
        Creates a new table map from the given configuration.
        Developer utility for bootstrapping new table configs.
        """
        ## make sure new_config is properly formatted json ##
        try:
            json.dumps(new_config)
        except Exception as e:
            print('ERROR: Config passed was not json. No mapping was created. {0}'.format(e))
            return
        ## write ##
        with open(self.table_map_location, 'w') as fp:
            json.dump(new_config, fp, indent=2)
        ## reload ##
        self.config = self.load_map()
