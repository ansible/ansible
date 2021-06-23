:orphan:

.. _playbooks_filters_ipaddr:

ipaddr filter
`````````````

.. versionadded:: 1.9

``ipaddr()`` is a Jinja2 filter designed to provide an interface to the `netaddr`_
Python package from within Ansible. It can operate on strings or lists of
items, test various data to check if they are valid IP addresses, and manipulate
the input data to extract requested information. ``ipaddr()`` works with both
IPv4 and IPv6 addresses in various forms. There are also additional functions
available to manipulate IP subnets and MAC addresses.

To use this filter in Ansible, you need to install the `netaddr`_ Python library on
a computer on which you use Ansible (it is not required on remote hosts).
It can usually be installed with either your system package manager or using
``pip``::

    pip install netaddr

.. _netaddr: https://pypi.org/project/netaddr/

.. contents:: Topics
   :local:
   :depth: 2
   :backlinks: top

Basic tests
^^^^^^^^^^^

``ipaddr()`` is designed to return the input value if a query is True, and
``False`` if a query is False. This way it can be easily used in chained
filters. To use the filter, pass a string to it:

.. code-block:: none

    {{ '192.0.2.0' | ipaddr }}

You can also pass the values as variables::

    {{ myvar | ipaddr }}

Here are some example test results of various input strings::

    # These values are valid IP addresses or network ranges
    '192.168.0.1'       -> 192.168.0.1
    '192.168.32.0/24'   -> 192.168.32.0/24
    'fe80::100/10'      -> fe80::100/10
    45443646733         -> ::a:94a7:50d
    '523454/24'         -> 0.7.252.190/24

    # Values that are not valid IP addresses or network ranges
    'localhost'         -> False
    True                -> False
    'space bar'         -> False
    False               -> False
    ''                  -> False
    ':'                 -> False
    'fe80:/10'          -> False

Sometimes you need either IPv4 or IPv6 addresses. To filter only for a particular
type, ``ipaddr()`` filter has two "aliases", ``ipv4()`` and ``ipv6()``.

Example use of an IPv4 filter::

    {{ myvar | ipv4 }}

A similar example of an IPv6 filter::

    {{ myvar | ipv6 }}

Here's some example test results to look for IPv4 addresses::

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
^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some configuration files require IPv6 addresses to be "wrapped" in square
brackets (``[ ]``). To accomplish that, you can use the ``ipwrap()`` filter. It
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
^^^^^^^^^^^^^

You can provide a single argument to each ``ipaddr()`` filter. The filter will then
treat it as a query and return values modified by that query. Lists will
contain only values that you are querying for.

Types of queries include:

- query by name: ``ipaddr('address')``, ``ipv4('network')``;
- query by CIDR range: ``ipaddr('192.168.0.0/24')``, ``ipv6('2001:db8::/32')``;
- query by index number: ``ipaddr('1')``, ``ipaddr('-1')``;

If a query type is not recognized, Ansible will raise an error.


Getting information about hosts and networks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here's our test list again::

    # Example list of values
    test_list = ['192.24.2.1', 'host.fqdn', '::1', '192.168.32.0/24', 'fe80::100/10', True, '', '42540766412265424405338506004571095040/64']

Let's take the list above and get only those elements that are host IP addresses
and not network ranges::

    # {{ test_list | ipaddr('address') }}
    ['192.24.2.1', '::1', 'fe80::100']

As you can see, even though some values had a host address with a CIDR prefix,
they were dropped by the filter. If you want host IP addresses with their correct
CIDR prefixes (as is common with IPv6 addressing), you can use the
``ipaddr('host')`` filter::

    # {{ test_list | ipaddr('host') }}
    ['192.24.2.1/32', '::1/128', 'fe80::100/10']

Filtering by IP address type also works::

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

By specifying a network range as a query, you can check if a given value is in
that range::

    # {{ test_list | ipaddr('192.0.0.0/8') }}
    ['192.24.2.1', '192.168.32.0/24']

If you specify a positive or negative integer as a query, ``ipaddr()`` will
treat this as an index and will return the specific IP address from a network
range, in the 'host/prefix' format::

    # First IP address (network address)
    # {{ test_list | ipaddr('net') | ipaddr('0') }}
    ['192.168.32.0/24', '2001:db8:32c:faad::/64']

    # Second IP address (usually the gateway host)
    # {{ test_list | ipaddr('net') | ipaddr('1') }}
    ['192.168.32.1/24', '2001:db8:32c:faad::1/64']

    # Last IP address (the broadcast address in IPv4 networks)
    # {{ test_list | ipaddr('net') | ipaddr('-1') }}
    ['192.168.32.255/24', '2001:db8:32c:faad:ffff:ffff:ffff:ffff/64']

You can also select IP addresses from a range by their index, from the start or
end of the range::

    # Returns from the start of the range
    # {{ test_list | ipaddr('net') | ipaddr('200') }}
    ['192.168.32.200/24', '2001:db8:32c:faad::c8/64']

    # Returns from the end of the range
    # {{ test_list | ipaddr('net') | ipaddr('-200') }}
    ['192.168.32.56/24', '2001:db8:32c:faad:ffff:ffff:ffff:ff38/64']

    # {{ test_list | ipaddr('net') | ipaddr('400') }}
    ['2001:db8:32c:faad::190/64']


Getting information from host/prefix values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You frequently use a combination of IP addresses and subnet prefixes
("CIDR"), this is even more common with IPv6. The ``ipaddr()`` filter can extract
useful data from these prefixes.

Here's an example set of two host prefixes (with some "control" values)::

    host_prefix = ['2001:db8:deaf:be11::ef3/64', '192.0.2.48/24', '127.0.0.1', '192.168.0.0/16']

First, let's make sure that we only work with correct host/prefix values, not
just subnets or single IP addresses::

    # {{ host_prefix | ipaddr('host/prefix') }}
    ['2001:db8:deaf:be11::ef3/64', '192.0.2.48/24']

In Debian-based systems, the network configuration stored in the ``/etc/network/interfaces`` file uses a combination of IP address, network address, netmask and broadcast address to configure an IPv4 network interface. We can get these values from a single 'host/prefix' combination:

.. code-block:: jinja

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

In the above example, we needed to handle the fact that values were stored in
a list, which is unusual in IPv4 networks, where only a single IP address can be
set on an interface. However, IPv6 networks can have multiple IP addresses set
on an interface::

  .. code-block:: jinja

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

If needed, you can extract subnet and prefix information from the 'host/prefix' value::

    # {{ host_prefix | ipaddr('host/prefix') | ipaddr('subnet') }}
    ['2001:db8:deaf:be11::/64', '192.0.2.0/24']

    # {{ host_prefix | ipaddr('host/prefix') | ipaddr('prefix') }}
    [64, 24]

Converting subnet masks to CIDR notation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Given a subnet in the form of network address and subnet mask, the ``ipaddr()`` filter can convert it into CIDR notation.  This can be useful for converting Ansible facts gathered about network configuration from subnet masks into CIDR format::

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

First concatenate the network and netmask::

    net_mask = "{{ ansible_default_ipv4.network }}/{{ ansible_default_ipv4.netmask }}"
    '192.168.0.0/255.255.255.0'

This result can be converted to canonical form with ``ipaddr()`` to produce a subnet in CIDR format::

    # {{ net_mask | ipaddr('prefix') }}
    '24'

    # {{ net_mask | ipaddr('net') }}
    '192.168.0.0/24'

Getting information about the network in CIDR notation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Given an IP address, the ``ipaddr()`` filter can produce the network address in CIDR notation.
This can be useful when you want to obtain the network address from the IP address in CIDR format.

Here's an example of IP address::

    ip_address = "{{ ansible_default_ipv4.address }}/{{ ansible_default_ipv4.netmask }}"
    '192.168.0.11/255.255.255.0'

This can be used to obtain the network address in CIDR notation format::

    # {{ ip_address | ipaddr('network/prefix') }}
    '192.168.0.0/24'

IP address conversion
^^^^^^^^^^^^^^^^^^^^^

Here's our test list again::

    # Example list of values
    test_list = ['192.24.2.1', 'host.fqdn', '::1', '192.168.32.0/24', 'fe80::100/10', True, '', '42540766412265424405338506004571095040/64']

You can convert IPv4 addresses into IPv6 addresses::

    # {{ test_list | ipv4('ipv6') }}
    ['::ffff:192.24.2.1/128', '::ffff:192.168.32.0/120']

Converting from IPv6 to IPv4 works very rarely::

    # {{ test_list | ipv6('ipv4') }}
    ['0.0.0.1/32']

But we can make a double conversion if needed::

    # {{ test_list | ipaddr('ipv6') | ipaddr('ipv4') }}
    ['192.24.2.1/32', '0.0.0.1/32', '192.168.32.0/24']

You can convert IP addresses to integers, the same way that you can convert
integers into IP addresses::

    # {{ test_list | ipaddr('address') | ipaddr('int') }}
    [3222798849, 1, '3232243712/24', '338288524927261089654018896841347694848/10', '42540766412265424405338506004571095040/64']

You can convert IPv4 address to `Hexadecimal notation <https://en.wikipedia.org/wiki/Hexadecimal>`_ with optional delimiter::

    # {{ '192.168.1.5' | ip4_hex }}
    c0a80105
    # {{ '192.168.1.5' | ip4_hex(':') }}
    c0:a8:01:05

