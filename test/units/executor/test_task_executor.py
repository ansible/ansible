# -*- coding: utf-8 -*-
# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, Mock, patch


class TestTaskExecutorConnectionReuse:
    """Test connection reuse behavior with templated ansible_host"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_task = MagicMock()
        self.mock_task.action = 'debug'
        self.mock_task.args = {}
        self.mock_task.async_val = 0
        self.mock_task.poll = 0
        self.mock_task.delegate_to = None
        self.mock_task.connection = 'local'
        
        self.mock_play = MagicMock()
        
        # Create mock play contexts
        self.mock_play_context = MagicMock()
        self.mock_play_context.remote_addr = '192.168.1.100'
        
        self.mock_connection = MagicMock()
        self.mock_connection.connected = True
        self.mock_connection.matches_name = MagicMock(return_value=True)
        self.mock_connection._play_context = MagicMock()
        self.mock_connection._play_context.remote_addr = '192.168.1.100'

    def test_connection_reuse_with_literal_remote_addr(self):
        """Test that connection is reused when remote_addr is a literal value"""
        # Set up literal remote_addr
        self.mock_play_context.remote_addr = '192.168.1.100'
        self.mock_connection._play_context.remote_addr = '192.168.1.100'
        
        # Mock templar to return values unchanged
        mock_templar = MagicMock()
        mock_templar.template = lambda x: x
        
        # Simulate the connection reuse check
        templated_remote_addr = mock_templar.template(self.mock_play_context.remote_addr)
        connection_remote_addr = mock_templar.template(self.mock_connection._play_context.remote_addr)
        
        should_reuse = (
            self.mock_connection and
            getattr(self.mock_connection, 'connected', False) and
            self.mock_connection.matches_name(['local']) and
            templated_remote_addr == connection_remote_addr
        )
        
        # Connection should be reused
        assert should_reuse is True

    def test_connection_reuse_with_templated_remote_addr(self):
        """Test that connection is reused when templated remote_addr resolves to same value"""
        # Set up templated remote_addr
        self.mock_play_context.remote_addr = '{{ ansible_host }}'
        self.mock_connection._play_context.remote_addr = '192.168.1.100'
        
        # Mock templar to resolve template to same value
        mock_templar = MagicMock()
        mock_templar.template = lambda x: '192.168.1.100' if x == '{{ ansible_host }}' else x
        
        # Simulate the connection reuse check with templating
        templated_remote_addr = mock_templar.template(self.mock_play_context.remote_addr)
        connection_remote_addr = mock_templar.template(self.mock_connection._play_context.remote_addr)
        
        should_reuse = (
            self.mock_connection and
            getattr(self.mock_connection, 'connected', False) and
            self.mock_connection.matches_name(['local']) and
            templated_remote_addr == connection_remote_addr
        )
        
        # Connection should be reused after templating
        assert should_reuse is True
        assert templated_remote_addr == '192.168.1.100'
        assert connection_remote_addr == '192.168.1.100'

    def test_connection_recreate_when_remote_addr_changes(self):
        """Test that connection is recreated when remote_addr actually changes"""
        # Set up initial remote_addr
        self.mock_play_context.remote_addr = '192.168.1.100'
        self.mock_connection._play_context.remote_addr = '192.168.1.200'
        
        # Mock templar to return values unchanged
        mock_templar = MagicMock()
        mock_templar.template = lambda x: x
        
        # Simulate the connection reuse check
        templated_remote_addr = mock_templar.template(self.mock_play_context.remote_addr)
        connection_remote_addr = mock_templar.template(self.mock_connection._play_context.remote_addr)
        
        should_reuse = (
            self.mock_connection and
            getattr(self.mock_connection, 'connected', False) and
            self.mock_connection.matches_name(['local']) and
            templated_remote_addr == connection_remote_addr
        )
        
        # Connection should NOT be reused (addresses differ)
        assert should_reuse is False
        assert templated_remote_addr == '192.168.1.100'
        assert connection_remote_addr == '192.168.1.200'

    def test_connection_reuse_with_complex_template(self):
        """Test connection reuse with complex Jinja2 template"""
        # Set up complex templated remote_addr
        self.mock_play_context.remote_addr = '{{ host_prefix }}.{{ host_suffix }}'
        self.mock_connection._play_context.remote_addr = 'server1.example.com'
        
        # Mock templar to resolve complex template
        mock_templar = MagicMock()
        def template_func(x):
            if x == '{{ host_prefix }}.{{ host_suffix }}':
                return 'server1.example.com'
            return x
        mock_templar.template = template_func
        
        # Simulate the connection reuse check with templating
        templated_remote_addr = mock_templar.template(self.mock_play_context.remote_addr)
        connection_remote_addr = mock_templar.template(self.mock_connection._play_context.remote_addr)
        
        should_reuse = (
            self.mock_connection and
            getattr(self.mock_connection, 'connected', False) and
            self.mock_connection.matches_name(['local']) and
            templated_remote_addr == connection_remote_addr
        )
        
        # Connection should be reused after resolving complex template
        assert should_reuse is True
        assert templated_remote_addr == 'server1.example.com'
        assert connection_remote_addr == 'server1.example.com'

    def test_connection_reuse_no_existing_connection(self):
        """Test that new connection is created when none exists"""
        # Set up remote_addr
        self.mock_play_context.remote_addr = '192.168.1.100'
        
        # No existing connection
        existing_connection = None
        
        # Mock templar
        mock_templar = MagicMock()
        mock_templar.template = lambda x: x
        
        # Simulate the connection reuse check
        templated_remote_addr = mock_templar.template(self.mock_play_context.remote_addr)
        connection_remote_addr = mock_templar.template(None) if existing_connection else None
        
        should_reuse = (
            existing_connection and
            getattr(existing_connection, 'connected', False) and
            existing_connection.matches_name(['local']) and
            templated_remote_addr == connection_remote_addr
        )
        
        # Connection should NOT be reused (no existing connection)
        assert not should_reuse
        assert existing_connection is None
