# Copyright: (c) 2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from collections.abc import MutableMapping

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.plugins.loader import cache_loader
from ansible.utils.display import Display


display = Display()


class FactCache(MutableMapping):

    def __init__(self, *args, **kwargs):

        self._plugin = cache_loader.get(C.CACHE_PLUGIN)
        if not self._plugin:
            raise AnsibleError('Unable to load the facts cache plugin (%s).' % (C.CACHE_PLUGIN))

        super(FactCache, self).__init__(*args, **kwargs)

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

    def first_order_merge(self, key, value):
        host_facts = {key: value}

        try:
            host_cache = self._plugin.get(key)
            if host_cache:
                host_cache.update(value)
                host_facts[key] = host_cache
        except KeyError:
            pass

        super(FactCache, self).update(host_facts)
