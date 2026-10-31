import os
import stat
import tempfile
import pathlib

from nfelodcm.nfelodcm.Engine.Storage.StorageBackend import (
    StorageBackend, StorageError, MissingObjectError
)


class LocalStorage(StorageBackend):
    """
    StorageBackend on the local filesystem. Keys are files under root.
    """

    def __init__(self, root):
        self.root = pathlib.Path(root)

    def prepare(self, folders):
        """
        Create each folder under root. Safe to call repeatedly.
        """
        for folder in folders:
            self.resolve(folder).mkdir(parents=True, exist_ok=True)

    def exists(self, key):
        """
        True when the key is a regular file. False only when the path is absent.
        """
        path = self.resolve(key)
        try:
            info = path.stat()
        except FileNotFoundError:
            return False
        except OSError as e:
            raise StorageError('STORAGE ERROR: exists failed for key {0}'.format(key)) from e
        ## a directory is not a stored object ##
        if not stat.S_ISREG(info.st_mode):
            raise StorageError('STORAGE ERROR: key {0} is not a file'.format(key))
        return True

    def read(self, key):
        """
        Return the file bytes
        """
        path = self.resolve(key)
        try:
            with open(path, 'rb') as handle:
                return handle.read()
        except FileNotFoundError as e:
            raise MissingObjectError('STORAGE ERROR: missing key {0}'.format(key)) from e
        except OSError as e:
            raise StorageError('STORAGE ERROR: read failed for key {0}'.format(key)) from e

    def write(self, key, data, content_type):
        """
        Atomic write: write to a temp file in the same directory,
        then os.replace to the target path. Prevents corruption
        from interrupted writes. Local files do not store content_type.
        """
        path = self.resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(
            dir=path.parent,
            suffix='.tmp',
            prefix='.storage_'
        )
        try:
            with os.fdopen(fd, 'wb') as handle:
                handle.write(data)
            os.replace(tmp_path, path)
        except BaseException:
            ## remove the temp file so a failed write leaves nothing behind ##
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def resolve(self, key):
        """
        Filesystem path for a validated key under root
        """
        return self.root / self.validate_key(key)
