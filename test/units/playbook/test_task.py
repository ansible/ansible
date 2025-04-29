# Copyright: (c) Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import unittest

from ansible.errors import AnsibleError
from ansible.playbook.task import Task


basic_command_task = dict(
    name='Test Task',
    command='echo hi'
)

kv_command_task = dict(
    action='command echo hi'
)


class TestTask(unittest.TestCase):
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

    def test_task_auto_name(self):
        assert 'name' not in kv_command_task
        Task.load(kv_command_task)
        self.assertNotIn('name', kv_command_task)
        t = Task.load(kv_command_task)
        self.assertEqual(t.get_name(), 'command')

    def test_delay(self):
        task_base = {'name': 'test', 'action': 'debug'}
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
                p.update(task_base)
                t = Task().load_data(p)
                self.assertEqual(t.get_validated_value('delay', t.fattributes.get('delay'), delay, None), expected)

        bad_params = [
            ('E', AnsibleError),
            ('1.E', AnsibleError),
            ('E.1', AnsibleError),
        ]
        for delay, expected in bad_params:
            with self.subTest(f'type "{type(delay)} was cast to float w/o error', delay=delay, expected=expected):
                p = dict(delay=delay)
                p.update(task_base)
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
