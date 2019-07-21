# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# utils
from __future__ import absolute_import, division, print_function
__metaclass__ = type


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


def get_arp_monitor_target_diff(want_item, have_item):
    want_arp_target = []
    have_arp_target = []

    want_arp_monitor = want_item.get('arp-monitor') or {}
    if want_arp_monitor and 'target' in want_arp_monitor:
        want_arp_target = want_arp_monitor['target']

    if not have_item:
        diff = want_arp_target
    else:
        have_arp_monitor = have_item.get('arp-monitor') or {}
        if have_arp_monitor and 'target' in have_arp_monitor:
            have_arp_target = have_arp_monitor['target']

        diff = list_diff_want_only(want_arp_target, have_arp_target)
    return diff



def list_diff_have_only(want_list, have_list):
    if have_list and not want_list:
        diff = have_list
    elif not have_list:
        diff = None
    else:
        diff = [i for i in have_list + want_list if i in have_list and i not in want_list]
    return diff


def list_diff_want_only(want_list, have_list):
    if have_list and not want_list:
        diff = None
    elif not have_list:
        diff = want_list
    else:
        diff = [i for i in have_list + want_list if i in want_list and i not in have_list]
    return diff


def add_bond_members(want_item, have_item):
    commands = []
    bond_name = want_item['name']
    diff_members = get_member_diff(want_item, have_item)
    if diff_members:
        for key in diff_members:
            commands.append(
                'set interfaces ethernet ' + key['member'] + ' bond-group ' + bond_name
            )
    return commands


def add_arp_monitor(updates, set_cmd, key, want_item, have_item):
    commands = []
    arp_monitor = updates.get('arp-monitor') or {}
    diff_targets = get_arp_monitor_target_diff(want_item, have_item)

    if 'interval' in arp_monitor:
        commands.append(
            set_cmd + ' ' + key + ' interval ' + str(arp_monitor['interval'])
        )
    if diff_targets:
        for target in diff_targets:
            commands.append(
                set_cmd + ' ' + key + ' target ' + target
            )
    return commands


def delete_bond_members(lag):
    commands = []
    for member in lag['members']:
        commands.append(
            'delete interfaces ethernet ' + member['member'] + ' bond-group ' + lag['name']
        )
    return commands


def update_arp_monitor(del_cmd, want_item, have_item):
    commands = []
    want_arp_target = []
    have_arp_target = []
    want_arp_monitor = want_item.get('arp-monitor') or {}
    have_arp_monitor = have_item.get('arp-monitor') or {}

    if want_arp_monitor and 'target' in want_arp_monitor:
        want_arp_target = want_arp_monitor['target']

    if have_arp_monitor and 'target' in have_arp_monitor:
        have_arp_target = have_arp_monitor['target']

    if 'interval' in have_arp_monitor and not want_arp_monitor:
        commands.append(del_cmd + ' ' + 'arp-monitor' + ' interval')
    if 'target' in have_arp_monitor:
        target_diff = list_diff_have_only(want_arp_target, have_arp_target)
        if target_diff:
            for target in target_diff:
                commands.append(del_cmd + ' ' + 'arp-monitor' + ' target ' + target)

    return commands


def update_bond_members(want_item, have_item):
    commands = []
    name = have_item['name']
    want_members = want_item.get('members') or []
    have_members = have_item.get('members') or []

    members_diff = list_diff_have_only(want_members, have_members)
    if members_diff:
        for member in members_diff:
            commands.append(
                'delete interfaces ethernet ' + member['member'] + ' bond-group ' + name
            )
    return commands
