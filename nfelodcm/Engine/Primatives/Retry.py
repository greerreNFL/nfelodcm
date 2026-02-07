import time
import requests
from typing import Callable, Any


## custom error types ##
class RetryableError(Exception):
    """
    Raised when all retries are exhausted on a transient error
    """
    pass


class AuthError(Exception):
    """
    Raised on 401/403 responses - no retry
    """
    pass


class ParseError(Exception):
    """
    Raised on parse/data errors - no retry
    """
    pass


def classify_error(e: Exception) -> str:
    """
    Classifies an exception as retryable, auth, or parse.
    Returns 'retryable', 'auth', or 'parse'.
    """
    ## HTTP errors ##
    if isinstance(e, requests.exceptions.HTTPError):
        status = getattr(e.response, 'status_code', None)
        if status in (401, 403):
            return 'auth'
        ## 4xx client errors (except auth) are not retryable - resource doesn't exist ##
        if status is not None and 400 <= status < 500:
            return 'parse'
        ## 5xx are retryable ##
        if status is not None and status >= 500:
            return 'retryable'
    ## connection and timeout errors are retryable ##
    if isinstance(e, (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        ConnectionError,
        TimeoutError
    )):
        return 'retryable'
    ## parse errors are not retryable ##
    if isinstance(e, (ValueError, KeyError, TypeError)):
        return 'parse'
    ## default to retryable for unknown errors ##
    return 'retryable'


def with_retry(
    fn: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    context: str = ''
) -> Any:
    """
    Executes fn() with exponential backoff retry logic.
    Only retries on retryable errors. Auth and parse errors raise immediately.
    Returns the result of fn().
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            last_error = e
            error_type = classify_error(e)
            ## auth errors raise immediately ##
            if error_type == 'auth':
                raise AuthError(
                    'AUTH ERROR{0}: {1}'.format(
                        ' ({0})'.format(context) if context else '',
                        e
                    )
                ) from e
            ## parse errors raise immediately ##
            if error_type == 'parse':
                raise ParseError(
                    'PARSE ERROR{0}: {1}'.format(
                        ' ({0})'.format(context) if context else '',
                        e
                    )
                ) from e
            ## retryable - backoff and retry ##
            if attempt < max_retries - 1:
                delay = min(base_delay * (2 ** attempt), max_delay)
                print('WARN: Retryable error{0}: {1}. Retrying in {2}s...'.format(
                    ' ({0})'.format(context) if context else '',
                    e,
                    delay
                ))
                time.sleep(delay)
    ## all retries exhausted ##
    raise RetryableError(
        'ERROR: All {0} retries exhausted{1}: {2}'.format(
            max_retries,
            ' ({0})'.format(context) if context else '',
            last_error
        )
    ) from last_error
