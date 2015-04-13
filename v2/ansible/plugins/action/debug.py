# Copyright 2012, Dag Wieers <dag@wieers.com>
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
from ansible.utils.boolean import boolean
from ansible.template import Templar

class ActionModule(ActionBase):
    ''' Print statements during execution '''

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=dict()):

        if 'msg' in self._task.args:
            if 'fail' in self._task.args and boolean(self._task.args['fail']):
                result = dict(failed=True, msg=self._task.args['msg'])
            else:
                result = dict(msg=self._task.args['msg'])
        # FIXME: move the LOOKUP_REGEX somewhere else
        elif 'var' in self._task.args: # and not utils.LOOKUP_REGEX.search(self._task.args['var']):
            templar = Templar(loader=self._loader, variables=task_vars)
            results = templar.template(self._task.args['var'], convert_bare=True)
            result = dict()
            result[self._task.args['var']] = results
        else:
            result = dict(msg='here we are')

        # force flag to make debug output module always verbose
        result['verbose_always'] = True

        return result
