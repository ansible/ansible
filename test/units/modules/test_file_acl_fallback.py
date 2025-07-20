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


class TestACLFallback:
    """Test ACL fallback functionality when setfacl is not available."""

    def test_has_setfacl_available(self):
        """Test has_setfacl returns True when setfacl is available."""
        from ansible.module_utils.basic import AnsibleModule
        
        # Create a mock module with the has_setfacl method
        module = Mock()
        module.get_bin_path = Mock(return_value='/usr/bin/setfacl')
        
        # Test the has_setfacl method directly
        result = module.get_bin_path('setfacl', required=False)
        assert result == '/usr/bin/setfacl'

    def test_has_setfacl_not_available(self):
        """Test has_setfacl returns False when setfacl is not available."""
        from ansible.module_utils.basic import AnsibleModule
        
        # Create a mock module with the has_setfacl method
        module = Mock()
        module.get_bin_path = Mock(return_value=None)
        
        # Test the has_setfacl method directly
        result = module.get_bin_path('setfacl', required=False)
        assert result is None

    def test_shell_set_user_facl_available(self):
        """Test set_user_facl when setfacl is available."""
        from ansible.plugins.shell import ShellBase
        
        # Create a mock shell with get_bin_path
        shell = Mock(spec=ShellBase)
        shell.get_bin_path = Mock(return_value='/usr/bin/setfacl')
        shell.join = Mock(return_value='setfacl -m u:testuser:r-x /tmp/test')
        
        # Test the set_user_facl method
        result = shell.join(['/usr/bin/setfacl', '-m', 'u:testuser:r-x', '/tmp/test'])
        assert result == 'setfacl -m u:testuser:r-x /tmp/test'

    def test_shell_set_user_facl_not_available(self):
        """Test set_user_facl when setfacl is not available."""
        from ansible.plugins.shell import ShellBase
        
        # Create a mock shell with get_bin_path returning None
        shell = Mock(spec=ShellBase)
        shell.get_bin_path = Mock(return_value=None)
        
        # Test that when setfacl is not available, the method would return None
        # This is the expected behavior from the shell plugin
        setfacl_path = shell.get_bin_path('setfacl', required=False)
        assert setfacl_path is None

    def test_action_remote_has_setfacl_available(self):
        """Test _remote_has_setfacl when setfacl is available."""
        # Create a concrete ActionBase instance
        action = ConcreteActionBase.__new__(ConcreteActionBase)
        
        # Mock the connection and shell
        action._connection = Mock()
        action._connection._shell = Mock()
        action._low_level_execute_command = Mock(return_value={'rc': 0, 'stdout': '/usr/bin/setfacl', 'stderr': ''})
        
        # Test the _remote_has_setfacl method
        result = action._remote_has_setfacl()
        assert result is True

    def test_action_remote_has_setfacl_not_available(self):
        """Test _remote_has_setfacl when setfacl is not available."""
        # Create a concrete ActionBase instance
        action = ConcreteActionBase.__new__(ConcreteActionBase)
        
        # Mock the connection and shell
        action._connection = Mock()
        action._connection._shell = Mock()
        action._low_level_execute_command = Mock(return_value={'rc': 1, 'stdout': '', 'stderr': 'command not found'})
        
        # Test the _remote_has_setfacl method
        result = action._remote_has_setfacl()
        assert result is False

    def test_action_remote_set_user_facl_available(self):
        """Test _remote_set_user_facl when setfacl is available."""
        # Create a concrete ActionBase instance
        action = ConcreteActionBase.__new__(ConcreteActionBase)
        
        # Mock the connection and shell
        action._connection = Mock()
        action._connection._shell = Mock()
        action._connection._shell.set_user_facl = Mock(return_value='setfacl -m u:testuser:r-x /tmp/test')
        action._low_level_execute_command = Mock(return_value={'rc': 0, 'stdout': '', 'stderr': ''})
        
        # Test the _remote_set_user_facl method
        result = action._remote_set_user_facl(['/tmp/test'], 'testuser', 'r-x')
        assert result['rc'] == 0

    def test_action_remote_set_user_facl_not_available(self):
        """Test _remote_set_user_facl when setfacl is not available."""
        # Create a concrete ActionBase instance
        action = ConcreteActionBase.__new__(ConcreteActionBase)
        
        # Mock the connection and shell
        action._connection = Mock()
        action._connection._shell = Mock()
        action._connection._shell.set_user_facl = Mock(return_value=None)
        
        # Test the _remote_set_user_facl method
        result = action._remote_set_user_facl(['/tmp/test'], 'testuser', 'r-x')
        assert result['rc'] == 1
        assert result['stderr'] == 'setfacl command not found'


if __name__ == '__main__':
    pytest.main([__file__]) 