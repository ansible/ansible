# (c) 2017, Brian Coca
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
'''
DOCUMENTATION:
    cache: yaml
    short_description: YAML formatted files.
    description:
        - This cache uses YAML formatted, per host, files saved to the filesystem.
    version_added: "2.3"
    author: Brian Coca (@bcoca)
'''

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import codecs

import yaml

from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.parsing.yaml.dumper import AnsibleDumper
from ansible.plugins.cache import BaseFileCacheModule


class CacheModule(BaseFileCacheModule):
    """
    A caching module backed by yaml files.
    """

    def _load(self, filepath):
        with codecs.open(filepath, 'r', encoding='utf-8') as f:
            return AnsibleLoader(f).get_single_data()

    def _dump(self, value, filepath):
        with codecs.open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(value, f, Dumper=AnsibleDumper, default_flow_style=False)
