# -*- coding: utf-8 -*-
# Copyright: (c) 2024, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, Mock, patch
from ansible.plugins.action.copy import ActionModule
from ansible.playbook.task import Task
from ansible.plugins.loader import connection_loader
from ansible.errors import AnsibleActionFail


class TestCopyActionValidation(unittest.TestCase):
    """Test parameter validation in the copy action plugin"""

    def setUp(self):
        self.play_context = Mock()
        self.play_context.shell = 'sh'
        self.connection = connection_loader.get('local', self.play_context)

    def _build_task(self, args):
        """Helper to build a task with given args"""
        task = MagicMock(Task)
        task.async_val = False
        task.diff = False
        task.check_mode = False
        task.environment = None
        task.args = args
        task.action = 'copy'
        return task

    def _build_action_module(self, args):
        """Helper to build an ActionModule with given args"""
        task = self._build_task(args)
        am = ActionModule(
            task, self.connection, self.play_context,
            loader=None, templar=None, shared_loader_obj=None
        )
        am.display = Mock()
        am._connection = self.connection
        # Mock methods that would try to execute commands or access filesystem
        am._make_tmp_path = Mock()
        am._remove_tmp_path = Mock()
        am._early_needs_tmp_path = Mock(return_value=False)
        return am

    def test_src_as_dict_raises_error(self):
        """Test that passing a dict as src raises a clear validation error"""
        args = {
            'src': {'foo': 'bar'},
            'dest': '/tmp/',
            'mode': '0755'
        }

        am = self._build_action_module(args)

        with self.assertRaises(AnsibleActionFail) as cm:
            am.run(task_vars={})

        # Should get a validation error, not an AttributeError
        error_msg = str(cm.exception)
        self.assertIn('src', error_msg.lower())

    def test_src_as_list_raises_error(self):
        """Test that passing a list as src raises a clear validation error"""
        args = {
            'src': ['/path/to/file1', '/path/to/file2'],
            'dest': '/tmp/',
        }

        am = self._build_action_module(args)

        with self.assertRaises(AnsibleActionFail) as cm:
            am.run(task_vars={})

        error_msg = str(cm.exception)
        self.assertIn('src', error_msg.lower())

    def test_missing_src_and_content_raises_error(self):
        """Test that missing both src and content raises validation error"""
        args = {
            'dest': '/tmp/',
        }

        am = self._build_action_module(args)

        with self.assertRaises(AnsibleActionFail) as cm:
            am.run(task_vars={})

        error_msg = str(cm.exception)
        # Should mention that src or content is required
        self.assertTrue('src' in error_msg.lower() or 'content' in error_msg.lower())

    def test_missing_dest_raises_error(self):
        """Test that missing dest raises validation error"""
        args = {
            'src': '/path/to/file',
        }

        am = self._build_action_module(args)

        with self.assertRaises(AnsibleActionFail) as cm:
            am.run(task_vars={})

        error_msg = str(cm.exception)
        self.assertIn('dest', error_msg.lower())

    def test_src_and_content_mutually_exclusive(self):
        """Test that providing both src and content raises validation error"""
        args = {
            'src': '/path/to/file',
            'content': 'some content',
            'dest': '/tmp/file',
        }

        am = self._build_action_module(args)

        with self.assertRaises(AnsibleActionFail) as cm:
            am.run(task_vars={})

        error_msg = str(cm.exception)
        # Should mention mutual exclusivity
        self.assertTrue('mutually exclusive' in error_msg.lower() or
                       ('src' in error_msg.lower() and 'content' in error_msg.lower()))

    def test_content_with_directory_dest_raises_error(self):
        """Test that content with directory dest (trailing slash) raises error"""
        args = {
            'content': 'some content',
            'dest': '/tmp/',
        }

        am = self._build_action_module(args)

        result = am.run(task_vars={})

        self.assertTrue(result.get('failed'))
        self.assertIn('content', result['msg'].lower())
        self.assertIn('dir', result['msg'].lower())

    def test_valid_src_and_dest_passes_validation(self):
        """Test that valid src and dest pass validation (will fail later in execution)"""
        args = {
            'src': '/path/to/file',
            'dest': '/tmp/file',
        }

        am = self._build_action_module(args)

        # Mock the parts that would fail due to file not existing
        with patch.object(am, '_find_needle', side_effect=Exception("File not found")):
            # Should get past validation and fail on file operations
            with self.assertRaises(Exception) as cm:
                am.run(task_vars={})

            # Should NOT be a validation error
            error_msg = str(cm.exception)
            self.assertNotIn('parameter', error_msg.lower())
            self.assertNotIn('argument', error_msg.lower())


if __name__ == '__main__':
    unittest.main()
