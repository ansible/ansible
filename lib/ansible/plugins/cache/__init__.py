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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import time
import errno
from abc import abstractmethod
from collections import MutableMapping

from ansible.errors import AnsibleError
from ansible.plugins import AnsiblePlugin
from ansible.module_utils._text import to_bytes

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class BaseCacheModule(MutableMapping, AnsiblePlugin):

    # Backwards compat only.  Just import the global display instead
    _display = display

    def __init__(self, *args, **kwargs):

        # in memory cache so plugins don't expire keys mid run
        self._cache = {}
        self._timeout = None

    @abstractmethod
    def get(self, key):
        return self._cache.get(key)

    @abstractmethod
    def set(self, key, value):
        self._cache[key] = value

    @abstractmethod
    def keys(self):
        pass

    @abstractmethod
    def contains(self, key):
        has = False
        if key in self._cache:
            has = True
        return has

    @abstractmethod
    def delete(self, key):
        self._cache.pop(key)

    @abstractmethod
    def flush(self):
        self._cache = {}

    def __getitem__(self, key):
        if not self.contains(key):
            raise KeyError
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __delitem__(self, key):
        self.delete(key)

    def __contains__(self, key):
        return self.contains(key)

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.keys())

    def copy(self):
        """ Return a primitive copy of the keys and values from the cache. """
        return dict(self._cache)

    def update(self, key, value):
        host_cache = self.get(key)
        host_cache.update(value)
        self.set(key, host_cache)


# for backwards compatiblity
FactCache = BaseCacheModule


class BaseFileCacheModule(BaseCacheModule):
    """
    A caching module backed by file based storage.
    """
    def __init__(self, *args, **kwargs):

        super(BaseFileCacheModule, self).__init__(*args, **kwargs)

        self._cache_dir = None

    def _get_cache_connection(self, source):
        if source:
            try:
                return os.path.expanduser(os.path.expandvars(source))
            except TypeError:
                pass

    def validate_cache_connection(self):
        if not self._cache_dir:
            raise AnsibleError("error, '%s' cache plugin requires the 'fact_caching_connection' config option "
                               "to be set (to a writeable directory path)" % self.plugin_name)

        if not os.path.exists(self._cache_dir):
            try:
                os.makedirs(self._cache_dir)
            except (OSError, IOError) as e:
                raise AnsibleError("error in '%s' cache plugin while trying to create cache dir %s : %s" % (self.plugin_name, self._cache_dir, to_bytes(e)))
        else:
            for x in (os.R_OK, os.W_OK, os.X_OK):
                if not os.access(self._cache_dir, x):
                    raise AnsibleError("error in '%s' cache, configured path (%s) does not have necessary permissions (rwx), disabling plugin" % (
                        self.plugin_name, self._cache_dir))

    def get(self, key):
        """ This checks the in memory cache first as the fact was not expired at 'gather time'
        and it would be problematic if the key did expire after some long running tasks and
        user gets 'undefined' error in the same play """

        if key not in self._cache:

            if self.has_expired(key) or key == "":
                raise KeyError

            cachefile = "%s/%s" % (self._cache_dir, key)
            try:
                value = self._load(cachefile)
                super(BaseFileCacheModule, self).set(key, value)
            except ValueError as e:
                display.warning("error in '%s' cache plugin while trying to read %s : %s. "
                                "Most likely a corrupt file, so erasing and failing." % (self.plugin_name, cachefile, to_bytes(e)))
                self.delete(key)
                raise AnsibleError("The cache file %s was corrupt, or did not otherwise contain valid data. "
                                   "It has been removed, so you can re-run your command now." % cachefile)
            except (OSError, IOError) as e:
                display.warning("error in '%s' cache plugin while trying to read %s : %s" % (self.plugin_name, cachefile, to_bytes(e)))
                raise KeyError
            except Exception as e:
                raise AnsibleError("Error while decoding the cache file %s: %s" % (cachefile, to_bytes(e)))

        return super(BaseFileCacheModule, self).get(key)

    def set(self, key, value):

        super(BaseFileCacheModule, self).set(key, value)

        cachefile = "%s/%s" % (self._cache_dir, key)
        try:
            self._dump(value, cachefile)
        except (OSError, IOError) as e:
            display.warning("error in '%s' cache plugin while trying to write to %s : %s" % (self.plugin_name, cachefile, to_bytes(e)))

    def has_expired(self, key):

        if self._timeout == 0:
            return True

        cachefile = "%s/%s" % (self._cache_dir, key)
        try:
            st = os.stat(cachefile)
        except (OSError, IOError) as e:
            if e.errno == errno.ENOENT:
                return False
            else:
                display.warning("error in '%s' cache plugin while trying to stat %s : %s" % (self.plugin_name, cachefile, to_bytes(e)))
                return False

        if time.time() - st.st_mtime <= self._timeout:
            return False

        super(BaseFileCacheModule, self).delete(key)

        return True

    def keys(self):
        keys = []
        for k in os.listdir(self._cache_dir):
            if not (k.startswith('.') or self.has_expired(k)):
                keys.append(k)
        return keys

    def contains(self, key):
        cachefile = "%s/%s" % (self._cache_dir, key)

        if super(BaseFileCacheModule, self).contains(key):
            return True

        if self.has_expired(key):
            return False
        try:
            os.stat(cachefile)
            return True
        except (OSError, IOError) as e:
            if e.errno == errno.ENOENT:
                return False
            else:
                display.warning("error in '%s' cache plugin while trying to stat %s : %s" % (self.plugin_name, cachefile, to_bytes(e)))

    def delete(self, key):

        super(BaseFileCacheModule, self).delete(key)

        try:
            os.remove("%s/%s" % (self._cache_dir, key))
        except (OSError, IOError):
            pass  # TODO: only pass on non existing?

    def flush(self):
        super(BaseFileCacheModule, self).flush()
        for key in self.keys():
            self.delete(key)

    def copy(self):
        ret = dict()
        for key in self.keys():
            ret[key] = self.get(key)
        return ret

    @abstractmethod
    def _load(self, filepath):
        """
        Read data from a filepath and return it as a value

        :arg filepath: The filepath to read from.
        :returns: The value stored in the filepath

        This method reads from the file on disk and takes care of any parsing
        and transformation of the data before returning it.  The value
        returned should be what Ansible would expect if it were uncached data.

        .. note:: Filehandles have advantages but calling code doesn't know
            whether this file is text or binary, should be decoded, or accessed via
            a library function.  Therefore the API uses a filepath and opens
            the file inside of the method.
        """
        pass

    @abstractmethod
    def _dump(self, value, filepath):
        """
        Write data to a filepath

        :arg value: The value to store
        :arg filepath: The filepath to store it at
        """
        pass
