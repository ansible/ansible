Jinja2 'ipaddr()' filter
========================

.. versionadded:: 1.9

``ipaddr()`` is a Jinja2 filter designed to provide an interface to `netaddr`_
Python package from within Ansible. It can operate on strings or lists of
items, test various data to check if they are valid IP addresses and manipulate
the input data to extract requested information. ``ipaddr()`` works both with
IPv4 and IPv6 addresses in various forms, there are also additional functions
available to manipulate IP subnets and MAC addresses.

To use this filter in Ansible, you need to install `netaddr`_ Python library on
a computer on which you use Ansible (it is not required on remote hosts).
It can usually be installed either via your system package manager, or using
``pip``::

    pip install netaddr

.. _netaddr: https://pypi.python.org/pypi/netaddr

.. contents:: Topics
   :local:
   :depth: 2
   :backlinks: top

Basic tests
-----------

``ipaddr()`` is designed to return the input value if a query is True, and
``False`` if query is False. This way it can be very easily used in chained
filters. To use the filter, pass a string to it::

    {{ '192.0.2.0' | ipaddr }}

You can also pass the values as variables::

    {{ myvar | ipaddr }}

Here are some example tests of various input strings::

    # These values are valid IP addresses or network ranges
    '192.168.0.1'       -> 192.168.0.1
    '192.168.32.0/24'   -> 192.168.32.0/24
    'fe80::100/10'      -> fe80::100/10
    45443646733         -> ::a:94a7:50d
    '523454/24'         -> 0.7.252.190/24

    # Values that are not valid IP addresses or network ranges:
    'localhost'         -> False
    True                -> False
    'space bar'         -> False
    False               -> False
    ''                  -> False
    ':'                 -> False
    'fe80:/10'          -> False

Sometimes you need either IPv4 or IPv6 addresses. To filter only for particular
type, ``ipaddr()`` filter has two "aliases", ``ipv4()`` and ``ipv6()``.

Example us of an IPv4 filter::

    {{ myvar | ipv4 }}

And similar example of an IPv6 filter::

    {{ myvar | ipv6 }}

Here's an example test to look for IPv4 addresses::

    '192.168.0.1'       -> 192.168.0.1
    '192.168.32.0/24'   -> 192.168.32.0/24
    'fe80::100/10'      -> False
    45443646733         -> False
    '523454/24'         -> 0.7.252.190/24

And the same data filtered for IPv6 addresses::

    '192.168.0.1'       -> False
    '192.168.32.0/24'   -> False
    'fe80::100/10'      -> fe80::100/10
    45443646733         -> ::a:94a7:50d
    '523454/24'         -> False


Filtering lists
---------------

You can filter entire lists - ``ipaddr()`` will return a list with values
valid for a particular query::

    # Example list of values
    test_list = ['192.24.2.1', 'host.fqdn', '::1', '192.168.32.0/24', 'fe80::100/10', True, '', '42540766412265424405338506004571095040/64']

    # {{ test_list | ipaddr }}
    ['192.24.2.1', '::1', '192.168.32.0/24', 'fe80::100/10', '2001:db8:32c:faad::/64']

    # {{ test_list | ipv4 }}
    ['192.24.2.1', '192.168.32.0/24']

    # {{ test_list | ipv6 }}
    ['::1', 'fe80::100/10', '2001:db8:32c:faad::/64']


Wrapping IPv6 addresses in [ ] brackets
---------------------------------------

Some configuration files require IPv6 addresses to be "wrapped" in square
brackets (``[ ]``). To accomplish that, you can use ``ipwrap()`` filter. It
will wrap all IPv6 addresses and leave any other strings intact::

    # {{ test_list | ipwrap }}
    ['192.24.2.1', 'host.fqdn', '[::1]', '192.168.32.0/24', '[fe80::100]/10', True, '', '[2001:db8:32c:faad::]/64']

As you can see, ``ipwrap()`` did not filter out non-IP address values, which is
usually what you want when for example you are mixing IP addresses with
hostnames. If you still want to filter out all non-IP address values, you can
chain both filters together::

    # {{ test_list | ipaddr | ipwrap }}
    ['192.24.2.1', '[::1]', '192.168.32.0/24', '[fe80::100]/10', '[2001:db8:32c:faad::]/64']


Basic queries
-------------

