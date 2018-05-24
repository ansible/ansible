# (c) 2014, Brian Coca, Josh Drake, et al
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    cache: jsonfile
    short_description: JSON formatted files.
    description:
        - This cache uses JSON formatted, per host, files saved to the filesystem.
    version_added: "1.9"
    author: Ansible Core (@ansible-core)
    options:
      _uri:
        required: True
        description:
          - Path in which the cache plugin will save the JSON files
        type: list
        env:
          - name: ANSIBLE_CACHE_PLUGIN_CONNECTION
        ini:
          - key: fact_caching_connection
            section: defaults
      _prefix:
        description: User defined prefix to use when creating the JSON files
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

try:
    import simplejson as json
except ImportError:
    import json

from ansible.parsing.ajson import AnsibleJSONEncoder, AnsibleJSONDecoder
from ansible.plugins.cache import BaseFileCacheModule


class CacheModule(BaseFileCacheModule):
    """
    A caching module backed by json files.
    """

    def _load(self, filepath):
        # Valid JSON is always UTF-8 encoded.
        with codecs.open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f, cls=AnsibleJSONDecoder)

    def _dump(self, value, filepath):
        with codecs.open(filepath, 'w', encoding='utf-8') as f:
            f.write(json.dumps(value, cls=AnsibleJSONEncoder, sort_keys=True, indent=4))
