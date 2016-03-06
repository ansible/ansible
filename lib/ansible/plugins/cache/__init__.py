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

from collections import MutableMapping

from ansible import constants as C
from ansible.plugins import cache_loader

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class FactCache(MutableMapping):

    def __init__(self, *args, **kwargs):
        self._plugin = cache_loader.get(C.CACHE_PLUGIN)
        # Backwards compat: self._display isn't really needed, just import the global display and use that.
        self._display = display

        if self._plugin is None:
            display.warning("Failed to load fact cache plugins")
            return

    def __getitem__(self, key):
        if key not in self:
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
