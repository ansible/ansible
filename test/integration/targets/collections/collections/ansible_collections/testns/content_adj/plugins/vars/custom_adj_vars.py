# Copyright 2019 RedHat, inc
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
#############################################
from __future__ import annotations

DOCUMENTATION = '''
    vars: custom_adj_vars
    version_added: "2.10"
    short_description: load host and group vars
    description: test loading host and group vars from a collection
    options:
      stage:
        default: all
        choices: ['all', 'inventory', 'task']
        type: str
        ini:
          - key: stage
            section: custom_adj_vars
        env:
          - name: ANSIBLE_VARS_PLUGIN_STAGE
'''

from ansible.plugins.vars import BaseVarsPlugin


class VarsModule(BaseVarsPlugin):

    def get_vars(self, loader, path, entities, cache=True):
        super(VarsModule, self).get_vars(loader, path, entities)
        return {'collection': 'adjacent', 'adj_var': 'value'}
