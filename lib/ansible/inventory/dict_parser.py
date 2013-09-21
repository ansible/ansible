#!/usr/bin/env python
# -*- coding: utf-8 -*-#
# @(#)dict_parser.py
#
#
# Copyright (C) 2013, GC3, University of Zurich. All rights reserved.
#
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

__author__ = 'Antonio Messina <antonio.s.messina@gmail.com>'
__docformat__ = 'reStructuredText'

from ansible.inventory.host import Host
from ansible.inventory.group import Group


class InventoryDictionary(object):
    """
    An Inventory that takes the host definitions from a dictionary.

      >>> inv = InventoryDictionary({'group1': ['host1', 'host2']})
      >>> sorted(inv.groups.keys())
      ['all', 'group1']
      >>> isinstance(inv.groups['group1'], Group)
      True
      >>> hosts = inv.groups['group1'].get_hosts()
      >>> h1host = [h for h in hosts if h.name == 'host1'][0]
      >>> sorted(h.name for h in hosts)
      ['host1', 'host2']
      >>> sorted([g.name for g in hosts[0].get_groups()])
      ['all', 'group1']
      >>> h1host.get_variables()['inventory_hostname']
      'host1'
      >>> h1host.get_variables()['group_names']
      ['group1']

    It also work with a dictionary of dictionaries, in case you want
    to pass host variables:

      >>> d = {'group1': {'host1': {'key': 'value'}}}
      >>> inv = InventoryDictionary(d)
      >>> sorted(inv.groups.keys())
      ['all', 'group1']
      >>> isinstance(inv.groups['group1'], Group)
      True
      >>> sorted(h.name for h in inv.groups['group1'].get_hosts())
      ['host1']
      >>> list(inv.groups['group1'].get_hosts())[0].get_variables()['key']
      'value'

    """
    def __init__(self, inventory):
        self._raw_inventory = inventory
        self.groups = self._parse()

    @staticmethod
    def _parse_hosts(hosts):
        """
        Parse a list or a dictionary and returns a list of `Host`
        classes.

          >>> hosts = InventoryDictionary._parse_hosts(['host1', 'host2'])
          >>> hosts[0].name
          'host1'

          >>> d = {'host1': {'key': 'value'}}
          >>> hosts = InventoryDictionary._parse_hosts(d)
          >>> h = hosts[0]
          >>> h.name
          'host1'
          >>> h.vars['key']
          'value'
        """
        hostlist = []
        for name in hosts:
            host = Host(name)
            hostlist.append(host)
            try:
                variables = hosts.get(name)
                for key, var in variables.items():
                    host.set_variable(key, var)
            except AttributeError:
                pass
        return hostlist

    def _parse(self):
        allgroups = Group(name='all')
        groups = {'all': allgroups}

        for group, hosts in self._raw_inventory.items():
            new_group = Group(name=group)
            allgroups.add_child_group(new_group)

            groups[group] = new_group

            for host in self._parse_hosts(hosts):
                new_group.add_host(host)

        return groups

    def get_host_variables(self, host):
        hosts = [h for h in self.groups.values()]
        if h.name == host.name:
            return h.get_variables()
        else:
            return {}

if __name__ == "__main__":
    import doctest
    doctest.testmod(name="dict_parser",
                    optionflags=doctest.NORMALIZE_WHITESPACE)
