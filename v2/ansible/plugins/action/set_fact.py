# Copyright 2013 Dag Wieers <dag@wieers.com>
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

from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase
from ansible.template import Templar
from ansible.utils.boolean import boolean

class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=dict()):
        templar = Templar(loader=self._loader, variables=task_vars)
        facts = dict()
        if self._task.args:
            for (k, v) in self._task.args.iteritems():
                k = templar.template(k)
                if isinstance(v, basestring) and v.lower() in ('true', 'false', 'yes', 'no'):
                    v = boolean(v)
                facts[k] = v
        return dict(changed=False, ansible_facts=facts)
