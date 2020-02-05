# Copyright (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}

DOCUMENTATION = '''
    inventory: toml
    version_added: "2.8"
    short_description: Uses a specific TOML file as an inventory source.
    description:
        - TOML based inventory format
        - File MUST have a valid '.toml' file extension
    notes:
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

example3: |
    [ungrouped.hosts]
    host1 = {}
    host2 = { ansible_host = "127.0.0.1", ansible_port = 44 }
    host3 = { ansible_host = "127.0.0.1", ansible_port = 45 }

    [g1.hosts]
    host4 = {}

    [g2.hosts]
    host4 = {}
'''

import os

from functools import partial

from ansible.errors import AnsibleFileNotFound, AnsibleParserError
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.common._collections_compat import MutableMapping, MutableSequence
from ansible.module_utils.six import string_types, text_type
from ansible.parsing.yaml.objects import AnsibleSequence, AnsibleUnicode
from ansible.plugins.inventory import BaseFileInventoryPlugin
from ansible.utils.display import Display

try:
    import toml
    HAS_TOML = True
except ImportError:
    HAS_TOML = False

display = Display()

WARNING_MSG = (
    'The TOML inventory format is marked as preview, which means that it is not guaranteed to have a backwards '
    'compatible interface.'
)


if HAS_TOML and hasattr(toml, 'TomlEncoder'):
    class AnsibleTomlEncoder(toml.TomlEncoder):
        def __init__(self, *args, **kwargs):
            super(AnsibleTomlEncoder, self).__init__(*args, **kwargs)
            # Map our custom YAML object types to dump_funcs from ``toml``
            self.dump_funcs.update({
                AnsibleSequence: self.dump_funcs.get(list),
                AnsibleUnicode: self.dump_funcs.get(str),
            })
    toml_dumps = partial(toml.dumps, encoder=AnsibleTomlEncoder())
else:
    def toml_dumps(data):
        return toml.dumps(convert_yaml_objects_to_native(data))


def convert_yaml_objects_to_native(obj):
    """Older versions of the ``toml`` python library, don't have a pluggable
    way to tell the encoder about custom types, so we need to ensure objects
    that we pass are native types.

    Only used on ``toml<0.10.0`` where ``toml.TomlEncoder`` is missing.

    This function recurses an object and ensures we cast any of the types from
    ``ansible.parsing.yaml.objects`` into their native types, effectively cleansing
    the data before we hand it over to ``toml``

    This function doesn't directly check for the types from ``ansible.parsing.yaml.objects``
    but instead checks for the types those objects inherit from, to offer more flexibility.
    """
    if isinstance(obj, dict):
        return dict((k, convert_yaml_objects_to_native(v)) for k, v in obj.items())
    elif isinstance(obj, list):
        return [convert_yaml_objects_to_native(v) for v in obj]
    elif isinstance(obj, text_type):
        return text_type(obj)
    else:
        return obj


class InventoryModule(BaseFileInventoryPlugin):
    NAME = 'toml'

    def _parse_group(self, group, group_data):
        if not isinstance(group_data, (MutableMapping, type(None))):
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
        if not file_name or not isinstance(file_name, string_types):
            raise AnsibleParserError("Invalid filename: '%s'" % to_native(file_name))

        b_file_name = to_bytes(self.loader.path_dwim(file_name))
        if not self.loader.path_exists(b_file_name):
            raise AnsibleFileNotFound("Unable to retrieve file contents", file_name=file_name)

        try:
            (b_data, private) = self.loader._get_file_contents(file_name)
            return toml.loads(to_text(b_data, errors='surrogate_or_strict'))
        except toml.TomlDecodeError as e:
            raise AnsibleParserError(
                'TOML file (%s) is invalid: %s' % (file_name, to_native(e)),
                orig_exc=e
            )
        except (IOError, OSError) as e:
            raise AnsibleParserError(
                "An error occurred while trying to read the file '%s': %s" % (file_name, to_native(e)),
                orig_exc=e
            )
        except Exception as e:
            raise AnsibleParserError(
                "An unexpected error occurred while parsing the file '%s': %s" % (file_name, to_native(e)),
                orig_exc=e
            )

    def parse(self, inventory, loader, path, cache=True):
        ''' parses the inventory file '''
        if not HAS_TOML:
            raise AnsibleParserError(
                'The TOML inventory plugin requires the python "toml" library'
            )

        display.warning(WARNING_MSG)

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
