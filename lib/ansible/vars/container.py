# Copyright (c) 2026 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from collections import ChainMap

from ansible import constants as C

_HASH_BEHAVE = C.config.get_config_value_and_origin('DEFAULT_HASH_BEHAVIOUR')


class VarsContainer(ChainMap):
    """
    ChainMap wrapper class, that handles particular needs of Ansible Variables
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __delitem__(self, item: str) -> None:
        """
        Override ChainMap to behave more like a dictionary
        and ensure that the key is deleted
        """
        found = False
        for m in self.maps:
            if item in m:
                found = True
                del m[item]

        if not found:
            raise KeyError

    def combine(self, new_data):
        """
        Handle updates 'the ansible way', using ChainMap to simulate an
        overwrite or a merge, depending on the hash behaviour setting
        see: ansible.utils.vars.combine_vars
        """
        if new_data != {}:
            if _HASH_BEHAVE == 'merge':
                from ansible.utils.vars import merge_hash
                merge = {}
                for key in new_data.keys():
                    if key in self:
                        merge[key] = merge_hash(self[key], new_data[key])
                    else:
                        merge[key] = new_data[key]
                new_data = merge

            self.maps.insert(0, new_data)

    def update(self, *args, **kwargs):
        """
        MutableMapping compatibility override

        The result should be the same as a dict update except if
        hash behaviour is set to merge
        """
        if args is not None:
            if hasattr(args, 'keys'):
                self.combine(args)
            elif len(args) > 1:
                self.combine(dict(args))
            elif args and args[0]:
                # non empty iterator with single item
                raise ValueError

        if kwargs:
            self.combine(kwargs)
