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

from . group import Group
from . host import Host

### List of things to change in Inventory
### Replace some lists with sets/frozensets.
###    Check where this makes sense to reveal externally
### Rename all caches to *_cache
### Standardize how caches are flushed for all caches if possible
### Think about whether retrieving variables should be methods of the
###     Groups/Hosts being queried with caches at that level
### Store things into a VarManager instead of inventory
### Merge list_hosts() and get_hosts()
### Merge list_groups() and groups_list()
### Merge get_variables() and get_host_variables()
### Restrictions:
###   Remove get_restriction()
###   Prefix restrict_to and lift_restriction with _ and note in docstring that
###       only playbook is to use these for implementing failed hosts.  This is
###       the closest that python has to a "friend function"
###   Can we get rid of restrictions altogether?
###   If we must keep restrictions, reimplement as a stack of sets.  Then
###       calling code will push and pop restrictions onto the inventory
### is_file() and basedir() => Change to properties
### Can we move the playbook variable resolving to someplace else?  Seems that:
###     1) It can change within a single session
###     2) Inventory shouldn't know about playbook.
###     Possibilities:
###     Host and groups read the host_vars and group_vars.  Both inventory and
###         playbook register paths that the hsot_vars and group_vars can read from.
###     The VariableManager reads the host_vars and group_vars and keeps them
###         layered depending on the context from which it's being asked what
###         the value of a variable is
###     Either of these results in getting rid of/moving to another class
###         Inventory.playbook_basedir() and Inventory.set_playbook_basedir()


### Questiony things:
### Do we want patterns to apply to both groups and hosts or only to hosts?
### Think about whether we could and want to go through the pattern_cache for
###    standard lookups
### Is this the current architecture:
###    We have a single Inventory per runner.
###    The Inventory may be initialized via:
###         an ini file
###         a directory of ini files
###         a script
###         a , separated string of hosts
###         a list of hosts
###         host_vars/*
###         group_vars/*
###    Do we want to change this so that multiple sources are allowed?
###    ansible -i /etc/ansible,./inventory,/opt/ansible/inventory_plugins/ec2.py,localhost
### What are vars_loaders?  What's their scope?  Why aren't the parsing of
###    inventory files and scripts implemented as a vars_loader?
### If we have add_group(), why no merge_group()?
### group = inven.get_group(name)
### if not group:
###     group = Group(name)
###     inven.add_group(group)
###
### vs
### group = Group(name)
### try:
###     inven.add_group(group)
### except:
###     inven.merge_group(group)
###
### vs:
### group = Group(name)
### inven.add_or_merge(group)

