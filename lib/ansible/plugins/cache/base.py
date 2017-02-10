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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import time
import errno
import codecs

from abc import ABCMeta, abstractmethod

from ansible import constants as C
from ansible.compat.six import with_metaclass
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

class BaseCacheModule(with_metaclass(ABCMeta, object)):

    # Backwards compat only.  Just import the global display instead
    _display = display

    @abstractmethod
    def get(self, key):
        pass

    @abstractmethod
    def set(self, key, value):
        pass

    @abstractmethod
    def keys(self):
        pass

    @abstractmethod
    def contains(self, key):
        pass

    @abstractmethod
    def delete(self, key):
        pass

    @abstractmethod
    def flush(self):
        pass

    @abstractmethod
    def copy(self):
        pass


class BaseFileCacheModule(BaseCacheModule):
    """
    A caching module backed by file based storage.
    """
    plugin_name = None
    read_mode = 'r'
    write_mode = 'w'
    encoding = 'utf-8'
    def __init__(self, *args, **kwargs):

        self._timeout = float(C.CACHE_PLUGIN_TIMEOUT)
        self._cache = {}
        self._cache_dir = None

        if C.CACHE_PLUGIN_CONNECTION:
            # expects a dir path
            self._cache_dir = os.path.expanduser(os.path.expandvars(C.CACHE_PLUGIN_CONNECTION))

        if not self._cache_dir:
            raise AnsibleError("error, '%s' cache plugin requires the 'fact_caching_connection' config option to be set (to a writeable directory path)" % self.plugin_name)

        if not os.path.exists(self._cache_dir):
            try:
                os.makedirs(self._cache_dir)
            except (OSError,IOError) as e:
                display.warning("error in '%s' cache plugin while trying to create cache dir %s : %s" % (self.plugin_name, self._cache_dir, to_bytes(e)))
                return None

    def get(self, key):
        """ This checks the in memory cache first as the fact was not expired at 'gather time'
        and it would be problematic if the key did expire after some long running tasks and
        user gets 'undefined' error in the same play """

        if key in self._cache:
            return self._cache.get(key)

        if self.has_expired(key) or key == "":
            raise KeyError

        cachefile = "%s/%s" % (self._cache_dir, key)
        try:
            with codecs.open(cachefile, self.read_mode, encoding=self.encoding) as f:
                try:
                    value = self._load(f)
                    self._cache[key] = value
                    return value
                except ValueError as e:
                    display.warning("error in '%s' cache plugin while trying to read %s : %s. Most likely a corrupt file, so erasing and failing." % (self.plugin_name, cachefile, to_bytes(e)))
                    self.delete(key)
                    raise AnsibleError("The cache file %s was corrupt, or did not otherwise contain valid data. It has been removed, so you can re-run your command now." % cachefile)
        except (OSError,IOError) as e:
            display.warning("error in '%s' cache plugin while trying to read %s : %s" % (self.plugin_name, cachefile, to_bytes(e)))
            raise KeyError
        except Exception as e:
            raise AnsibleError("Error while decoding the cache file %s: %s" % (cachefile, to_bytes(e)))

    def set(self, key, value):

        self._cache[key] = value

        cachefile = "%s/%s" % (self._cache_dir, key)
        try:
            f = codecs.open(cachefile, self.write_mode, encoding=self.encoding)
        except (OSError,IOError) as e:
            display.warning("error in '%s' cache plugin while trying to write to %s : %s" % (self.plugin_name, cachefile, to_bytes(e)))
            pass
        else:
            self._dump(value, f)
        finally:
            try:
                f.close()
            except UnboundLocalError:
                pass

    def has_expired(self, key):

        if self._timeout == 0:
            return False

        cachefile = "%s/%s" % (self._cache_dir, key)
        try:
            st = os.stat(cachefile)
        except (OSError,IOError) as e:
            if e.errno == errno.ENOENT:
                return False
            else:
                display.warning("error in '%s' cache plugin while trying to stat %s : %s" % (self.plugin_name, cachefile, to_bytes(e)))
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
                display.warning("error in '%s' cache plugin while trying to stat %s : %s" % (self.plugin_name, cachefile, to_bytes(e)))
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

    def _load(self, f):
        raise AnsibleError("Plugin '%s' must implement _load method" % self.plugin_name)

    def _dump(self, value, f):
        raise AnsibleError("Plugin '%s' must implement _dump method" % self.plugin_name)

