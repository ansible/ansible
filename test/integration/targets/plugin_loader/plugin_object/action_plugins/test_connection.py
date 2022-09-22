# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase
from ansible.plugins.loader import connection_loader


class ActionModule(ActionBase):

    TRANSFERS_FILES = False
    _VALID_ARGS = frozenset(('connection_name', 'connection_name_matches', 'connection_name_mismatches'))

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        expected_name = self._task.args.get('connection_name')
        expected_aliases = self._task.args.get('connection_aliases')
        expected_matches = self._task.args.get('connection_name_matches')
        expected_mismatches = self._task.args.get('connection_name_mismatches')

        result = {
            'connection_name': self._connection.ansible_name,
            'expected_connection_name': expected_name,
            'expected_connection_matches': expected_matches,
            'expected_connection_mismatches': expected_mismatches,
            'failures': [],
        }

        if expected_name is not None and self._connection.ansible_name != expected_name:
            result['failures'].append(f'{self._connection.ansible_name} != {expected_name}')
        for name in expected_matches or []:
            missing_matches = []
            context = connection_loader.find_plugin_with_context(name)
            if not context.resolved or context.resolved_fqcn != self._connection.ansible_name:
                missing_matches.append(name)
            if missing_matches:
                result['failures'].append(f'Did not match name(s): {", ".join(missing_matches)}')
        for name in expected_mismatches or []:
            matches = []
            context = connection_loader.find_plugin_with_context(name)
            if context.resolved and context._resolved_fqcn == self._connection.ansible_name:
                matches.append(name)
            if matches:
                result['failures'].append(f'Matched name(s): {", ".join(matches)}')

        result['failed'] = bool(result['failures'])
        return result
