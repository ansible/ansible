# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# utils

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import dict_diff, is_masklen, to_netmask, search_obj_in_list


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


def dict_to_set(sample_dict):
    # Generate a set with passed dictionary for comparison
    test_dict = {}
    if isinstance(sample_dict, dict):
        for k, v in iteritems(sample_dict):
            if v is not None:
                if isinstance(v, list):
                    if isinstance(v[0], dict):
                        li = []
                        for each in v:
                            for key, value in iteritems(each):
                                if isinstance(value, list):
                                    each[key] = tuple(value)
                            li.append(tuple(iteritems(each)))
                        v = tuple(li)
                    else:
                        v = tuple(v)
                elif isinstance(v, dict):
                    li = []
                    for key, value in iteritems(v):
                        if isinstance(value, list):
                            v[key] = tuple(value)
                    li.extend(tuple(iteritems(v)))
                    v = tuple(li)
                test_dict.update({k: v})
        return_set = set(tuple(iteritems(test_dict)))
    else:
        return_set = set(sample_dict)
    return return_set


def filter_dict_having_none_value(want, have):
    # Generate dict with have dict value which is None in want dict
    test_dict = dict()
    test_key_dict = dict()
    name = want.get('name')
    if name:
        test_dict['name'] = name
    diff_ip = False
    want_ip = ''
    for k, v in iteritems(want):
        if isinstance(v, dict):
            for key, value in iteritems(v):
                if value is None:
                    dict_val = have.get(k).get(key)
                    test_key_dict.update({key: dict_val})
                test_dict.update({k: test_key_dict})
        if isinstance(v, list) and isinstance(v[0], dict):
            for key, value in iteritems(v[0]):
                if value is None:
                    dict_val = have.get(k).get(key)
                    test_key_dict.update({key: dict_val})
                test_dict.update({k: test_key_dict})
            # below conditions checks are added to check if
            # secondary IP is configured, if yes then delete
            # the already configured IP if want and have IP
            # is different else if it's same no need to delete
            for each in v:
                if each.get('secondary'):
                    want_ip = each.get('address').split('/')
                    have_ip = have.get('ipv4')
                    for each in have_ip:
                        if len(want_ip) > 1 and each.get('secondary'):
                            have_ip = each.get('address').split(' ')[0]
                            if have_ip != want_ip[0]:
                                diff_ip = True
                    if each.get('secondary') and diff_ip is True:
                        test_key_dict.update({'secondary': True})
                    test_dict.update({'ipv4': test_key_dict})
                # Checks if want doesn't have secondary IP but have has secondary IP set
                elif have.get('ipv4'):
                    if [True for each_have in have.get('ipv4') if 'secondary' in each_have]:
                        test_dict.update({'ipv4': {'secondary': True}})
        if k == 'l2protocol':
            if want[k] != have.get('l2protocol') and have.get('l2protocol'):
                test_dict.update({k: v})
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


def diff_list_of_dicts(w, h):
    """
    Returns a list containing diff between
    two list of dictionaries
    """
    if not w:
        w = []
    if not h:
        h = []

    diff = []
    for w_item in w:
        h_item = search_obj_in_list(w_item['member'], h, key='member') or {}
        d = dict_diff(h_item, w_item)
        if d:
            if 'member' not in d.keys():
                d['member'] = w_item['member']
            diff.append(d)

    return diff


def validate_ipv4(value, module):
    if value:
        address = value.split('/')
        if len(address) != 2:
            module.fail_json(msg='address format is <ipv4 address>/<mask>, got invalid format {0}'.format(value))

        if not is_masklen(address[1]):
            module.fail_json(msg='invalid value for mask: {0}, mask should be in range 0-32'.format(address[1]))


def validate_ipv6(value, module):
    if value:
        address = value.split('/')
        if len(address) != 2:
            module.fail_json(msg='address format is <ipv6 address>/<mask>, got invalid format {0}'.format(value))
        else:
            if not 0 <= int(address[1]) <= 128:
                module.fail_json(msg='invalid value for mask: {0}, mask should be in range 0-128'.format(address[1]))


def validate_n_expand_ipv4(module, want):
    # Check if input IPV4 is valid IP and expand IPV4 with its subnet mask
    ip_addr_want = want.get('address')
    if len(ip_addr_want.split(' ')) > 1:
        return ip_addr_want
    validate_ipv4(ip_addr_want, module)
    ip = ip_addr_want.split('/')
    if len(ip) == 2:
        ip_addr_want = '{0} {1}'.format(ip[0], to_netmask(ip[1]))

    return ip_addr_want


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
    elif name.lower().startswith('fa'):
        if_type = 'FastEthernet'
    elif name.lower().startswith('fo'):
        if_type = 'FortyGigE'
    elif name.lower().startswith('te'):
        if_type = 'TenGigE'
    elif name.lower().startswith('twe'):
        if_type = 'TwentyFiveGigE'
    elif name.lower().startswith('hu'):
        if_type = 'HundredGigE'
    elif name.lower().startswith('vl'):
        if_type = 'Vlan'
    elif name.lower().startswith('lo'):
        if_type = 'Loopback'
    elif name.lower().startswith('be'):
        if_type = 'Bundle-Ether'
    elif name.lower().startswith('bp'):
        if_type = 'Bundle-POS'
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
    elif interface.upper().startswith('FA'):
        return 'FastEthernet'
    elif interface.upper().startswith('FO'):
        return 'FortyGigE'
    elif interface.upper().startswith('ET'):
        return 'Ethernet'
    elif interface.upper().startswith('LO'):
        return 'Loopback'
    elif interface.upper().startswith('BE'):
        return 'Bundle-Ether'
    elif interface.upper().startswith('NV'):
        return 'nve'
    elif interface.upper().startswith('TWE'):
        return 'TwentyFiveGigE'
    elif interface.upper().startswith('HU'):
        return 'HundredGigE'
    elif interface.upper().startswith('PRE'):
        return 'preconfigure'
    else:
        return 'unknown'
