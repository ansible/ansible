# (c) 2014, Brian Coca, Josh Drake, et al
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
# FIXME: can we store these as something else before we ship it?
import sys
import time

try:
    import simplejson as json
except ImportError:
    import json

from ansible import constants as C
from ansible.utils import jsonify
from ansible.cache.base import BaseCacheModule

try:
    from redis import StrictRedis
except ImportError:
    print "The 'redis' python module is required, 'pip install redis'"
    sys.exit(1)

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

        self._timeout = float(C.CACHE_PLUGIN_TIMEOUT)
        self._prefix = C.CACHE_PLUGIN_PREFIX
        self._cache = StrictRedis(*connection)
        self._keys_set = 'ansible_cache_keys'

    def _make_key(self, key):
        return self._prefix + key

    def get(self, key):
        value = self._cache.get(self._make_key(key))
        # guard against the key not being removed from the zset;
        # this could happen in cases where the timeout value is changed
        # between invocations
        if value is None:
            self.delete(key)
            raise KeyError
        return json.loads(value)

    def set(self, key, value):
        value2 = jsonify(value)
        if self._timeout > 0: # a timeout of 0 is handled as meaning 'never expire'
            self._cache.setex(self._make_key(key), int(self._timeout), value2)
        else:
            self._cache.set(self._make_key(key), value2)

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

    def copy(self):
        # FIXME: there is probably a better way to do this in redis
        ret = dict()
        for key in self.keys():
            ret[key] = self.get(key)
        return ret
