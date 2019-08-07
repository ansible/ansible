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


def flatten_dict(x):
    result = {}
    if not isinstance(x, dict):
        return result

    for key, value in iteritems(x):
        if isinstance(value, dict):
            result.update(flatten_dict(value))
        else:
            result[key] = value

    return result


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


def pad_commands(commands, interface):
    commands.insert(0, 'interface {0}'.format(interface))
