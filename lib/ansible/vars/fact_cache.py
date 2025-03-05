# Copyright: (c) 2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import annotations

import typing as t

from collections.abc import MutableMapping

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.plugins.cache import BaseCacheModule
from ansible.plugins.loader import cache_loader
from ansible.utils.display import Display


display = Display()


class FactCache(MutableMapping[str, dict[str, object]]):
    def __init__(self, *args, **kwargs) -> None:
        self._plugin: BaseCacheModule = cache_loader.get(C.CACHE_PLUGIN)

        if not self._plugin:
            raise AnsibleError('Unable to load the facts cache plugin (%s).' % (C.CACHE_PLUGIN))

        super(FactCache, self).__init__(*args, **kwargs)

    def __getitem__(self, key: str) -> dict[str, object]:
        if not self._plugin.contains(key):
            raise KeyError(key)

        return self._plugin.get(key)

    def __setitem__(self, key: str, value: dict[str, object]) -> None:
        self._plugin.set(key, value)

    def __delitem__(self, key: str) -> None:
        self._plugin.delete(key)

    def __contains__(self, key: object) -> bool:
        return self._plugin.contains(key)

    def __iter__(self) -> t.Iterator[str]:
        return iter(self._plugin.keys())

    def __len__(self) -> int:
        return len(self._plugin.keys())

    def copy(self) -> dict[str, dict[str, object]]:
        """ Return a primitive copy of the keys and values from the cache. """
        return dict(self)

    def keys(self):
        return self._plugin.keys()

    def flush(self) -> None:
        """ Flush the fact cache of all keys. """
        self._plugin.flush()

    def first_order_merge(self, key: str, value: dict[str, object]) -> None:
        display.deprecated(
            "API 'first_order_merge' is deprecated, please update the usage",
            version="2.22"
        )

        host_facts = {key: value}

        try:
            host_cache = self._plugin.get(key)

            if host_cache:
                host_cache.update(value)
                host_facts[key] = host_cache
        except KeyError:
            pass

        super(FactCache, self).update(host_facts)
