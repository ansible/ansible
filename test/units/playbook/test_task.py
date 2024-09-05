# Copyright: (c) Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import unittest

from unittest.mock import patch

from ansible import errors
from ansible.parsing.yaml import objects
from ansible.playbook.task import Task
from ansible.plugins.loader import init_plugin_loader


basic_command_task = dict(
    name='Test Task',
    command='echo hi'
)

kv_command_task = dict(
    action='command echo hi'
)

# See #36848
kv_bad_args_str = '- apk: sdfs sf sdf 37'
kv_bad_args_ds = {'apk': 'sdfs sf sdf 37'}


class TestTask(unittest.TestCase):

    def setUp(self):
        self._task_base = {'name': 'test', 'action': 'debug'}

    def tearDown(self):
        pass

    def test_construct_empty_task(self):
        Task()

    def test_construct_task_with_role(self):
        pass

    def test_construct_task_with_block(self):
        pass

    def test_construct_task_with_role_and_block(self):
        pass

    def test_load_task_simple(self):
        t = Task.load(basic_command_task)
        assert t is not None
        self.assertEqual(t.get_name(), basic_command_task['name'])
        self.assertEqual(t.action, 'command')
        self.assertEqual(t.args, dict(_raw_params='echo hi'))

    def test_load_task_kv_form(self):
        t = Task.load(kv_command_task)
        self.assertEqual(t.action, 'command')
        self.assertEqual(t.args, dict(_raw_params='echo hi'))

    @patch.object(errors.AnsibleError, '_get_error_lines_from_file')
    def test_load_task_kv_form_error_36848(self, mock_get_err_lines):
        init_plugin_loader()
        ds = objects.AnsibleMapping(kv_bad_args_ds)
        ds.ansible_pos = ('test_task_faux_playbook.yml', 1, 1)
        mock_get_err_lines.return_value = (kv_bad_args_str, '')

        with self.assertRaises(errors.AnsibleParserError) as cm:
            Task.load(ds)

        self.assertIsInstance(cm.exception, errors.AnsibleParserError)
        self.assertEqual(cm.exception.obj, ds)
        self.assertEqual(cm.exception.obj, kv_bad_args_ds)
        self.assertIn("The error appears to be in 'test_task_faux_playbook.yml", cm.exception.message)
        self.assertIn(kv_bad_args_str, cm.exception.message)
        self.assertIn('apk', cm.exception.message)
        self.assertEqual(cm.exception.message.count('The offending line'), 1)
        self.assertEqual(cm.exception.message.count('The error appears to be in'), 1)

    def test_task_auto_name(self):
        self.assertNotIn('name', kv_command_task)
        t = Task.load(kv_command_task)
        self.assertEqual(t.get_name(), 'command')

    def test_delay(self):
        good_params = [
            (0, 0),
            (0.1, 0.1),
            ('0.3', 0.3),
            ('0.03', 0.03),
            ('12', 12),
            (12, 12),
            (1.2, 1.2),
            ('1.2', 1.2),
            ('1.0', 1),
        ]
        for delay, expected in good_params:
            with self.subTest(f'type "{type(delay)}" was not cast to float', delay=delay, expected=expected):
                p = dict(delay=delay)
                p.update(self._task_base)
                t = Task().load_data(p)
                self.assertEqual(t.get_validated_value('delay', t.fattributes.get('delay'), delay, None), expected)

        bad_params = [
            ('E', ValueError),
            ('1.E', ValueError),
            ('E.1', ValueError),
        ]
        for delay, expected in bad_params:
            with self.subTest(f'type "{type(delay)} was cast to float w/o error', delay=delay, expected=expected):
                p = dict(delay=delay)
                p.update(self._task_base)
                t = Task().load_data(p)
                with self.assertRaises(expected):
                    dummy = t.get_validated_value('delay', t.fattributes.get('delay'), delay, None)

    def test_task_auto_name_with_role(self):
        pass

    def test_load_task_complex_form(self):
        pass

    def test_can_load_module_complex_form(self):
        pass

    def test_local_action_implies_delegate(self):
        pass

    def test_local_action_conflicts_with_delegate(self):
        pass

    def test_delegate_to_parses(self):
        pass
