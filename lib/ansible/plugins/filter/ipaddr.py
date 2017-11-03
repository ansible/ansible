# (c) 2014, Maciej Delmanowski <drybjed@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from functools import partial
import types

try:
    import netaddr
except ImportError:
    # in this case, we'll make the filters return error messages (see bottom)
    netaddr = None
else:
    class mac_linux(netaddr.mac_unix):
        pass
    mac_linux.word_fmt = '%.2x'

from ansible import errors


# ---- IP address and network query helpers ----
def _empty_ipaddr_query(v, vtype):
    # We don't have any query to process, so just check what type the user
    # expects, and return the IP address in a correct format
    if v:
        if vtype == 'address':
            return str(v.ip)
        elif vtype == 'network':
            return str(v)


def _first_last(v):
    if v.size == 2:
        first_usable = int(netaddr.IPAddress(v.first))
        last_usable = int(netaddr.IPAddress(v.last))
        return first_usable, last_usable
    elif v.size > 1:
        first_usable = int(netaddr.IPAddress(v.first + 1))
        last_usable = int(netaddr.IPAddress(v.last - 1))
        return first_usable, last_usable


def _6to4_query(v, vtype, value):
    if v.version == 4:

        if v.size == 1:
            ipconv = str(v.ip)
        elif v.size > 1:
            if v.ip != v.network:
                ipconv = str(v.ip)
            else:
                ipconv = False

        if ipaddr(ipconv, 'public'):
            numbers = list(map(int, ipconv.split('.')))

        try:
            return '2002:{:02x}{:02x}:{:02x}{:02x}::1/48'.format(*numbers)
        except:
            return False

    elif v.version == 6:
        if vtype == 'address':
            if ipaddr(str(v), '2002::/16'):
                return value
        elif vtype == 'network':
            if v.ip != v.network:
                if ipaddr(str(v.ip), '2002::/16'):
                    return value
            else:
                return False


def _ip_query(v):
    if v.size == 1:
        return str(v.ip)
    if v.size > 1:
        # /31 networks in netaddr have no broadcast address
        if v.ip != v.network or not v.broadcast:
            return str(v.ip)


def _gateway_query(v):
    if v.size > 1:
        if v.ip != v.network:
            return str(v.ip) + '/' + str(v.prefixlen)


def _address_prefix_query(v):
    if v.size > 1:
        if v.ip != v.network:
            return str(v.ip) + '/' + str(v.prefixlen)


def _bool_ipaddr_query(v):
    if v:
        return True


def _broadcast_query(v):
    if v.size > 2:
        return str(v.broadcast)


def _cidr_query(v):
    return str(v)


def _cidr_lookup_query(v, iplist, value):
    try:
        if v in iplist:
            return value
    except:
        return False


def _first_usable_query(v, vtype):
    if vtype == 'address':
        "Does it make sense to raise an error"
        raise errors.AnsibleFilterError('Not a network address')
    elif vtype == 'network':
        if v.size == 2:
            return str(netaddr.IPAddress(int(v.network)))
        elif v.size > 1:
            return str(netaddr.IPAddress(int(v.network) + 1))


def _host_query(v):
    if v.size == 1:
        return str(v)
    elif v.size > 1:
        if v.ip != v.network:
            return str(v.ip) + '/' + str(v.prefixlen)


def _hostmask_query(v):
    return str(v.hostmask)


def _int_query(v, vtype):
    if vtype == 'address':
        return int(v.ip)
    elif vtype == 'network':
        return str(int(v.ip)) + '/' + str(int(v.prefixlen))


def _ip_prefix_query(v):
    if v.size == 2:
        return str(v.ip) + '/' + str(v.prefixlen)
    elif v.size > 1:
        if v.ip != v.network:
            return str(v.ip) + '/' + str(v.prefixlen)


def _ip_netmask_query(v):
    if v.size == 2:
        return str(v.ip) + ' ' + str(v.netmask)
    elif v.size > 1:
        if v.ip != v.network:
            return str(v.ip) + ' ' + str(v.netmask)

'''
def _ip_wildcard_query(v):
    if v.size == 2:
        return str(v.ip) + ' ' + str(v.hostmask)
    elif v.size > 1:
        if v.ip != v.network:
            return str(v.ip) + ' ' + str(v.hostmask)
'''


def _ipv4_query(v, value):
    if v.version == 6:
        try:
            return str(v.ipv4())
        except:
            return False
    else:
        return value


