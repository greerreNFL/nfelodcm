import abc


## storage error types ##
class StorageError(Exception):
    """
    Raised when a storage request fails
    """
    pass


class MissingObjectError(StorageError):
    """
    Raised when a read finds no object at the key
    """
    pass


class StorageBackend(abc.ABC):
    """
    Base class for storage adapters. DCMStorage presents the active backend
    to the package as one file tree. Adapters only move bytes for a key.
    They do not parse CSV or JSON and they do not construct state models.

    Keys are relative posix paths, ie Data/Parts/pbp/2024.csv
    """

    @abc.abstractmethod
    def prepare(self, folders):
        """
        Make each folder key in the DCM layout ready for writes
        """

    @abc.abstractmethod
    def exists(self, key):
        """
        True when an object is stored at the key. False only when the
        object is confirmed missing. Any other failure raises StorageError.
        """

    @abc.abstractmethod
    def read(self, key):
        """
        Return the object bytes. Raises MissingObjectError when the object
        is missing and StorageError on any other failure.
        """

    @abc.abstractmethod
    def write(self, key, data, content_type):
        """
        Replace the object at the key with data
        """

    def validate_key(self, key):
        """
        Returns the key when it is a relative posix key with no empty,
        '.', or '..' segment. Raises StorageError otherwise.
        """
        ## a key must be a non-empty relative posix string ##
        if not isinstance(key, str) or key == '' or key.startswith('/') or '\\' in key:
            raise StorageError('STORAGE ERROR: invalid key {0}'.format(key))
        ## no segment may be empty or point outside the tree ##
        for segment in key.split('/'):
            if segment in ('', '.', '..'):
                raise StorageError('STORAGE ERROR: invalid key {0}'.format(key))
        return key
