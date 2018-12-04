# Copyright: (c) 2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils.common._collections_compat import MutableMapping
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

    def update(self, *args):
        """ We override the normal update to ensure we always use the 'setter' method """
        if len(args) == 2:
            display.deprecated('Calling FactCache.update(key, value) is deprecated.  Use the'
                               ' normal dict.update() signature of FactCache.update({key: value})'
                               ' instead.', version='2.12')
            host_facts = {args[0]: args[1]}
        elif len(args) == 1:
            host_facts = args[0]
        else:
            raise TypeError('update expected at most 1 argument, got {0}'.format(len(args)))

        for key in host_facts:
            try:
                host_cache = self._plugin.get(key)
                if host_cache:
                    host_cache.update(host_facts[key])
                else:
                    host_cache = host_facts[key]
                self._plugin.set(key, host_cache)
            except KeyError:
                self._plugin.set(key, host_facts[key])
