# (c) 2012-2013, Michael DeHaan <michael.dehaan@gmail.com>
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

class VarsModule(object):

    """
    Loads variables from group_vars/<groupname> and host_vars/<hostname> in directories parallel
    to the inventory base directory or in the same directory as the playbook.  Variables in the playbook
    dir will win over the inventory dir if files are in both.
    """

    def __init__(self, inventory):

        """ constructor """

        self.inventory = inventory

    def run(self, host):

        """ main body of the plugin, does actual loading """

        inventory = self.inventory
        basedir = inventory.playbook_basedir()
        if basedir is not None: 
            basedir = os.path.abspath(basedir)
        self.pb_basedir = basedir

        # sort groups by depth so deepest groups can override the less deep ones
        groupz = sorted(inventory.groups_for_host(host.name), key=lambda g: g.depth)
        groups = [ g.name for g in groupz ]
        inventory_basedir = inventory.basedir()

        results = {}
        scan_pass = 0

        # look in both the inventory base directory and the playbook base directory
        for basedir in [ inventory_basedir, self.pb_basedir ]:


            # this can happen from particular API usages, particularly if not run
            # from /usr/bin/ansible-playbook
            if basedir is None:
                continue

            scan_pass = scan_pass + 1

            # it's not an eror if the directory does not exist, keep moving
            if not os.path.exists(basedir):
                continue

            # save work of second scan if the directories are the same
            if inventory_basedir == self.pb_basedir and scan_pass != 1:
                continue

            # load vars in dir/group_vars/name_of_group
            for x in groups:

                p = os.path.join(basedir, "group_vars/%s" % x)

                # the file can be <groupname> or end in .yml or .yaml
                # currently ALL will be loaded, even if more than one
                paths = [p, '.'.join([p, 'yml']), '.'.join([p, 'yaml'])]

                for path in paths:

                    if os.path.exists(path) and not os.path.isdir(path):
                        data = utils.parse_yaml_from_file(path)
                        if type(data) != dict:
                            raise errors.AnsibleError("%s must be stored as a dictionary/hash" % path)

                        # combine vars overrides by default but can be configured to do a hash
                        # merge in settings

                        results = utils.combine_vars(results, data)

            # group vars have been loaded
            # load vars in inventory_dir/hosts_vars/name_of_host
            # these have greater precedence than group variables

            p = os.path.join(basedir, "host_vars/%s" % host.name)

            # again allow the file to be named filename or end in .yml or .yaml
            paths = [p, '.'.join([p, 'yml']), '.'.join([p, 'yaml'])]

            for path in paths:

                if os.path.exists(path) and not os.path.isdir(path):
                    data = utils.parse_yaml_from_file(path)
                    if type(data) != dict:
                        raise errors.AnsibleError("%s must be stored as a dictionary/hash" % path)
                    results = utils.combine_vars(results, data)

        # all done, results is a dictionary of variables for this particular host.
        return results