You can convert IP addresses to PTR records::

    # {% for address in test_list | ipaddr %}
    # {{ address | ipaddr('revdns') }}
    # {% endfor %}
    1.2.24.192.in-addr.arpa.
    1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.ip6.arpa.
    0.32.168.192.in-addr.arpa.
    0.0.1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.8.e.f.ip6.arpa.
    0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.d.a.a.f.c.2.3.0.8.b.d.0.1.0.0.2.ip6.arpa.


Converting IPv4 address to a 6to4 address
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A `6to4`_ tunnel is a way to access the IPv6 Internet from an IPv4-only network. If you
have a public IPv4 address, you can automatically configure its IPv6
equivalent in the ``2002::/16`` network range. After conversion you will gain
access to a ``2002:xxxx:xxxx::/48`` subnet which could be split into 65535
``/64`` subnets if needed.

To convert your IPv4 address, just send it through the ``'6to4'`` filter. It will
be automatically converted to a router address (with a ``::1/48`` host address)::

    # {{ '193.0.2.0' | ipaddr('6to4') }}
    2002:c100:0200::1/48

.. _6to4: https://en.wikipedia.org/wiki/6to4

Finding IP addresses within a range
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To find usable IP addresses within an IP range, try these ``ipaddr`` filters:

To find the next usable IP address in a range, use ``next_usable`` ::

    # {{ '192.168.122.1/24' | ipaddr('next_usable') }}
    192.168.122.2

