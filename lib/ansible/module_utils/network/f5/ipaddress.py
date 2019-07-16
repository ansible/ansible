# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.network.common.utils import validate_ip_address

try:
    # Ansible 2.6 and later
    from ansible.module_utils.network.common.utils import validate_ip_v6_address
except ImportError:
    import socket

    # Ansible 2.5 and earlier
    #
    # This method is simply backported from the 2.6 source code.
    def validate_ip_v6_address(address):
        try:
            socket.inet_pton(socket.AF_INET6, address)
        except socket.error:
            return False
        return True


try:
    from library.module_utils.compat.ipaddress import ip_interface
    from library.module_utils.compat.ipaddress import ip_network
except ImportError:
    from ansible.module_utils.compat.ipaddress import ip_interface
    from ansible.module_utils.compat.ipaddress import ip_network


def is_valid_ip(addr, type='all'):
    if type in ['all', 'ipv4']:
        if validate_ip_address(addr):
            return True
    if type in ['all', 'ipv6']:
        if validate_ip_v6_address(addr):
            return True
    return False


def ipv6_netmask_to_cidr(mask):
    """converts an IPv6 netmask to CIDR form

    According to the link below, CIDR is the only official way to specify
    a subset of IPv6. With that said, the same link provides a way to
    loosely convert an netmask to a CIDR.

    Arguments:
      mask (string): The IPv6 netmask to convert to CIDR

    Returns:
      int: The CIDR representation of the netmask

    References:
      https://stackoverflow.com/a/33533007
      http://v6decode.com/
    """
    bit_masks = [
        0, 0x8000, 0xc000, 0xe000, 0xf000, 0xf800,
        0xfc00, 0xfe00, 0xff00, 0xff80, 0xffc0,
        0xffe0, 0xfff0, 0xfff8, 0xfffc, 0xfffe,
        0xffff
    ]
    count = 0
    try:
        for w in mask.split(':'):
            if not w or int(w, 16) == 0:
                break
            count += bit_masks.index(int(w, 16))
        return count
    except Exception:
        return -1


def is_valid_ip_network(address):
    try:
        ip_network(u'{0}'.format(address))
        return True
    except ValueError:
        return False


def is_valid_ip_interface(address):
    try:
        ip_interface(u'{0}'.format(address))
        return True
    except ValueError:
        return False


def get_netmask(address):
    addr = ip_network(u'{0}'.format(address))
    netmask = addr.netmask.compressed
    return netmask


def compress_address(address):
    addr = ip_network(u'{0}'.format(address))
    result = addr.compressed.split('/')[0]
    return result
