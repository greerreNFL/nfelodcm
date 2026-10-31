import io
import json
import pathlib
import datetime

import pandas as pd

import nfelodcm.nfelodcm.Utilities.paths as paths
from nfelodcm.nfelodcm.Utilities.calc_season_state import calc_season_state, infer_season_state
from nfelodcm.nfelodcm.Engine.Types import TableState, IterState, SeasonState
from nfelodcm.nfelodcm.Engine.Storage.StorageBackend import (
    StorageBackend, StorageError, MissingObjectError
)
from nfelodcm.nfelodcm.Engine.Storage.Adapters import LocalStorage


class DCMStorage():
    """
    The configured storage for the process. Presents the active
    StorageBackend to the package as one consistent file tree of
    CSVs and JSON. Callers pass storage paths from Utilities/paths.py.
    """

    ## storage layout ##
    PACKAGE_ROOT = paths.PACKAGE_ROOT
    DATA_DIR = paths.DATA_DIR
    STATE_DIR = paths.STATE_DIR
    TABLE_STATE_DIR = paths.TABLE_STATE_DIR
    GLOBAL_STATE_DIR = paths.GLOBAL_STATE_DIR
    PARTS_DATA_DIR = paths.PARTS_DATA_DIR
    PARTS_STATE_DIR = paths.PARTS_STATE_DIR
    FOLDERS = (
        DATA_DIR,
        PARTS_DATA_DIR,
        TABLE_STATE_DIR,
        PARTS_STATE_DIR,
        GLOBAL_STATE_DIR,
    )

    ## active backend ##
    backend = None

    ## season state in memory, and as stored on the active backend ##
    ## stored_season_state is None until the active backend is checked ##
    SEASON_STATE_SLA_SECONDS = 1800
    season_state = None
    stored_season_state = None

    @classmethod
    def configure(cls, backend):
        """
        Prepare and reconcile a backend, then make it the active backend.
        A failure raises and leaves the previous backend active.
        """
        if not isinstance(backend, StorageBackend):
            raise StorageError('STORAGE ERROR: configure requires a StorageBackend')
        ## ready the candidate before anything reads from it ##
        backend.prepare([cls.object_key(folder) for folder in cls.FOLDERS])
        cls.reconcile(backend)
        ## publish. Season state in memory is kept, but the new backend is unchecked ##
        cls.backend = backend
        cls.stored_season_state = None

    @classmethod
    def reconcile(cls, backend):
        """
        Checks each packaged map for a stored CSV on the backend. Missing
        CSVs have their state reset so freshness does not assume a current
        file. Existence is collected before any state is reset, so a
        storage error aborts with no resets.
        """
        ## pass 1: existence only ##
        found = []
        for map_path in paths.MAPS_DIR.glob('*.json'):
            table = map_path.stem
            found.append((
                table,
                backend.exists(cls.object_key(paths.data_path(table))),
                backend.exists(cls.object_key(paths.iter_state_path(table)))
            ))
        ## pass 2: reset confirmed gaps ##
        for table, csv_exists, iter_exists in found:
            if csv_exists:
                continue
            backend.write(
                cls.object_key(paths.table_state_path(table)),
                cls.json_bytes(TableState().to_dict()),
                'application/json'
            )
            if iter_exists:
                backend.write(
                    cls.object_key(paths.iter_state_path(table)),
                    cls.json_bytes(IterState().to_dict()),
                    'application/json'
                )

    @classmethod
    def get_season_state(cls):
        """
        Returns season state, calculating it only when neither memory nor
        the active backend has a state within SEASON_STATE_SLA_SECONDS.
        A valid state in memory is written to a backend that lacks it.
        """
        ## valid in memory ##
        if cls.season_state_valid(cls.season_state):
            ## already stored on this backend ##
            if cls.stored_season_state == cls.season_state:
                return cls.season_state
            ## the backend is unchecked, so a newer state may already be stored ##
            if cls.stored_season_state is None:
                stored = cls.read_model(SeasonState, paths.SEASON_STATE_JSON)
                if stored == cls.season_state:
                    cls.stored_season_state = stored
                    return cls.season_state
                if cls.season_state_valid(stored) and cls.updated_at(stored) > cls.updated_at(cls.season_state):
                    cls.season_state = stored
                    cls.stored_season_state = stored
                    return cls.season_state
            ## store the state in memory on this backend ##
            cls.store_season_state(cls.season_state)
            return cls.season_state
        ## memory is missing or stale, so use a valid stored state ##
        stored = cls.read_model(SeasonState, paths.SEASON_STATE_JSON)
        cls.stored_season_state = stored
        if cls.season_state_valid(stored):
            cls.season_state = stored
            return cls.season_state
        ## neither is valid, so calculate ##
        try:
            state = calc_season_state()
        except Exception as e:
            ## fall back to the newest stale state, then to the month ##
            print('WARN: Could not set season states with nflgamedata.')
            print('       {0}'.format(e))
            stale = [s for s in (cls.season_state, stored) if cls.updated_at(s) is not None]
            if len(stale) > 0:
                print('       Using the last calculated season state instead.')
                return max(stale, key=cls.updated_at)
            print('       Inferring from date instead.')
            return infer_season_state()
        cls.store_season_state(state)
        return cls.season_state

    @classmethod
    def store_season_state(cls, state):
        """
        Hold season state in memory and write it to the active backend.
        If the write fails, memory differs from stored and the next call
        retries the write.
        """
        cls.season_state = state
        cls.write_json(paths.SEASON_STATE_JSON, state.to_dict())
        cls.stored_season_state = state

    @classmethod
    def season_state_valid(cls, state):
        """
        True when the state was calculated within SEASON_STATE_SLA_SECONDS
        """
        updated = cls.updated_at(state)
        if updated is None:
            return False
        age = datetime.datetime.now(datetime.timezone.utc) - updated
        return age.total_seconds() < cls.SEASON_STATE_SLA_SECONDS

    @classmethod
    def updated_at(cls, state):
        """
        UTC datetime of a state's last_updated, or None when it has none
        """
        if state is None or state.last_updated is None:
            return None
        try:
            return datetime.datetime.fromisoformat(
                state.last_updated
            ).astimezone(datetime.timezone.utc)
        except (TypeError, ValueError):
            return None

    @classmethod
    def current_backend(cls):
        """
        The active backend. An unconfigured process configures
        LocalStorage at the package root on first use.
        """
        if cls.backend is None:
            cls.configure(LocalStorage(cls.PACKAGE_ROOT))
        return cls.backend

    @classmethod
    def read_csv(cls, path, **kwargs):
        """
        Read a stored CSV into a dataframe. A missing CSV raises
        MissingObjectError.
        """
        raw = cls.current_backend().read(cls.object_key(path))
        return pd.read_csv(io.BytesIO(raw), **kwargs)

    @classmethod
    def write_csv(cls, path, df):
        """
        Write a dataframe to a stored CSV
        """
        buffer = io.BytesIO()
        df.to_csv(buffer, index=False)
        cls.current_backend().write(cls.object_key(path), buffer.getvalue(), 'text/csv')

    @classmethod
    def read_json(cls, path):
        """
        Return the stored JSON value. Missing, non-UTF-8, and invalid
        JSON return {}.
        """
        try:
            raw = cls.current_backend().read(cls.object_key(path))
        except MissingObjectError:
            return {}
        try:
            return json.loads(raw.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {}

    @classmethod
    def read_model(cls, model, path):
        """
        Read a stored state file from the active backend and return it as
        an instance of the given JsonModel class. Storage counterpart of
        JsonModel.load, which only reads package files.

        Parameters:
        * model: JsonModel class (not an instance) to build, ie TableState,
          IterState, or SeasonState
        * path: storage path of the state file, ie paths.SEASON_STATE_JSON

        Returns an instance of model. Unknown keys are ignored and missing
        keys use the model's defaults. Field values are not type checked.
        A missing or unreadable file, or JSON that is not an object, returns
        the model's default instance. Storage failures raise.
        """
        try:
            return model.from_dict(cls.read_json(path))
        except AttributeError:
            return model()

    @classmethod
    def write_json(cls, path, data):
        """
        Write a JSON-serializable value to a storage path
        """
        cls.current_backend().write(cls.object_key(path), cls.json_bytes(data), 'application/json')

    @classmethod
    def json_bytes(cls, data):
        """
        UTF-8 JSON bytes for a stored value
        """
        return json.dumps(data, indent=2).encode('utf-8')

    @classmethod
    def object_key(cls, path):
        """
        Posix object key for a storage path from Utilities/paths.py
        """
        return pathlib.Path(path).as_posix()
