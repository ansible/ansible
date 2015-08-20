# Copyright 2015 Abhijit Menon-Sen <ams@2ndQuadrant.com>
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

import ast
import shlex
import re

from ansible import constants as C
from ansible.errors import *
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible.inventory.expand_hosts import detect_range
from ansible.inventory.expand_hosts import expand_hostname_range
from ansible.utils.unicode import to_unicode

class InventoryParser(object):
    """
    Takes an INI-format inventory file and builds a list of groups and subgroups
    with their associated hosts and variable settings.
    """

    def __init__(self, filename=C.DEFAULT_HOST_LIST):
        self.filename = filename

        # Start with an empty host list and the default 'all' and
        # 'ungrouped' groups.

        self.hosts = {}
        self.patterns = {}
        self.groups = dict(
            all = Group(name='all'),
            ungrouped = Group(name='ungrouped')
        )

        # Read in the hosts, groups, and variables defined in the
        # inventory file.

        with open(filename) as fh:
            self._parse(fh.readlines())

        # Finally, add all top-level groups (including 'ungrouped') as
        # children of 'all'.

        for group in self.groups.values():
            if group.depth == 0 and group.name != 'all':
                self.groups['all'].add_child_group(group)

        # Note: we could discard self.hosts after this point.

    def _raise_error(self, message):
        raise AnsibleError("%s:%d: " % (self.filename, self.lineno) + message)

    def _parse(self, lines):
        '''
        Populates self.groups from the given array of lines. Raises an error on
        any parse failure.
        '''

        self._compile_patterns()

        # We behave as though the first line of the inventory is '[ungrouped]',
        # and begin to look for host definitions. We make a single pass through
        # each line of the inventory, building up self.groups and adding hosts,
        # subgroups, and setting variables as we go.

        pending_declarations = {}
        groupname = 'ungrouped'
        state = 'hosts'

        self.lineno = 0
        for line in lines:
            self.lineno += 1

            line = line.strip()

            # Skip empty lines and comments
            if line == '' or line.startswith(";") or line.startswith("#"):
                continue

            # Is this a [section] header? That tells us what group we're parsing
            # definitions for, and what kind of definitions to expect.

            m = self.patterns['section'].match(line)
            if m:
                (groupname, state) = m.groups()

                state = state or 'hosts'
                if state not in ['hosts', 'children', 'vars']:
                    title = ":".join(m.groups())
                    self._raise_error("Section [%s] has unknown type: %s" % (title, state))

                # If we haven't seen this group before, we add a new Group.
                #
                # Either [groupname] or [groupname:children] is sufficient to
                # declare a group, but [groupname:vars] is allowed only if the
                # group is declared elsewhere (not necessarily earlier). We add
                # the group anyway, but make a note in pending_declarations to
                # check at the end.

                if groupname not in self.groups:
                    self.groups[groupname] = Group(name=groupname)

                    if state == 'vars':
                        pending_declarations[groupname] = dict(line=self.lineno, state=state, name=groupname)

                # When we see a declaration that we've been waiting for, we can
                # delete the note.

                if groupname in pending_declarations and state != 'vars':
                    del pending_declarations[groupname]

                continue

            # It's not a section, so the current state tells us what kind of
            # definition it must be. The individual parsers will raise an
            # error if we feed them something they can't digest.

            # [groupname] contains host definitions that must be added to
            # the current group.
            if state == 'hosts':
                hosts = self._parse_host_definition(line)
                for h in hosts:
                    self.groups[groupname].add_host(h)

            # [groupname:vars] contains variable definitions that must be
            # applied to the current group.
            elif state == 'vars':
                (k, v) = self._parse_variable_definition(line)
                self.groups[groupname].set_variable(k, v)

            # [groupname:children] contains subgroup names that must be
            # added as children of the current group. The subgroup names
            # must themselves be declared as groups, but as before, they
            # may only be declared later.
            elif state == 'children':
                child = self._parse_group_name(line)

                if child not in self.groups:
                    self.groups[child] = Group(name=child)
                    pending_declarations[child] = dict(line=self.lineno, state=state, name=child, parent=groupname)

                self.groups[groupname].add_child_group(self.groups[child])

                # Note: there's no reason why we couldn't accept variable
                # definitions here, and set them on the named child group.

            # This is a fencepost. It can happen only if the state checker
            # accepts a state that isn't handled above.
            else:
                self._raise_error("Entered unhandled state: %s" % (state))

        # Any entries in pending_declarations not removed by a group declaration
        # above mean that there was an unresolved forward reference. We report
        # only the first such error here.

        for g in pending_declarations:
            decl = pending_declarations[g]
            if decl['state'] == 'vars':
                raise AnsibleError("%s:%d: Section [%s:vars] not valid for undefined group: %s" % (self.filename, decl['line'], decl['name'], decl['name']))
            elif decl['state'] == 'children':
                raise AnsibleError("%s:%d: Section [%s:children] includes undefined group: %s" % (self.filename, decl['line'], decl['parent'], decl['name']))

    def _parse_group_name(self, line):
        '''
        Takes a single line and tries to parse it as a group name. Returns the
        group name if successful, or raises an error.
        '''

        m = self.patterns['groupname'].match(line)
        if m:
            return m.group(1)

        self._raise_error("Expected group name, got: %s" % (line))

    def _parse_variable_definition(self, line):
        '''
        Takes a string and tries to parse it as a variable definition. Returns
        the key and value if successful, or raises an error.
        '''

        # TODO: We parse variable assignments as a key (anything to the left of
        # an '='"), an '=', and a value (anything left) and leave the value to
        # _parse_value to sort out. We should be more systematic here about
        # defining what is acceptable, how quotes work, and so on.

        if '=' in line:
            (k, v) = [e.strip() for e in line.split("=", 1)]
            return (k, self._parse_value(v))

        self._raise_error("Expected key=value, got: %s" % (line))

    def _parse_host_definition(self, line):
        '''
        Takes a single line and tries to parse it as a host definition. Returns
        a list of Hosts if successful, or raises an error.
        '''

        # A host definition comprises (1) a non-whitespace hostname or range,
        # optionally followed by (2) a series of key="some value" assignments.
        # We ignore any trailing whitespace and/or comments. For example, here
        # are a series of host definitions in a group:
        #
        # [groupname]
        # alpha
        # beta:2345 user=admin      # we'll tell shlex
        # gamma sudo=True user=root # to ignore comments

        try:
            tokens = shlex.split(line, comments=True)
        except ValueError as e:
            self._raise_error("Error parsing host definition '%s': %s" % (varstring, e))

        (hostnames, port) = self._expand_hostpattern(tokens[0])
        hosts = self._Hosts(hostnames, port)

        # Try to process anything remaining as a series of key=value pairs.

        variables = {}
        for t in tokens[1:]:
            if '=' not in t:
                self._raise_error("Expected key=value host variable assignment, got: %s" % (t))
            (k, v) = t.split('=', 1)
            variables[k] = self._parse_value(v)

        # Apply any variable settings found to every host.

        for h in hosts:
            for k in variables:
                h.set_variable(k, variables[k])
                if k == 'ansible_ssh_host':
                    h.ipv4_address = variables[k]

        return hosts

    def _expand_hostpattern(self, hostpattern):
        '''
        Takes a single host pattern and returns a list of hostnames and an
        optional port number that applies to all of them.
        '''

        # Is a port number specified?
        #
        # This may be a mandatory :NN suffix on any square-bracketed expression
        # (IPv6 address, IPv4 address, host name, host pattern), or an optional
        # :NN suffix on an IPv4 address, host name, or pattern. IPv6 addresses
        # must be in square brackets if a port is specified.

        port = None

        for type in ['bracketed_hostport', 'hostport']:
            m = self.patterns[type].match(hostpattern)
            if m:
                (hostpattern, port) = m.groups()
                continue

        # Now we're left with just the pattern, which results in a list of one
        # or more hostnames, depending on whether it contains any [x:y] ranges.
        #
        # FIXME: We could be more strict here about validation.

        if detect_range(hostpattern):
            hostnames = expand_hostname_range(hostpattern)
        else:
            hostnames = [hostpattern]

        return (hostnames, port)

    def _Hosts(self, hostnames, port):
        '''
        Takes a list of hostnames and a port (which may be None) and returns a
        list of Hosts (without recreating anything in self.hosts).
        '''

        hosts = []

        # Note that we decide whether or not to create a Host based solely on
        # the (non-)existence of its hostname in self.hosts. This means that one
        # cannot add both "foo:22" and "foo:23" to the inventory. This behaviour
        # is preserved for now, but this may be an easy FIXME.

        for hn in hostnames:
            if hn not in self.hosts:
                self.hosts[hn] = Host(name=hn, port=port)
            hosts.append(self.hosts[hn])

        return hosts

    @staticmethod
    def _parse_value(v):
        '''
        Does something with something and returns something. Not for mere
        mortals such as myself to interpret.
        '''
        if "#" not in v:
            try:
                v = ast.literal_eval(v)
            # Using explicit exceptions.
            # Likely a string that literal_eval does not like. We wil then just set it.
            except ValueError:
                # For some reason this was thought to be malformed.
                pass
            except SyntaxError:
                # Is this a hash with an equals at the end?
                pass
        return to_unicode(v, nonstring='passthru', errors='strict')

    def get_host_variables(self, host):
        return {}

    def _compile_patterns(self):
        '''
        Compiles the regular expressions required to parse the inventory and
        stores them in self.patterns.
        '''

        # Section names are square-bracketed expressions at the beginning of a
        # line, comprising (1) a group name optionally followed by (2) a tag
        # that specifies the contents of the section. We ignore any trailing
        # whitespace and/or comments. For example:
        #
        # [groupname]
        # [somegroup:vars]
        # [naughty:children] # only get coal in their stockings

        self.patterns['section'] = re.compile(
            r'''^\[
                    ([^:\]\s]+)             # group name (see groupname below)
                    (?::(\w+))?             # optional : and tag name
                \]
                \s*                         # ignore trailing whitespace
                (?:\#.*)?                   # and/or a comment till the
                $                           # end of the line
            ''', re.X
        )

        # FIXME: What are the real restrictions on group names, or rather, what
        # should they be? At the moment, they must be non-empty sequences of non
        # whitespace characters excluding ':' and ']', but we should define more
        # precise rules in order to support better diagnostics. The same applies
        # to hostnames. It seems sensible for them both to follow DNS rules.

        self.patterns['groupname'] = re.compile(
            r'''^
                ([^:\]\s]+)
                \s*                         # ignore trailing whitespace
                (?:\#.*)?                   # and/or a comment till the
                $                           # end of the line
            ''', re.X
        )

        # The following patterns match the various ways in which a port number
        # may be specified on an IPv6 address, IPv4 address, hostname, or host
        # pattern. All of the above may be enclosed in square brackets with a
        # mandatory :NN suffix; or all but the first may be given without any
        # brackets but with an :NN suffix.

        self.patterns['bracketed_hostport'] = re.compile(
            r'''^
                \[(.+)\]                    # [host identifier]
                :([0-9]+)                   # :port number
                $
            ''', re.X
        )

        self.patterns['hostport'] = re.compile(
            r'''^
                ((?:                        # We want to match:
                    [^:\[\]]                # (a non-range character
                    |                       # ...or...
                    \[[^\]]*\]              # a complete bracketed expression)
                )*)                         # repeated as many times as possible
                :([0-9]+)                   # followed by a port number
                $
            ''', re.X
        )
