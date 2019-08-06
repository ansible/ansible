# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# utils


from __future__ import absolute_import, division, print_function
__metaclass__ = type


def search_obj_in_list(name, lst, key='name'):
    for item in lst:
        if item[key] == name:
            return item
    return None


def get_interface_type(interface):
    """Gets the type of interface
    """
    if interface.startswith('eth'):
        return 'ethernet'
    elif interface.startswith('bond'):
        return 'bonding'
    elif interface.startswith('vti'):
        return 'vti'
    elif interface.startswith('lo'):
        return 'loopback'


def dict_delete(base, comparable):
    """
    This function generates a dict containing key, value pairs for keys
    that are present in the `base` dict but not present in the `comparable`
    dict.

    :param base: dict object to base the diff on
    :param comparable: dict object to compare against base
    :returns: new dict object with key, value pairs that needs to be deleted.

    """
    to_delete = dict()

    for key in base:
        if isinstance(base[key], dict):
            sub_diff = dict_delete(base[key], comparable.get(key, {}))
            if sub_diff:
                to_delete[key] = sub_diff
        else:
            if key not in comparable:
                to_delete[key] = base[key]

    return to_delete


def diff_list_of_dicts(want, have):
    diff = []

    set_w = set(tuple(d.items()) for d in want)
    set_h = set(tuple(d.items()) for d in have)
    difference = set_w.difference(set_h)

    for element in difference:
        diff.append(dict((x, y) for x, y in element))

    return diff
