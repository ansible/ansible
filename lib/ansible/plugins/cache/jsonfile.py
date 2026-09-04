# (c) 2014, Brian Coca, Josh Drake, et al
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
    name: jsonfile
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
        env:
          - name: ANSIBLE_CACHE_PLUGIN_CONNECTION
        ini:
          - key: fact_caching_connection
            section: defaults
        type: path
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
      persistent:
        version_added: "2.22"
        description: Set to False to use the cache filename and lossy format used prior to ansible-core 2.19.
        default: True
        type: bool
        env:
          - name: ANSIBLE_CACHE_JSONFILE_PERSISTENT
        ini:
          - key: fact_caching_jsonfile_persistent
            section: defaults
"""

import json
import pathlib

from ansible.plugins.cache import BaseFileCacheModule


class CacheModule(BaseFileCacheModule):
    """A caching module backed by json files."""

    @property
    def _persistent(self):
        # evaluate on request, since the plugin loader initializes defs before checking _persistent
        return self.get_option("persistent")

    def _load(self, filepath: str) -> object:
        return json.loads(pathlib.Path(filepath).read_text())

    def _dump(self, value: object, filepath: str) -> None:
        pathlib.Path(filepath).write_text(json.dumps(value))
