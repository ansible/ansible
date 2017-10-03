# (c) 2017, Red Hat, Inc. <support@ansible.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)

from ansible.plugins.loader import action_loader, connection_loader, filter_loader, lookup_loader, module_loader, test_loader

class SharedPluginLoaderObj:
    '''
    A simple object to make pass the various plugin loaders to
    the forked processes over the queue easier
    '''
    def __init__(self):
        self.action_loader = action_loader
        self.connection_loader = connection_loader
        self.filter_loader = filter_loader
        self.lookup_loader = lookup_loader
        self.module_loader = module_loader
        self.test_loader = test_loader

