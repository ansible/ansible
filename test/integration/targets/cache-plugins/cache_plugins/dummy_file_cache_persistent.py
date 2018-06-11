from __future__ import annotations

DOCUMENTATION = """
    name: dummy_file_cache
    short_description: dummy file cache
    description: see short
    options:
        _uri:
          required: True
          description:
            - Path in which the cache plugin will save the files
          env:
            - name: ANSIBLE_CACHE_PLUGIN_CONNECTION
          ini:
            - key: fact_caching_connection
              section: defaults
          type: path
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
"""

import os
import pathlib
import typing as t

from ansible.plugins.cache import BaseFileCacheModule


class CacheModule(BaseFileCacheModule):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def _load(self, thefile: str) -> object:
        with open(thefile, 'r') as jfile:
            return eval(thefile.read())

    def _dump(self, value: object, thefile: str) -> None:
        with open(thefile, 'w') as afile:
            afile.write(str(value))
