# (c) 2013, Daniel Hokka Zakrisson <daniel@hozac.com>
# (c) 2014, Serge van Ginderachter <serge@vanginderachter.be>
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible import constants as C
from ansible.errors import AnsibleError

from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible.utils.vars import combine_vars

from ansible.inventory.ini import InventoryParser as InventoryINIParser
from ansible.inventory.script import InventoryScript

__all__ = ['get_file_parser']

def get_file_parser(hostsfile, groups, loader):
    # check to see if the specified file starts with a
    # shebang (#!/), so if an error is raised by the parser
    # class we can show a more apropos error

    shebang_present = False
    processed = False
    myerr = []
    parser = None

    try:
        inv_file = open(hostsfile)
        first_line = inv_file.readlines()[0]
        inv_file.close()
        if first_line.startswith('#!'):
            shebang_present = True
    except:
        pass

    if loader.is_executable(hostsfile):
        try:
            parser = InventoryScript(loader=loader, groups=groups, filename=hostsfile)
            processed = True
        except Exception as e:
            myerr.append("The file %s is marked as executable, but failed to execute correctly. " % hostsfile + \
                            "If this is not supposed to be an executable script, correct this with `chmod -x %s`." % hostsfile)
            myerr.append(str(e))

    if not processed:
        try:
            parser = InventoryINIParser(loader=loader, groups=groups, filename=hostsfile)
            processed = True
        except Exception as e:
            if shebang_present and not loader.is_executable(hostsfile):
                myerr.append("The file %s looks like it should be an executable inventory script, but is not marked executable. " % hostsfile + \
                              "Perhaps you want to correct this with `chmod +x %s`?" % hostsfile)
            else:
                myerr.append(str(e))

    if not processed and myerr:
        raise AnsibleError( '\n'.join(myerr) )

    return parser

