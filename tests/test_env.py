"""
Tests for env utility (GitHub token loading)
"""
import os
import pytest
from unittest.mock import patch

from nfelodcm.nfelodcm.Utilities.env import get_github_token, get_github_headers


class TestGetGithubToken:
    def test_returns_none_when_not_set(self):
        """No GITHUB_TOKEN env var returns None"""
        with patch.dict(os.environ, {}, clear=True):
            assert get_github_token() is None

    def test_returns_token_when_set(self):
        """GITHUB_TOKEN env var returns the token"""
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'ghp_test123'}):
            assert get_github_token() == 'ghp_test123'


class TestGetGithubHeaders:
    def test_empty_headers_when_no_token(self):
        """No token returns empty dict"""
        with patch.dict(os.environ, {}, clear=True):
            headers = get_github_headers()
            assert headers == {}

    def test_auth_header_when_token_set(self):
        """Token set returns Authorization header"""
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'ghp_test123'}):
            headers = get_github_headers()
            assert headers == {'Authorization': 'token ghp_test123'}
