# (c) 2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2018, Ansible Project
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

import copy
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
from ansible.utils.display import Display
from ansible.vars.fact_cache import FactCache as RealFactCache

display = Display()


class FactCache(RealFactCache):
    """
    This is for backwards compatibility.  Will be removed after deprecation.  It was removed as it
    wasn't actually part of the cache plugin API.  It's actually the code to make use of cache
    plugins, not the cache plugin itself.  Subclassing it wouldn't yield a usable Cache Plugin and
    there was no facility to use it as anything else.
    """
    def __init__(self, *args, **kwargs):
        display.deprecated('ansible.plugins.cache.FactCache has been moved to'
                           ' ansible.vars.fact_cache.FactCache.  If you are looking for the class'
                           ' to subclass for a cache plugin, you want'
                           ' ansible.plugins.cache.BaseCacheModule or one of its subclasses.',
                           version='2.12')
        super(FactCache, self).__init__(*args, **kwargs)


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


class BaseFileCacheModule(BaseCacheModule):
    """
    A caching module backed by file based storage.
    """
    def __init__(self, *args, **kwargs):

        try:
            super(BaseFileCacheModule, self).__init__(*args, **kwargs)
            self._cache_dir = self._get_cache_connection(self.get_option('_uri'))
            self._timeout = float(self.get_option('_timeout'))
        except KeyError:
            self._cache_dir = self._get_cache_connection(C.CACHE_PLUGIN_CONNECTION)
            self._timeout = float(C.CACHE_PLUGIN_TIMEOUT)
        self.plugin_name = self.__module__.split('.')[-1]
        self._cache = {}
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

    def _get_cache_file_name(self, key):
        prefix = self.get_option('_prefix')
        if prefix:
            cachefile = "%s/%s%s" % (self._cache_dir, prefix, key)
        else:
            cachefile = "%s/%s" % (self._cache_dir, key)
        return cachefile

    def get(self, key):
        """ This checks the in memory cache first as the fact was not expired at 'gather time'
        and it would be problematic if the key did expire after some long running tasks and
        user gets 'undefined' error in the same play """

        if key not in self._cache:

            if self.has_expired(key) or key == "":
                raise KeyError

            cachefile = self._get_cache_file_name(key)
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

        cachefile = self._get_cache_file_name(key)
        try:
            self._dump(value, cachefile)
        except (OSError, IOError) as e:
            display.warning("error in '%s' cache plugin while trying to write to %s : %s" % (self.plugin_name, cachefile, to_bytes(e)))

    def has_expired(self, key):

        if self._timeout == 0:
            return False

        cachefile = self._get_cache_file_name(key)
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
        cachefile = self._get_cache_file_name(key)

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
            os.remove(self._get_cache_file_name(key))
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


class CachePluginAdjudicator(MutableMapping):
    """
    Intermediary between a cache dictionary and a CacheModule
    """
    def __init__(self, plugin_name='memory', **kwargs):
        self._cache = {}
        self._retrieved = {}

        self._plugin = cache_loader.get(plugin_name, **kwargs)
        if not self._plugin:
            raise AnsibleError('Unable to load the cache plugin (%s).' % plugin_name)

        self._plugin_name = plugin_name

    def update_cache_if_changed(self):
        if self._retrieved != self._cache:
            self.set_cache()

    def set_cache(self):
        for top_level_cache_key in self._cache.keys():
            self._plugin.set(top_level_cache_key, self._cache[top_level_cache_key])
        self._retrieved = copy.deepcopy(self._cache)

    def load_whole_cache(self):
        for key in self._plugin.keys():
            self._cache[key] = self._plugin.get(key)

    def __repr__(self):
        return to_text(self._cache)

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.keys())

    def _do_load_key(self, key):
        load = False
        if all([
            key not in self._cache,
            key not in self._retrieved,
            self._plugin_name != 'memory',
            self._plugin.contains(key),
        ]):
            load = True
        return load

    def __getitem__(self, key):
        if self._do_load_key(key):
            try:
                self._cache[key] = self._plugin.get(key)
            except KeyError:
                pass
            else:
                self._retrieved[key] = self._cache[key]
        return self._cache[key]

    def get(self, key, default=None):
        if self._do_load_key(key):
            try:
                self._cache[key] = self._plugin.get(key)
            except KeyError as e:
                pass
            else:
                self._retrieved[key] = self._cache[key]
        return self._cache.get(key, default)

    def items(self):
        return self._cache.items()

    def values(self):
        return self._cache.values()

    def keys(self):
        return self._cache.keys()

    def pop(self, key, *args):
        if args:
            return self._cache.pop(key, args[0])
        return self._cache.pop(key)

    def __delitem__(self, key):
        del self._cache[key]

    def __setitem__(self, key, value):
        self._cache[key] = value

    def flush(self):
        for key in self._cache.keys():
            self._plugin.delete(key)
        self._cache = {}

    def update(self, value):
        self._cache.update(value)
