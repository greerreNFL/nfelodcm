import nfelodcm.nfelodcm.Utilities as utils
import nfelodcm.nfelodcm.Engine.Assignments as assignments
from nfelodcm.nfelodcm.Engine.Storage import DCMStorage, MissingObjectError

class TableIO():
    """
    Reads and writes a mapped CSV through DCMStorage using the columns
    and dtypes on its map. The combined table CSV includes the columns
    its assignments add. Raw season parts are stored before assignments,
    so they are read with assigned=False.
    """

    def __init__(self, config, data_path, assigned=True):
        self.config = config
        self.columns, self.dtypes = utils.extract_map(config.map)
        self.data_path = data_path
        self.df = None
        if assigned:
            self.add_assignment_cols()

    def add_assignment_cols(self):
        """
        Add columns to the dataframe based on the assignments in the config
        """
        for assignment in self.config.assignments:
            cols_added = assignments.assignment_columns_added(assignment)
            for col in cols_added:
                if col[0] not in self.columns:
                    self.columns.append(col[0])
                    self.dtypes[col[0]] = col[1]

    def read(self):
        """
        Read the stored CSV into self.df. Returns False when the CSV is
        missing or does not have every mapped column, so the caller can
        pull fresh data. Storage failures raise.
        """
        ## read the object once ##
        try:
            df = DCMStorage.read_csv(
                self.data_path,
                dtype=self.dtypes,
                engine=self.config.engine
            )
        except MissingObjectError:
            return False
        ## check the stored file has every column in the config ##
        for col in self.columns:
            if col not in df.columns:
                return False
        ## drop stored columns the map no longer has ##
        extra_cols = [col for col in df.columns if col not in self.columns]
        if len(extra_cols) > 0:
            df = df.drop(columns=extra_cols)
        self.df = df
        return True

    def write(self):
        """
        Write the data to the stored CSV
        """
        if self.df is None:
            raise Exception('Dataframe is None. Cannot write. Please load a DF into the TableIO object first.')
        DCMStorage.write_csv(self.data_path, self.df)