def _ipv6_query(v, value):
    if v.version == 4:
        return str(v.ipv6())
    else:
        return value


def _last_usable_query(v, vtype):
    if vtype == 'address':
        "Does it make sense to raise an error"
        raise errors.AnsibleFilterError('Not a network address')
    elif vtype == 'network':
        if v.size > 1:
            first_usable, last_usable = _first_last(v)
            return str(netaddr.IPAddress(last_usable))


def _link_local_query(v, value):
    v_ip = netaddr.IPAddress(str(v.ip))
    if v.version == 4:
        if ipaddr(str(v_ip), '169.254.0.0/24'):
            return value

    elif v.version == 6:
        if ipaddr(str(v_ip), 'fe80::/10'):
            return value


def _loopback_query(v, value):
    v_ip = netaddr.IPAddress(str(v.ip))
    if v_ip.is_loopback():
        return value


def _multicast_query(v, value):
    if v.is_multicast():
        return value


def _net_query(v):
    if v.size > 1:
        if v.ip == v.network:
            return str(v.network) + '/' + str(v.prefixlen)


def _netmask_query(v):
    return str(v.netmask)


def _network_query(v):
    '''Return the network of a given IP or subnet'''
    if v.size > 1:
        return str(v.network)


def _network_id_query(v):
    '''Return the network of a given IP or subnet'''
    return str(v.network)


def _network_netmask_query(v):
    return str(v.network) + ' ' + str(v.netmask)


def _network_wildcard_query(v):
    return str(v.network) + ' ' + str(v.hostmask)


def _next_usable_query(v, vtype):
    if vtype == 'address':
        "Does it make sense to raise an error"
        raise errors.AnsibleFilterError('Not a network address')
    elif vtype == 'network':
        if v.size > 1:
            first_usable, last_usable = _first_last(v)
            next_ip = int(netaddr.IPAddress(int(v.ip) + 1))
            if next_ip >= first_usable and next_ip <= last_usable:
                return str(netaddr.IPAddress(int(v.ip) + 1))


def _prefix_query(v):
    return int(v.prefixlen)


def _previous_usable_query(v, vtype):
    if vtype == 'address':
        "Does it make sense to raise an error"
        raise errors.AnsibleFilterError('Not a network address')
    elif vtype == 'network':
        if v.size > 1:
            first_usable, last_usable = _first_last(v)
            previous_ip = int(netaddr.IPAddress(int(v.ip) - 1))
            if previous_ip >= first_usable and previous_ip <= last_usable:
                return str(netaddr.IPAddress(int(v.ip) - 1))


def _private_query(v, value):
    if v.is_private():
        return value


def _public_query(v, value):
    v_ip = netaddr.IPAddress(str(v.ip))
    if (v_ip.is_unicast() and not v_ip.is_private() and
            not v_ip.is_loopback() and not v_ip.is_netmask() and
            not v_ip.is_hostmask()):
        return value


def _range_usable_query(v, vtype):
    if vtype == 'address':
        "Does it make sense to raise an error"
        raise errors.AnsibleFilterError('Not a network address')
    elif vtype == 'network':
        if v.size > 1:
            first_usable, last_usable = _first_last(v)
            first_usable = str(netaddr.IPAddress(first_usable))
            last_usable = str(netaddr.IPAddress(last_usable))
            return "{0}-{1}".format(first_usable, last_usable)


def _revdns_query(v):
    v_ip = netaddr.IPAddress(str(v.ip))
    return v_ip.reverse_dns


def _size_query(v):
    return v.size


def _size_usable_query(v):
    if v.size == 1:
        return 0
    elif v.size == 2:
        return 2
    return v.size - 2


def _subnet_query(v):
    return str(v.cidr)


def _type_query(v):
    if v.size == 1:
        return 'address'
    if v.size > 1:
        if v.ip != v.network:
            return 'address'
        else:
            return 'network'


def _unicast_query(v, value):
    if v.is_unicast():
        return value


def _version_query(v):
    return v.version


def _wrap_query(v, vtype, value):
    if v.version == 6:
        if vtype == 'address':
            return '[' + str(v.ip) + ']'
        elif vtype == 'network':
            return '[' + str(v.ip) + ']/' + str(v.prefixlen)
    else:
        return value


# ---- HWaddr query helpers ----
def _bare_query(v):
    v.dialect = netaddr.mac_bare
    return str(v)


def _bool_hwaddr_query(v):
    if v:
        return True