You can provide single argument to each ``ipaddr()`` filter. Filter will then
treat it as a query and return values modified by that query. Lists will
contain only values that you are querying for.

Types of queries include:

- query by name: ``ipaddr('address')``, ``ipv4('network')``;
- query by CIDR range: ``ipaddr('192.168.0.0/24')``, ``ipv6('2001:db8::/32')``;
- query by index number: ``ipaddr('1')``, ``ipaddr('-1')``;

If a query type is not recognized, Ansible will raise an error.


Getting information about hosts and networks
--------------------------------------------

Here's our test list again::

    # Example list of values
    test_list = ['192.24.2.1', 'host.fqdn', '::1', '192.168.32.0/24', 'fe80::100/10', True, '', '42540766412265424405338506004571095040/64']

Lets take above list and get only those elements that are host IP addresses,
and not network ranges::

    # {{ test_list | ipaddr('address') }}
    ['192.24.2.1', '::1', 'fe80::100']

As you can see, even though some values had a host address with a CIDR prefix,
it was dropped by the filter. If you want host IP addresses with their correct
CIDR prefixes (as is common with IPv6 addressing), you can use
``ipaddr('host')`` filter::

    # {{ test_list | ipaddr('host') }}
    ['192.24.2.1/32', '::1/128', 'fe80::100/10']

Filtering by IP address types also works::

    # {{ test_list | ipv4('address') }}
    ['192.24.2.1']

    # {{ test_list | ipv6('address') }}
    ['::1', 'fe80::100']

You can check if IP addresses or network ranges are accessible on a public
Internet, or if they are in private networks::

    # {{ test_list | ipaddr('public') }}
    ['192.24.2.1', '2001:db8:32c:faad::/64']

    # {{ test_list | ipaddr('private') }}
    ['192.168.32.0/24', 'fe80::100/10']

You can check which values are specifically network ranges::

    # {{ test_list | ipaddr('net') }}
    ['192.168.32.0/24', '2001:db8:32c:faad::/64']

You can also check how many IP addresses can be in a certain range::

    # {{ test_list | ipaddr('net') | ipaddr('size') }}
    [256, 18446744073709551616L]

By specifying a network range as a query, you can check if given value is in
that range::

    # {{ test_list | ipaddr('192.0.0.0/8') }}
    ['192.24.2.1', '192.168.32.0/24']

If you specify a positive or negative integer as a query, ``ipaddr()`` will
treat this as an index and will return specific IP address from a network
range, in the 'host/prefix' format::

    # First IP address (network address)
    # {{ test_list | ipaddr('net') | ipaddr('0') }}
    ['192.168.32.0/24', '2001:db8:32c:faad::/64']

    # Second IP address (usually gateway host)
    # {{ test_list | ipaddr('net') | ipaddr('1') }}
    ['192.168.32.1/24', '2001:db8:32c:faad::1/64']

    # Last IP address (broadcast in IPv4 networks)
    # {{ test_list | ipaddr('net') | ipaddr('-1') }}
    ['192.168.32.255/24', '2001:db8:32c:faad:ffff:ffff:ffff:ffff/64']

You can also select IP addresses from a range by their index, from the start or
end of the range::

    # {{ test_list | ipaddr('net') | ipaddr('200') }}
    ['192.168.32.200/24', '2001:db8:32c:faad::c8/64']

    # {{ test_list | ipaddr('net') | ipaddr('-200') }}
    ['192.168.32.56/24', '2001:db8:32c:faad:ffff:ffff:ffff:ff38/64']

    # {{ test_list | ipaddr('net') | ipaddr('400') }}
    ['2001:db8:32c:faad::190/64']


Getting information from host/prefix values
-------------------------------------------

Very frequently you use combination of IP addresses and subnet prefixes
("CIDR"), this is even more common with IPv6. ``ipaddr()`` filter can extract
useful data from these prefixes.

Here's an example set of two host prefixes (with some "control" values)::

    host_prefix = ['2001:db8:deaf:be11::ef3/64', '192.0.2.48/24', '127.0.0.1', '192.168.0.0/16']

First, let's make sure that we only work with correct host/prefix values, not
just subnets or single IP addresses::

    # {{ test_list | ipaddr('host/prefix') }}
    ['2001:db8:deaf:be11::ef3/64', '192.0.2.48/24']

