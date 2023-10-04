# (c) 2014, Brian Coca, Josh Drake, et al
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = '''
    cache: configurable_redis
    short_description: Use Redis DB for cache
    description:
        - This cache uses JSON formatted, per host records saved in Redis.
    version_added: "1.9"
    requirements:
      - redis>=2.4.5 (python lib)
    options:
      _uri:
        description:
          - A colon separated string of connection information for Redis.
        required: True
        env:
          - name: ANSIBLE_CACHE_PLUGIN_CONNECTION
        ini:
          - key: fact_caching_connection
            section: defaults
      _prefix:
        description: User defined prefix to use when creating the DB entries
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

from ansible.errors import AnsibleError
from ansible.parsing.ajson import AnsibleJSONEncoder, AnsibleJSONDecoder
from ansible.plugins.cache import BaseCacheModule
from ansible.utils.display import Display

try:
    from redis import StrictRedis, VERSION
except ImportError:
    raise AnsibleError("The 'redis' python module (version 2.4.5 or newer) is required for the redis fact cache, 'pip install redis'")

display = Display()


class CacheModule(BaseCacheModule):
    """
    A caching module backed by redis.
    Keys are maintained in a zset with their score being the timestamp
    when they are inserted. This allows for the usage of 'zremrangebyscore'
    to expire keys. This mechanism is used or a pattern matched 'scan' for
    performance.
    """
    def __init__(self, *args, **kwargs):
        connection = []

        super(CacheModule, self).__init__(*args, **kwargs)
        if self.get_option('_uri'):
            connection = self.get_option('_uri').split(':')
        self._timeout = float(self.get_option('_timeout'))
        self._prefix = self.get_option('_prefix')

        self._cache = {}
        self._db = StrictRedis(*connection)
        self._keys_set = 'ansible_cache_keys'

    def _make_key(self, key):
        return self._prefix + key

    def get(self, key):

        if key not in self._cache:
            value = self._db.get(self._make_key(key))
            # guard against the key not being removed from the zset;
            # this could happen in cases where the timeout value is changed
            # between invocations
            if value is None:
                self.delete(key)
                raise KeyError
            self._cache[key] = json.loads(value, cls=AnsibleJSONDecoder)

        return self._cache.get(key)

    def set(self, key, value):

        value2 = json.dumps(value, cls=AnsibleJSONEncoder, sort_keys=True, indent=4)
        if self._timeout > 0:  # a timeout of 0 is handled as meaning 'never expire'
            self._db.setex(self._make_key(key), int(self._timeout), value2)
        else:
            self._db.set(self._make_key(key), value2)

        if VERSION[0] == 2:
            self._db.zadd(self._keys_set, time.time(), key)
        else:
            self._db.zadd(self._keys_set, {key: time.time()})
        self._cache[key] = value

    def _expire_keys(self):
        if self._timeout > 0:
            expiry_age = time.time() - self._timeout
            self._db.zremrangebyscore(self._keys_set, 0, expiry_age)

    def keys(self):
        self._expire_keys()
        return self._db.zrange(self._keys_set, 0, -1)

    def contains(self, key):
        self._expire_keys()
        return (self._db.zrank(self._keys_set, key) is not None)

    def delete(self, key):
        if key in self._cache:
            del self._cache[key]
        self._db.delete(self._make_key(key))
        self._db.zrem(self._keys_set, key)

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
