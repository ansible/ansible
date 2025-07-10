# Copyright (c) 2023 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.cli.config import _mask_sensitive_value


class TestConfigCLI:
    """Test ansible-config CLI functionality."""

    def test_mask_sensitive_value_token(self):
        """Test that authentication tokens are properly masked."""
        # Test long token
        long_token = 'very_long_authentication_token_123456789'
        result = _mask_sensitive_value('token', long_token)
        assert result == 'ver**********************************789'
        assert len(result) == len(long_token)

    def test_mask_sensitive_value_password(self):
        """Test that passwords are properly masked."""
        # Test password
        password = 'secretpassword123'
        result = _mask_sensitive_value('password', password)
        assert result == 'sec***********123'
        assert len(result) == len(password)

    def test_mask_sensitive_value_client_secret(self):
        """Test that client secrets are properly masked."""
        # Test client secret
        client_secret = 'abcdefgh'
        result = _mask_sensitive_value('client_secret', client_secret)
        assert result == 'a*******'
        assert len(result) == len(client_secret)

    def test_mask_sensitive_value_short_values(self):
        """Test masking of short sensitive values."""
        # Test short values
        short_token = 'ab'
        result = _mask_sensitive_value('token', short_token)
        assert result == 'a*'

        short_password = 'x'
        result = _mask_sensitive_value('password', short_password)
        assert result == 'x'

    def test_mask_sensitive_value_empty_values(self):
        """Test handling of empty/None values."""
        # Test empty string
        result = _mask_sensitive_value('token', '')
        assert result == ''

        # Test None
        result = _mask_sensitive_value('token', None)
        assert result is None

    def test_mask_sensitive_value_non_sensitive_settings(self):
        """Test that non-sensitive settings are not masked."""
        # Test non-sensitive settings
        url = 'https://galaxy.ansible.com'
        result = _mask_sensitive_value('url', url)
        assert result == url

        username = 'testuser'
        result = _mask_sensitive_value('username', username)
        assert result == username

    def test_mask_sensitive_value_non_string_values(self):
        """Test that non-string values are handled correctly."""
        # Test integer
        result = _mask_sensitive_value('token', 123)
        assert result == 123

        # Test boolean
        result = _mask_sensitive_value('password', True)
        assert result is True
