# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = '''
    cache: notjsonfile
    short_description: NotJSON cache plugin
    description: This cache uses is NOT JSON
    author: Ansible Core (@ansible-core)
    version_added: 0.7.0
    options:
      _uri:
        required: True
        description:
          - Path in which the cache plugin will save the JSON files
        env:
          - name: ANSIBLE_CACHE_PLUGIN_CONNECTION
            version_added: 1.2.0
        ini:
          - key: fact_caching_connection
            section: notjsonfile_cache
          - key: fact_caching_connection
            section: defaults
      _prefix:
        description: User defined prefix to use when creating the JSON files
        env:
          - name: ANSIBLE_CACHE_PLUGIN_PREFIX
            version_added: 1.1.0
        ini:
          - key: fact_caching_prefix
            section: defaults
          - key: fact_caching_prefix
            section: notjson_cache
            deprecated:
              alternative: section is notjsonfile_cache
              why: Another test deprecation
              removed_at_date: '2050-01-01'
          - key: fact_caching_prefix
            section: notjsonfile_cache
      _timeout:
        default: 86400
        description: Expiration timeout for the cache plugin data
        env:
          - name: ANSIBLE_CACHE_PLUGIN_TIMEOUT
          - name: ANSIBLE_NOTJSON_CACHE_PLUGIN_TIMEOUT
            deprecated:
              alternative: do not use a variable
              why: Test deprecation
              version: '3.0.0'
        ini:
          - key: fact_caching_timeout
            section: defaults
          - key: fact_caching_timeout
            section: notjsonfile_cache
        vars:
          - name: notsjonfile_fact_caching_timeout
            version_added: 1.5.0
        type: integer
      removeme:
        default: 86400
        description: Expiration timeout for the cache plugin data
        deprecated:
            alternative: cause i need to test it
            why: Test deprecation
            version: '2.0.0'
        env:
          - name: ANSIBLE_NOTJSON_CACHE_PLUGIN_REMOVEME
'''

from ansible.plugins.cache import BaseFileCacheModule


class CacheModule(BaseFileCacheModule):
    """
    A caching module backed by json files.
    """
    def _dump(self):
        pass

    def _load(self):
        pass