def _int_hwaddr_query(v):
    return int(v)


def _cisco_query(v):
    v.dialect = netaddr.mac_cisco
    return str(v)


def _empty_hwaddr_query(v, value):
    if v:
        return value


def _linux_query(v):
    v.dialect = mac_linux
    return str(v)


def _postgresql_query(v):
    v.dialect = netaddr.mac_pgsql
    return str(v)


def _unix_query(v):
    v.dialect = netaddr.mac_unix
    return str(v)


def _win_query(v):
    v.dialect = netaddr.mac_eui48
    return str(v)


# ---- IP address and network filters ----
def ipaddr(value, query='', version=False, alias='ipaddr'):
    ''' Check if string is an IP address or network and filter it '''

    query_func_extra_args = {
        '': ('vtype',),
        '6to4': ('vtype', 'value'),
        'cidr_lookup': ('iplist', 'value'),
        'first_usable': ('vtype',),
        'int': ('vtype',),
        'ipv4': ('value',),
        'ipv6': ('value',),
        'last_usable': ('vtype',),
        'link-local': ('value',),
        'loopback': ('value',),
        'lo': ('value',),
        'multicast': ('value',),
        'next_usable': ('vtype',),
        'previous_usable': ('vtype',),
        'private': ('value',),
        'public': ('value',),
        'unicast': ('value',),
        'range_usable': ('vtype',),
        'wrap': ('vtype', 'value'),
    }

    query_func_map = {
        '': _empty_ipaddr_query,
        '6to4': _6to4_query,
        'address': _ip_query,
        'address/prefix': _address_prefix_query,  # deprecate
        'bool': _bool_ipaddr_query,
        'broadcast': _broadcast_query,
        'cidr': _cidr_query,
        'cidr_lookup': _cidr_lookup_query,
        'first_usable': _first_usable_query,
        'gateway': _gateway_query,  # deprecate
        'gw': _gateway_query,  # deprecate
        'host': _host_query,
        'host/prefix': _address_prefix_query,  # deprecate
        'hostmask': _hostmask_query,
        'hostnet': _gateway_query,  # deprecate
        'int': _int_query,
        'ip': _ip_query,
        'ip/prefix': _ip_prefix_query,
        'ip_netmask': _ip_netmask_query,
        # 'ip_wildcard': _ip_wildcard_query, built then could not think of use case
        'ipv4': _ipv4_query,
        'ipv6': _ipv6_query,
        'last_usable': _last_usable_query,
        'link-local': _link_local_query,
        'lo': _loopback_query,
        'loopback': _loopback_query,
        'multicast': _multicast_query,
        'net': _net_query,
        'next_usable': _next_usable_query,
        'netmask': _netmask_query,
        'network': _network_query,
        'network_id': _network_id_query,
        'network/prefix': _subnet_query,
        'network_netmask': _network_netmask_query,
        'network_wildcard': _network_wildcard_query,
        'prefix': _prefix_query,
        'previous_usable': _previous_usable_query,
        'private': _private_query,
        'public': _public_query,
        'range_usable': _range_usable_query,
        'revdns': _revdns_query,
        'router': _gateway_query,  # deprecate
        'size': _size_query,
        'size_usable': _size_usable_query,
        'subnet': _subnet_query,
        'type': _type_query,
        'unicast': _unicast_query,
        'v4': _ipv4_query,
        'v6': _ipv6_query,
        'version': _version_query,
        'wildcard': _hostmask_query,
        'wrap': _wrap_query,
    }

    vtype = None

    if not value:
        return False

    elif value is True:
        return False

    # Check if value is a list and parse each element
    elif isinstance(value, (list, tuple, types.GeneratorType)):

        _ret = []
        for element in value:
            if ipaddr(element, str(query), version):
                _ret.append(ipaddr(element, str(query), version))

        if _ret:
            return _ret
        else:
            return list()

    # Check if value is a number and convert it to an IP address
    elif str(value).isdigit():

        # We don't know what IP version to assume, so let's check IPv4 first,
        # then IPv6
        try:
            if ((not version) or (version and version == 4)):
                v = netaddr.IPNetwork('0.0.0.0/0')
                v.value = int(value)
                v.prefixlen = 32
            elif version and version == 6:
                v = netaddr.IPNetwork('::/0')
                v.value = int(value)
                v.prefixlen = 128

        # IPv4 didn't work the first time, so it definitely has to be IPv6
        except:
            try:
                v = netaddr.IPNetwork('::/0')
                v.value = int(value)
                v.prefixlen = 128

            # The value is too big for IPv6. Are you a nanobot?
            except:
                return False

        # We got an IP address, let's mark it as such
        value = str(v)
        vtype = 'address'

    # value has not been recognized, check if it's a valid IP string
    else:
        try:
            v = netaddr.IPNetwork(value)

            # value is a valid IP string, check if user specified
            # CIDR prefix or just an IP address, this will indicate default
            # output format
            try:
                address, prefix = value.split('/')
                vtype = 'network'
            except:
                vtype = 'address'

        # value hasn't been recognized, maybe it's a numerical CIDR?
        except:
            try:
                address, prefix = value.split('/')
                address.isdigit()
                address = int(address)
                prefix.isdigit()
                prefix = int(prefix)

            # It's not numerical CIDR, give up
            except:
                return False

            # It is something, so let's try and build a CIDR from the parts
            try:
                v = netaddr.IPNetwork('0.0.0.0/0')
                v.value = address
                v.prefixlen = prefix

            # It's not a valid IPv4 CIDR
            except:
                try:
                    v = netaddr.IPNetwork('::/0')
                    v.value = address
                    v.prefixlen = prefix

                # It's not a valid IPv6 CIDR. Give up.
                except:
                    return False

            # We have a valid CIDR, so let's write it in correct format
            value = str(v)
            vtype = 'network'

    # We have a query string but it's not in the known query types. Check if
    # that string is a valid subnet, if so, we can check later if given IP
    # address/network is inside that specific subnet
    try:
        # ?? 6to4 and link-local were True here before.  Should they still?
        if query and (query not in query_func_map or query == 'cidr_lookup') and ipaddr(query, 'network'):
            iplist = netaddr.IPSet([netaddr.IPNetwork(query)])
            query = 'cidr_lookup'
    except:
        pass

    # This code checks if value maches the IP version the user wants, ie. if
    # it's any version ("ipaddr()"), IPv4 ("ipv4()") or IPv6 ("ipv6()")
    # If version does not match, return False
    if version and v.version != version:
        return False

    extras = []
    for arg in query_func_extra_args.get(query, tuple()):
        extras.append(locals()[arg])
    try:
        return query_func_map[query](v, *extras)
    except KeyError:
        try:
            float(query)
            if v.size == 1:
                if vtype == 'address':
                    return str(v.ip)
                elif vtype == 'network':
                    return str(v)

            elif v.size > 1:
                try:
                    return str(v[query]) + '/' + str(v.prefixlen)
                except:
                    return False

            else:
                return value

        except:
            raise errors.AnsibleFilterError(alias + ': unknown filter type: %s' % query)

    return False


