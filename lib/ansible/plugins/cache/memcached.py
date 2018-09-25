# (c) 2014, Brian Coca, Josh Drake, et al
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    cache: memcached
    short_description: Use memcached DB for cache
    description:
        - This cache uses JSON formatted, per host records saved in memcached.
    version_added: "1.9"
    requirements:
      - memcache (python lib)
    options:
      _uri:
        description:
          - List of connection information for the memcached DBs
        default: ['127.0.0.1:11211']
        type: list
        env:
          - name: ANSIBLE_CACHE_PLUGIN_CONNECTION
        ini:
          - key: fact_caching_connection
            section: defaults
      _prefix:
        description: User defined prefix to use when creating the DB entries
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

import collections
import os
import time
from multiprocessing import Lock
from itertools import chain

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.plugins.cache import BaseCacheModule

try:
    import memcache
except ImportError:
    raise AnsibleError("python-memcached is required for the memcached fact cache")


class ProxyClientPool(object):
    """
    Memcached connection pooling for thread/fork safety. Inspired by py-redis
    connection pool.

    Available connections are maintained in a deque and released in a FIFO manner.
    """

    def __init__(self, *args, **kwargs):
        self.max_connections = kwargs.pop('max_connections', 1024)
        self.connection_args = args
        self.connection_kwargs = kwargs
        self.reset()

    def reset(self):
        self.pid = os.getpid()
        self._num_connections = 0
        self._available_connections = collections.deque(maxlen=self.max_connections)
        self._locked_connections = set()
        self._lock = Lock()

    def _check_safe(self):
        if self.pid != os.getpid():
            with self._lock:
                if self.pid == os.getpid():
                    # bail out - another thread already acquired the lock
                    return
                self.disconnect_all()
                self.reset()

    def get_connection(self):
        self._check_safe()
        try:
            connection = self._available_connections.popleft()
        except IndexError:
            connection = self.create_connection()
        self._locked_connections.add(connection)
        return connection

    def create_connection(self):
        if self._num_connections >= self.max_connections:
            raise RuntimeError("Too many memcached connections")
        self._num_connections += 1
        return memcache.Client(*self.connection_args, **self.connection_kwargs)

    def release_connection(self, connection):
        self._check_safe()
        self._locked_connections.remove(connection)
        self._available_connections.append(connection)

    def disconnect_all(self):
        for conn in chain(self._available_connections, self._locked_connections):
            conn.disconnect_all()

    def __getattr__(self, name):
        def wrapped(*args, **kwargs):
            return self._proxy_client(name, *args, **kwargs)
        return wrapped

    def _proxy_client(self, name, *args, **kwargs):
        conn = self.get_connection()

        try:
            return getattr(conn, name)(*args, **kwargs)
        finally:
            self.release_connection(conn)


class CacheModuleKeys(collections.MutableSet):
    """
    A set subclass that keeps track of insertion time and persists
    the set in memcached.
    """
    PREFIX = 'ansible_cache_keys'

    def __init__(self, cache, *args, **kwargs):
        self._cache = cache
        self._keyset = dict(*args, **kwargs)

    def __contains__(self, key):
        return key in self._keyset

    def __iter__(self):
        return iter(self._keyset)

    def __len__(self):
        return len(self._keyset)

    def add(self, key):
        self._keyset[key] = time.time()
        self._cache.set(self.PREFIX, self._keyset)

    def discard(self, key):
        del self._keyset[key]
        self._cache.set(self.PREFIX, self._keyset)

    def remove_by_timerange(self, s_min, s_max):
        for k in self._keyset.keys():
            t = self._keyset[k]
            if s_min < t < s_max:
                del self._keyset[k]
        self._cache.set(self.PREFIX, self._keyset)


class CacheModule(BaseCacheModule):

    def __init__(self, *args, **kwargs):
        if C.CACHE_PLUGIN_CONNECTION:
            connection = C.CACHE_PLUGIN_CONNECTION.split(',')
        else:
            connection = ['127.0.0.1:11211']

        self._timeout = C.CACHE_PLUGIN_TIMEOUT
        self._prefix = C.CACHE_PLUGIN_PREFIX
        self._cache = {}
        self._db = ProxyClientPool(connection, debug=0)
        self._keys = CacheModuleKeys(self._db, self._db.get(CacheModuleKeys.PREFIX) or [])

    def _make_key(self, key):
        return "{0}{1}".format(self._prefix, key)

    def _expire_keys(self):
        if self._timeout > 0:
            expiry_age = time.time() - self._timeout
            self._keys.remove_by_timerange(0, expiry_age)

    def get(self, key):
        if key not in self._cache:
            value = self._db.get(self._make_key(key))
            # guard against the key not being removed from the keyset;
            # this could happen in cases where the timeout value is changed
            # between invocations
            if value is None:
                self.delete(key)
                raise KeyError
            self._cache[key] = value

        return self._cache.get(key)

    def set(self, key, value):
        self._db.set(self._make_key(key), value, time=self._timeout, min_compress_len=1)
        self._cache[key] = value
        self._keys.add(key)

    def keys(self):
        self._expire_keys()
        return list(iter(self._keys))

    def contains(self, key):
        self._expire_keys()
        return key in self._keys

    def delete(self, key):
        del self._cache[key]
        self._db.delete(self._make_key(key))
        self._keys.discard(key)

    def flush(self):
        for key in self.keys():
            self.delete(key)

    def copy(self):
        return self._keys.copy()

    def __getstate__(self):
        return dict()

    def __setstate__(self, data):
        self.__init__()
