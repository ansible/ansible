# (c) 2014, Michael DeHaan <michael.dehaan@gmail.com>
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
from __future__ import absolute_import

import collections
import pickle
import sys
import time

from ansible import constants as C
from ansible.cache.base import BaseCacheModule

try:
    from redis import StrictRedis
except ImportError:
    print "The 'redis' Python module is required for the redis fact cache"
    sys.exit(1)


class PickledRedis(StrictRedis):
    """
    A subclass of StricRedis that uses the pickle module to store and load
    representations of the provided values.
    """
    def get(self, name):
        pickled_value = super(PickledRedis, self).get(name)
        if pickled_value is None:
            return None
        return pickle.loads(pickled_value)

    def set(self, name, value, *args, **kwargs):
        return super(PickledRedis, self).set(name, pickle.dumps(value), *args, **kwargs)

    def setex(self, name, time, value):
        return super(PickledRedis, self).setex(name, time, pickle.dumps(value))


class CacheModule(BaseCacheModule):
    """
    A caching module backed by redis.

    Keys are maintained in a zset with their score being the timestamp
    when they are inserted. This allows for the usage of 'zremrangebyscore'
    to expire keys. This mechanism is used or a pattern matched 'scan' for
    performance.
    """
    def __init__(self, *args, **kwargs):
        if C.CACHE_PLUGIN_CONNECTION:
            connection = C.CACHE_PLUGIN_CONNECTION.split(':')
        else:
            connection = []

        self._timeout = C.CACHE_PLUGIN_TIMEOUT
        self._prefix = C.CACHE_PLUGIN_PREFIX
        self._cache = PickledRedis(*connection)
        self._keys_set = 'ansible_cache_keys'

    def _make_key(self, key):
        return "{}{}".format(self._prefix, key)

    def get(self, key):
        value = self._cache.get(self._make_key(key))
        # guard against the key not being removed from the zset;
        # this could happen in cases where the timeout value is changed
        # between invocations
        if value is None:
            self.delete(key)
            raise KeyError
        return value

    def set(self, key, value):
        if self._timeout > 0: # a timeout of 0 is handled as meaning 'never expire'
            self._cache.setex(self._make_key(key), self._timeout, value)
        else:
            self._cache.set(self._make_key(key), value)

        self._cache.zadd(self._keys_set, time.time(), key)

    def _expire_keys(self):
        if self._timeout > 0:
            expiry_age = time.time() - self._timeout
        self._cache.zremrangebyscore(self._keys_set, 0, expiry_age)

    def keys(self):
        self._expire_keys()
        return self._cache.zrange(self._keys_set, 0, -1)

    def contains(self, key):
        self._expire_keys()
        return (self._cache.zrank(self._keys_set, key) >= 0)

    def delete(self, key):
        self._cache.delete(self._make_key(key))
        self._cache.zrem(self._keys_set, key)

    def flush(self):
        for key in self.keys():
            self.delete(key)