def ipwrap(value, query=''):
    try:
        if isinstance(value, (list, tuple, types.GeneratorType)):
            _ret = []
            for element in value:
                if ipaddr(element, query, version=False, alias='ipwrap'):
                    _ret.append(ipaddr(element, 'wrap'))
                else:
                    _ret.append(element)

            return _ret
        else:
            _ret = ipaddr(value, query, version=False, alias='ipwrap')
            if _ret:
                return ipaddr(_ret, 'wrap')
            else:
                return value

    except:
        return value


def ipv4(value, query=''):
    return ipaddr(value, query, version=4, alias='ipv4')


def ipv6(value, query=''):
    return ipaddr(value, query, version=6, alias='ipv6')


# Split given subnet into smaller subnets or find out the biggest subnet of
# a given IP address with given CIDR prefix
# Usage:
#
#  - address or address/prefix | ipsubnet
#      returns CIDR subnet of a given input
#
#  - address/prefix | ipsubnet(cidr)
#      returns number of possible subnets for given CIDR prefix
#
#  - address/prefix | ipsubnet(cidr, index)
#      returns new subnet with given CIDR prefix
#
#  - address | ipsubnet(cidr)
#      returns biggest subnet with given CIDR prefix that address belongs to
#
#  - address | ipsubnet(cidr, index)
#      returns next indexed subnet which contains given address
def ipsubnet(value, query='', index='x'):
    ''' Manipulate IPv4/IPv6 subnets '''

    try:
        vtype = ipaddr(value, 'type')
        if vtype == 'address':
            v = ipaddr(value, 'cidr')
        elif vtype == 'network':
            v = ipaddr(value, 'subnet')

        value = netaddr.IPNetwork(v)
    except:
        return False

    if not query:
        return str(value)

    elif str(query).isdigit():
        vsize = ipaddr(v, 'size')
        query = int(query)

        try:
            float(index)
            index = int(index)

            if vsize > 1:
                try:
                    return str(list(value.subnet(query))[index])
                except:
                    return False

            elif vsize == 1:
                try:
                    return str(value.supernet(query)[index])
                except:
                    return False

        except:
            if vsize > 1:
                try:
                    return str(len(list(value.subnet(query))))
                except:
                    return False

            elif vsize == 1:
                try:
                    return str(value.supernet(query)[0])
                except:
                    return False

    return False


