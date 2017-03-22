# Copyright 2017 RedHat, inc
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
'''
DOCUMENTATION:
    inventory: group_host_vars
    version_added: "2.4"
    short_description: In charge of loading group_vars and host_vars
    description:
        - Loads YAML vars into corresponding groups/hosts.
        - Files are restricted by extension to one of .yaml, .json, .yml or no extension.
        - Only applies to inventory sources that are existing paths.
    notes:
        - It takes the place of the previously hardcoded group_vars/host_vars loading.
'''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.errors import AnsibleParserError
from ansible.module_utils._text import to_bytes
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.utils.path import basedir

class InventoryModule(BaseInventoryPlugin):

    NAME = 'group_host_vars'
    TYPE = 'processor'

    def __init__(self):

        super(InventoryModule, self).__init__()
        self._basedir = ''

    def parse(self, inventory, loader, path, cache=True):
        ''' parses the inventory file '''

        super(InventoryModule, self).parse(inventory, loader, path)

        self._basedir = basedir(path)

        try:
            # load vars
            for objects, subdir in ((inventory.groups, 'group_vars'), (inventory.hosts, 'host_vars')):
                opath = os.path.realpath(os.path.join(self._basedir, subdir))
                b_opath = to_bytes(opath)
                # no need to do much if path does not exist for basedir
                if os.path.exists(b_opath):
                    if os.path.isdir(b_opath):
                        loader.load_vars_files(objects, opath, unsafe=True)
                    else:
                        self.display.warning("Found %s that is not a directory, skipping: %s" % (subdir, opath))

        except Exception as e:
            raise AnsibleParserError(e)

