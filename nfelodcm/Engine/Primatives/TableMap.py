import json
import pathlib

class TableMap():
    """ load and update table maps """
    
    def __init__(self, table):
        self.table = table
        self.table_map_location = '{0}/Maps/{1}.json'.format(
            pathlib.Path(__file__).parent.parent.parent.resolve(),
            table
        )
        self.table_data_location = '{0}/Data/{1}.csv'.format(
            pathlib.Path(__file__).parent.parent.parent.resolve(),
            table
        )
        self.config = self.load_map()
        
    def load_map(self):
        """
        Loads the configuration json for a given table.
        """
        try:
            with open(self.table_map_location, 'r') as fp:
                config = json.load(fp)
                return config
        except Exception as e:
            print('ERROR: Could not load map for {0}'.format(self.table))
            print('       Use create_map from this class instance to create a new map')
            return None
    
    def update_map(self, new_config):
        """
        Loads the configuration json for a given table, and updates it with the new configuration
        """
        ## helper to update congfig -- wrapped in update_map as it should not be used ##
        ## outside of update_map, which also writes ##
        def update_config(old_config, new_config):
            for key, value in new_config.items():
                if key not in old_config:
                    print('WARN: {0} not in current config and will not be added'.format(key))
                else:
                    old_config[key] = value
            return old_config
        
        if self.config is None:
            print('WARN: No config exists for {0}. Use create_map() to create a table map'.format(self.table))
            return
        else:
            ## update ##
            config = update_config(self.config, new_config)
            ## write ##
            with open(self.table_map_location, 'w') as fp:
                json.dump(config, fp, indent=2)
            ## reload ##
            self.config = self.load_map()

    def create_map(self, new_config):
        """
        Creates a new table map from the given configuration
        """
        ## make sure new_confi is properly formatted json ##
        try:
            json.dumps(new_config)
        except Exception as e:
            print('ERROR: Config passed was not json. No mapping was created'.format(e))
            return
        ## write ##
        with open(self.table_map_location, 'w') as fp:
            json.dump(new_config, fp, indent=2)
        ## reload ##
        self.config = self.load_map()