# Returns the nth host within a network described by value.
# Usage:
#
#  - address or address/prefix | nthhost(nth)
#      returns the nth host within the given network
def nthhost(value, query=''):
    ''' Get the nth host within a given network '''
    try:
        vtype = ipaddr(value, 'type')
        if vtype == 'address':
            v = ipaddr(value, 'cidr')
        elif vtype == 'network':
            v = ipaddr(value, 'subnet')

        value = netaddr.IPNetwork(v)
    except:
        return False

    if not query:
        return False

    try:
        nth = int(query)
        if value.size > nth:
            return value[nth]

    except ValueError:
        return False

    return False


# Returns the next nth usable ip within a network described by value.
def next_nth_usable(value, offset):
    try:
        vtype = ipaddr(value, 'type')
        if vtype == 'address':
            v = ipaddr(value, 'cidr')
        elif vtype == 'network':
            v = ipaddr(value, 'subnet')

        v = netaddr.IPNetwork(v)
    except:
        return False

    if type(offset) != int:
        raise errors.AnsibleFilterError('Must pass in an interger')
    if v.size > 1:
        first_usable, last_usable = _first_last(v)
        nth_ip = int(netaddr.IPAddress(int(v.ip) + offset))
        if nth_ip >= first_usable and nth_ip <= last_usable:
            return str(netaddr.IPAddress(int(v.ip) + offset))


# Returns the previous nth usable ip within a network described by value.
def previous_nth_usable(value, offset):
    try:
        vtype = ipaddr(value, 'type')
        if vtype == 'address':
            v = ipaddr(value, 'cidr')
        elif vtype == 'network':
            v = ipaddr(value, 'subnet')

        v = netaddr.IPNetwork(v)
    except:
        return False

    if type(offset) != int:
        raise errors.AnsibleFilterError('Must pass in an interger')
    if v.size > 1:
        first_usable, last_usable = _first_last(v)
        nth_ip = int(netaddr.IPAddress(int(v.ip) - offset))
        if nth_ip >= first_usable and nth_ip <= last_usable:
            return str(netaddr.IPAddress(int(v.ip) - offset))


def _range_checker(ip_check, first, last):
    '''
    Tests whether an ip address is within the bounds of the first and last address.

    :param ip_check: The ip to test if it is within first and last.
    :param first: The first IP in the range to test against.
    :param last: The last IP in the range to test against.

    :return: bool
    '''
    if ip_check >= first and ip_check <= last:
        return True
    else:
        return False


def _address_normalizer(value):
    '''
    Used to validate an address or network type and return it in a consistent format.
    This is being used for future use cases not currently available such as an address range.

    :param value: The string representation of an address or network.

    :return: The address or network in the normalized form.
    '''
    try:
        vtype = ipaddr(value, 'type')
        if vtype == 'address' or vtype == "network":
            v = ipaddr(value, 'subnet')
    except:
        return False

    return v


def network_in_usable(value, test):
    '''
    Checks whether 'test' is a useable address or addresses in 'value'

    :param: value: The string representation of an address or network to test against.
    :param test: The string representation of an address or network to validate if it is within the range of 'value'.

    :return: bool
    '''
    # normalize value and test variables into an ipaddr
    v = _address_normalizer(value)
    w = _address_normalizer(test)

    # get first and last addresses as integers to compare value and test; or cathes value when case is /32
    v_first = ipaddr(ipaddr(v, 'first_usable') or ipaddr(v, 'address'), 'int')
    v_last = ipaddr(ipaddr(v, 'last_usable') or ipaddr(v, 'address'), 'int')
    w_first = ipaddr(ipaddr(w, 'network') or ipaddr(w, 'address'), 'int')
    w_last = ipaddr(ipaddr(w, 'broadcast') or ipaddr(w, 'address'), 'int')

    if _range_checker(w_first, v_first, v_last) and _range_checker(w_last, v_first, v_last):
        return True
    else:
        return False


