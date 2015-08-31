# (c) 2015, Ansible Inc,
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

    def run(self, tmp=None, task_vars=dict()):
        ''' handler for package operations '''

        name  = self._task.args.get('name', None)
        state = self._task.args.get('state', None)
        module = self._task.args.get('use', 'auto')

        if module == 'auto':
            try:
                module = self._templar.template('{{ansible_service_mgr}}')
            except:
                pass # could not get it from template!

        if module == 'auto':
            facts = self._execute_module(module_name='setup', module_args=dict(filter='ansible_service_mgr'), task_vars=task_vars)
            self._display.debug("Facts %s" % facts)
            if not 'failed' in facts:
                module = getattr(facts['ansible_facts'], 'ansible_service_mgr', 'auto')

        if not module or module == 'auto' or module not in self._shared_loader_obj.module_loader:
            module = 'service'

        if module != 'auto':
            # run the 'service' module
            new_module_args = self._task.args.copy()
            if 'use' in new_module_args:
                del new_module_args['use']

            self._display.vvvv("Running %s" % module)
            return self._execute_module(module_name=module, module_args=new_module_args, task_vars=task_vars)

        else:

            return {'failed': True, 'msg': 'Could not detect which service manager to use. Try gathering facts or setting the "use" option.'}