class InventoryDirectory(object):
    ''' Host inventory parser for ansible using a directory of inventories. '''

    def __init__(self, loader, groups=None, filename=C.DEFAULT_HOST_LIST):
        if groups is None:
            groups = dict()

        self.names = os.listdir(filename)
        self.names.sort()
        self.directory = filename
        self.parsers = []
        self.hosts = {}
        self.groups = groups

        self._loader = loader

        for i in self.names:

            # Skip files that end with certain extensions or characters
            if any(i.endswith(ext) for ext in C.DEFAULT_INVENTORY_IGNORE):
                continue
            # Skip hidden files
            if i.startswith('.') and not i.startswith('./'):
                continue
            # These are things inside of an inventory basedir
            if i in ("host_vars", "group_vars", "vars_plugins"):
                continue
            fullpath = os.path.join(self.directory, i)
            if os.path.isdir(fullpath):
                parser = InventoryDirectory(loader=loader, groups=groups, filename=fullpath)
            else:
                parser = get_file_parser(fullpath, self.groups, loader)
                if parser is None:
                    #FIXME: needs to use display
                    import warnings
                    warnings.warning("Could not find parser for %s, skipping" % fullpath)
                    continue

            self.parsers.append(parser)

            # retrieve all groups and hosts form the parser and add them to
            # self, don't look at group lists yet, to avoid
            # recursion trouble, but just make sure all objects exist in self
            newgroups = parser.groups.values()
            for group in newgroups:
                for host in group.hosts:
                    self._add_host(host)
            for group in newgroups:
                self._add_group(group)

            # now check the objects lists so they contain only objects from
            # self; membership data in groups is already fine (except all &
            # ungrouped, see later), but might still reference objects not in self
            for group in self.groups.values():
                # iterate on a copy of the lists, as those lists get changed in
                # the loop
                # list with group's child group objects:
                for child in group.child_groups[:]:
                    if child != self.groups[child.name]:
                        group.child_groups.remove(child)
                        group.child_groups.append(self.groups[child.name])
                # list with group's parent group objects:
                for parent in group.parent_groups[:]:
                    if parent != self.groups[parent.name]:
                        group.parent_groups.remove(parent)
                        group.parent_groups.append(self.groups[parent.name])
                # list with group's host objects:
                for host in group.hosts[:]:
                    if host != self.hosts[host.name]:
                        group.hosts.remove(host)
                        group.hosts.append(self.hosts[host.name])
                    # also check here that the group that contains host, is
                    # also contained in the host's group list
                    if group not in self.hosts[host.name].groups:
                        self.hosts[host.name].groups.append(group)

        # extra checks on special groups all and ungrouped
        # remove hosts from 'ungrouped' if they became member of other groups
        if 'ungrouped' in self.groups:
            ungrouped = self.groups['ungrouped']
            # loop on a copy of ungrouped hosts, as we want to change that list
            for host in ungrouped.hosts[:]:
                if len(host.groups) > 1:
                    host.groups.remove(ungrouped)
                    ungrouped.hosts.remove(host)

        # remove hosts from 'all' if they became member of other groups
        # all should only contain direct children, not grandchildren
        # direct children should have dept == 1
        if 'all' in self.groups:
            allgroup = self.groups['all' ]
            # loop on a copy of all's  child groups, as we want to change that list
            for group in allgroup.child_groups[:]:
                # groups might once have beeen added to all, and later be added
                # to another group: we need to remove the link wit all then
                if len(group.parent_groups) > 1 and allgroup in group.parent_groups:
                    # real children of all have just 1 parent, all
                    # this one has more, so not a direct child of all anymore
                    group.parent_groups.remove(allgroup)
                    allgroup.child_groups.remove(group)
                elif allgroup not in group.parent_groups:
                    # this group was once added to all, but doesn't list it as
                    # a parent any more; the info in the group is the correct
                    # info
                    allgroup.child_groups.remove(group)


    def _add_group(self, group):
        """ Merge an existing group or add a new one;
            Track parent and child groups, and hosts of the new one """

        if group.name not in self.groups:
            # it's brand new, add him!
            self.groups[group.name] = group
        # the Group class does not (yet) implement __eq__/__ne__,
        # so unlike Host we do a regular comparison here
        if self.groups[group.name] != group:
            # different object, merge
            self._merge_groups(self.groups[group.name], group)

    def _add_host(self, host):
        if host.name not in self.hosts:
            # Papa's got a brand new host
            self.hosts[host.name] = host
        # because the __eq__/__ne__ methods in Host() compare the
        # name fields rather than references, we use id() here to
        # do the object comparison for merges
        if self.hosts[host.name] != host:
            # different object, merge
            self._merge_hosts(self.hosts[host.name], host)

    def _merge_groups(self, group, newgroup):
        """ Merge all of instance newgroup into group,
            update parent/child relationships
            group lists may still contain group objects that exist in self with
            same name, but was instanciated as a different object in some other
            inventory parser; these are handled later """

        # name
        if group.name != newgroup.name:
            raise AnsibleError("Cannot merge group %s with %s" % (group.name, newgroup.name))

        # depth
        group.depth = max([group.depth, newgroup.depth])

        # hosts list (host objects are by now already added to self.hosts)
        for host in newgroup.hosts:
            grouphosts = dict([(h.name, h) for h in group.hosts])
            if host.name in grouphosts:
                # same host name but different object, merge
                self._merge_hosts(grouphosts[host.name], host)
            else:
                # new membership, add host to group from self
                # group from self will also be added again to host.groups, but
                # as different object
                group.add_host(self.hosts[host.name])
                # now remove this the old object for group in host.groups
                for hostgroup in [g for g in host.groups]:
                    if hostgroup.name == group.name and hostgroup != self.groups[group.name]:
                        self.hosts[host.name].groups.remove(hostgroup)


        # group child membership relation
        for newchild in newgroup.child_groups:
            # dict with existing child groups:
            childgroups = dict([(g.name, g) for g in group.child_groups])
            # check if child of new group is already known as a child
            if newchild.name not in childgroups:
                self.groups[group.name].add_child_group(newchild)

        # group parent membership relation
        for newparent in newgroup.parent_groups:
            # dict with existing parent groups:
            parentgroups = dict([(g.name, g) for g in group.parent_groups])
            # check if parent of new group is already known as a parent
            if newparent.name not in parentgroups:
                if newparent.name not in self.groups:
                    # group does not exist yet in self, import him
                    self.groups[newparent.name] = newparent
                # group now exists but not yet as a parent here
                self.groups[newparent.name].add_child_group(group)

        # variables
        group.vars = combine_vars(group.vars, newgroup.vars)

    def _merge_hosts(self,host, newhost):
        """ Merge all of instance newhost into host """

        # name
        if host.name != newhost.name:
            raise AnsibleError("Cannot merge host %s with %s" % (host.name, newhost.name))

        # group membership relation
        for newgroup in newhost.groups:
            # dict with existing groups:
            hostgroups = dict([(g.name, g) for g in host.groups])
            # check if new group is already known as a group
            if newgroup.name not in hostgroups:
                if newgroup.name not in self.groups:
                    # group does not exist yet in self, import him
                    self.groups[newgroup.name] = newgroup
                # group now exists but doesn't have host yet
                self.groups[newgroup.name].add_host(host)

        # variables
        host.vars = combine_vars(host.vars, newhost.vars)

    def get_host_variables(self, host):
        """ Gets additional host variables from all inventories """
        vars = {}
        for i in self.parsers:
            vars.update(i.get_host_variables(host))
        return vars

