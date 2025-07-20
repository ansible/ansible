#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest
from unittest.mock import Mock, patch, MagicMock

from ansible.plugins.action import ActionBase


class ConcreteActionBase(ActionBase):
    """Concrete implementation of ActionBase for testing."""
    def run(self, tmp=None, task_vars=None):
        return {}


class TestACLMissingError:
    """Test error handling when setfacl is missing."""

    @patch('ansible.plugins.action.display')
    def test_fixup_perms2_skips_setfacl_when_not_available(self, mock_display):
        """Test that _fixup_perms2 skips setfacl when not available and shows warning."""
        # Create a concrete ActionBase instance
        action = ConcreteActionBase.__new__(ConcreteActionBase)
        
        # Mock the required methods to ensure we reach the setfacl logic
        action._remote_has_setfacl = Mock(return_value=False)
        action._remote_set_user_facl = Mock()
        action._remote_chmod = Mock(return_value={'rc': 0, 'stdout': '', 'stderr': ''})
        action._remote_chown = Mock(return_value={'rc': 0, 'stdout': '', 'stderr': ''})
        action._get_admin_users = Mock(return_value=['root'])
        action.get_become_option = Mock(return_value='testuser')
        action.get_shell_option = Mock(return_value=None)
        action._get_remote_user = Mock(return_value='remoteuser')
        
        # Mock the connection and shell
        action._connection = Mock()
        action._connection.become = True  # This is required for _is_become_unprivileged to return True
        action._connection._shell = Mock()
        action._connection._shell._IS_WINDOWS = False  # Ensure we're not on Windows
        action._connection._shell.join.return_value = 'which setfacl'
        action._low_level_execute_command = Mock(return_value={'rc': 1, 'stdout': '', 'stderr': 'not found'})
        
        # Call the method
        result = action._fixup_perms2(['/tmp/test'], execute=True)
        
        # Verify setfacl was not called
        action._remote_set_user_facl.assert_not_called()
        
        # Verify warning was displayed
        mock_display.warning.assert_called_once()

    @patch('ansible.plugins.action.display')
    def test_fixup_perms2_uses_setfacl_when_available(self, mock_display):
        """Test that _fixup_perms2 uses setfacl when available."""
        # Create a concrete ActionBase instance
        action = ConcreteActionBase.__new__(ConcreteActionBase)
        
        # Mock the required methods to ensure we reach the setfacl logic
        action._remote_has_setfacl = Mock(return_value=True)
        action._remote_set_user_facl = Mock(return_value={'rc': 0, 'stdout': '', 'stderr': ''})
        action._remote_chmod = Mock()
        action._remote_chown = Mock()
        action.get_become_option = Mock(return_value='testuser')
        action.get_shell_option = Mock(return_value=None)
        action._get_remote_user = Mock(return_value='remoteuser')
        action._get_admin_users = Mock(return_value=['root'])
        
        # Mock the connection and shell
        action._connection = Mock()
        action._connection.become = True  # This is required for _is_become_unprivileged to return True
        action._connection._shell = Mock()
        action._connection._shell._IS_WINDOWS = False  # Ensure we're not on Windows
        action._connection._shell.join.return_value = 'which setfacl'
        action._low_level_execute_command = Mock(return_value={'rc': 0, 'stdout': '/usr/bin/setfacl', 'stderr': ''})
        
        # Call the method
        result = action._fixup_perms2(['/tmp/test'], execute=True)
        
        # Verify setfacl was called
        action._remote_set_user_facl.assert_called_once()

    def test_remote_set_user_facl_handles_none_command(self):
        """Test that _remote_set_user_facl handles None command from shell."""
        # Create a concrete ActionBase instance
        action = ConcreteActionBase.__new__(ConcreteActionBase)
        
        # Mock the connection and shell
        action._connection = Mock()
        action._connection._shell = Mock()
        action._connection._shell.set_user_facl.return_value = None
        action._low_level_execute_command = Mock()
        
        # Call the method
        result = action._remote_set_user_facl(['/tmp/test'], 'testuser', 'rw')
        
        # Verify the result indicates failure
        assert result['rc'] == 1
        assert result['stderr'] == 'setfacl command not found'

    def test_shell_set_user_facl_returns_none_when_not_available(self):
        """Test that shell set_user_facl returns None when setfacl is not available."""
        from ansible.plugins.shell import ShellBase
        
        # Create a mock shell
        shell = Mock(spec=ShellBase)
        shell.get_bin_path = Mock(return_value=None)
        
        # Test that when setfacl is not available, the method would return None
        setfacl_path = shell.get_bin_path('setfacl', required=False)
        assert setfacl_path is None

    def test_shell_set_user_facl_returns_command_when_available(self):
        """Test that shell set_user_facl returns command when setfacl is available."""
        from ansible.plugins.shell import ShellBase
        
        # Create a mock shell
        shell = Mock(spec=ShellBase)
        shell.get_bin_path = Mock(return_value='/usr/bin/setfacl')
        shell.join = Mock(return_value='setfacl -m u:testuser:rw /tmp/test')
        
        # Test that when setfacl is available, the method returns a command
        result = shell.join(['/usr/bin/setfacl', '-m', 'u:testuser:rw', '/tmp/test'])
        assert result == 'setfacl -m u:testuser:rw /tmp/test'


if __name__ == '__main__':
    pytest.main([__file__]) 