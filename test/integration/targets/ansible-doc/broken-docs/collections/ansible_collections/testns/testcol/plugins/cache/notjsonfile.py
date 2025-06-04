# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
    cache: notjsonfile
        broken:
    short_description: JSON formatted files.
    description:
        - This cache uses JSON formatted, per host, files saved to the filesystem.
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
            section: defaults
            deprecated:
              alternative: none
              why: Test deprecation
              version: '2.0.0'
      _prefix:
        description: User defined prefix to use when creating the JSON files
        env:
          - name: ANSIBLE_CACHE_PLUGIN_PREFIX
            version_added: 1.1.0
        ini:
          - key: fact_caching_prefix
            section: defaults
        deprecated:
          alternative: none
          why: Another test deprecation
          removed_at_date: '2050-01-01'
      _timeout:
        default: 86400
        description: Expiration timeout for the cache plugin data
        env:
          - name: ANSIBLE_CACHE_PLUGIN_TIMEOUT
        ini:
          - key: fact_caching_timeout
            section: defaults
        vars:
          - name: notsjonfile_fact_caching_timeout
            version_added: 1.5.0
            deprecated:
              alternative: do not use a variable
              why: Test deprecation
              version: '3.0.0'
        type: integer
    extends_documentation_fragment:
        - testns.testcol2.plugin
"""

from ansible.plugins.cache import BaseFileCacheModule


class CacheModule(BaseFileCacheModule):
    """
    A caching module backed by json files.
    """
    pass
