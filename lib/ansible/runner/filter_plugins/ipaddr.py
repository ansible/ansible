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

from ansible import errors

try:
    import netaddr
except Exception, e:
    raise errors.AnsibleFilterError('python-netaddr package is not installed')


# ---- IP address and network filters ----

def ipaddr(value, query = '', version = False, alias = 'ipaddr'):
    ''' Check if string is an IP address or network and filter it '''

    query_types = [ 'type', 'bool', 'int', 'version', 'size', 'address', 'ip', 'host', \
                    'network', 'subnet', 'prefix', 'broadcast', 'netmask', 'hostmask', \
                    'unicast', 'multicast', 'private', 'public', 'loopback', 'lo', \
                    'revdns', 'wrap', 'ipv6', 'v6', 'ipv4', 'v4', 'cidr', 'net', \
                    'hostnet', 'router', 'gateway', 'gw', 'host/prefix', 'address/prefix' ]

    if not value:
        return False

    elif value == True:
        return False

    # Check if value is a list and parse each element
    elif isinstance(value, (list, tuple)):

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

    v_ip = netaddr.IPAddress(str(v.ip))

    # We have a query string but it's not in the known query types. Check if
    # that string is a valid subnet, if so, we can check later if given IP
    # address/network is inside that specific subnet
    try:
        if query and query not in query_types and ipaddr(query, 'network'):
            iplist = netaddr.IPSet([netaddr.IPNetwork(query)])
            query = 'cidr_lookup'
    except:
        None

    # This code checks if value maches the IP version the user wants, ie. if
    # it's any version ("ipaddr()"), IPv4 ("ipv4()") or IPv6 ("ipv6()")
    # If version does not match, return False
    if version and v.version != version:
        return False

    # We don't have any query to process, so just check what type the user
    # expects, and return the IP address in a correct format
    if not query:
        if v:
            if vtype == 'address':
                return str(v.ip)
            elif vtype == 'network':
                return str(v)

    elif query == 'type':
        if v.size == 1:
            return 'address'
        if v.size > 1:
            if v.ip != v.network:
                return 'address'
            else:
                return 'network'

    elif query == 'bool':
        if v:
            return True

    elif query == 'int':
        if vtype == 'address':
            return int(v.ip)
        elif vtype == 'network':
            return str(int(v.ip)) + '/' + str(int(v.prefixlen))

    elif query == 'version':
        return v.version

    elif query == 'size':
        return v.size

    elif query in [ 'address', 'ip' ]:
        if v.size == 1:
            return str(v.ip)
        if v.size > 1:
            if v.ip != v.network:
                return str(v.ip)

    elif query == 'host':
        if v.size == 1:
            return str(v)
        elif v.size > 1:
            if v.ip != v.network:
                return str(v.ip) + '/' + str(v.prefixlen)

    elif query == 'net':
        if v.size > 1:
            if v.ip == v.network:
                return str(v.network) + '/' + str(v.prefixlen)

    elif query in [ 'hostnet', 'router', 'gateway', 'gw', 'host/prefix', 'address/prefix' ]:
        if v.size > 1:
            if v.ip != v.network:
                return str(v.ip) + '/' + str(v.prefixlen)

    elif query == 'network':
        if v.size > 1:
            return str(v.network)

    elif query == 'subnet':
        return str(v.cidr)

    elif query == 'cidr':
        return str(v)

    elif query == 'prefix':
        return int(v.prefixlen)

    elif query == 'broadcast':
        if v.size > 1:
            return str(v.broadcast)

    elif query == 'netmask':
        if v.size > 1:
            return str(v.netmask)

    elif query == 'hostmask':
        return str(v.hostmask)

    elif query == 'unicast':
        if v.is_unicast():
            return value

    elif query == 'multicast':
        if v.is_multicast():
            return value

    elif query == 'link-local':
        if v.version == 4:
            if ipaddr(str(v_ip), '169.254.0.0/24'):
                return value

        elif v.version == 6:
            if ipaddr(str(v_ip), 'fe80::/10'):
                return value

    elif query == 'private':
        if v.is_private():
            return value

    elif query == 'public':
        if v_ip.is_unicast() and not v_ip.is_private() and \
            not v_ip.is_loopback() and not v_ip.is_netmask() and \
            not v_ip.is_hostmask():
            return value

    elif query in [ 'loopback', 'lo' ]:
        if v_ip.is_loopback():
            return value

    elif query == 'revdns':
            return v_ip.reverse_dns

    elif query == 'wrap':
        if v.version == 6:
            if vtype == 'address':
                return '[' + str(v.ip) + ']'
            elif vtype == 'network':
                return '[' + str(v.ip) + ']/' + str(v.prefixlen)
        else:
            return value

    elif query in [ 'ipv6', 'v6' ]:
        if v.version == 4:
            return str(v.ipv6())
        else:
            return value

    elif query in [ 'ipv4', 'v4' ]:
        if v.version == 6:
            try:
                return str(v.ipv4())
            except:
                return False
        else:
            return value

    elif query == '6to4':

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

    elif query == 'cidr_lookup':
        try:
            if v in iplist:
                return value
        except:
            return False

    else:
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


