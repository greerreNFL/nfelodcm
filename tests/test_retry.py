"""
Tests for Retry utility (classify_error, with_retry)
"""
import pytest
import requests

from nfelodcm.nfelodcm.Engine.Primatives.Retry import (
    classify_error, with_retry,
    RetryableError, AuthError, ParseError
)


class TestClassifyError:
    def test_connection_error_is_retryable(self):
        """ConnectionError classified as retryable"""
        assert classify_error(ConnectionError()) == 'retryable'

    def test_timeout_error_is_retryable(self):
        """TimeoutError classified as retryable"""
        assert classify_error(TimeoutError()) == 'retryable'

    def test_requests_connection_error_is_retryable(self):
        """requests.ConnectionError classified as retryable"""
        assert classify_error(requests.exceptions.ConnectionError()) == 'retryable'

    def test_requests_timeout_is_retryable(self):
        """requests.Timeout classified as retryable"""
        assert classify_error(requests.exceptions.Timeout()) == 'retryable'

    def test_value_error_is_parse(self):
        """ValueError classified as parse"""
        assert classify_error(ValueError('bad')) == 'parse'

    def test_key_error_is_parse(self):
        """KeyError classified as parse"""
        assert classify_error(KeyError('missing')) == 'parse'

    def test_type_error_is_parse(self):
        """TypeError classified as parse"""
        assert classify_error(TypeError('wrong type')) == 'parse'

    def test_http_401_is_auth(self):
        """401 HTTPError classified as auth"""
        resp = requests.models.Response()
        resp.status_code = 401
        err = requests.exceptions.HTTPError(response=resp)
        assert classify_error(err) == 'auth'

    def test_http_403_is_auth(self):
        """403 HTTPError classified as auth"""
        resp = requests.models.Response()
        resp.status_code = 403
        err = requests.exceptions.HTTPError(response=resp)
        assert classify_error(err) == 'auth'

    def test_http_404_is_parse(self):
        """404 HTTPError classified as parse (not retryable)"""
        resp = requests.models.Response()
        resp.status_code = 404
        err = requests.exceptions.HTTPError(response=resp)
        assert classify_error(err) == 'parse'

    def test_http_500_is_retryable(self):
        """500 HTTPError classified as retryable"""
        resp = requests.models.Response()
        resp.status_code = 500
        err = requests.exceptions.HTTPError(response=resp)
        assert classify_error(err) == 'retryable'

    def test_unknown_error_is_retryable(self):
        """Unknown exceptions default to retryable"""
        assert classify_error(RuntimeError('unknown')) == 'retryable'


class TestWithRetry:
    def test_success_on_first_try(self):
        """Successful fn returns immediately"""
        result = with_retry(lambda: 42, max_retries=3)
        assert result == 42

    def test_success_after_retries(self):
        """Recovers after transient failures"""
        call_count = {'n': 0}
        def flaky():
            call_count['n'] += 1
            if call_count['n'] < 3:
                raise ConnectionError('transient')
            return 'ok'
        result = with_retry(flaky, max_retries=3, base_delay=0.01)
        assert result == 'ok'
        assert call_count['n'] == 3

    def test_exhausted_retries_raises_retryable_error(self):
        """All retries exhausted raises RetryableError"""
        def always_fail():
            raise ConnectionError('always')
        with pytest.raises(RetryableError):
            with_retry(always_fail, max_retries=2, base_delay=0.01)

    def test_auth_error_raises_immediately(self):
        """Auth errors do not retry"""
        call_count = {'n': 0}
        def auth_fail():
            call_count['n'] += 1
            resp = requests.models.Response()
            resp.status_code = 401
            raise requests.exceptions.HTTPError(response=resp)
        with pytest.raises(AuthError):
            with_retry(auth_fail, max_retries=3, base_delay=0.01)
        assert call_count['n'] == 1

    def test_parse_error_raises_immediately(self):
        """Parse errors do not retry"""
        call_count = {'n': 0}
        def parse_fail():
            call_count['n'] += 1
            raise ValueError('bad parse')
        with pytest.raises(ParseError):
            with_retry(parse_fail, max_retries=3, base_delay=0.01)
        assert call_count['n'] == 1

    def test_context_in_error_message(self):
        """Context string appears in error message"""
        def always_fail():
            raise ConnectionError('fail')
        with pytest.raises(RetryableError, match='my_context'):
            with_retry(always_fail, max_retries=1, base_delay=0.01, context='my_context')
