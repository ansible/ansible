# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# utils
from __future__ import absolute_import, division, print_function
__metaclass__ = type
from ansible.module_utils.six import iteritems


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


def get_lst_diff_for_dicts(want, have, lst):
    """
    This function generates a list containing values
    that are only in want and not in list in have dict
    :param want: dict object to want
    :param have: dict object to have
    :param lst: list the diff on
    :return: new list object with values which are only in want.
    """
    if not have:
        diff = want.get(lst) or []

    else:
        want_elements = want.get(lst) or {}
        have_elements = have.get(lst) or {}
        diff = list_diff_want_only(want_elements, have_elements)
    return diff


def list_diff_have_only(want_list, have_list):
    """
    This function generated the list containing values
    that are only in have list.
    :param want_list:
    :param have_list:
    :return: new list with values which are only in have list
    """
    if have_list and not want_list:
        diff = have_list
    elif not have_list:
        diff = None
    else:
        diff = [i for i in have_list + want_list if i in have_list and i not in want_list]
    return diff


def list_diff_want_only(want_list, have_list):
    """
    This function generated the list containing values
    that are only in want list.
    :param want_list:
    :param have_list:
    :return: new list with values which are only in want list
    """
    if have_list and not want_list:
        diff = None
    elif not have_list:
        diff = want_list
    else:
        diff = [i for i in have_list + want_list if i in want_list and i not in have_list]
    return diff


def search_dict_tv_in_list(d_val1, d_val2, lst, key1, key2):
    """
    This function return the dict object if it exist in list.
    :param d_val1:
    :param d_val2:
    :param lst:
    :param key1:
    :param key2:
    :return:
    """
    obj = next((item for item in lst if item[key1] == d_val1 and item[key2] == d_val2), None)
    if obj:
        return obj
    else:
        return None


def key_value_in_dict(have_key, have_value, want_dict):
    """
    This function checks whether the key and values exist in dict
    :param have_key:
    :param have_value:
    :param want_dict:
    :return:
    """
    for key, value in iteritems(want_dict):
        if key == have_key and value == have_value:
            return True
    return False


def is_dict_element_present(dict, key):
    """
    This function checks whether the key is present in dict.
    :param dict:
    :param key:
    :return:
    """
    for item in dict:
        if item == key:
            return True
    return False
