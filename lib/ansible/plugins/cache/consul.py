# (c) 2019, Christophe FERREIRA
# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    cache: Consul
    short_description: Use Consul kv for cache
    description:
        - This cache uses JSON formatted, per host records saved in Consul.
    version_added: "2.8"
    requirements:
      - python-consul
    options:
      _uri:
        description:
          - A colon separated string of connection information for Consul host:port:token.
        required: True
        env:
          - name: ANSIBLE_CACHE_PLUGIN_CONNECTION
        ini:
          - key: fact_caching_connection
            section: defaults
      _prefix:
        description: User defined prefix to use when creating the kv entries
        default: ansible_facts
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

import time
import json

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.parsing.ajson import AnsibleJSONEncoder, AnsibleJSONDecoder
from ansible.plugins.cache import BaseCacheModule
from ansible.utils.display import Display

try:
    import consul
except ImportError:
    raise AnsibleError("The 'consul' python module is required for the consul fact cache, 'pip install python-consul'")

display = Display()


class CacheModule(BaseCacheModule):
    """
    A caching module backed by consul kv.

    """
    def __init__(self, *args, **kwargs):
        connection = []

        try:
            super(CacheModule, self).__init__(*args, **kwargs)
            if self.get_option('_uri'):
                connection_host = self.get_option('_uri').split(':')[0]
                connection_port = self.get_option('_uri').split(':')[1]
                connection_token = self.get_option('_uri').split(':')[2]
            self._timeout = float(self.get_option('_timeout'))
            self._prefix = self.get_option('_prefix')
        except KeyError:
            display.deprecated('Rather than importing CacheModules directly, '
                               'use ansible.plugins.loader.cache_loader', version='2.12')
            if C.CACHE_PLUGIN_CONNECTION:
                connection_host = C.CACHE_PLUGIN_CONNECTION.split(':')[0]
                connection_port = C.CACHE_PLUGIN_CONNECTION.split(':')[1]
                connection_token = C.CACHE_PLUGIN_CONNECTION.split(':')[2]
            self._timeout = float(C.CACHE_PLUGIN_TIMEOUT)
            self._prefix = C.CACHE_PLUGIN_PREFIX

        self._cache = {}
        self._db = consul.Consul(host=connection_host,
                         port=connection_port,
                         token=connection_token)
        self._keys_set = 'ansible_cache_keys'

    def _make_key(self, key):
        return self._prefix + key

    def _expire_keys(self):
        if self._timeout > 0:
            expiry_age = time.time() - self._timeout
            self._keys.remove_by_timerange(0, expiry_age)

    def keys(self):
        self._expire_keys()
        return list(iter(self._keys))

    def get(self, key):

        if key not in self._cache:
            value = self._db.kv.get(self._make_key(key))
            if value is None:
                self.delete(key)
                raise KeyError
            self._cache[key] = json.loads(value, cls=AnsibleJSONDecoder)
        return self._cache.get(key)

    def set(self, key, value):

        value2 = json.dumps(value, cls=AnsibleJSONEncoder, sort_keys=True, indent=4)
        self._db.kv.put(self._make_key(key), value2)
        self._cache[key] = value

    def delete(self, key):
        del self._cache[key]
        self._db.kv.delete(self._make_key(key))
        self._keys.discard(key)

    def flush(self):
        for key in self.keys():
            self.delete(key)

    def copy(self):
        # TODO: there is probably a better way to do this in redis
        ret = dict()
        for key in self.keys():
            ret[key] = self.get(key)
        return ret

    def __getstate__(self):
        return dict()

    def __setstate__(self, data):
        self.__init__()
