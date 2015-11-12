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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import time
import errno
import codecs

try:
    import simplejson as json
except ImportError:
    import json

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.parsing.utils.jsonify import jsonify
from ansible.plugins.cache.base import BaseCacheModule
from ansible.utils.unicode import to_bytes

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class CacheModule(BaseCacheModule):
    """
    A caching module backed by json files.
    """
    def __init__(self, *args, **kwargs):

        self._timeout = float(C.CACHE_PLUGIN_TIMEOUT)
        self._cache = {}
        self._cache_dir = os.path.expandvars(os.path.expanduser(C.CACHE_PLUGIN_CONNECTION)) # expects a dir path
        if not self._cache_dir:
            raise AnsibleError("error, fact_caching_connection is not set, cannot use fact cache")

        if not os.path.exists(self._cache_dir):
            try:
                os.makedirs(self._cache_dir)
            except (OSError,IOError) as e:
                display.warning("error while trying to create cache dir %s : %s" % (self._cache_dir, to_bytes(e)))
                return None

    def get(self, key):

        if self.has_expired(key) or key == "":
            raise KeyError

        if key in self._cache:
            return self._cache.get(key)

        cachefile = "%s/%s" % (self._cache_dir, key)
        try:
            with codecs.open(cachefile, 'r', encoding='utf-8') as f:
                try:
                    value = json.load(f)
                    self._cache[key] = value
                    return value
                except ValueError as e:
                    display.warning("error while trying to read %s : %s. Most likely a corrupt file, so erasing and failing." % (cachefile, to_bytes(e)))
                    self.delete(key)
                    raise AnsibleError("The JSON cache file %s was corrupt, or did not otherwise contain valid JSON data."
                            " It has been removed, so you can re-run your command now." % cachefile)
        except (OSError,IOError) as e:
            display.warning("error while trying to read %s : %s" % (cachefile, to_bytes(e)))
            raise KeyError

    def set(self, key, value):

        self._cache[key] = value

        cachefile = "%s/%s" % (self._cache_dir, key)
        try:
            f = codecs.open(cachefile, 'w', encoding='utf-8')
        except (OSError,IOError) as e:
            display.warning("error while trying to write to %s : %s" % (cachefile, to_bytes(e)))
            pass
        else:
            f.write(jsonify(value))
        finally:
            f.close()

    def has_expired(self, key):

        cachefile = "%s/%s" % (self._cache_dir, key)
        try:
            st = os.stat(cachefile)
        except (OSError,IOError) as e:
            if e.errno == errno.ENOENT:
                return False
            else:
                display.warning("error while trying to stat %s : %s" % (cachefile, to_bytes(e)))
                pass

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
        cachefile = "%s/%s" % (self._cache_dir, key)

        if key in self._cache:
            return True

        if self.has_expired(key):
            return False
        try:
            os.stat(cachefile)
            return True
        except (OSError,IOError) as e:
            if e.errno == errno.ENOENT:
                return False
            else:
                display.warning("error while trying to stat %s : %s" % (cachefile, to_bytes(e)))
                pass

    def delete(self, key):
        try:
            del self._cache[key]
        except KeyError:
            pass
        try:
            os.remove("%s/%s" % (self._cache_dir, key))
        except (OSError, IOError):
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