class Inventory:
        '''
        Collect variables for hosts and groups from inventory
        '''
    def __init__(self, host_list=C.DEFAULT_HOST_LIST, vault_password=None):
        '''
        :kwarg host_list: A filename for an inventory file or script or a list
            of hosts
        :kwarg vault_password: Password to use if any of the inventory sources
            are in an ansible vault
        '''
        pass

    def get_hosts(self, pattern="all"):
        '''
        Find all hosts matching a pattern string

        This also takes into account any inventory restrictions or applied
        subsets.

        :kwarg pattern: An fnmatch pattern that hosts must match on.  Multiple
            patterns may be separated by ";" and ":".  Defaults to the special
            pattern "all" which means to return all hosts.
        :returns: list of hosts
        '''
        pass

    def clear_pattern_cache(self):
        '''
        Invalidate the pattern cache
        '''
        #### Possibly not needed?
        # Former docstring:
        #   Called exclusively by the add_host plugin to allow patterns to be
        #   recalculated
        pass

    def groups_for_host(self, host):
        '''
        Return the groupnames to which a host belongs

        :arg host: Name of host to lookup
        :returns: list of groupnames
        '''
        pass

    def groups_list(self):
        '''
        Return a mapping of group name to hostnames which belong to the group

        :returns: dict of groupnames mapped to a list of hostnames within that group
        '''
        pass

    def get_groups(self):
        '''
        Retrieve the Group objects known to the Inventory

        :returns: list of :class:`Group`s belonging to the Inventory
        '''
        pass

    def get_host(self, hostname):
        '''
        Retrieve the Host object for a hostname

        :arg hostname: hostname associated with the :class:`Host`
        :returns: :class:`Host` object whose hostname was requested
        '''
        pass

    def get_group(self, groupname):
        '''
        Retrieve the Group object for a groupname

        :arg groupname: groupname associated with the :class:`Group`
        :returns: :class:`Group` object whose groupname was requested
        '''
        pass

    def get_group_variables(self, groupname, update_cached=False, vault_password=None):
        '''
        Retrieve the variables set on a group

        :arg groupname: groupname to retrieve variables for
        :kwarg update_cached: if True, retrieve the variables from the source
            and refresh the cache for this variable
        :kwarg vault_password: Password to use if any of the inventory sources
            are in an ansible vault
        :returns: dict mapping group variable names to values
        '''
        pass

    def get_variables(self, hostname, update_cached=False, vault_password=None):
        '''
        Retrieve the variables set on a host

        :arg hostname: hostname to retrieve variables for
        :kwarg update_cached: if True, retrieve the variables from the source
            and refresh the cache for this variable
        :kwarg vault_password: Password to use if any of the inventory sources
            are in an ansible vault
        :returns: dict mapping host variable names to values
        '''
        ### WARNING: v1 implementation ignores update_cached and vault_password
        pass

    def get_host_variables(self, hostname, update_cached=False, vault_password=None):
        '''
        Retrieve the variables set on a host

        :arg hostname: hostname to retrieve variables for
        :kwarg update_cached: if True, retrieve the variables from the source
            and refresh the cache for this variable
        :kwarg vault_password: Password to use if any of the inventory sources
            are in an ansible vault
        :returns: dict mapping host variable names to values
        '''
        pass

    def add_group(self, group):
        '''
        Add a new group to the inventory

        :arg group: Group object to add to the inventory
        '''
        pass

    def list_hosts(self, pattern="all"):
        '''
        Retrieve a list of hostnames for a pattern

        :kwarg pattern: Retrieve hosts which match this pattern.  The special
            pattern "all" matches every host the inventory knows about.
        :returns: list of hostnames
        '''
        ### Notes: Differences with get_hosts:
        ### get_hosts returns hosts, this returns host names
        ### This adds the implicit localhost/127.0.0.1 as a name but not as
        ### a host
        pass

    def list_groups(self):
        '''
        Retrieve list of groupnames
        :returns: list of groupnames
        '''
        pass

    def get_restriction(self):
        '''
        Accessor for the private _restriction attribute.
        '''
        ### Note: In v1, says to be removed.
        ### Not used by anything at all.
        pass

    def restrict_to(self, restriction):
        '''
        Restrict get and list operations to hosts given in the restriction

        :arg restriction:
        '''
        ### The v1 docstring says:
        ### Used by the main playbook code to exclude failed hosts, don't use
        ### this for other reasons
        pass

    def lift_restriction(self):
        '''
        Remove a restriction
        '''
        pass

    def also_restrict_to(self, restriction):
        '''
        Restrict get and list operations to hosts in the additional restriction
        '''
        ### Need to explore use case here -- maybe we want to restrict for
        ### several different reasons.  Within a certain scope we restrict
        ### again for a separate reason?
        pass

    def lift_also_restriction(self):
        '''
        Remove an also_restriction
        '''
        # HACK -- dead host skipping
        pass

    def subset(self, subset_pattern):
        """
        Limits inventory results to a subset of inventory that matches a given
        pattern, such as to select a subset of a hosts selection that also
        belongs to a certain geographic group or numeric slice.
        Corresponds to --limit parameter to ansible-playbook

        :arg subset_pattern: The pattern to limit with.  If this is None it
            clears the subset.  Multiple patterns may be specified as a comma,
            semicolon, or colon separated string.
        """
        pass

    def is_file(self):
        '''
        Did inventory come from a file?

        :returns: True if the inventory is file based, False otherwise
        '''
        pass

    def basedir(self):
        '''
        What directory was inventory read from

        :returns: the path to the directory holding the inventory.  None if
            the inventory is not file based
        '''
        pass

    def src(self):
        '''
        What's the complete path to the inventory file?

        :returns: Complete path to the inventory file.  None if inventory is
            not file-based
        '''
        pass

    def playbook_basedir(self):
        '''
        Retrieve the directory of the current playbook
        '''
        ### I want to move this out of inventory

        pass

    def set_playbook_basedir(self, dir):
        '''
        Tell Inventory the basedir of the current playbook so Inventory can
        look for host_vars and group_vars there.
        '''
        ### I want to move this out of inventory
        pass

    def get_host_vars(self, host, new_pb_basedir=False):
        '''
        Loads variables from host_vars/<hostname>

        The variables are loaded from subdirectories located either in the
        inventory base directory or the playbook base directory.  Variables in
        the playbook dir will win over the inventory dir if files are in both.
        '''
        pass

    def get_group_vars(self, group, new_pb_basedir=False):
        '''
        Loads variables from group_vars/<hostname>

        The variables are loaded from subdirectories located either in the
        inventory base directory or the playbook base directory.  Variables in
        the playbook dir will win over the inventory dir if files are in both.
        '''
        pass
