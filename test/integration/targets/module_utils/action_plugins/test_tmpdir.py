# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        results = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        results['remote_tmp'] = self._connection._shell.get_option('remote_tmp')
        results['invoke1'] = self._execute_module(task_vars=task_vars)
        results['invoke2'] = self._execute_module(task_vars=task_vars)

        self._remove_tmp_path(self._connection._shell.tmpdir)

        return results
