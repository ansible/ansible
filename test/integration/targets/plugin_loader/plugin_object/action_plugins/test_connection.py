# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    TRANSFERS_FILES = False
    _VALID_ARGS = frozenset(('connection_name', 'connection_aliases', 'connection_name_matches', 'connection_name_mismatches'))

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        expected_name = self._task.args.get('connection_name')
        expected_aliases = self._task.args.get('connection_aliases')
        expected_matches = self._task.args.get('connection_name_matches')
        expected_mismatches = self._task.args.get('connection_name_mismatches')

        result = {
            'connection_name': self._connection.ansible_name,
            'connection_aliases': self._connection.ansible_aliases,
            'expected_connection_name': expected_name,
            'expected_connection_aliases': expected_aliases,
            'expected_connection_matches': expected_matches,
            'expected_connection_mismatches': expected_mismatches,
            'failures': [],
        }

        if expected_name is not None and self._connection.ansible_name != expected_name:
            result['failures'].append(f'{self._connection.ansible_name} != {expected_name}')
        if expected_aliases is not None and self._connection.ansible_aliases != expected_aliases:
            result['failures'].append(f'{self._connection.ansible_aliases} != {expected_aliases}')
        if expected_matches and (missing_matches := [match for match in expected_matches if not self._connection.matches_name([match])]):
            result['failures'].append(f'Did not match name(s): {", ".join(missing_matches)}')
        if expected_mismatches and (matches := [match for match in expected_mismatches if self._connection.matches_name([match])]):
            result['failures'].append(f'Matched name(s): {", ".join(matches)}')

        result['failed'] = bool(result['failures'])
        return result
