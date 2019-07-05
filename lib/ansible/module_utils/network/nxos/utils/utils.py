import socket

from ansible.module_utils.six import iteritems


def search_obj_in_list(name, lst):
    for o in lst:
        if o['name'] == name:
            return o
    return None


def eliminate_null_keys(cfg_dict):
    if not cfg_dict:
        return None
    if isinstance(cfg_dict, list):
        final_cfg = []
        for cfg in cfg_dict:
            final_cfg.append(_null_keys(cfg))
    else:
        final_cfg = _null_keys(cfg_dict)

    return final_cfg


def _null_keys(cfg):
    final_cfg = {}
    for k, v in iteritems(cfg):
        if v:
            if isinstance(v, dict):
                final_cfg.update(eliminate_null_keys(v))
            else:
                final_cfg.update({k: v})
    return final_cfg


def validate_ipv4_addr(address):
    address = address.split('/')[0]
    try:
        socket.inet_aton(address)
    except socket.error:
        return False
    return address.count('.') == 3


def validate_ipv6_addr(address):
    address = address.split('/')[0]
    try:
        socket.inet_pton(socket.AF_INET6, address)
    except socket.error:
        return False
    return True


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

    if name.lower().startswith('et'):
        if_type = 'Ethernet'
    elif name.lower().startswith('vl'):
        if_type = 'Vlan'
    elif name.lower().startswith('lo'):
        if_type = 'loopback'
    elif name.lower().startswith('po'):
        if_type = 'port-channel'
    elif name.lower().startswith('nv'):
        if_type = 'nve'
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
    if interface.upper().startswith('ET'):
        return 'ethernet'
    elif interface.upper().startswith('VL'):
        return 'svi'
    elif interface.upper().startswith('LO'):
        return 'loopback'
    elif interface.upper().startswith('MG'):
        return 'management'
    elif interface.upper().startswith('MA'):
        return 'management'
    elif interface.upper().startswith('PO'):
        return 'portchannel'
    elif interface.upper().startswith('NV'):
        return 'nve'
    else:
        return 'unknown'


def vlan_range_to_list(vlans):
    result = []
    if vlans:
        for part in vlans.split(','):
            if part == 'none':
                break
            if '-' in part:
                a, b = part.split('-')
                a, b = int(a), int(b)
                result.extend(range(a, b + 1))
            else:
                a = int(part)
                result.append(a)
        return numerical_sort(result)
    return result


def numerical_sort(string_int_list):
    """Sorts list of integers that are digits in numerical order.
    """

    as_int_list = []

    for vlan in string_int_list:
        as_int_list.append(int(vlan))
    as_int_list.sort()
    return as_int_list
