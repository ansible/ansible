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
from abc import ABCMeta, abstractmethod
from collections import MutableMapping

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils.six import with_metaclass
from ansible.module_utils._text import to_bytes
from ansible.plugins.loader import cache_loader

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
    def __init__(self, *args, **kwargs):

        self.plugin_name = self.__module__.split('.')[-1]
        self._timeout = float(C.CACHE_PLUGIN_TIMEOUT)
        self._cache = {}
        self._cache_dir = self._get_cache_connection(C.CACHE_PLUGIN_CONNECTION)
        self._set_inventory_cache_override(**kwargs)
        self.validate_cache_connection()

    def _get_cache_connection(self, source):
        if source:
            try:
                return os.path.expanduser(os.path.expandvars(source))
            except TypeError:
                pass

    def _set_inventory_cache_override(self, **kwargs):
        if kwargs.get('cache_timeout'):
            self._timeout = kwargs.get('cache_timeout')
        if kwargs.get('cache_connection'):
            self._cache_dir = self._get_cache_connection(kwargs.get('cache_connection'))

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
                self._cache[key] = value
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

        return self._cache.get(key)

    def set(self, key, value):

        self._cache[key] = value

        cachefile = "%s/%s" % (self._cache_dir, key)
        try:
            self._dump(value, cachefile)
        except (OSError, IOError) as e:
            display.warning("error in '%s' cache plugin while trying to write to %s : %s" % (self.plugin_name, cachefile, to_bytes(e)))

    def has_expired(self, key):

        if self._timeout == 0:
            return False

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
        except (OSError, IOError) as e:
            if e.errno == errno.ENOENT:
                return False
            else:
                display.warning("error in '%s' cache plugin while trying to stat %s : %s" % (self.plugin_name, cachefile, to_bytes(e)))

    def delete(self, key):
        try:
            del self._cache[key]
        except KeyError:
            pass
        try:
            os.remove("%s/%s" % (self._cache_dir, key))
        except (OSError, IOError):
            pass  # TODO: only pass on non existing?

    def flush(self):
        self._cache = {}
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


class FactCache(MutableMapping):

    def __init__(self, *args, **kwargs):

        self._plugin = cache_loader.get(C.CACHE_PLUGIN)
        if not self._plugin:
            raise AnsibleError('Unable to load the facts cache plugin (%s).' % (C.CACHE_PLUGIN))

        # Backwards compat: self._display isn't really needed, just import the global display and use that.
        self._display = display

        # in memory cache so plugins don't expire keys mid run
        self._cache = {}

    def __getitem__(self, key):
        if not self._plugin.contains(key):
            raise KeyError
        return self._plugin.get(key)

    def __setitem__(self, key, value):
        self._plugin.set(key, value)

    def __delitem__(self, key):
        self._plugin.delete(key)

    def __contains__(self, key):
        return self._plugin.contains(key)

    def __iter__(self):
        return iter(self._plugin.keys())

    def __len__(self):
        return len(self._plugin.keys())

    def copy(self):
        """ Return a primitive copy of the keys and values from the cache. """
        return dict(self)

    def keys(self):
        return self._plugin.keys()

    def flush(self):
        """ Flush the fact cache of all keys. """
        self._plugin.flush()

    def update(self, key, value):
        host_cache = self._plugin.get(key)
        host_cache.update(value)
        self._plugin.set(key, host_cache)


class InventoryFileCacheModule(BaseFileCacheModule):
    """
    A caching module backed by file based storage.
    """
    def __init__(self, plugin_name, timeout, cache_dir):

        self.plugin_name = plugin_name
        self._timeout = timeout
        self._cache = {}
        self._cache_dir = self._get_cache_connection(cache_dir)
        self.validate_cache_connection()
        self._plugin = self.get_plugin(plugin_name)

    def validate_cache_connection(self):
        try:
            super(InventoryFileCacheModule, self).validate_cache_connection()
        except AnsibleError as e:
            cache_connection_set = False
        else:
            cache_connection_set = True

        if not cache_connection_set:
            raise AnsibleError("error, '%s' inventory cache plugin requires the one of the following to be set:\n"
                               "ansible.cfg:\n[default]: fact_caching_connection,\n[inventory]: cache_connection;\n"
                               "Environment:\nANSIBLE_INVENTORY_CACHE_CONNECTION,\nANSIBLE_CACHE_PLUGIN_CONNECTION."
                               "to be set to a writeable directory path" % self.plugin_name)

    def get(self, cache_key):

        if not self.contains(cache_key):
            # Check if cache file exists
            raise KeyError

        return super(InventoryFileCacheModule, self).get(cache_key)

    def get_plugin(self, plugin_name):
        plugin = cache_loader.get(plugin_name, cache_connection=self._cache_dir, cache_timeout=self._timeout)
        if not plugin:
            raise AnsibleError('Unable to load the facts cache plugin (%s).' % (plugin_name))
        self._cache = {}
        return plugin

    def _load(self, path):
        return self._plugin._load(path)

    def _dump(self, value, path):
        return self._plugin._dump(value, path)
