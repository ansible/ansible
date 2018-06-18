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
    group_var1 = "value2"

    [all.hosts.test1]

    [all.hosts.test2]
    var1 = "value1"

    [all.children.last_group]
    hosts = "test1"

    [all.children.other_group.vars]
    g2_var2 = "value3"

    [all.children.last_group.vars]
    last_var = "MYVALUE"

    [all.children.other_group.children.group_x]
    hosts = "test5"

    [all.children.other_group.hosts.test4]
    ansible_host = "127.0.0.1"
'''

import os

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
            raise AnsibleParserError("an error occurred while trying to read the file '%s': %s" % (file_name, to_native(e)), orig_exc=e)