In Debian-based systems, network configuration stored in ``/etc/network/interfaces`` file uses combination of IP address, network address, netmask and broadcast address to configure IPv4 network interface. We can get these values from single 'host/prefix' combination::

    # Jinja2 template
    {% set ipv4_host = host_prefix | unique | ipv4('host/prefix') | first %}
    iface eth0 inet static
        address   {{ ipv4_host | ipaddr('address') }}
        network   {{ ipv4_host | ipaddr('network') }}
        netmask   {{ ipv4_host | ipaddr('netmask') }}
        broadcast {{ ipv4_host | ipaddr('broadcast') }}

    # Generated configuration file
    iface eth0 inet static
        address   192.0.2.48
        network   192.0.2.0
        netmask   255.255.255.0
        broadcast 192.0.2.255

In above example, we needed to handle the fact that values were stored in
a list, which is unusual in IPv4 networks, where only single IP address can be
set on an interface. However, IPv6 networks can have multiple IP addresses set
on an interface::

    # Jinja2 template
    iface eth0 inet6 static
      {% set ipv6_list = host_prefix | unique | ipv6('host/prefix') %}
      address {{ ipv6_list[0] }}
      {% if ipv6_list | length > 1 %}
      {% for subnet in ipv6_list[1:] %}
      up   /sbin/ip address add {{ subnet }} dev eth0
      down /sbin/ip address del {{ subnet }} dev eth0
      {% endfor %}
      {% endif %}

    # Generated configuration file
    iface eth0 inet6 static
      address 2001:db8:deaf:be11::ef3/64

If needed, you can extract subnet and prefix information from 'host/prefix' value::

    # {{ host_prefix | ipaddr('host/prefix') | ipaddr('subnet') }}
    ['2001:db8:deaf:be11::/64', '192.0.2.0/24']

    # {{ host_prefix | ipaddr('host/prefix') | ipaddr('prefix') }}
    [64, 24]

Converting subnet masks to CIDR notation
----------------------------------------

Given a subnet in the form of network address and subnet mask, it can be converted into CIDR notation using ``ipaddr()``.  This can be useful for converting Ansible facts gathered about network configuration from subnet masks into CIDR format::

    ansible_default_ipv4: {
        address: "192.168.0.11", 
        alias: "eth0", 
        broadcast: "192.168.0.255", 
        gateway: "192.168.0.1", 
        interface: "eth0", 
        macaddress: "fa:16:3e:c4:bd:89", 
        mtu: 1500, 
        netmask: "255.255.255.0", 
        network: "192.168.0.0", 
        type: "ether"
    }

First concatenate network and netmask::

    net_mask = "{{ ansible_default_ipv4.network }}/{{ ansible_default_ipv4.netmask }}"
    '192.168.0.0/255.255.255.0'

This result can be canonicalised with ``ipaddr()`` to produce a subnet in CIDR format::

    # {{ net_mask | ipaddr('prefix') }}
    '24'

    # {{ net_mask | ipaddr('net') }}
    '192.168.0.0/24'


IP address conversion
---------------------

Here's our test list again::

    # Example list of values
    test_list = ['192.24.2.1', 'host.fqdn', '::1', '192.168.32.0/24', 'fe80::100/10', True, '', '42540766412265424405338506004571095040/64']

You can convert IPv4 addresses into IPv6 addresses::

    # {{ test_list | ipv4('ipv6') }}
    ['::ffff:192.24.2.1/128', '::ffff:192.168.32.0/120']

Converting from IPv6 to IPv4 works very rarely::

    # {{ test_list | ipv6('ipv4') }}
    ['0.0.0.1/32']

But we can make double conversion if needed::

    # {{ test_list | ipaddr('ipv6') | ipaddr('ipv4') }}
    ['192.24.2.1/32', '0.0.0.1/32', '192.168.32.0/24']

You can convert IP addresses to integers, the same way that you can convert
integers into IP addresses::

    # {{ test_list | ipaddr('address') | ipaddr('int') }}
    [3222798849, 1, '3232243712/24', '338288524927261089654018896841347694848/10', '42540766412265424405338506004571095040/64']

You can convert IP addresses to PTR records::

    # {% for address in test_list | ipaddr %}
    # {{ address | ipaddr('revdns') }}
    # {% endfor %}
    1.2.24.192.in-addr.arpa.
    1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.ip6.arpa.
    0.32.168.192.in-addr.arpa.
    0.0.1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.8.e.f.ip6.arpa.
    0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.d.a.a.f.c.2.3.0.8.b.d.0.1.0.0.2.ip6.arpa.