To find the last usable IP address from a range, use ``last_usable``::

    # {{ '192.168.122.1/24' | ipaddr('last_usable') }}
    192.168.122.254

To find the available range of IP addresses from the given network address, use ``range_usable``::

    # {{ '192.168.122.1/24' | ipaddr('range_usable') }}
    192.168.122.1-192.168.122.254

To find the next nth usable IP address within a range, use ``next_nth_usable``::

    # {{ '192.168.122.1/24' | next_nth_usable(2) }}
    192.168.122.3

In this example, ``next_nth_usable`` returns the second usable IP address for the given IP range.


IP Math
^^^^^^^

.. versionadded:: 2.7

The ``ipmath()`` filter can be used to do simple IP math/arithmetic.

Here are a few simple examples::

    # {{ '192.168.1.5' | ipmath(5) }}
    192.168.1.10

    # {{ '192.168.0.5' | ipmath(-10) }}
    192.167.255.251

    # {{ '192.168.1.1/24' | ipmath(5) }}
    192.168.1.6

    # {{ '192.168.1.6/24' | ipmath(-5) }}
    192.168.1.1

    # {{ '192.168.2.6/24' | ipmath(-10) }}
    192.168.1.252

    # {{ '2001::1' | ipmath(10) }}
    2001::b

    # {{ '2001::5' | ipmath(-10) }}
    2000:ffff:ffff:ffff:ffff:ffff:ffff:fffb



Subnet manipulation
^^^^^^^^^^^^^^^^^^^

The ``ipsubnet()`` filter can be used to manipulate network subnets in several ways.

Here is an example IP address and subnet::

    address = '192.168.144.5'
    subnet  = '192.168.0.0/16'

To check if a given string is a subnet, pass it through the filter without any
arguments. If the given string is an IP address, it will be converted into
a subnet::

    # {{ address | ipsubnet }}
    192.168.144.5/32

    # {{ subnet | ipsubnet }}
    192.168.0.0/16

