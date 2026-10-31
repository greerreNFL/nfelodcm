import gzip
import urllib.parse

import requests

from nfelodcm.nfelodcm.Engine.Storage.StorageBackend import (
    StorageBackend, StorageError, MissingObjectError
)


class SupabaseStorage(StorageBackend):
    """
    StorageBackend on the Supabase Storage REST API.

    url is the project origin, https://<project-ref>.supabase.co.
    A URL that already ends in /storage/v1 is accepted and normalized
    to that origin. Callers normally pass SUPABASE_STORAGE_URL.

    key is the service role key. Callers normally pass
    SUPABASE_SERVICE_ROLE_KEY. This class does not read either variable.

    bucket is an existing bucket. This class does not create one.

    prefix is an optional folder in the bucket. When set, every key is
    stored under it, ie prefix='dcm' stores Data/games.csv at
    dcm/Data/games.csv.

    CSV keys are gzip compressed by this class and stored with a .gz
    suffix, ie Data/games.csv is stored at Data/games.csv.gz. Other keys
    are stored as given. Supabase stores the compressed bytes as is.
    """

    ## gzip level for csv objects ##
    GZIP_LEVEL = 6

    def __init__(self, url, key, bucket, prefix=None):
        ## parse the url, which must be the project origin ##
        if not isinstance(url, str):
            raise StorageError('STORAGE ERROR: url must be the project origin')
        parsed = urllib.parse.urlparse(url.strip())
        ## require a scheme and host, ie https://<project-ref>.supabase.co ##
        if parsed.scheme not in ('https', 'http') or not parsed.hostname:
            raise StorageError('STORAGE ERROR: url must be the project origin')
        ## accept a url that already ends in /storage/v1 by dropping that path ##
        path = parsed.path.rstrip('/')
        if path == '/storage/v1':
            path = ''
        ## any other path, query, or fragment is rejected ##
        if path or parsed.query or parsed.fragment:
            raise StorageError('STORAGE ERROR: url must be the project origin with no path')
        ## rebuild the origin, keeping a port if one was given ##
        netloc = parsed.hostname
        if parsed.port:
            netloc = '{0}:{1}'.format(parsed.hostname, parsed.port)
        self.base = '{0}://{1}'.format(parsed.scheme, netloc)
        ## the key and bucket are required. Neither is read from the environment ##
        if not isinstance(key, str) or key.strip() == '':
            raise StorageError('STORAGE ERROR: key is required')
        if not isinstance(bucket, str) or bucket.strip() == '':
            raise StorageError('STORAGE ERROR: bucket is required')
        self.key = key.strip()
        self.bucket = bucket.strip()
        ## the bucket is one url segment, so it cannot contain a separator ##
        if '/' in self.bucket or '\\' in self.bucket:
            raise StorageError('STORAGE ERROR: invalid bucket')
        ## optional folder in the bucket. Every key is stored under it ##
        self.prefix = None
        if prefix is not None:
            self.prefix = self.validate_key(prefix)

    def __repr__(self):
        ## the key is never included ##
        return 'SupabaseStorage(url={0}, bucket={1}, prefix={2})'.format(
            self.base,
            self.bucket,
            self.prefix
        )

    def prepare(self, folders):
        """
        Confirms each folder prefix can be listed. An empty prefix gets a
        .keep object. A list failure raises and creates nothing.
        """
        for folder in folders:
            prefix = self.validate_key(folder)
            ## list one object so an empty prefix can be told from a failure ##
            response = self.request(
                'POST',
                '{0}/storage/v1/object/list/{1}'.format(
                    self.base,
                    urllib.parse.quote(self.bucket, safe='')
                ),
                'prepare',
                prefix,
                json={
                    'prefix': self.resolve(prefix),
                    'limit': 1,
                    'offset': 0,
                }
            )
            rows = None
            if response.status_code == 200:
                rows = self.response_json(response)
            if not isinstance(rows, list):
                raise self.storage_error('prepare', prefix, response)
            ## mark an empty prefix so the folder is visible in the bucket ##
            if len(rows) == 0:
                self.write('{0}/.keep'.format(prefix), b'keep', 'text/plain')

    def exists(self, key):
        """
        True on HTTP 200 from the object info endpoint
        """
        response = self.request(
            'GET',
            self.object_url('object/info', key),
            'exists',
            key
        )
        if response.status_code == 200:
            return True
        if self.is_missing(response):
            return False
        raise self.storage_error('exists', key, response)

    def read(self, key):
        """
        Download the object bytes. CSV objects are decompressed.
        """
        response = self.request(
            'GET',
            self.object_url('object', key),
            'read',
            key
        )
        if response.status_code == 200:
            if not self.is_compressed(key):
                return response.content
            try:
                return gzip.decompress(response.content)
            except (OSError, EOFError):
                raise StorageError('STORAGE ERROR: read failed for bucket {0} key {1}. Object is not valid gzip'.format(
                    self.bucket,
                    key
                )) from None
        if self.is_missing(response):
            raise MissingObjectError('STORAGE ERROR: missing key {0} in bucket {1}'.format(
                key,
                self.bucket
            ))
        raise self.storage_error('read', key, response)

    def write(self, key, data, content_type):
        """
        Upload or replace the object. CSV objects are compressed first.
        Other bodies are the raw bytes.
        """
        ## gzip compress csv keys ##
        if self.is_compressed(key):
            data = gzip.compress(data, compresslevel=self.GZIP_LEVEL, mtime=0)
            content_type = 'application/gzip'
        ## the connect timeout is the deadline for sending the whole body ##
        response = self.request(
            'POST',
            self.object_url('object', key),
            'write',
            key,
            timeout=(120, 120),
            data=data,
            headers={
                'Content-Type': content_type,
                'x-upsert': 'true',
            }
        )
        if response.status_code != 200:
            raise self.storage_error('write', key, response)

    def request(self, method, url, operation, key, timeout=(10, 120), **kwargs):
        """
        Send one authenticated Storage REST request. One attempt, no retry.
        timeout is (connect, read). The connect value also bounds sending
        the body.
        """
        ## auth headers, merged with any request specific headers ##
        headers = {
            'apikey': self.key,
            'Authorization': 'Bearer {0}'.format(self.key),
        }
        headers.update(kwargs.pop('headers', {}))
        try:
            return requests.request(
                method,
                url,
                headers=headers,
                timeout=timeout,
                **kwargs
            )
        except requests.exceptions.RequestException:
            ## the requests exception holds the headers, so it is not chained ##
            raise StorageError('STORAGE ERROR: {0} failed for bucket {1} key {2} with no response'.format(
                operation,
                self.bucket,
                key
            )) from None

    def object_url(self, kind, key):
        """
        Storage REST URL for a validated key. Each path segment is quoted.
        """
        quoted_key = '/'.join(
            urllib.parse.quote(segment, safe='') for segment in self.resolve(key).split('/')
        )
        return '{0}/storage/v1/{1}/{2}/{3}'.format(
            self.base,
            kind,
            urllib.parse.quote(self.bucket, safe=''),
            quoted_key
        )

    def resolve(self, key):
        """
        Bucket object name for a validated key. CSV keys get a .gz suffix.
        The prefix is prepended when one was given.
        """
        key = self.validate_key(key)
        if self.is_compressed(key):
            key = '{0}.gz'.format(key)
        if self.prefix is None:
            return key
        return '{0}/{1}'.format(self.prefix, key)

    def is_compressed(self, key):
        """
        True for CSV keys, which are stored gzip compressed
        """
        return self.validate_key(key).endswith('.csv')

    def response_json(self, response):
        """
        Parsed JSON body, or None when the body is not JSON
        """
        try:
            return response.json()
        except ValueError:
            return None

    def error_body(self, response):
        """
        Error body as a dict. Empty when the body is not a JSON object.
        """
        body = self.response_json(response)
        if isinstance(body, dict):
            return body
        return {}

    def error_code(self, body):
        """
        Storage error code from an error body, or None
        """
        return body.get('code') or body.get('error')

    def is_missing(self, response):
        """
        True for the NoSuchKey error code, or a 404 with no error code.
        NoSuchBucket, InvalidJWT, AccessDenied, and other errors are failures.
        """
        code = self.error_code(self.error_body(response))
        if code == 'NoSuchKey':
            return True
        return response.status_code == 404 and not code

    def storage_error(self, operation, key, response):
        """
        StorageError for a failed response. The API key is never included.
        """
        body = self.error_body(response)
        return StorageError('STORAGE ERROR: {0} failed for bucket {1} key {2} status {3} code {4} {5}'.format(
            operation,
            self.bucket,
            key,
            response.status_code,
            self.error_code(body),
            body.get('message') or ''
        ))
