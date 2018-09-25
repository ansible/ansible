# (c) 2017, Brian Coca
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    cache: yaml
    short_description: YAML formatted files.
    description:
        - This cache uses YAML formatted, per host, files saved to the filesystem.
    version_added: "2.3"
    author: Brian Coca (@bcoca)
    options:
      _uri:
        required: True
        description:
          - Path in which the cache plugin will save the files
        type: list
        env:
          - name: ANSIBLE_CACHE_PLUGIN_CONNECTION
        ini:
          - key: fact_caching_connection
            section: defaults
      _prefix:
        description: User defined prefix to use when creating the files
        env:
          - name: ANSIBLE_CACHE_PLUGIN_PREFIX
        ini:
          - key: fact_caching_prefix
            section: defaults
      _timeout:
        default: 86400
        description: Expiration timeout for the cache plugin data
        env:
          - name: ANSIBLE_CACHE_PLUGIN_TIMEOUT
        ini:
          - key: fact_caching_timeout
            section: defaults
        type: integer
'''


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
