# Copyright: 2018, Adam Stevko <adam.stevko@gmail.com>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause )

import socket

from ansible.module_utils.validators.core import check_type_int, check_type_str


def check_type_port(value):
    ''' Validate TCP/UDP ports '''
    value = check_type_int(value)
    if 0 <= value <= 65535:
        return value
    raise ValueError("Invalid port value provided: %s" % str(value))


def check_type_l3_proto(self, value):
    ''' Validate network layer protocols '''
    value = check_type_str(value)
    try:
        socket.getprotobyname(value)
    except socket.error:
        raise ValueError("Invalid network layer protocol value provided: %s" % value)
    return value


def check_type_l4_proto(self, value):
    ''' Validate transport layer protocols '''
    value = check_type_str(value)
    try:
        socket.getprotobyname(value)
    except socket.error:
        raise ValueError("Invalid transport layer protocol value provided: %s" % value)
    return value


def check_type_l7_proto(self, value):
    ''' Validate application layer protocols '''
    value = check_type_str(value)
    try:
        socket.getservbyname(value)
    except socket.error:
        raise ValueError("Invalid application layer service value provided: %s" % value)
    return value


def check_type_ipaddr(self, value):
    ''' Validate IPv4 and IPv6 addresses in classical or CIDR notations '''
    value = check_type_str(value)
    ip_address, netmask = None, None
    if value.count('/') == 1:
        ip_address, netmask = value.split('/')
    else:
        ip_address = value
    if len(ip_address.split('.')) == 4:
        try:
            socket.inet_pton(socket.AF_INET, ip_address)
        except socket.error:
            raise ValueError("Invalid IPv4 address value provided: %s" % value)
        if netmask:
            if len(netmask.split('.')) == 4:
                try:
                    socket.inet_pton(socket.AF_INET, ip_address)
                except socket.error:
                    raise ValueError("Invalid netmask value provided: %s" % value)
            elif not 0 <= int(netmask) <= 32:
                raise ValueError("Invalid CIDR netmask value provided: %s" % value)
    else:
        try:
            socket.inet_pton(socket.AF_INET6, ip_address)
        except socket.error:
            raise ValueError("Invalid IPv6 address value provided: %s" % value)
        if netmask and not 0 <= int(netmask) <= 128:
            raise ValueError("Invalid netmask value provided: %s" % value)
    return value
