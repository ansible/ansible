# Copyright (c) 2016 Red Hat Inc
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

# General networking tools that may be used by all modules

import re
from struct import pack
from socket import inet_ntoa

from ansible.module_utils.six.moves import zip


VALID_MASKS = [2**8 - 2**i for i in range(0, 9)]


def is_netmask(val):
    parts = str(val).split('.')
    if not len(parts) == 4:
        return False
    for part in parts:
        try:
            if int(part) not in VALID_MASKS:
                raise ValueError
        except ValueError:
            return False
    return True


def is_masklen(val):
    try:
        return 0 <= int(val) <= 32
    except ValueError:
        return False


def to_netmask(val):
    """ converts a masklen to a netmask """
    if not is_masklen(val):
        raise ValueError('invalid value for masklen')

    bits = 0
    for i in range(32 - int(val), 32):
        bits |= (1 << i)

    return inet_ntoa(pack('>I', bits))


def to_masklen(val):
    """ converts a netmask to a masklen """
    if not is_netmask(val):
        raise ValueError('invalid value for netmask: %s' % val)

    bits = list()
    for x in val.split('.'):
        octet = bin(int(x)).count('1')
        bits.append(octet)

    return sum(bits)


def to_subnet(addr, mask, dotted_notation=False):
    """ coverts an addr / mask pair to a subnet in cidr notation """
    try:
        if not is_masklen(mask):
            raise ValueError
        cidr = int(mask)
        mask = to_netmask(mask)
    except ValueError:
        cidr = to_masklen(mask)

    addr = addr.split('.')
    mask = mask.split('.')

    network = list()
    for s_addr, s_mask in zip(addr, mask):
        network.append(str(int(s_addr) & int(s_mask)))

    if dotted_notation:
        return '%s %s' % ('.'.join(network), to_netmask(cidr))
    return '%s/%s' % ('.'.join(network), cidr)


def to_ipv6_subnet(addr):
    """ IPv6 addresses are eight groupings. The first four groupings (64 bits) comprise the subnet address. """

    # https://tools.ietf.org/rfc/rfc2374.txt

    # Split by :: to identify omitted zeros
    ipv6_prefix = addr.split('::')[0]

    # Get the first four groups, or as many as are found + ::
    found_groups = []
    for group in ipv6_prefix.split(':'):
        found_groups.append(group)
        if len(found_groups) == 4:
            break
    if len(found_groups) < 4:
        found_groups.append('::')

    # Concatenate network address parts
    network_addr = ''
    for group in found_groups:
        if group != '::':
            network_addr += str(group)
        network_addr += str(':')

    # Ensure network address ends with ::
    if not network_addr.endswith('::'):
        network_addr += str(':')
    return network_addr


def to_ipv6_network(addr):
    """ IPv6 addresses are eight groupings. The first three groupings (48 bits) comprise the network address. """

    # Split by :: to identify omitted zeros
    ipv6_prefix = addr.split('::')[0]

    # Get the first three groups, or as many as are found + ::
    found_groups = []
    for group in ipv6_prefix.split(':'):
        found_groups.append(group)
        if len(found_groups) == 3:
            break
    if len(found_groups) < 3:
        found_groups.append('::')

    # Concatenate network address parts
    network_addr = ''
    for group in found_groups:
        if group != '::':
            network_addr += str(group)
        network_addr += str(':')

    # Ensure network address ends with ::
    if not network_addr.endswith('::'):
        network_addr += str(':')
    return network_addr


def to_bits(val):
    """ converts a netmask to bits """
    bits = ''
    for octet in val.split('.'):
        bits += bin(int(octet))[2:].zfill(8)
    return str


def is_mac(mac_address):
    """
    Validate MAC address for given string
    Args:
        mac_address: string to validate as MAC address

    Returns: (Boolean) True if string is valid MAC address, otherwise False
    """
    mac_addr_regex = re.compile('[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$')
    return bool(mac_addr_regex.match(mac_address.lower()))
