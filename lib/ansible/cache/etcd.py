# (c) 2014, Michael Scherer
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
import json

from ansible import constants as C
from ansible.cache.base import BaseCacheModule

try:
    from etcd.client import Client
except ImportError:
    import sys
    print "The 'etcd' python module is required, 'pip install etcd'"
    sys.exit(1)


class CacheModule(BaseCacheModule):
    """
    A caching module backed by etcd.
    """
    def __init__(self, *args, **kwargs):
        self._timeout = int(C.CACHE_PLUGIN_TIMEOUT)
        if C.CACHE_PLUGIN_CONNECTION:
                self._cache = Client(C.CACHE_PLUGIN_CONNECTION)
        else:
                self._cache = Client()
        self._prefix = C.CACHE_PLUGIN_PREFIX 

    def _make_key(self, key):
        return '/%s/%s' % (self._prefix, key)

    def get(self, key):
        r = self._cache.node.get(self._make_key(key))
        return json.loads(r.node.value)

    def set(self, key, value):
        self._cache.node.set(self._make_key(key), json.dumps(value),
                             ttl=self._timeout)

    def keys(self):
        try:
            return [i.key.split('/')[-1] for i in
                    self._cache.node.get('/ansible/facts/').node.children]
        except KeyError:
            return []

    # FIXME use a better way than exception, maybe be too slow
    def contains(self, key):
        try:
            self._cache.node.get(self._make_key(key))
        except KeyError:
            return False
        return True

    def delete(self, key):
        self._cache.node.delete(self._make_key(key), value)

    def flush(self):
        for key in self.keys():
            self.delete(key)

    def copy(self):
        ret = dict()
        for key in self.keys():
            ret[key] = self.get(key)
        return ret
