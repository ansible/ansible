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
from __future__ import annotations

import copy
import hashlib
import os
import tempfile
import time
import typing as t

from abc import abstractmethod
from collections import abc as c

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils.common.file import S_IRWU_RG_RO
from ansible.module_utils.common.text.converters import to_bytes
from ansible.plugins import AnsiblePlugin
from ansible.plugins.loader import cache_loader
from ansible.utils.collection_loader import resource_from_fqcr
from ansible.utils.display import Display

display = Display()


class BaseCacheModule(AnsiblePlugin):

    _PATH_CHARS = frozenset({'/', '..', '<', '>', '|'})

    # Backwards compat only.  Just import the global display instead
    _display = display
    _persistent = True
    """Plugins that do not persist data between runs can set False to bypass schema-version key munging and JSON serialization wrapper."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()

        self.set_options(var_options=args, direct=kwargs)

    @abstractmethod
    def get(self, key: str) -> dict[str, object]:
        pass

    @abstractmethod
    def set(self, key: str, value: dict[str, object]) -> None:
        pass

    @abstractmethod
    def keys(self) -> t.Sequence[str]:
        pass

    @abstractmethod
    def contains(self, key: object) -> bool:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass

    @abstractmethod
    def flush(self) -> None:
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
        self.plugin_name = resource_from_fqcr(self.__module__)
        self._cache = {}
        self.validate_cache_connection()
        self._sanitized = {}
        self._files = {}

    def _get_cache_connection(self, source):
        if source:
            try:
                return os.path.expanduser(os.path.expandvars(source))
            except TypeError:
                pass

    def _sanitize_key(self, key: str) -> str:
        """
        Ensures key name is safe to use on the filesystem
        """
        if key not in self._sanitized:
            for invalid in self._PATH_CHARS:
                if invalid in key:
                    self._sanitized[key] = hashlib.sha256(key.encode()).hexdigest()[:max(len(key), 12)]
                    break
            else:
                self._sanitized[key] = key
        return self._sanitized[key]

    def validate_cache_connection(self):
        if not self._cache_dir:
            raise AnsibleError(f"'{self.plugin_name!r}' cache plugin requires the 'fact_caching_connection' configuration option "
                               "to be set (to a writeable directory path)")

        if not os.path.exists(self._cache_dir):
            try:
                os.makedirs(self._cache_dir)
            except OSError as ex:
                raise AnsibleError(f"Error in {self.plugin_name!r} cache plugin while trying to create cache dir {self._cache_dir!r}.") from ex
        else:
            for x in (os.R_OK, os.W_OK, os.X_OK):
                if not os.access(self._cache_dir, x):
                    raise AnsibleError(f"'{self.plugin_name!r}' cache, configured path ({self._cache_dir}) does not have necessary permissions (rwx),"
                                       " disabling plugin")

    def _get_cache_file_name(self, key: str) -> str:
        if key not in self._files:
            safe = self._sanitize_key(key)  # use key or filesystem safe hash of key
            prefix = self.get_option('_prefix')
            if not prefix:
                prefix = ''
            self._files[key] = os.path.join(self._cache_dir, prefix + safe)
        return self._files[key]

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
            except FileNotFoundError:
                raise KeyError
            except Exception as ex:
                raise AnsibleError(f"Error while accessing the cache file {cachefile!r}.") from ex

        return self._cache.get(key)

    def set(self, key, value):

        self._cache[key] = value

        cachefile = self._get_cache_file_name(key)
        tmpfile_handle, tmpfile_path = tempfile.mkstemp(dir=self._cache_dir)
        try:
            try:
                self._dump(value, tmpfile_path)
            except OSError as ex:
                display.error_as_warning(f"Error in {self.plugin_name!r} cache plugin while trying to write to {tmpfile_path!r}.", exception=ex)
            try:
                os.close(tmpfile_handle)  # os.rename fails if handle is still open in WSL
                os.rename(tmpfile_path, cachefile)
                os.chmod(cachefile, mode=S_IRWU_RG_RO)
            except OSError as ex:
                display.error_as_warning(f"Error in {self.plugin_name!r} cache plugin while trying to move {tmpfile_path!r} to {cachefile!r}.", exception=ex)
        finally:
            try:
                os.unlink(tmpfile_path)
            except OSError:
                pass

    def has_expired(self, key):

        if self._timeout == 0:
            return False

        cachefile = self._get_cache_file_name(key)
        try:
            st = os.stat(cachefile)
        except FileNotFoundError:
            return False
        except OSError as ex:
            display.error_as_warning(f"Error in {self.plugin_name!r} cache plugin while trying to stat {cachefile!r}.", exception=ex)

            return False

        if time.time() - st.st_mtime <= self._timeout:
            return False

        if key in self._cache:
            del self._cache[key]
        return True

    def keys(self):
        # When using a prefix we must remove it from the key name before
        # checking the expiry and returning it to the caller. Keys that do not
        # share the same prefix cannot be fetched from the cache.
        prefix = self.get_option('_prefix')
        prefix_length = len(prefix)
        keys = []
        for k in os.listdir(self._cache_dir):
            if k.startswith('.') or not k.startswith(prefix):
                continue

            k = k[prefix_length:]
            if not self.has_expired(k):
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
        except FileNotFoundError:
            return False
        except OSError as ex:
            display.error_as_warning(f"Error in {self.plugin_name!r} cache plugin while trying to stat {cachefile!r}.", exception=ex)

    def delete(self, key):
        try:
            del self._cache[key]
        except KeyError:
            pass
        try:
            os.remove(self._get_cache_file_name(key))
        except OSError:
            pass  # TODO: only pass on non existing?

    def flush(self):
        self._cache = {}
        for key in self.keys():
            self.delete(key)

    @abstractmethod
    def _load(self, filepath: str) -> object:
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
    def _dump(self, value: object, filepath: str) -> None:
        """
        Write data to a filepath

        :arg value: The value to store
        :arg filepath: The filepath to store it at
        """
        pass


class CachePluginAdjudicator(c.MutableMapping):
    """Batch update wrapper around a cache plugin."""

    def __init__(self, plugin_name='memory', **kwargs):
        self._cache = {}
        self._retrieved = {}
        self._plugin = cache_loader.get(plugin_name, **kwargs)

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
        return repr(self._cache)

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.keys())

    def _do_load_key(self, key):
        load = False

        if key not in self._cache and key not in self._retrieved and self._plugin._persistent and self._plugin.contains(key):
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
            except KeyError:
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

    def clear(self):
        self.flush()

    def flush(self):
        self._plugin.flush()
        self._cache = {}

    def update(self, value):
        self._cache.update(value)
