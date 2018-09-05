# Copyright (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    inventory: toml
    version_added: "2.7"
    short_description: Uses a specific TOML file as an inventory source.
    description:
        - "TOML based inventory, starts with the 'all' group and has hosts/vars/children entries."
        - Host entries can have sub-entries defined, which will be treated as variables.
        - Vars entries are normal group vars.
        - "Children are 'child groups', which can also have their own vars/hosts/children and so on."
        - File MUST have a valid '.toml' file extension
    notes:
        - To function it requires the 'toml' plugin being whitelisted in configuration.
        - Requires the 'toml' python library
'''

EXAMPLES = '''
example1: |
    [all.vars]
    has_java = false

    [web]
    children = [
        "apache",
        "nginx"
    ]
    vars = { http_port = 8080, myvar = 23 }

    [web.hosts]
    host1 = {}
    host2 = { ansible_port = 222 }

    [apache.hosts]
    tomcat1 = {}
    tomcat2 = { myvar = 34 }
    tomcat3 = { mysecret = "03#pa33w0rd" }

    [nginx.hosts]
    jenkins1 = {}

    [nginx.vars]
    has_java = true

example2: |
    [ungrouped.hosts]
    host1 = {}
    host2 = { ansible_host = 127.0.0.1, ansible_port = 44 }
    host3 = { ansible_host = 127.0.0.1, ansible_port = 45 }

    [g1.hosts]
    host4 = {}

    [g2.hosts]
    host4 = {}
'''

import os

from collections import MutableMapping

from ansible.errors import AnsibleFileNotFound, AnsibleParserError
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_bytes, to_native
from ansible.plugins.inventory import BaseFileInventoryPlugin
from ansible.plugins.inventory.yaml import InventoryModule as YAMLInventoryModule

try:
    import toml
    HAS_TOML = True
except ImportError:
    HAS_TOML = False


class InventoryModule(YAMLInventoryModule):
    NAME = 'toml'

    def __init__(self):
        if not HAS_TOML:
            raise AnsibleParserError('The TOML inventory plugin requires the python "toml" library')

        super(InventoryModule, self).__init__()

    def verify_file(self, path):

        valid = False
        if BaseFileInventoryPlugin.verify_file(self, path):
            file_name, ext = os.path.splitext(path)
            if ext == '.toml':
                valid = True
        return valid

    def _load_file(self, file_name):
        if not file_name or not isinstance(file_name, string_types):
            raise AnsibleParserError("Invalid filename: '%s'" % to_native(file_name))

        b_file_name = to_bytes(self.loader.path_dwim(file_name))
        if not self.loader.path_exists(b_file_name):
            raise AnsibleFileNotFound("Unable to retrieve file contents", file_name=file_name)

        try:
            with open(b_file_name, 'r') as f:
                return toml.load(f)
        except (IOError, OSError) as e:
            raise AnsibleParserError(
                "an error occurred while trying to read the file '%s': %s" % (file_name, to_native(e)),
                orig_exc=e
            )

    def _parse_group(self, group, group_data):

        if isinstance(group_data, (MutableMapping, type(None))):

            self.inventory.add_group(group)

            if group_data is not None:
                # make sure they are dicts
                for section in ('vars', 'children', 'hosts'):
                    if section in group_data:
                        # convert strings to dicts as these are allowed
                        if isinstance(group_data[section], string_types):
                            group_data[section] = {group_data[section]: None}

                        if section in ('vars', 'hosts') and not isinstance(group_data[section], (MutableMapping, type(None))):
                            raise AnsibleParserError('Invalid "%s" entry for "%s" group, requires a dictionary, found "%s" instead.' %
                                                     (section, group, type(group_data[section])))
                        elif section in ('children',) and not isinstance(group_data[section], list):
                            raise AnsibleParserError('Invalid "%s" entry for "%s" group, requires a list, found "%s" instead.' %
                                                     (section, group, type(group_data[section])))

                for key in group_data:
                    if key == 'vars':
                        for var in group_data['vars']:
                            self.inventory.set_variable(group, var, group_data['vars'][var])

                    elif key == 'children':
                        for subgroup in group_data['children']:
                            self._parse_group(subgroup, {})
                            self.inventory.add_child(group, subgroup)

                    elif key == 'hosts':
                        for host_pattern in group_data['hosts']:
                            hosts, port = self._parse_host(host_pattern)
                            self._populate_host_vars(hosts, group_data['hosts'][host_pattern] or {}, group, port)
                    else:
                        self.display.warning('Skipping unexpected key (%s) in group (%s), only "vars", "children" and "hosts" are valid' % (key, group))
                        pass

        else:
            self.display.warning("Skipping '%s' as this is not a valid group definition" % group)