def network_in_network(value, test):
    '''
    Checks whether the 'test' address or addresses are in 'value', including broadcast and network

    :param: value: The network address or range to test against.
    :param test: The address or network to validate if it is within the range of 'value'.

    :return: bool
    '''
    # normalize value and test variables into an ipaddr
    v = _address_normalizer(value)
    w = _address_normalizer(test)

    # get first and last addresses as integers to compare value and test; or cathes value when case is /32
    v_first = ipaddr(ipaddr(v, 'network') or ipaddr(v, 'address'), 'int')
    v_last = ipaddr(ipaddr(v, 'broadcast') or ipaddr(v, 'address'), 'int')
    w_first = ipaddr(ipaddr(w, 'network') or ipaddr(w, 'address'), 'int')
    w_last = ipaddr(ipaddr(w, 'broadcast') or ipaddr(w, 'address'), 'int')

    if _range_checker(w_first, v_first, v_last) and _range_checker(w_last, v_first, v_last):
        return True
    else:
        return False


# Returns the SLAAC address within a network for a given HW/MAC address.
# Usage:
#
#  - prefix | slaac(mac)
def slaac(value, query=''):
    ''' Get the SLAAC address within given network '''
    try:
        vtype = ipaddr(value, 'type')
        if vtype == 'address':
            v = ipaddr(value, 'cidr')
        elif vtype == 'network':
            v = ipaddr(value, 'subnet')

        if ipaddr(value, 'version') != 6:
            return False

        value = netaddr.IPNetwork(v)
    except:
        return False

    if not query:
        return False

    try:
        mac = hwaddr(query, alias='slaac')

        eui = netaddr.EUI(mac)
    except:
        return False

    return eui.ipv6(value.network)


# ---- HWaddr / MAC address filters ----
def hwaddr(value, query='', alias='hwaddr'):
    ''' Check if string is a HW/MAC address and filter it '''

    query_func_extra_args = {
        '': ('value',),
    }

    query_func_map = {
        '': _empty_hwaddr_query,
        'bare': _bare_query,
        'bool': _bool_hwaddr_query,
        'int': _int_hwaddr_query,
        'cisco': _cisco_query,
        'eui48': _win_query,
        'linux': _linux_query,
        'pgsql': _postgresql_query,
        'postgresql': _postgresql_query,
        'psql': _postgresql_query,
        'unix': _unix_query,
        'win': _win_query,
    }

    try:
        v = netaddr.EUI(value)
    except:
        if query and query != 'bool':
            raise errors.AnsibleFilterError(alias + ': not a hardware address: %s' % value)

    extras = []
    for arg in query_func_extra_args.get(query, tuple()):
        extras.append(locals()[arg])
    try:
        return query_func_map[query](v, *extras)
    except KeyError:
        raise errors.AnsibleFilterError(alias + ': unknown filter type: %s' % query)

    return False


def macaddr(value, query=''):
    return hwaddr(value, query, alias='macaddr')


def _need_netaddr(f_name, *args, **kwargs):
    raise errors.AnsibleFilterError('The %s filter requires python-netaddr be '
                                    'installed on the ansible controller' % f_name)


def ip4_hex(arg):
    ''' Convert an IPv4 address to Hexadecimal notation '''
    numbers = list(map(int, arg.split('.')))
    return '{:02x}{:02x}{:02x}{:02x}'.format(*numbers)


# ---- Ansible filters ----
class FilterModule(object):
    ''' IP address and network manipulation filters '''
    filter_map = {
        # IP addresses and networks
        'ipaddr': ipaddr,
        'ipwrap': ipwrap,
        'ip4_hex': ip4_hex,
        'ipv4': ipv4,
        'ipv6': ipv6,
        'ipsubnet': ipsubnet,
        'next_nth_usable': next_nth_usable,
        'network_in_network': network_in_network,
        'network_in_usable': network_in_usable,
        'nthhost': nthhost,
        'previous_nth_usable': previous_nth_usable,
        'slaac': slaac,

        # MAC / HW addresses
        'hwaddr': hwaddr,
        'macaddr': macaddr
    }

    def filters(self):
        if netaddr:
            return self.filter_map
        else:
            # Need to install python-netaddr for these filters to work
            return dict((f, partial(_need_netaddr, f)) for f in self.filter_map)
