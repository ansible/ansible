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

import os
import time
import errno
import codecs

try:
    import simplejson as json
except ImportError:
    import json

from ansible import constants as C
from ansible import utils
from ansible.cache.base import BaseCacheModule

class CacheModule(BaseCacheModule):
    """
    A caching module backed by json files.
    """
    def __init__(self, *args, **kwargs):

        self._timeout = float(C.CACHE_PLUGIN_TIMEOUT)
        self._cache = {}
        self._cache_dir = C.CACHE_PLUGIN_CONNECTION # expects a dir path
        if not self._cache_dir:
            utils.exit("error, fact_caching_connection is not set, cannot use fact cache")

        if not os.path.exists(self._cache_dir):
            try:
                os.makedirs(self._cache_dir)
            except (OSError,IOError), e:
                utils.warning("error while trying to create cache dir %s : %s" % (self._cache_dir, str(e)))
                return None

    def get(self, key):

        if key in self._cache:
            return self._cache.get(key)

        if self.has_expired(key):
           raise KeyError

        cachefile = "%s/%s" % (self._cache_dir, key)
        try:
            f = codecs.open(cachefile, 'r', encoding='utf-8')
        except (OSError,IOError), e:
            utils.warning("error while trying to read %s : %s" % (cachefile, str(e)))
        else:
            value = json.load(f)
            self._cache[key] = value
            return value
        finally:
            f.close()

    def set(self, key, value):

        self._cache[key] = value

        cachefile = "%s/%s" % (self._cache_dir, key)
        try:
            f = codecs.open(cachefile, 'w', encoding='utf-8')
        except (OSError,IOError), e:
            utils.warning("error while trying to write to %s : %s" % (cachefile, str(e)))
        else:
            f.write(utils.jsonify(value))
        finally:
            f.close()

    def has_expired(self, key):

        cachefile = "%s/%s" % (self._cache_dir, key)
        try:
            st = os.stat(cachefile)
        except (OSError,IOError), e:
            if e.errno == errno.ENOENT:
                return False
            else:
                utils.warning("error while trying to stat %s : %s" % (cachefile, str(e)))

        if time.time() - st.st_mtime <= self._timeout:
            return False

        if key in self._cache:
            del self._cache[key]
        return True

    def keys(self):
        keys = []
        for k in os.listdir(self._cache_dir):
            if not (k.startswith('.') or self.has_expired(k)):
                keys.append(k)
        return keys

    def contains(self, key):

        if key in self._cache:
            return True

        if self.has_expired(key):
            return False
        try:
            st = os.stat("%s/%s" % (self._cache_dir, key))
            return True
        except (OSError,IOError), e:
            if e.errno == errno.ENOENT:
                return False
            else:
                utils.warning("error while trying to stat %s : %s" % (cachefile, str(e)))

    def delete(self, key):
        del self._cache[key]
        try:
            os.remove("%s/%s" % (self._cache_dir, key))
        except (OSError,IOError), e:
            pass #TODO: only pass on non existing?

    def flush(self):
        self._cache = {}
        for key in self.keys():
            self.delete(key)

    def copy(self):
        ret = dict()
        for key in self.keys():
            ret[key] = self.get(key)
        return ret
