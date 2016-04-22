# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
from ansible import constants as C

from . aggregate import InventoryAggregateParser

class InventoryDirectoryParser(InventoryAggregateParser):

    CONDITION="is_dir(%s)"

    def __init__(self, inven_directory):
        directory = inven_directory
        names = os.listdir(inven_directory)
        filtered_names = []

        # Clean up the list of filenames
        for filename in names:
            # Skip files that end with certain extensions or characters
            if any(filename.endswith(ext) for ext in C.DEFAULT_INVENTORY_IGNORE):
                continue
            # Skip hidden files
            if filename.startswith('.') and not filename.startswith('.{0}'.format(os.path.sep)):
                continue
            # These are things inside of an inventory basedir
            if filename in ("host_vars", "group_vars", "vars_plugins"):
                continue
            fullpath = os.path.join(directory, filename)
            filtered_names.append(fullpath)

        super(InventoryDirectoryParser, self).__init__(filtered_names)

    def parse(self):
        return super(InventoryDirectoryParser, self).parse()