If you specify a subnet size as the first parameter of the  ``ipsubnet()`` filter, and
the subnet size is **smaller than the current one**, you will get the number of subnets
a given subnet can be split into::

    # {{ subnet | ipsubnet(20) }}
    16

The second argument of the ``ipsubnet()`` filter is an index number; by specifying it
you can get a new subnet with the specified size::

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
the first argument, the ``ipsubnet()`` filter will instead return the biggest subnet that
contains that given IP address::

    # {{ address | ipsubnet(20) }}
    192.168.144.0/20

By specifying an index number as a second argument, you can select smaller and
smaller subnets::

    # First subnet
    # {{ address | ipsubnet(18, 0) }}
    192.168.128.0/18

    # Last subnet
    # {{ address | ipsubnet(18, -1) }}
    192.168.144.4/31

    # Fifth subnet
    # {{ address | ipsubnet(18, 5) }}
    192.168.144.0/23

    # Fifth to last subnet
    # {{ address | ipsubnet(18, -5) }}
    192.168.144.0/27

By specifying another subnet as a second argument, if the second subnet includes
the first, you can determine the rank of the first subnet in the second ::

    # The rank of the IP in the subnet (the IP is the 36870nth /32 of the subnet)
    # {{ address | ipsubnet(subnet) }}
    36870

    # The rank in the /24 that contain the address
    # {{ address | ipsubnet('192.168.144.0/24') }}
    6

    # An IP with the subnet in the first /30 in a /24
    # {{ '192.168.144.1/30' | ipsubnet('192.168.144.0/24') }}
    1

    # The fifth subnet /30 in a /24
    # {{ '192.168.144.16/30' | ipsubnet('192.168.144.0/24') }}
    5

If the second subnet doesn't include the first subnet, the ``ipsubnet()`` filter raises an error.


You can use the ``ipsubnet()`` filter with the ``ipaddr()`` filter to, for example, split
a given ``/48`` prefix into smaller ``/64`` subnets::

    # {{ '193.0.2.0' | ipaddr('6to4') | ipsubnet(64, 58820) | ipaddr('1') }}
    2002:c100:200:e5c4::1/64

Because of the size of IPv6 subnets, iteration over all of them to find the
correct one may take some time on slower computers, depending on the size
difference between the subnets.

Subnet Merging
^^^^^^^^^^^^^^

.. versionadded:: 2.6

The ``cidr_merge()`` filter can be used to merge subnets or individual addresses
into their minimal representation, collapsing overlapping subnets and merging
adjacent ones wherever possible::

    {{ ['192.168.0.0/17', '192.168.128.0/17', '192.168.128.1' ] | cidr_merge }}
    # => ['192.168.0.0/16']

    {{ ['192.168.0.0/24', '192.168.1.0/24', '192.168.3.0/24'] | cidr_merge }}
    # => ['192.168.0.0/23', '192.168.3.0/24']

Changing the action from 'merge' to 'span' will instead return the smallest
subnet which contains all of the inputs::

    {{ ['192.168.0.0/24', '192.168.3.0/24'] | cidr_merge('span') }}
    # => '192.168.0.0/22'

    {{ ['192.168.1.42', '192.168.42.1'] | cidr_merge('span') }}
    # => '192.168.0.0/18'

MAC address filter
^^^^^^^^^^^^^^^^^^

You can use the ``hwaddr()`` filter to check if a given string is a MAC address or
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

The supported formats result in the following conversions for the ``1a:2b:3c:4d:5e:6f`` MAC address::

    bare: 1A2B3C4D5E6F
    bool: True
    int: 28772997619311
    cisco: 1a2b.3c4d.5e6f
    eui48 or win: 1A-2B-3C-4D-5E-6F
    linux or unix: 1a:2b:3c:4d:5e:6f:
    pgsql, postgresql, or psql: 1a2b3c:4d5e6f

.. seealso::

   :ref:`about_playbooks`
       An introduction to playbooks
   :ref:`playbooks_filters`
       Introduction to Jinja2 filters and their uses
   :ref:`playbooks_conditionals`
       Conditional statements in playbooks
   :ref:`playbooks_variables`
       All about variables
   :ref:`playbooks_loops`
       Looping in playbooks
   :ref:`playbooks_reuse_roles`
       Playbook organization by roles
   :ref:`playbooks_best_practices`
       Best practices in playbooks
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.libera.chat <https://libera.chat/>`_
       #ansible IRC chat channel
