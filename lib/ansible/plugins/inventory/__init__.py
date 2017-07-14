# (c) 2017,  Red Hat, inc
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
__metaclass__ = type

import os
import hashlib
import string

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes
from ansible.template import Templar

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class BaseInventoryPlugin(object):
    """ Parses an Inventory Source"""

    TYPE = 'generator'

    def __init__(self, cache=None):

        self.inventory = None
        self.display = display
        self.cache = cache

    def parse(self, inventory, loader, path, cache=True):
        ''' Populates self.groups from the given data. Raises an error on any parse failure.  '''

        self.loader = loader
        self.inventory = inventory

    def verify_file(self, path):
        ''' Verify if file is usable by this plugin, base does minimal accessability check '''

        b_path = to_bytes(path)
        return (os.path.exists(b_path) and os.access(b_path, os.R_OK))

    def get_cache_prefix(self, path):
        ''' create predictable unique prefix for plugin/inventory '''

        m = hashlib.sha1()
        m.update(to_bytes(self.NAME))
        d1 = m.hexdigest()

        n = hashlib.sha1()
        n.update(to_bytes(path))
        d2 = n.hexdigest()

        return 's_'.join([d1[:5], d2[:5]])

    def clear_cache(self):
        pass

    def populate_host_vars(self, hosts, variables, group=None, port=None):
        for host in hosts:
            self.inventory.add_host(host, group=group, port=port)
            for k in variables:
                self.inventory.set_variable(host, k, variables[k])

    def _compose(self, template, variables):
        ''' helper method for pluigns to compose variables for Ansible based on jinja2 expression and inventory vars'''
        t = Templar(loader=self.loader, variables=variables)
        return t.do_template('%s%s%s' % (t.environment.variable_start_string, template, t.environment.variable_end_string), disable_lookups=True)


class BaseFileInventoryPlugin(BaseInventoryPlugin):
    """ Parses a File based Inventory Source"""

    TYPE = 'storage'

    def __init__(self, cache=None):

        # file based inventories are always local so no need for cache
        super(BaseFileInventoryPlugin, self).__init__(cache=None)


# Helper methods
def detect_range(line=None):
    '''
    A helper function that checks a given host line to see if it contains
    a range pattern described in the docstring above.

    Returns True if the given line contains a pattern, else False.
    '''
    return '[' in line


def expand_hostname_range(line=None):
    '''
    A helper function that expands a given line that contains a pattern
    specified in top docstring, and returns a list that consists of the
    expanded version.

    The '[' and ']' characters are used to maintain the pseudo-code
    appearance. They are replaced in this function with '|' to ease
    string splitting.

    References: http://ansible.github.com/patterns.html#hosts-and-groups
    '''
    all_hosts = []
    if line:
        # A hostname such as db[1:6]-node is considered to consists
        # three parts:
        # head: 'db'
        # nrange: [1:6]; range() is a built-in. Can't use the name
        # tail: '-node'

        # Add support for multiple ranges in a host so:
        # db[01:10:3]node-[01:10]
        # - to do this we split off at the first [...] set, getting the list
        #   of hosts and then repeat until none left.
        # - also add an optional third parameter which contains the step. (Default: 1)
        #   so range can be [01:10:2] -> 01 03 05 07 09

        (head, nrange, tail) = line.replace('[', '|', 1).replace(']', '|', 1).split('|')
        bounds = nrange.split(":")
        if len(bounds) != 2 and len(bounds) != 3:
            raise AnsibleError("host range must be begin:end or begin:end:step")
        beg = bounds[0]
        end = bounds[1]
        if len(bounds) == 2:
            step = 1
        else:
            step = bounds[2]
        if not beg:
            beg = "0"
        if not end:
            raise AnsibleError("host range must specify end value")
        if beg[0] == '0' and len(beg) > 1:
            rlen = len(beg)  # range length formatting hint
            if rlen != len(end):
                raise AnsibleError("host range must specify equal-length begin and end formats")

            def fill(x):
                return str(x).zfill(rlen)  # range sequence

        else:
            fill = str

        try:
            i_beg = string.ascii_letters.index(beg)
            i_end = string.ascii_letters.index(end)
            if i_beg > i_end:
                raise AnsibleError("host range must have begin <= end")
            seq = list(string.ascii_letters[i_beg:i_end + 1:int(step)])
        except ValueError:  # not an alpha range
            seq = range(int(beg), int(end) + 1, int(step))

        for rseq in seq:
            hname = ''.join((head, fill(rseq), tail))

            if detect_range(hname):
                all_hosts.extend(expand_hostname_range(hname))
            else:
                all_hosts.append(hname)

        return all_hosts
