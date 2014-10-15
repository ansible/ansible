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

class Inventory:
    def __init__(self, host_list=C.DEFAULT_HOST_LIST, vault_password=None):
        pass
    def get_hosts(self, pattern="all"):
        pass
    def clear_pattern_cache(self):
        # Possibly not needed?
        pass
    def groups_for_host(self, host):
        pass
    def groups_list(self):
        pass
    def get_groups(self):
        pass
    def get_host(self, hostname):
        pass
    def get_group(self, groupname):
        pass
    def get_group_variables(self, groupname, update_cached=False, vault_password=None):
        pass
    def get_variables(self, hostname, update_cached=False, vault_password=None):
        pass
    def get_host_variables(self, hostname, update_cached=False, vault_password=None):
        pass
    def add_group(self, group):
        pass
    def list_hosts(self, pattern="all"):
        pass
    def list_groups(self):
        pass
    def get_restriction(self):
        pass
    def restrict_to(self, restriction):
        pass
    def also_restrict_to(self, restriction):
        pass
    def subset(self, subset_pattern):
        pass
    def lift_restriction(self):
        # HACK -- 
        pass
    def lift_also_restriction(self):
        # HACK -- dead host skipping
        pass
    def is_file(self):
        pass
    def basedir(self):
        pass
    def src(self):
        pass
    def playbook_basedir(self):
        pass
    def set_playbook_basedir(self, dir):
        pass
    def get_host_vars(self, host, new_pb_basedir=False):
        pass
    def get_group_vars(self, group, new_pb_basedir=False):
        pass

