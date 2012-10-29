# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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

import os
import glob
from ansible import errors
from ansible import utils

class VarsModule(object):

    def __init__(self, inventory):
        self.inventory = inventory

    def run(self, host):
        # return the inventory variables for the host

        inventory = self.inventory
        #hostrec = inventory.get_host(host)

        groupz = sorted(inventory.groups_for_host(host.name), key=lambda g: g.depth)
        groups = [ g.name for g in groupz ]
        basedir = inventory.basedir()

        if basedir is None:
            # could happen when inventory is passed in via the API
            return

        results = {}

        # load vars in playbook_dir/group_vars/name_of_group
        for x in groups:
            path = os.path.join(basedir, "group_vars/%s" % x)
            if os.path.exists(path):
                data = utils.parse_yaml_from_file(path)
                if type(data) != dict:
                    raise errors.AnsibleError("%s must be stored as a dictionary/hash" % path)
                results.update(data)

        # load vars in playbook_dir/group_vars/name_of_host
        path = os.path.join(basedir, "host_vars/%s" % host.name)
        if os.path.exists(path):
            data = utils.parse_yaml_from_file(path)
            if type(data) != dict:
                raise errors.AnsibleError("%s must be stored as a dictionary/hash" % path)
            results.update(data)

        return results

