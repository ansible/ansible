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
import ansible.constants as C


def vars_file_matches(f, name):
    # A vars file matches if either:
    # - the basename of the file equals the value of 'name'
    # - the basename of the file, stripped its extension, equals 'name'
    if os.path.basename(f) == name:
        return True
    elif '.'.join(os.path.basename(f).split('.')[:-1]) == name:
        return True
    else:
        return False

def vars_files(vars_dir, name):
    files = []
    try:
        candidates = [os.path.join(vars_dir, f) for f in os.listdir(vars_dir)]
    except OSError:
        return files
    for f in candidates:
        if os.path.isfile(f) and vars_file_matches(f, name):
            files.append(f)
        elif os.path.isdir(f):
            files.extend(vars_files(f, name))
    return sorted(files)


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

        # load vars in inventory_dir/group_vars/name_of_group
        for x in groups:
            group_vars_dir = os.path.join(basedir, "group_vars")
            group_vars_files = vars_files(group_vars_dir, x)
            for path in group_vars_files:
                data = utils.parse_yaml_from_file(path)
                if type(data) != dict:
                    raise errors.AnsibleError("%s must be stored as a dictionary/hash" % path)
                if C.DEFAULT_HASH_BEHAVIOUR == "merge":
                    # let data content override results if needed
                    results = utils.merge_hash(results, data)
                else:
                    results.update(data)

        # load vars in inventory_dir/hosts_vars/name_of_host
        host_vars_dir = os.path.join(basedir, "host_vars")
        host_vars_files = vars_files(host_vars_dir, host.name)
        for path in host_vars_files:
            data = utils.parse_yaml_from_file(path)
            if type(data) != dict:
                raise errors.AnsibleError("%s must be stored as a dictionary/hash" % path)
            if C.DEFAULT_HASH_BEHAVIOUR == "merge":
                # let data content override results if needed
                results = utils.merge_hash(results, data)
            else:
                results.update(data)
        return results

