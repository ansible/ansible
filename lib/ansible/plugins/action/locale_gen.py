# Based on service.py (c) 2015, Ansible Inc,
# Copyright (C) 2017 Red Hat, modified by Pierre-Louis Bonicoli
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        ''' handler for package operations '''

        self._supports_check_mode = True
        self._supports_async = True

        result = super(ActionModule, self).run(tmp, task_vars)

        distribution = self._task.args.get('distribution', 'auto').lower()
        if distribution == 'auto':
            try:
                if self._task.delegate_to:  # if we delegate, we should use delegated host's facts
                    distribution = self._templar.template("{{hostvars['%s']['ansible_facts']['ansible_distribution']}}" % self._task.delegate_to)
                else:
                    distribution = self._templar.template('{{ansible_facts["ansible_distribution"]}}')
            except:
                pass  # could not get it from template!

        if distribution == 'auto':
            facts = self._execute_module(module_name='setup', module_args=dict(gather_subset='!all'), task_vars=task_vars)
            self._display.debug("Facts %s" % facts)
            if 'ansible_facts' in facts:
                distribution = facts['ansible_facts'].get('ansible_distribution')

        if distribution == 'auto':
            return {
                'failed': True,
                'msg': 'Could not detect which distribution is used.',
            }

        new_module_args = self._task.args.copy()
        new_module_args['distribution'] = distribution
        result.update(self._execute_module(module_name='locale_gen', module_args=new_module_args, task_vars=task_vars, wrap_async=self._task.async))

        return result