def ipwrap(value, query = ''):
    try:
        if isinstance(value, (list, tuple)):
            _ret = []
            for element in value:
                if ipaddr(element, query, version = False, alias = 'ipwrap'):
                    _ret.append(ipaddr(element, 'wrap'))
                else:
                    _ret.append(element)

            return _ret
        else:
            _ret = ipaddr(value, query, version = False, alias = 'ipwrap')
            if _ret:
                return ipaddr(_ret, 'wrap')
            else:
                return value

    except:
        return value


def ipv4(value, query = ''):
    return ipaddr(value, query, version = 4, alias = 'ipv4')


def ipv6(value, query = ''):
    return ipaddr(value, query, version = 6, alias = 'ipv6')


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
def ipsubnet(value, query = '', index = 'x'):
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


# ---- HWaddr / MAC address filters ----

def hwaddr(value, query = '', alias = 'hwaddr'):
    ''' Check if string is a HW/MAC address and filter it '''

    try:
        v = netaddr.EUI(value)
    except:
        if query and query not in [ 'bool' ]:
            raise errors.AnsibleFilterError(alias + ': not a hardware address: %s' % value)

    if not query:
        if v:
            return value

    elif query == 'bool':
        if v:
            return True

    elif query in [ 'win', 'eui48' ]:
        v.dialect = netaddr.mac_eui48
        return str(v)

    elif query == 'unix':
        v.dialect = netaddr.mac_unix
        return str(v)

    elif query in [ 'pgsql', 'postgresql', 'psql' ]:
        v.dialect = netaddr.mac_pgsql
        return str(v)

    elif query == 'cisco':
        v.dialect = netaddr.mac_cisco
        return str(v)

    elif query == 'bare':
        v.dialect = netaddr.mac_bare
        return str(v)

    elif query == 'linux':
        v.dialect = mac_linux
        return str(v)

    else:
        raise errors.AnsibleFilterError(alias + ': unknown filter type: %s' % query)

    return False

class mac_linux(netaddr.mac_unix): pass
mac_linux.word_fmt = '%.2x'


def macaddr(value, query = ''):
    return hwaddr(value, query, alias = 'macaddr')


# ---- Ansible filters ----

class FilterModule(object):
    ''' IP address and network manipulation filters '''

    def filters(self):
        return {

            # IP addresses and networks
            'ipaddr': ipaddr,
            'ipwrap': ipwrap,
            'ipv4': ipv4,
            'ipv6': ipv6,
            'ipsubnet': ipsubnet,

            # MAC / HW addresses
            'hwaddr': hwaddr,
            'macaddr': macaddr

        }

