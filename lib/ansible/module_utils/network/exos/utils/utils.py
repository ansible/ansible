from __future__ import absolute_import, division, print_function
__metaclass__ = type


def search_obj_in_list(item, lst, key):
    for o in lst:
        if o[key] == item:
            return o
    return None
