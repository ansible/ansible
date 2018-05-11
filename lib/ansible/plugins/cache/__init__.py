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

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils.six import with_metaclass
from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.common._collections_compat import MutableMapping
from ansible.plugins import AnsiblePlugin
from ansible.plugins.loader import cache_loader

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class BaseCacheModule(AnsiblePlugin):

    # Backwards compat only.  Just import the global display instead
    _display = display

    def __init__(self, *args, **kwargs):
        self._load_name = self.__module__.split('.')[-1]
        super(BaseCacheModule, self).__init__()
        self.set_options(var_options=args, direct=kwargs)

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


def _set_plugin(func):
    def method_wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        for unique_cache in list(self.top_level_reference.keys()):
            cache_contents = self._recursively_get_values(self.top_level_reference.value)[unique_cache]
            self._plugin.set(unique_cache, cache_contents)
        return result
    return method_wrapper


def _get_plugin(func):
    def method_wrapper(self, key, *args, **kwargs):
        # Check for a brand new cache and attempt to load the key from the plugin if so
        if not self.top_level_reference.keys() and self._plugin.contains(key):
            try:
                # set the cache object and return the simple dict of the cache contents
                cache_contents = self._plugin.get(key)
                self.top_level_reference.set(key, cache_contents)
                return cache_contents
            except KeyError:
                # Cache expired
                pass
        # return the cache object so the inventory plugin can populate it like a dictionary
        return func(self, key, *args, **kwargs)
    return method_wrapper


class CacheObject(MutableMapping):
    def __init__(self, value={}, top_level_reference=None, plugin=None, plugin_kwargs={}):
        self.value = value
        self.simple_dict = self._recursively_get_values(self.value)
        # New Cache
        if top_level_reference is None:
            top_level_reference = self
            # Backwards compat for FactCache - FIXME
            if plugin is None:
                plugin_name = C.CACHE_PLUGIN
            else:
                plugin_name = plugin
            plugin = cache_loader.get(plugin_name, **plugin_kwargs)
            if plugin is None:
                raise AnsibleError('Unable to load the facts cache plugin ({0}).'.format(plugin_name))

        self.top_level_reference = top_level_reference
        self._plugin = plugin

    def __repr__(self):
        return to_text(self.simple_dict)

    def __contains__(self, key):
        # Check for a brand new cache and update it with the plugin if possible
        if not self.top_level_reference.keys() and self._plugin.contains(key):
            try:
                self.top_level_reference.set(key, self._plugin.get(key))
            except KeyError:
                # Cache expired
                pass
        return key in self.keys()

    def __iter__(self):
        return iter(self.simple_dict)

    def __len__(self):
        return len(self.keys())

    @_get_plugin
    def __getitem__(self, key):
        return self.value[key]

    def copy(self):
        return CacheObject(dict(self.simple_dict), plugin=self._plugin._load_name)

    def items(self):
        return self.simple_dict.items()

    def values(self):
        return self.simple_dict.values()

    def keys(self):
        # This breaks with FactCache FIXME
        return self.simple_dict.keys()

    @_get_plugin
    def get(self, key, default=None):
        try:
            return self.value[key]
        except KeyError:
            return default

    def _recursively_get_values(self, item):
        if isinstance(item, CacheObject):
            return self._recursively_get_values(item.value)
        elif isinstance(item, dict):
            return dict((k, self._recursively_get_values(v)) for k, v in item.items())
        elif isinstance(item, list):
            return [self._recursively_get_values(v) for v in item]
        else:
            return item

    @_set_plugin
    def pop(self, key, *args):
        if args and key not in self.keys():
            return args[0]
        value = self.simple_dict[key]
        del self[key]
        return value

    @_set_plugin
    def __delitem__(self, key):
        del self.simple_dict[key]
        del self.value[key]

    def set(self, key, value):
        self[key] = value

    @_set_plugin
    def __setitem__(self, key, value):
        self.value[key] = self._recursively_set(value)
        self.simple_dict = self._recursively_get_values(self.value)

    def _recursively_set(self, value):
        if not value:
            return CacheObject(value, self.top_level_reference, self._plugin)
        elif isinstance(value, dict):
            return CacheObject(value, self.top_level_reference, self._plugin)
        elif isinstance(value, list):
            return [self._recursively_set(v) for v in value]
        else:
            return CacheObject(value, self.top_level_reference, self._plugin)

    def flush(self):
        self.top_level_reference.value = {}
        self._plugin.flush()

    @_set_plugin
    def update(self, key, value):
        key_cache = self.simple_dict[key]
        key_cache.update(value)
        self[key] = key_cache


class BaseFileCacheModule(BaseCacheModule):
    """
    A caching module backed by file based storage.
    """
    def __init__(self, *args, **kwargs):
        super(BaseFileCacheModule, self).__init__(*args, **kwargs)
        self.plugin_name = self.__module__.split('.')[-1]
        self._cache = {}
        self._timeout = float(self.get_option('_timeout'))
        self._cache_dir = self._get_cache_connection(self.get_option('_uri'))
        self.validate_cache_connection()

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


# Backwards compatibility FIXME
#FactCache = CacheObject

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
