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

    def test_src_as_dict_raises_clear_error(self):
        """A dict passed as src should raise a clear error, not an AttributeError.

        Regression test for https://github.com/ansible/ansible/issues/86607
        """
        args = {
            'src': {'foo': 'bar'},
            'dest': '/tmp/',
            'mode': '0755',
        }

        am = self._build_action_module(args)

        with self.assertRaises(AnsibleActionFail) as cm:
            am.run(task_vars={})

        error_msg = str(cm.exception)
        self.assertIn('src must be a string', error_msg)
        self.assertIn('dict', error_msg)
        # Make sure the original opaque error is not what surfaces.
        self.assertNotIn('endswith', error_msg)

    def test_src_as_list_raises_clear_error(self):
        """A list passed as src should raise a clear error."""
        args = {
            'src': ['/path/to/file1', '/path/to/file2'],
            'dest': '/tmp/',
        }

        am = self._build_action_module(args)

        with self.assertRaises(AnsibleActionFail) as cm:
            am.run(task_vars={})

        error_msg = str(cm.exception)
        self.assertIn('src must be a string', error_msg)
        self.assertIn('list', error_msg)

    def test_dest_as_dict_raises_clear_error(self):
        """A dict passed as dest should raise a clear error."""
        args = {
            'src': '/path/to/file',
            'dest': {'foo': 'bar'},
        }

        am = self._build_action_module(args)

        with self.assertRaises(AnsibleActionFail) as cm:
            am.run(task_vars={})

        error_msg = str(cm.exception)
        self.assertIn('dest must be a string', error_msg)
        self.assertIn('dict', error_msg)

    def test_missing_src_and_content_fails(self):
        """Missing both src and content returns a failed result with the expected message."""
        args = {
            'dest': '/tmp/',
        }

        am = self._build_action_module(args)
        result = am.run(task_vars={})

        self.assertTrue(result.get('failed'))
        self.assertEqual(result['msg'], 'src (or content) is required')

    def test_missing_dest_fails(self):
        """Missing dest returns a failed result with the expected message."""
        args = {
            'src': '/path/to/file',
        }

        am = self._build_action_module(args)
        result = am.run(task_vars={})

        self.assertTrue(result.get('failed'))
        self.assertEqual(result['msg'], 'dest is required')

    def test_src_and_content_mutually_exclusive(self):
        """Providing both src and content returns a failed result."""
        args = {
            'src': '/path/to/file',
            'content': 'some content',
            'dest': '/tmp/file',
        }

        am = self._build_action_module(args)
        result = am.run(task_vars={})

        self.assertTrue(result.get('failed'))
        self.assertEqual(result['msg'], 'src and content are mutually exclusive')

    def test_content_with_directory_dest_fails(self):
        """content with a directory dest (trailing slash) returns a failed result."""
        args = {
            'content': 'some content',
            'dest': '/tmp/',
        }

        am = self._build_action_module(args)
        result = am.run(task_vars={})

        self.assertTrue(result.get('failed'))
        self.assertEqual(result['msg'], 'can not use content with a dir as dest')

    def test_valid_string_src_passes_validation(self):
        """Valid string src/dest pass type validation and proceed to file lookup."""
        args = {
            'src': '/path/to/file',
            'dest': '/tmp/file',
        }

        am = self._build_action_module(args)

        # _find_needle is where execution proceeds to after validation; failing
        # here proves we got past the type/required validation.
        with patch.object(am, '_find_needle', side_effect=Exception("File not found")):
            with self.assertRaises(Exception) as cm:
                am.run(task_vars={})

            error_msg = str(cm.exception)
            self.assertNotIn('must be a string', error_msg)
            self.assertNotIn('argument', error_msg.lower())


if __name__ == '__main__':
    unittest.main()
