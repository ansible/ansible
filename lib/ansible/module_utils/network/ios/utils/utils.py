#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# utils

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.six import iteritems


def remove_command_from_config_list(interface, cmd, commands):
    # To delete the passed config
    if interface not in commands:
        commands.insert(0, interface)
    commands.append('no %s' % cmd)
    return commands


def add_command_to_config_list(interface, cmd, commands):
    # To set the passed config
    if interface not in commands:
        commands.insert(0, interface)
    commands.append(cmd)


def dict_diff(sample_dict):
    # Generate a set with passed dictionary for comparison
    test_dict = {}
    for k, v in iteritems(sample_dict):
        if v is not None:
            test_dict.update({k: v})
    return_set = set(tuple(test_dict.items()))
    return return_set


def filter_dict_having_none_value(want, have):
    # Generate dict with have dict value which is None in want dict
    test_dict = dict()
    test_dict['name'] = want.get('name')
    for k, v in iteritems(want):
        if v is None:
            val = have.get(k)
            test_dict.update({k: val})
    return test_dict


def remove_duplicate_interface(commands):
    # Remove duplicate interface from commands
    set_cmd = []
    for each in commands:
        if 'interface' in each:
            if each not in set_cmd:
                set_cmd.append(each)
        else:
            set_cmd.append(each)

    return set_cmd


def search_obj_in_list(name, lst):
    for o in lst:
        if o['name'] == name:
            return o
    return None


def normalize_interface(name):
    """Return the normalized interface name
    """
    if not name:
        return

    def _get_number(name):
        digits = ''
        for char in name:
            if char.isdigit() or char in '/.':
                digits += char
        return digits

    if name.lower().startswith('gi'):
        if_type = 'GigabitEthernet'
    elif name.lower().startswith('te'):
        if_type = 'TenGigabitEthernet'
    elif name.lower().startswith('fa'):
        if_type = 'FastEthernet'
    elif name.lower().startswith('fo'):
        if_type = 'FortyGigabitEthernet'
    elif name.lower().startswith('long'):
        if_type = 'LongReachEthernet'
    elif name.lower().startswith('et'):
        if_type = 'Ethernet'
    elif name.lower().startswith('vl'):
        if_type = 'Vlan'
    elif name.lower().startswith('lo'):
        if_type = 'loopback'
    elif name.lower().startswith('po'):
        if_type = 'port-channel'
    elif name.lower().startswith('nv'):
        if_type = 'nve'
    elif name.lower().startswith('twe'):
        if_type = 'TwentyFiveGigE'
    elif name.lower().startswith('hu'):
        if_type = 'HundredGigE'
    else:
        if_type = None

    number_list = name.split(' ')
    if len(number_list) == 2:
        number = number_list[-1].strip()
    else:
        number = _get_number(name)

    if if_type:
        proper_interface = if_type + number
    else:
        proper_interface = name

    return proper_interface


def get_interface_type(interface):
    """Gets the type of interface
    """

    if interface.upper().startswith('GI'):
        return 'GigabitEthernet'
    elif interface.upper().startswith('TE'):
        return 'TenGigabitEthernet'
    elif interface.upper().startswith('FA'):
        return 'FastEthernet'
    elif interface.upper().startswith('FO'):
        return 'FortyGigabitEthernet'
    elif interface.upper().startswith('LON'):
        return 'LongReachEthernet'
    elif interface.upper().startswith('ET'):
        return 'Ethernet'
    elif interface.upper().startswith('VL'):
        return 'Vlan'
    elif interface.upper().startswith('LO'):
        return 'loopback'
    elif interface.upper().startswith('PO'):
        return 'port-channel'
    elif interface.upper().startswith('NV'):
        return 'nve'
    elif interface.upper().startswith('TWE'):
        return 'TwentyFiveGigE'
    elif interface.upper().startswith('HU'):
        return 'HundredGigE'
    else:
        return 'unknown'