Converting IPv4 address to 6to4 address
---------------------------------------

`6to4`_ tunnel is a way to access IPv6 Internet from IPv4-only network. If you
have a public IPv4 address, you automatically can configure it's IPv6
equivalent in ``2002::/16`` network range - after conversion you will gain
access to a ``2002:xxxx:xxxx::/48`` subnet which could be split into 65535
``/64`` subnets if needed.

To convert your IPv4 address, just send it through ``'6to4'`` filter. It will
be automatically converted to a router address (with ``::1/48`` host address)::

    # {{ '193.0.2.0' | ipaddr('6to4') }}
    2002:c100:0200::1/48

.. _6to4: https://en.wikipedia.org/wiki/6to4


Subnet manipulation
-------------------

``ipsubnet()`` filter can be used to manipulate network subnets in several ways.

Here is some example IP address and subnet::

    address = '192.168.144.5'
    subnet  = '192.168.0.0/16'

To check if a given string is a subnet, pass it through the filter without any
arguments. If given string is an IP address, it will be converted into
a subnet::

    # {{ address | ipsubnet }}
    192.168.144.5/32

    # {{ subnet | ipsubnet }}
    192.168.0.0/16

If you specify a subnet size as first parameter of ``ipsubnet()`` filter, and
subnet size is **smaller than current one**, you will get number of subnets
a given subnet can be split into::

    # {{ subnet | ipsubnet(20) }}
    16

Second argument of ``ipsubnet()`` filter is an index number; by specifying it
you can get new subnet with specified size::

    # First subnet
    # {{ subnet | ipsubnet(20, 0) }}
    192.168.0.0/20

    # Last subnet
    # {{ subnet | ipsubnet(20, -1) }}
    192.168.240.0/20

    # Fifth subnet
    # {{ subnet | ipsubnet(20, 5) }}
    192.168.80.0/20

    # Fifth to last subnet
    # {{ subnet | ipsubnet(20, -5) }}
    192.168.176.0/20

If you specify an IP address instead of a subnet, and give a subnet size as
a first argument, ``ipsubnet()`` filter will instead return biggest subnet that
contains a given IP address::

    # {{ address | ipsubnet(20) }}
    192.168.128.0/18

By specifying an index number as a second argument, you can select smaller and
smaller subnets::

    # First subnet
    # {{ subnet | ipsubnet(18, 0) }}
    192.168.128.0/18

    # Last subnet
    # {{ subnet | ipsubnet(18, -1) }}
    192.168.144.4/31

    # Fifth subnet
    # {{ subnet | ipsubnet(18, 5) }}
    192.168.144.0/23

    # Fifth to last subnet
    # {{ subnet | ipsubnet(18, -5) }}
    192.168.144.0/27

You can use ``ipsubnet()`` filter with ``ipaddr()`` filter to for example split
given ``/48`` prefix into smaller, ``/64`` subnets::

    # {{ '193.0.2.0' | ipaddr('6to4') | ipsubnet(64, 58820) | ipaddr('1') }}
    2002:c100:200:e5c4::1/64

Because of the size of IPv6 subnets, iteration over all of them to find the
correct one may take some time on slower computers, depending on the size
difference between subnets.


MAC address filter
------------------

You can use ``hwaddr()`` filter to check if a given string is a MAC address or
convert it between various formats. Examples::

    # Example MAC address
    macaddress = '1a:2b:3c:4d:5e:6f'

    # Check if given string is a MAC address
    # {{ macaddress | hwaddr }}
    1a:2b:3c:4d:5e:6f

    # Convert MAC address to PostgreSQL format
    # {{ macaddress | hwaddr('pgsql') }}
    1a2b3c:4d5e6f

    # Convert MAC address to Cisco format
    # {{ macaddress | hwaddr('cisco') }}
    1a2b.3c4d.5e6f

.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   :doc:`playbooks_filters`
       Introduction to Jinja2 filters and their uses
   :doc:`playbooks_conditionals`
       Conditional statements in playbooks
   :doc:`playbooks_variables`
       All about variables
   :doc:`playbooks_loops`
       Looping in playbooks
   :doc:`playbooks_roles`
       Playbook organization by roles
   :doc:`playbooks_best_practices`
       Best practices in playbooks
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel


