# Copyright (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
    name: toml
    version_added: "2.8"
    short_description: Uses a specific TOML file as an inventory source.
    description:
        - TOML based inventory format
        - File MUST have a valid '.toml' file extension
"""

EXAMPLES = r"""# fmt: toml
# Example 1
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

# Example 2
[all.vars]
has_java = false

[web]
children = [
    "apache",
    "nginx"
]

[web.vars]
http_port = 8080
myvar = 23

[web.hosts.host1]
[web.hosts.host2]
ansible_port = 222

[apache.hosts.tomcat1]

[apache.hosts.tomcat2]
myvar = 34

[apache.hosts.tomcat3]
mysecret = "03#pa33w0rd"

[nginx.hosts.jenkins1]

[nginx.vars]
has_java = true

# Example 3
[ungrouped.hosts]
host1 = {}
host2 = { ansible_host = "127.0.0.1", ansible_port = 44 }
host3 = { ansible_host = "127.0.0.1", ansible_port = 45 }

[g1.hosts]
host4 = {}

[g2.hosts]
host4 = {}
"""

import os
import tomllib

from collections.abc import MutableMapping, MutableSequence

from ansible.errors import AnsibleFileNotFound, AnsibleParserError
from ansible.plugins.inventory import BaseFileInventoryPlugin
from ansible.utils.display import Display

display = Display()


class InventoryModule(BaseFileInventoryPlugin):
    NAME = 'toml'

    trusted_by_default = True  # we need the inventory system to mark trust for us, since we're not manually traversing var assignments

    def _parse_group(self, group, group_data):
        if group_data is not None and not isinstance(group_data, MutableMapping):
            self.display.warning("Skipping '%s' as this is not a valid group definition" % group)
            return

        group = self.inventory.add_group(group)
        if group_data is None:
            return

        for key, data in group_data.items():
            if key == 'vars':
                if not isinstance(data, MutableMapping):
                    raise AnsibleParserError(
                        'Invalid "vars" entry for "%s" group, requires a dict, found "%s" instead.' %
                        (group, type(data))
                    )
                for var, value in data.items():
                    self.inventory.set_variable(group, var, value)

            elif key == 'children':
                if not isinstance(data, MutableSequence):
                    raise AnsibleParserError(
                        'Invalid "children" entry for "%s" group, requires a list, found "%s" instead.' %
                        (group, type(data))
                    )
                for subgroup in data:
                    self._parse_group(subgroup, {})
                    self.inventory.add_child(group, subgroup)

            elif key == 'hosts':
                if not isinstance(data, MutableMapping):
                    raise AnsibleParserError(
                        'Invalid "hosts" entry for "%s" group, requires a dict, found "%s" instead.' %
                        (group, type(data))
                    )
                for host_pattern, value in data.items():
                    hosts, port = self._expand_hostpattern(host_pattern)
                    self._populate_host_vars(hosts, value, group, port)
            else:
                self.display.warning(
                    'Skipping unexpected key "%s" in group "%s", only "vars", "children" and "hosts" are valid' %
                    (key, group)
                )

    def _load_file(self, file_name):
        if not file_name or not isinstance(file_name, str):
            raise AnsibleParserError("Invalid filename: '%s'" % file_name)

        if not self.loader.path_exists(file_name):
            raise AnsibleFileNotFound("Unable to retrieve file contents", file_name=file_name)

        try:
            return tomllib.loads(self.loader.get_text_file_contents(file_name))
        except tomllib.TOMLDecodeError as ex:
            raise AnsibleParserError(f'TOML file {file_name!r} is invalid.') from ex
        except Exception as ex:
            raise AnsibleParserError(f'An error occurred while parsing the file {file_name!r}.') from ex

    def parse(self, inventory, loader, path, cache=True):
        """ parses the inventory file """
        super(InventoryModule, self).parse(inventory, loader, path)
        self.set_options()

        try:
            data = self._load_file(path)
        except Exception as e:
            raise AnsibleParserError(e)

        if not data:
            raise AnsibleParserError('Parsed empty TOML file')
        elif data.get('plugin'):
            raise AnsibleParserError('Plugin configuration TOML file, not TOML inventory')

        for group_name in data:
            self._parse_group(group_name, data[group_name])

    def verify_file(self, path):
        if super(InventoryModule, self).verify_file(path):
            file_name, ext = os.path.splitext(path)
            if ext == '.toml':
                return True
        return False
