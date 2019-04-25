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

    def update(self, *args):
        """
        Backwards compat shim

        We thought we needed this to ensure we always called the plugin's set() method but
        MutableMapping.update() will call our __setitem__() just fine.  It's the calls to update
        that we need to be careful of.  This contains a bug::

            fact_cache[host.name].update(facts)

        It retrieves a *copy* of the facts for host.name and then updates the copy.  So the changes
        aren't persisted.

        Instead we need to do::

            fact_cache.update({host.name, facts})

        Which will use FactCache's update() method.

        We currently need this shim for backwards compat because the update() method that we had
        implemented took key and value as arguments instead of taking a dict.  We can remove the
        shim in 2.12 as MutableMapping.update() should do everything that we need.
        """
        if len(args) == 2:
            # Deprecated.  Call the new function with this name
            display.deprecated('Calling FactCache().update(key, value) is deprecated.  Use'
                               ' FactCache().first_order_merge(key, value) if you want the old'
                               ' behaviour or use FactCache().update({key: value}) if you want'
                               ' dict-like behaviour.', version='2.12')
            return self.first_order_merge(*args)

        elif len(args) == 1:
            host_facts = args[0]

        else:
            raise TypeError('update expected at most 1 argument, got {0}'.format(len(args)))

        super(FactCache, self).update(host_facts)
