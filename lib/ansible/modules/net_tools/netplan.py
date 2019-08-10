#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, Luis Eduardo <leduardo@lsd.ufcg.edu.br>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: netplan
author:
    - Luis Eduardo (@lets00)
short_description: Manage network configurations using netplan.
version_added: "2.9"
description:
    - This module allows to you manage network configurations using netplan.
      It creates/edits a netplan YAML file, saves on /etc/netplan/ directory
      and apply the YAML files on system (neplan apply).

requirements: [ PyYAML, netplan ]
notes:
    - Introduction to Netplan U(https://github.com/CanonicalLtd/netplan/blob/master/doc/netplan.md)
options:
  filename:
    description:
      - Name of file that will be create or open to add/remove network
        interfaces.
    required: true
    type: str

  renderer:
    description:
      - Network backend to use for this definition. Currently supported
        are C(networkd)(default) and C(NetworkManager).
    choices: [ networkd, NetworkManager ]
    required: false
    type: str

  version:
    description:
      - The syntax of the YAML file currently being used. Default is 2.
    required: false
    type: int

  interface_id:
    description:
      - Interface ID that must be unique.
    required: true
    type: str

  type:
    description:
      - Interface type. Some types support additional parameters.
        C(bridges) specific params:C(ageing_time), C(priority),
        C(port_priority), C(forward_delay), C(hello_time), C(max_age),
        C(path_cost) and C(stp).

        C(bonds) specific params:C(bonding_mode), C(lacp_rate),
        C(mii_monitor_interval), C(min_links), C(transmit_hash_policy),
        C(ad_select), C(all_slaves_active), C(arp_interval), C(arp_ip_targets),
        C(arp_validate), C(arp_all_targets), C(up_delay), C(down_delay),
        C(fail_over_mac_policy), C(gratuitous_arp), C(packets_per_slave),
        C(primary_reselect_policy), C(resend_igmp), C(learn_packet_interval)
        and C(primary).

        C(tunnels) specific params:C(tunneling_mode), C(local), C(remote),
        C(key), C(keys_input_output).

        C(vlans) specific params:C(id) and C(link).

        C(wifis) specific params:C(access_points_ssid),
        C(access_points_password) and C(access_points_mode).
    choices: [ bridges, bonds, tunnels, ethernets, vlans, wifis ]
    required: true
    type: str

  state:
    description:
      - C(present) add/update a net interface on C(filename);
        C(absent) remove a net interface on C(filename).
    choices: [ present, absent ]
    required: true
    type: str

  dhcp4:
    description:
      - Enable/Disable DHCP for IPv4. Default is disabled.
        Supported for all device types.
    required: false
    type: bool

  dhcp6:
    description:
      - Enable/Disable DHCP for IPv6. Default is disabled.
        Supported for all device types.
    required: false
    type: bool

  ipv6_privacy:
    description:
      - Enable IPv6 Privacy Extensions (RFC 4941) for the specified interface,
        and prefer temporary addresses. Defaults to false
        (no privacy extensions). There is currently no way to have a
        private address but prefer the public address. Supported for all device
        types.
    required: false
    type: bool

  link_local:
    description:
      - Configure the link_local addresses to bring up. Valid options are
        C(ipv4) and C(ipv6) (default), which respectively allow enabling IPv4
        and IPv6 link local addressing. Supported for all device types.
    choices: [ ipv4, ipv6 ]
    required: false
    type: str

  critical:
    description:
      - Designate the connection as "critical to the system", meaning that
        special care will be taken by systemd-networkd to not release the IP
        from DHCP when it the daemon is restarted. Networkd backend only.
        False for default. Supported for all device types.
    required: false
    type: bool

  dhcp_identifier:
    description:
      - When set to C(mac); pass that setting over to systemd-networkd to use
        the device's MAC address as a unique identifier rather than a
        RFC4361-compliant Client ID. This has no effect when NetworkManager
        is used as a renderer. Supported for all device types.
    required: false
    type: str

  accept_ra:
    description:
      - Accept Router Advertisement that would have the kernel configure IPv6
        by itself. When enabled, accept Router Advertisements. When disabled,
        do not respond to Router Advertisements. If unset use the host kernel
        default setting. Supported for all device types.
    required: false
    type: bool

  addresses:
    description:
      - Addresses statically assigned to the interface. They are used in
        addition to the autoconfigured ones, and are represented in
        CIDR notation. Supported for all device types.
    required: false
    type: list

  gateway4:
    description:
      - Set default gateway for IPv4, for manual address configuration.
        This requires setting addresses too. Gateway IPs must be in a form
        recognized by C(inet_pton). Supported for all device types.
    required: false
    type: str

  gateway6:
    description:
      - Set default gateway for IPv6, for manual address configuration.
        This requires setting addresses too. Gateway IPs must be in a form
        recognized by C(inet_pton). Supported for all device types.
    required: false
    type: str

  nameservers_search:
    description:
      -  Set a list of DNS servers search domains.
         Supported for all device types.
    required: false
    type: list

  nameservers_addresses:
    description:
      -  Set a list of ipv4/ipv6 DNS servers.
         Supported for all device types.
    required: false
    type: list

  macaddress:
    description:
      - Set the device's MAC address. The MAC address must be in the form
        XX:XX:XX:XX:XX:XX. Supported for all device types.
    required: false
    type: str

  mtu:
    description:
      - Set the Maximum Transmission Unit for the interface.
        The default is 1500. Valid values depend on your network interface.
        Supported for all device types.
    required: false
    type: int

  optional:
    description:
      - An optional device is not required for booting. Normally, networkd
        will wait some time for device to become configured before proceeding
        with booting. However, if a device is marked as optional, networkd will
        not wait for it. This is only supported by networkd, and the
        default is false. Supported for all device types.
    required: false
    type: bool

  optional_addresses:
    description:
      - Specify types of addresses that are not required for a device to be
        considered online. This changes the behavior of backends at boot time
        to avoid waiting for addresses that are marked optional, and thus
        consider the interface as "usable" sooner. This does not disable
        these addresses, which will be brought up anyway.
        Supported for all device types.
    required: false
    type: list

  match_name:
    description:
      - This selects the current interface name in physical devices
        by various hardware properties. Globs are supported.
        Supported only physical devices.
    required: false
    type: str

  match_macaddress:
    description:
      - This selects the physical device that matchs with MAC address
        in the form "XX:XX:XX:XX:XX:XX". Globs are not supported.
        Supported only physical devices.
    required: false
    type: str

  match_driver:
    description:
      - This selects the physical device that matchs with Kernel driver name
        corresponding to the C(DRIVER) udev property. Globs are supported.
        Supported only physical devices.
    required: false
    type: str

  set_name:
    description:
      - This property can be used to give that device a more
        specific/desirable/nicer name than the default from udev's ifnames.
        Supported only physical devices.
    required: false
    type: str

  wakeonlan:
    description:
      - Enable/Disable(default) wake on LAN. Supported only physical devices.
    required: false
    type: bool

  dhcp4_overrides_use_dns:
    description:
      - The DNS servers received from the DHCP server will be used and take
        precedence statically-configured ones. Only C(networkd) backend and
        C(dhcp4) must be true. Supported for all device types.
    required: false
    type: bool

  dhcp4_overrides_use_ntp:
    description:
      - The NTP servers received from the DHCP server will be used by
        systemd-timesyncd and take precedence statically-configured
        ones. Only C(networkd) backend and C(dhcp4) must be true.
        Supported for all device types.
    required: false
    type: bool

  dhcp4_overrides_use_hostname:
    description:
      - The hostname received from the DHCP server will be set as the transient
        hostname of the system. Only C(networkd) backend and C(dhcp4)
        must be true. Supported for all device types.
    required: false
    type: bool

  dhcp4_overrides_send_hostname:
    description:
      - The machine's hostname will be sent to the DHCP serverself.
        Only C(networkd) backend and C(dhcp4) must be true.
        Supported for all device types.
    required: false
    type: bool

  dhcp4_overrides_hostname:
    description:
      - Use this value for the hostname which is sent to the DHCP server,
        instead of machine's hostname. Only C(networkd) backend and C(dhcp4)
        must be true. Supported for all device types.
    required: false
    type: str

  dhcp6_overrides_use_dns:
    description:
      - The DNS servers received from the DHCP server will be used and take
        precedence over any statically. Only C(networkd) backend and C(dhcp6)
        must be true. Supported for all device types.
    required: false
    type: bool

  dhcp6_overrides_use_ntp:
    description:
      - The NTP servers received from the DHCP server will be used by
        systemd-timesyncd and take precedence over any statically configured
        ones. Only C(networkd) backend and C(dhcp6) must be true.
        Supported for all device types.
    required: false
    type: bool

  dhcp6_overrides_use_hostname:
    description:
      - The hostname received from the DHCP server will be set as the transient
        hostname of the system. Only C(networkd) backend and C(dhcp6)
        must be true. Supported for all device types.
    required: false
    type: bool

  dhcp6_overrides_send_hostname:
    description:
      - The machine's hostname will be sent to the DHCP serverself.
        Only C(networkd) backend and C(dhcp6) must be true.
        Supported for all device types.
    required: false
    type: bool

  dhcp6_overrides_hostname:
    description:
      - Use this value for the hostname which is sent to the DHCP server,
        instead of machine's hostname. Only C(networkd) backend and C(dhcp6)
        must be true. Supported for all device types.
    required: false
    type: str

  routes:
    description:
      - Defines standard static routes for an interface. The routes must be
        defined using a list of dicts, E.g:- {to:0.0.0.0/0, via:1.1.1.1/8}.
        Valid dict keys are:C(from) set a source IP address for traffic going
        through the route;
        C(to) defines the destination address for the route;
        C(via) defines the gateway address to use for this route;
        C(on_link) specifies that the route is directly connected to
        the interface (boolean);
        C(metric) specifies the relative priority of the route.
        Must be a positive integer value;
        C(type) specifies the type of route. Valid options are "unicast"
        (default), "unreachable", "blackhole" or "prohibit";
        C(scope) defines the route scope, how wide-ranging it is to the network.
        Possible values are "global", "link", or "host";
        C(table) defines the table number to use for the route.
        In some scenarios, it may be useful to set routes in a separate
        routing table. It may also be used to refer to routing policy rules
        which also accept a table parameter. Allowed values are positive
        integers starting from 1. Some values are already in use to refer to
        specific routing tables:see C(/etc/iproute2/rt_tables).

        At least the suboptions I(to) and I(via) must be specified.
        Supported for all device types.
    required: false
    type: list

  routing_policy:
    description:
      - Defines  extra routing policy for a network, where traffic may be
        handled specially based on the source IP, firewall marking, etc.
        The routing_policy must be defined using a list of dicts,
        E.g:- {from:192.168.0.0/24, table:102}. Valid dict keys are:C(from)
        set a source IP address to match traffic for this policy rule;
        C(to) match on traffic going to the specified destination;
        C(table) specifies the table number to match for the route.
        In some scenarios, it may be useful to set routes in a separate
        routing table. It may also be used to refer to routes which also accept
        a table parameter. Allowed values are positive integers starting from 1.
        Some values are already in use to refer to specific routing tables:see
        C(/etc/iproute2/rt_tables);
        C(priority) specifies a priority for the routing policy rule, to
        influence the order in which routing rules are processed. A higher
        number means lower priority (rules are processed in order by increasing
        priority number);
        C(mark) defines a mark that this routing policy rule match on
        traffic that has been marked by the iptables firewall with this value.
        Allowed values are positive integers starting from 1;
        C(type_of_service) defines this policy rule based on the type of
        service number applied to the traffic;
        Supported for all devices types.
    required: false
    type: list

  auth_key_management:
    description:
      - The supported key management modes are C(none) (no key management);
        C(psk) (WPA with pre-shared key, common for home wifi); C(eap) (WPA
        with EAP, common for enterprise wifi); and C(802.1x) (used primarily
        for wired Ethernet connections). Supported ethernets and wifis device
        types.
    choices: [ none, psk, eap, 802.1x ]
    required: false
    type: str

  auth_password:
    description:
      - The password string for EAP, or the pre-shared key for WPA-PSK.
         Supported ethernets and wifis device types.
    required: false
    type: str

  auth_method:
    description:
      - The EAP/802.1x method to use. The supported EAP/802.1x methods are
        C(tls) (TLS), C(peap) (Protected EAP), and C(ttls) (Tunneled TLS).
        I(auth_key_management=eap) or I(auth_key_management=802.1x).
        Supported ethernets and wifis device types.
    choices: [ tls, peap, ttls ]
    required: false
    type: str

  auth_identity:
    description:
      - The identity to use for EAP/802.1x.
        I(auth_key_management=eap) or I(auth_key_management=802.1x).
        Supported ethernets and wifis device types.
    required: false
    type: str

  auth_anonymous_identity:
    description:
      - The identity to pass over the unencrypted channel if the chosen
        EAP/802.1x method supports passing a different tunnelled identity.
        I(auth_key_management=eap) or I(auth_key_management=802.1x).
        Supported ethernets and wifis device types.
    required: false
    type: str

  auth_ca_certificate:
    description:
      - Path to a file with one or more trusted certificate authority (CA)
        certificates.
        I(auth_key_management=eap) or I(auth_key_management=802.1x).
        Supported ethernets and wifis device types.
    required: false
    type: str

  auth_client_certificate:
    description:
      - Path to a file containing the certificate to be used by the client
        during authentication.
        I(auth_key_management=eap) or I(auth_key_management=802.1x).
        Supported ethernets and wifis device types.
    required: false
    type: str

  auth_client_key:
    description:
      - Path to a file containing the private key corresponding to
        C(auth_client_certificate).
        I(auth_key_management=eap) or I(auth_key_management=802.1x).
        Supported ethernets and wifis device types.
    required: false
    type: str

  auth_client_key_password:
    description:
      - Password to use to decrypt the private key specified in
        C(auth_client_key) if it is encrypted.
        I(auth_key_management=eap) or I(auth_key_management=802.1x).
        Supported ethernets and wifis device types.
    required: false
    type: str

  interfaces:
    description:
      - All devices matching this ID list will be added or associated to
        bridges or bonds. Required if I(state=present) and I(type=bonds) or
        I(type=bridges). Supported bridges and bonds device types.
    required: false
    type: list

  bonding_mode:
    description:
      - Set the link bonding mode used for the interfaces.
        Required if I(state=present) and I(type=bonds).
        Supported only bond device types.
    choices: [ balance-rr, active-backup, balance-xor, broadcast,
               802.3ad, balance-tlb, balance-alb ]
    required: false
    type: str

  lacp_rate:
    description:
      - Set the rate at which LACP DUs are transmitted. This is only useful
        in 802.3ad mode. Possible values are C(slow) (30 seconds, default),
        and C(fast) (every second). Supported only bond device types.
    choices: [ slow, fast ]
    required: false
    type: str

  mii_monitor_interval:
    description:
      - Specifies the interval for MII monitoring (verifying if an interface
        of the bond has carrier). The default is 0; which disables MII
        monitoring. This is equivalent to the MIIMonitorSec= field for the
        networkd backend. Supported only bond device types.
    required: false
    type: int

  min_links:
    description:
      - The minimum number of links up in a bond to consider the bond
        interface to be up (default is 1). Supported only bond device types.
    required: false
    type: int

  transmit_hash_policy:
    description:
      - Specifies the transmit hash policy for the selection of slaves. This
        is only useful in balance-xor, 802.3ad and balance-tlb modes. Possible
        values are C(layer2), C(layer3+4), C(layer2+3), C(encap2+3), and
        C(encap3+4). Supported only bond device types.
    choices: [ layer2, layer3+4, layer2+3, encap2+3, encap3+4 ]
    required: false
    type: str

  ad_select:
    description:
      - Set the aggregation selection mode. Possible values are C(stable),
        C(bandwidth), and C(count). This option is only used in C(802.3ad)
        mode. Supported only bond device types.
    choices: [ stable, bandwidth, count ]
    required: false
    type: str

  all_slaves_active:
    description:
      - If the bond should drop duplicate frames received on inactive ports,
        set this option to C(false). If they should be delivered, set this
        option to C(true). The default value is false, and is the desirable
        behavior in most situations. Supported only bond device types.
    required: false
    type: bool

  arp_interval:
    description:
      - Set the interval value for how frequently ARP link monitoring should
        happen. The default value is 0, which disables ARP monitoring.
        For the networkd backend, this maps to the ARPIntervalSec= property.
        Supported only bond device types.
    required: false
    type: int

  arp_ip_targets:
    description:
      - IPs of other hosts on the link which should be sent ARP requests in
        order to validate that a slave is up. This option is only used when
        C(arp_interval) is set to a value other than 0. At least one IP
        address must be given for ARP link monitoring to function. Only IPv4
        addresses are supported. You can specify up to 16 IP addresses. The
        default value is an empty list. Supported only bond device types.
    required: false
    type: list

  arp_validate:
    description:
      - Configure how ARP replies are to be validated when using ARP link
        monitoring. Possible values are C(none), C(active), C(backup),
        and C(all). Supported only bond device types.
        Supported only bond device types.
    choices: [ none, active, backup, all ]
    required: false
    type: str

  arp_all_targets:
    description:
      - Specify whether to use any ARP IP target being up as sufficient for
        a slave to be considered up; or if all the targets must be up. This
        is only used for C(active-backup) mode when C(arp_validate) is
        enabled. Possible values are C(any) and C(all).
        Supported only bond device types.
    choices: [ any, all ]
    required: false
    type: str

  up_delay:
    description:
      - Specify the delay before enabling a link once the link is physically
        up. The default value is 0. This maps to the UpDelaySec= property for
        the networkd renderer. Supported only bond device types.
    required: false
    type: int

  down_delay:
    description:
      - Specify the delay before disabling a link once the link has been
        lost. The default value is 0. This maps to the DownDelaySec=
        property for the networkd renderer. Supported only bond device types.
    required: false
    type: int

  fail_over_mac_policy:
    description:
      - Set whether to set all slaves to the same MAC address when adding
        them to the bond, or how else the system should handle MAC addresses.
        The possible values are C(none), C(active), and C(follow).
        Supported only bond device types.
    required: false
    choices: [ none, active, follow ]
    type: str

  gratuitous_arp:
    description:
      - Specify how many ARP packets to send after failover. Once a link is
        up on a new slave, a notification is sent and possibly repeated if
        this value is set to a number greater than 1. The default value
        is 1 and valid values are between 1 and 255. This only affects
        C(active-backup) mode. Supported only bond device types.
    required: false
    type: int

  packets_per_slave:
    description:
      - In C(balance-rr) mode, specifies the number of packets to transmit
        on a slave before switching to the next. When this value is set to
        0, slaves are chosen at random. Allowable values are between
        0 and 65535. The default value is 1. This setting is
        only used in C(balance-rr) mode. Supported only bond device types.
    required: false
    type: int

  primary_reselect_policy:
    description:
      - Specific the reselection policy for the primary slave. On failure of
        the active slave, the system will use this policy to decide how the new
        active slave will be chosen and how recovery will be handled. The
        possible values are C(always), C(better), and C(failure).
        Supported only bond device types.
    required: false
    choices: [ always, better, failure ]
    type: str

  resend_igmp:
    description:
      - Specifies how many IGMP membership reports are issued on a failover
        event. Values range from 0 to 255. 0 disables sending membership
        reports. Otherwise, the first membership report is sent on failover and
        subsequent reports are sent at 200ms intervals. In modes C(balance-rr),
        C(active-backup), C(balance-tlb) and C(balance-alb), a failover can
        switch IGMP traffic from one slave to another.
        Supported only bond device types.
    required: false
    type: int

  learn_packet_interval:
    description:
      - Specify the interval (seconds) between sending learning packets to
        each slave.  The value range is between 1 and 0x7fffffff.
        The default value is 1. This option only affects C(balance-tlb)
        and C(balance-alb) modes. Using the networkd renderer, this field
        maps to the LearnPacketIntervalSec= property.
        Supported only bond device types.
    required: false
    type: int

  primary:
    description:
      - Specify a device to be used as a primary slave, or preferred device
        to use as a slave for the bond (ie. the preferred device to send
        data through), whenever it is available. This only affects
        C(active-backup), C(balance-alb), and C(balance-tlb) bonding_modes.
        Supported only bond device types.
    required: false
    type: str

  ageing_time:
    description:
      - Set the period of time (in seconds) to keep a MAC address in the
        forwarding database after a packet is received. This maps to the
        AgeingTimeSec= property when the networkd renderer is used.
        Supported only bridge device types.
    required: false
    type: int

  priority:
    description:
      - Set the priority value for the bridge. This value should be a
        number between 0 and 65535. Lower values mean higher priority.
        The bridge with the higher priority will be elected as
        the root bridge. Supported only bridge device types.
    required: false
    type: int

  port_priority:
    description:
      - Specify the period of time the bridge will remain in Listening and
        Learning states before getting to the Forwarding state. This field
        maps to the ForwardDelaySec= property for the networkd renderer.
        If no time suffix is specified, the value will be interpreted as
        seconds. You must define an array, with a interface name and the
        forward delay. E.g:['eno1', 15]. Supported only bridge device types.
    required: false
    type: list

  forward_delay:
    description:
      - Specify the period of time (in seconds) the bridge will remain in
        Listening and Learning states before getting to the Forwarding state.
        This field maps to the ForwardDelaySec= property for the networkd
        renderer. Supported only bridge device types.
    required: false
    type: int

  hello_time:
    description:
      - Specify the interval (in seconds) between two hello packets being sent
        out from the root and designated bridges. Hello packets communicate
        information about the network topology. When the networkd renderer
        is used, this maps to the HelloTimeSec= property.
        Supported only bridge device types.
    required: false
    type: int

  max_age:
    description:
      - Set the maximum age (in seconds) of a hello packet. If the last hello
        packet is older than that value, the bridge will attempt to become the
        root bridge. This maps to the MaxAgeSec= property when the networkd.
        Supported only bridge device types.
    required: false
    type: int

  path_cost:
    description:
      - Set the cost of a path on the bridge. Faster interfaces should have
        a lower cost. This allows a finer control on the network topology
        so that the fastest paths are available whenever possible.
        You must define a list, with a interface name and the path-cost.
        E.g:['eno1', 15]. Supported only bridge device types.
    required: false
    type: list

  stp:
    description:
      - Define whether the bridge should use Spanning Tree Protocol. The
        default value is C(true), which means that Spanning Tree should be
        used. Supported only bridge device types.
    required: false
    type: bool

  tunneling_mode:
    description:
      - Defines the tunnel mode. Valid options are sit, gre, ip6gre, ipip,
        ipip6, ip6ip6, vti, and vti6. Additionally, the networkd backend also
        supports gretap and ip6gretap modes. In addition, the NetworkManager
        backend supports isatap tunnels.
        Required if I(state=present) and I(type=tunnels).
        Supported only tunnel device types.
    required: false
    choices: [ sit, gre, ip6gre, ipip, ipip6, ip6ip6, vti, vti6, gretap,
               ip6gretap, isatap ]
    type: str

  local:
    description:
       - Defines the address of the local endpoint of the tunnel.
         Required if I(state=present) and I(type=tunnels).
         Supported only tunnel device types.
    required: false
    type: str

  remote:
    description:
      - Defines the address of the remote endpoint of the tunnel.
        Required if I(state=present) and I(type=tunnels).
        Supported only tunnel device types.
    required: false
    type: str

  key:
    description:
      - Specifiy key to use for the tunnel. The key can be a number or a dotted
        quad (an IPv4 address). It is used for identification of IP transforms.
        This is only required for C(vti) and C(vti6) when using the C(networkd)
        backend, and for C(gre) or C(ip6gre) tunnels when using the
        NetworkManager backend. Supported only tunnel device types.
    required: false
    type: str

  keys_input_output:
    description:
      - Specifiy input and output keys to use for the tunnel. If this param is
        defined, you can't define the key param. The first value passed on list
        is the input key and the second value is the output key.
        E.g:[1234, 5678]. Supported only tunnel device types.
    required: false
    type: list

  id:
    description:
      - VLAN ID, a number between 0 and 4094. Supported only vlan device types.
    required: false
    type: int

  link:
    description:
      - netplan ID of the underlying device definition on which this VLAN
        gets created. Supported only vlan device types.
    required: false
    type: str

  access_points_ssid:
    description:
      - Network SSID. Required if I(state=present) and (type=wifis).
        Supported only wifi device types.
    required: false
    type: str

  access_points_password:
    description:
      - Enable WPA2 authentication and set the passphrase for it. If defined
        C(None), the network is assumed to be open. Other authentication modes
        are not currently supported.
        Required if I(state=present) and (type=wifis).
        Supported only wifi device types.
    required: false
    type: str

  access_points_mode:
    description:
      - Possible access point modes are C(infrastructure) (the default),
        C(ap) (create an access point to which other devices can connect),
        and C(adhoc) (peer to peer networks without a central access point).
        C(ap) is only supported with C(NetworkManager).
        Required if I(state=present) and (type=wifis).
        Supported only wifi device types.
    required: false
    choices: [ infrastructure, ap, adhoc ]
    type: str
'''

EXAMPLES = '''
 - name: Add eth1 interface
   netplan:
     filename: 10-interfaces
     type: ethernets
     interface_id: eth1
     state: present
     dhcp4: false
     addresses:
       - 192.168.1.100/24

 - name: Add eth2 interface
   netplan:
     filename: 10-interfaces
     type: ethernets
     interface_id: eth2
     state: present
     dhcp4: false
     addresses:
       - 192.168.2.100/24
     routes:
       - {to: 0.0.0.0/0, via: 192.168.2.1/24, type: unicast, scope: global}
       - {to: 10.0.0.0/0, via: 192.168.2.2/24}
     routing_policy:
        - {from: 192.168.100.0/24, table: 1, priority: 10}
        - {from: 192.168.200.0/24, table: 2, mark: 100}


 - name: Add br0 bridge interface
   netplan:
     filename: 11-bridges
     type: bridges
     interfaces:
       - eth1
       - eth2
     interface_id: br0
     state: present
     ageing_time: 100
     priority: 2
     port_priority:
       - [eth1, 20]
       - [eth2, 15]
     path_cost:
       - [eth1, 20]
       - [eth2, 15]
     forward_delay: 150
     hello_time: 200
     max_age: 500
     stp: false
     dhcp4: false
     addresses:
       - 192.168.1.1/24
       - 192.168.1.2/24

 - name: Add br1 bridge interface
   netplan:
     filename: 11-bridges
     type: bridges
     interface_id: br1
     state: present
     dhcp4: false

 - name: Add vlan config interfaces
   netplan:
     filename: 12-vlans
     interface_id: brvlan15
     state: present
     type: vlans
     id: 15
     link: br0

 - name: Remove vlan config interfaces into netplan YAML file
   netplan:
     filename: 12-vlans
     interface_id: brvlan15
     type: vlans
     state: absent

 - name: Add ethernet config interfaces
   netplan:
     filename: 10-interfaces
     interface_id: eth0
     type: ethernets
     state: present
     addresses:
       - 192.168.0.1/24
       - 192.168.1.1/24

 - name: Add bridge config interface
   netplan:
     filename: 11-bridges
     interface_id: br0
     type: bridge
     interfaces: eth1
     state: present

 - name: Create bond0 interface
   netplan:
     filename: 13-bonds
     type: bonds
     interface_id: bond0
     state: present
     bonding_mode: 802.3ad
     lacp_rate: slow
     mii_monitor_interval: 10
     min_links: 10
     up_delay: 20
     down_delay: 30
     all_slaves_active: true
     ad_select: stable
     arp_interval: 15
     arp_validate: all
     arp_all_targets: all
     fail_over_mac_policy: none
     arp_ip_targets: [10.10.10.10, 20.20.20.20]
     interfaces: [br0, br1]
     dhcp4: true

 - name: Create tunnel0 interface
   netplan:
     filename: 14-tunnel
     type: tunnels
     interface_id: tunnel0
     tunneling_mode: sit
     local: 1.1.1.1
     remote: 2.2.2.2
     addresses:
       - 9.9.9.9/8
     state: present
     dhcp4: false

 - name: Up veths interfaces
   netplan:
     filename: 15-wifis
     type: wifis
     interface_id: wifi00
     state: present
     access_points_ssid: asdf
     access_points_password: test1234
     access_points_mode: infrastructure
     auth_key_management: eap
     auth_method: tls
     auth_anonymous_identity: "@cust.example.com"
     auth_identity: "cert-joe@cust.example.com"
     auth_ca_certificate: /etc/ssl/cust-cacrt.pem
     auth_client_certificate: /etc/ssl/cust-crt.pem
     auth_client_key: /etc/ssl/cust-key.pem
     auth_client_key_password: "d3cryptPr1v4t3K3y"
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
import copy
import os.path
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

NETPLAN_PATH = '/etc/netplan'

SPECIFC_ANSIBLE_NETPLAN = ['filename', 'renderer', 'version', 'type',
                           'interface_id', 'state']

GENERAL = ['addresses', 'dhcp4', 'dhcp6', 'ipv6_privacy', 'link_local',
           'critical', 'dhcp_identifier', 'accept_ra', 'addresses',
           'gateway4', 'gateway6', 'nameservers_search',
           'nameservers_addresses', 'macaddress', 'optional',
           'optional_addresses', 'routes', 'routing_policy']

MATCH = ['match_name', 'match_macaddress', 'match_driver']

PHYSICAL = MATCH + ['set_name', 'wakeonlan']

DHCP_OVERRIDES = ['dhcp4_overrides_use_dns',
                  'dhcp4_overrides_use_ntp',
                  'dhcp4_overrides_use_hostname',
                  'dhcp4_overrides_send_hostname',
                  'dhcp4_overrides_hostname',
                  'dhcp6_overrides_use_dns',
                  'dhcp6_overrides_use_ntp',
                  'dhcp6_overrides_use_hostname',
                  'dhcp6_overrides_send_hostname',
                  'dhcp6_overrides_hostname']

ROUTES = ['from', 'to', 'via', 'on_link', 'metric', 'type', 'scope', 'table']

ROUTING_POLICY = ['from', 'to', 'table', 'priority', 'mark', 'type_of_service']

AUTH = ['auth_key_management', 'auth_password', 'auth_method', 'auth_identity',
        'auth_anonymous_identity', 'auth_ca_certificate',
        'auth_client_certificate', 'auth_client_key',
        'auth_client_key_password']

BONDS = ['bonding_mode', 'lacp_rate', 'mii_monitor_interval', 'min_links',
         'transmit_hash_policy', 'ad_select', 'all_slaves_active',
         'arp_interval', 'arp_ip_targets', 'arp_validate', 'arp_all_targets',
         'up_delay', 'down_delay', 'fail_over_mac_policy', 'gratuitous_arp',
         'packets_per_slave', 'primary_reselect_policy', 'resend_igmp',
         'learn_packet_interval', 'primary']

BRIDGES = ['ageing_time', 'priority', 'port_priority', 'forward_delay',
           'hello_time', 'max_age', 'path_cost', 'stp']

TUNNELS = ['tunneling_mode', 'local', 'remote', 'key', 'keys_input_output']

VLANS = ['id', 'link']

WIFIS = ['access_points_ssid', 'access_points_password', 'access_points_mode']


def validate_args(module):
    if module.params['state'] == 'present':
        # validate general params
        if module.params.get('routes'):
            for route in module.params.get('routes'):
                # to and via specified
                if not route.get('to') or not route.get('via'):
                    module.fail_json(msg='Route keys \'to\' and \'via\' must be specified on route dict')
                # on_link specified
                if route.get('on_link'):
                    on_link_values = ['true', 'false']
                    if route.get('on_link') not in on_link_values:
                        module.fail_json(msg='Routes on_link supported: {0}'.format(on_link_values))
                # metric specified
                if route.get('metric'):
                    if int(route.get('metric')) < 0:
                        module.fail_json(msg='Routes metric must be a positive integer value')
                # type specified
                if route.get('type'):
                    type_values = ['unicast', 'unreachable', 'blackhole', 'prohibit']
                    if route.get('type') not in type_values:
                        module.fail_json(msg='Routes type supported: {0}'.format(type_values))
                # scope specified
                if route.get('scope'):
                    scope_values = ['global', 'link', 'host']
                    if route.get('scope') not in scope_values:
                        module.fail_json(msg='Routes scope supported: {0}'.format(scope_values))
                # table specified
                # Verify /etc/iproute2/rt_tables before try to add a table.
                if route.get('table'):
                    if int(route.get('table')) < 1:
                        module.fail_json(msg='Routes table values must be positive integers starting from 1.')
                for route_keys in route.keys():
                    if route_keys not in ROUTES:
                        module.fail_json(msg='Routes subparams supported: {0}'.format(ROUTES))
        if module.params.get('routing_policy'):
            for rp in module.params.get('routing_policy'):
                # table specified
                # Verify /etc/iproute2/rt_tables before try to add a table.
                if rp.get('table'):
                    if int(rp.get('table')) < 1:
                        module.fail_json(msg='Routing_policy table values must be positive integers starting from 1.')
                # mark specified
                if rp.get('mark'):
                    if int(rp.get('mark')) < 1:
                        module.fail_json(msg='Routing_policy mark values must be positive integers starting from 1.')
                for rp_key in rp.keys():
                    if rp_key not in ROUTING_POLICY:
                        module.fail_json(msg='Routing_policy subparams supported: {0}'.format(ROUTING_POLICY))
        if module.params['type'] == 'bridges':
            for key in module.params:
                if module.params.get(key):
                    if key in BONDS:
                        module.fail_json(msg='BONDs options can not be defined with bridge Type')
                    if key in TUNNELS:
                        module.fail_json(msg='TUNNELs options can not be defined with bridge Type')
                    if key in VLANS:
                        module.fail_json(msg='VLANs options can not be defined with bridge Type')
                    if key in WIFIS:
                        module.fail_json(msg='WIFIs options can not be defined with bridge Type')
                    if key in PHYSICAL:
                        module.fail_json(msg='PHYSICALs options can not be defined with bridge Type')
                    if key in AUTH:
                        module.fail_json(msg='AUTHs options can not be defined with bridge Type')
        if module.params['type'] == 'bonds':
            if not module.params.get('interfaces') or not module.params.get('bonding_mode'):
                module.fail_json(msg='bonds type require: [interfaces, bonding_mode]')
            for key in module.params:
                if module.params.get(key):
                    if key in BRIDGES:
                        module.fail_json(msg='BRIDGES options can not be defined with bonds Type')
                    if key in TUNNELS:
                        module.fail_json(msg='TUNNELs options can not be defined with bonds Type')
                    if key in VLANS:
                        module.fail_json(msg='VLANS options can not be defined with bonds Type')
                    if key in WIFIS:
                        module.fail_json(msg='WIFIs options can not be defined with bonds Type')
                    if key in PHYSICAL:
                        module.fail_json(msg='PHYSICALs options can not be defined with bonds Type')
                    if key in AUTH:
                        module.fail_json(msg='AUTHs options can not be defined with bond Type')
                    # Verify bonds params dependences:
                    # lacpt_rate depends on bonding_mode == 802.3ad
                    # transmit_hash_policy depends on bonding_mode == 802.3ad or balance-tlb or balance-xor
                    # ad_select depends on bonding_mode == 802.3ad
                    # arp_all_target depends on bonding_mode == active-backup and arp_validate == true
                    # gratuitous_arp depends on bonding_mode == active-backup
                    # packets_per_slave depends on bonding_mode == balance-rr
                    # learn_packet_interval depends on bonding_mode == balance-tlb or balance-alb
                    # primary depends on bonding_mode == active-backup or balance-tlb or balance-alb
                    if key == 'lacpt_rate' or key == 'ad_select':
                        if module.params['bonding_mode'] != '802.3ad':
                            module.fail_json(msg='bonding_mode must be 802.3ad to define {0} param'.format(key))
                    if key == 'transmit_hash_policy':
                        if module.params['bonding_mode'] != '802.3ad' or module.params['bonding_mode'] != 'balance-tlb' \
                           or module.params['bonding_mode'] != 'balance-xor':
                            module.fail_json(msg='bonding_mode must be 802.3ad or balance-tlb or balance-xor to define {0} param'.format(key))
                    if key == 'arp_all_target':
                        if module.params['bonding_mode'] != 'active-backup' and not module.params['arp_validate']:
                            module.fail_json(msg='bonding_mode and arp_validade both must be active-backup and true to define {0} param'.format(key))
                    if key == 'gratuitous_arp':
                        if module.params['bonding_mode'] != 'active-backup':
                            module.fail_json(msg='bonding_mode must be active-backup to define {0} param'.format(key))
                    if key == 'packets_per_slave':
                        if module.params['bonding_mode'] != 'balance-rr':
                            module.fail_json(msg='bonding_mode must be balance-rr to define {0} param'.format(key))
                    if key == 'learn_packet_interval':
                        if module.params['bonding_mode'] != 'balance-tlb' or module.params['bonding_mode'] != 'balance-alb':
                            module.fail_json(msg='bonding_mode must be balance-tlb or balance-alb to define {0} param'.format(key))
                    if key == 'primary':
                        if module.params['bonding_mode'] != 'active-backup' or module.params['bonding_mode'] != 'balance-tlb' or \
                           module.params['bonding_mode'] != 'balance-alb':
                            module.fail_json(msg='bonding_mode must be active-backup or balance-tlb or balance-alb to define {0} param'.format(key))
        if module.params['type'] == 'tunnels':
            if not module.params.get('tunneling_mode') or not module.params.get('local') or not module.params.get('remote'):
                module.fail_json(msg='tunnels type require: [tunneling_mode, local, remote]')
            for key in module.params:
                if module.params.get(key):
                    if key in BONDS:
                        module.fail_json(msg='BONDs options can not be defined with tunnel Type')
                    if key in BRIDGES:
                        module.fail_json(msg='BRIDGES options can not be defined with tunnel Type')
                    if key in VLANS:
                        module.fail_json(msg='VLANs options can not be defined with tunnel Type')
                    if key in WIFIS:
                        module.fail_json(msg='WIFIs options can not be defined with tunnel Type')
                    if key in AUTH:
                        module.fail_json(msg='AUTHs options can not be defined with tunnel Type')
                    if key in PHYSICAL:
                        module.fail_json(msg='PHYSICALs options can not be defined with tunnel Type')
                    if key == 'interfaces':
                        module.fail_json(msg='interfaces can not be defined with tunnel Type')
                    # gretap and ip6gretap tunneling_mode only supported if renderer == networkd
                    # isatap tunneling_mode only supported if renderer == NetworkManager
                    if key == 'tunneling_mode':
                        if module.params['tunneling_mode'] == 'gretap' or module.params['tunneling_mode'] == 'ip6gretap':
                            if module.params['renderer'] == 'NetworkManager':
                                module.fail_json(msg="gretap and ip6gretap tunneling_mode are only supported on networkd render")
                        if module.params['tunneling_mode'] == 'isatap':
                            if module.params['renderer'] == 'networkd' or not module.params.get('renderer'):
                                module.fail_json(msg="isatap tunneling_mode is only supported on NetworkManager render")
        if module.params['type'] == 'ethernets':
            for key in module.params:
                if module.params.get(key):
                    if key in BONDS:
                        module.fail_json(msg='BONDS options can not be defined with ethernets Type')
                    if key in BRIDGES:
                        module.fail_json(msg='BRIDGES options can not be defined with ethernets Type')
                    if key in TUNNELS:
                        module.fail_json(msg='TUNNELs options can not be defined with ethernets Type')
                    if key in VLANS:
                        module.fail_json(msg='VLANS options can not be defined with ethernets Type')
                    if key in WIFIS:
                        module.fail_json(msg='WIFIs options can not be defined with ethernets Type')
                    if key == 'interfaces':
                        module.fail_json(msg='interfaces can not be defined with ethernets Type')
                    if key in AUTH[2:]:
                        if not module.params.get('auth_key_management') or not module.params.get('auth_password'):
                            module.fail_json(msg='Define auth_key_management and auth_password to use {0}.'.format(key))
                        if module.params.get('auth_key_management') != 'eap' and module.params.get('auth_key_management') != '802.1x':
                            module.fail_json(msg='auth_key_management needs to be eap or 802.1x to use {0}.'.format(key))
        if module.params['type'] == 'vlans':
            if not module.params.get('id') or not module.params.get('link'):
                module.fail_json(msg='vlans type require: [id, link]')
            for key in module.params:
                if module.params.get(key):
                    if key in BONDS:
                        module.fail_json(msg='BONDS options can not be defined with vlans Type')
                    if key in BRIDGES:
                        module.fail_json(msg='BRIDGES options can not be defined with vlans Type')
                    if key in TUNNELS:
                        module.fail_json(msg='TUNNELS options can not be defined with vlans Type')
                    if key in WIFIS:
                        module.fail_json(msg='WIFIs options can not be defined with vlans Type')
                    if key in PHYSICAL:
                        module.fail_json(msg='PHYSICALs options can not be defined with vlans Type')
                    if key in AUTH:
                        module.fail_json(msg='AUTHs options can not be defined with vlans Type')
                    if key == 'interfaces':
                        module.fail_json(msg='interfaces can not be defined with vlan Type')
        if module.params['type'] == 'wifis':
            if not module.params.get('access_points_ssid') or not module.params.get('access_points_password') or not module.params.get('access_points_mode'):
                module.fail_json(msg='wifis type require: [access_points_ssid, access_points_password, access_points_mode]')
            for key in module.params:
                if module.params.get(key):
                    if key in BONDS:
                        module.fail_json(msg='BONDS options can not be defined with wifis Type')
                    if key in BRIDGES:
                        module.fail_json(msg='BRIDGES options can not be defined with wifis Type')
                    if key in TUNNELS:
                        module.fail_json(msg='TUNNELS options can not be defined with wifis Type')
                    if key in VLANS:
                        module.fail_json(msg='VLANS options can not be defined with wifis Type')
                    if key == 'interfaces':
                        module.fail_json(msg='interfaces can not be defined with wifis Type')
                    if key in AUTH[2:]:
                        if not module.params.get('auth_key_management') or not module.params.get('auth_password'):
                            module.fail_json(msg='Define auth_key_management and auth_password to use {0}.'.format(key))
                        if module.params.get('auth_key_management') != 'eap' and module.params.get('auth_key_management') != '802.1x':
                            module.fail_json(msg='auth_key_management needs to be eap or 802.1x to use {0}.'.format(key))
    else:
        for key in module.params:
            if module.params.get(key):
                if key in BRIDGES + BONDS + TUNNELS + VLANS + WIFIS + DHCP_OVERRIDES + GENERAL + PHYSICAL + AUTH + ['interfaces']:
                    module.fail_json(msg="When state is absent, just use this params:[filename, type, interface_id]")


def get_netplan_dict(params):
    # Alias to improve readability
    p_type = params.get('type')
    p_ifid = params.get('interface_id')

    netplan_dict = {'network': dict()}
    # Define default netplan version and renderes both to 2 and networkd
    if params.get('version'):
        netplan_dict['network']['version'] = params.get('version')
    else:
        netplan_dict['network']['version'] = 2
    if params.get('renderer'):
        netplan_dict['network']['renderer'] = params.get('renderer')
    else:
        netplan_dict['network']['renderer'] = 'networkd'
    netplan_dict['network'][p_type] = dict()
    netplan_dict['network'][p_type][p_ifid] = dict()
    for key in params:
        if key not in SPECIFC_ANSIBLE_NETPLAN and params.get(key):
            if key in MATCH:
                match_option = '{0}'.format(key.split('match_')[1])
                if not netplan_dict['network'][p_type][p_ifid].get('match'):
                    netplan_dict['network'][p_type][p_ifid]['match'] = dict()
                netplan_dict['network'][p_type][p_ifid]['match'][match_option] = params.get(key)
            # dhcp4_overrides
            elif key in DHCP_OVERRIDES:
                override_option = '{0}'.format(key.split('dhcp4_overrides_')[1].replace('_', '-'))
                if not netplan_dict['network'][p_type][p_ifid].get('dhcp4-overrides'):
                    netplan_dict['network'][p_type][p_ifid]['dhcp4-overrides'] = dict()
                netplan_dict['network'][p_type][p_ifid]['dhcp4-overrides'][override_option] = params.get(key)
            elif key in BONDS:
                if not netplan_dict['network'][p_type][p_ifid].get('parameters'):
                    netplan_dict['network'][p_type][p_ifid]['parameters'] = dict()
                # Put bonding_mode param into mode param.
                # This is used because mode param is used in others locals like: Tunnels and wifis.
                if key == 'bonding_mode':
                    netplan_dict['network'][p_type][p_ifid]['parameters']['mode'] = params.get(key)
                else:
                    netplan_dict['network'][p_type][p_ifid]['parameters'][key.replace('_', '-')] = params.get(key)
            elif key in BRIDGES:
                if not netplan_dict['network'][p_type][p_ifid].get('parameters'):
                    netplan_dict['network'][p_type][p_ifid]['parameters'] = dict()
                if key == 'path_cost':
                    if not netplan_dict['network'][p_type][p_ifid]['parameters'].get('path-cost'):
                        netplan_dict['network'][p_type][p_ifid]['parameters']['path-cost'] = dict()
                    for pc in params.get(key):
                        netplan_dict['network'][p_type][p_ifid]['parameters']['path-cost'][pc[0]] = pc[1]
                elif key == 'port_priority':
                    if not netplan_dict['network'][p_type][p_ifid]['parameters'].get('port-priority'):
                        netplan_dict['network'][p_type][p_ifid]['parameters']['port-priority'] = dict()
                    for pp in params.get(key):
                        netplan_dict['network'][p_type][p_ifid]['parameters']['port-priority'][pp[0]] = pp[1]
                else:
                    netplan_dict['network'][p_type][p_ifid]['parameters'][key.replace('_', '-')] = params.get(key)
            elif key in TUNNELS:
                if key == 'tunneling_mode':
                    netplan_dict['network'][p_type][p_ifid]['mode'] = params.get(key)
                elif key == 'keys_input_output':
                    if not netplan_dict['network'][p_type][p_ifid]['mode'].get('keys'):
                        netplan_dict['network'][p_type][p_ifid]['mode']['keys'] = dict()
                    netplan_dict['network'][p_type][p_ifid]['mode']['keys']['input'] = params.get(key)[0]
                    netplan_dict['network'][p_type][p_ifid]['mode']['keys']['output'] = params.get(key)[1]
                else:
                    netplan_dict['network'][p_type][p_ifid][key.replace('_', '-')] = params.get(key)
            elif key in WIFIS:
                if key != 'access_points_ssid':
                    wifi_option = key.split('access_points_')[1]
                    if not netplan_dict['network'][p_type][p_ifid].get('access-points'):
                        netplan_dict['network'][p_type][p_ifid]['access-points'] = dict()
                    if not netplan_dict['network'][p_type][p_ifid]['access-points'].get(params.get('access_points_ssid')):
                        netplan_dict['network'][p_type][p_ifid]['access-points'][params.get('access_points_ssid')] = dict()
                    netplan_dict['network'][p_type][p_ifid]['access-points'][params.get('access_points_ssid')][wifi_option] = params.get(key)
            elif key in AUTH:
                auth_option = key.split('auth_')[1].replace('_', '-')
                if p_type == 'wifis':
                    if not netplan_dict['network'][p_type][p_ifid].get('access-points'):
                        netplan_dict['network'][p_type][p_ifid]['access-points'] = dict()
                    if not netplan_dict['network'][p_type][p_ifid]['access-points'].get(params.get('access_points_ssid')):
                        netplan_dict['network'][p_type][p_ifid]['access-points'][params.get('access_points_ssid')] = dict()
                    if not netplan_dict['network'][p_type][p_ifid]['access-points'][params.get('access_points_ssid')].get('auth'):
                        netplan_dict['network'][p_type][p_ifid]['access-points'][params.get('access_points_ssid')]['auth'] = dict()
                    netplan_dict['network'][p_type][p_ifid]['access-points'][params.get('access_points_ssid')]['auth'][auth_option] = params.get(key)
                else:
                    # type == ethernets
                    if not netplan_dict['network'][p_type][p_ifid].get('auth'):
                        netplan_dict['network'][p_type][p_ifid]['auth'] = dict()
                    netplan_dict['network'][p_type][p_ifid]['auth'][auth_option] = params.get(key)
            else:
                netplan_dict['network'][p_type][p_ifid][key.replace('_', '-')] = params.get(key)
    return netplan_dict


def update_file_dict(module_dict, file_dict):
    for key in module_dict.keys():
        if not file_dict.get(key):
            file_dict[key] = module_dict[key]
        else:
            if isinstance(file_dict[key], list):
                temp_list = file_dict[key]
                for l in module_dict[key]:
                    if l not in temp_list:
                        temp_list.append(l)
                file_dict[key] = []
                file_dict[key] = temp_list
            elif isinstance(file_dict[key], dict):
                file_dict[key] = update_file_dict(module_dict[key], file_dict[key])
            else:
                file_dict[key] = module_dict[key]
    return file_dict


def main():
    argument_spec = {
        'filename': {'required': True},
        'renderer': {'choices': ['networkd', 'NetworkManager'],
                     'required': False},
        'version': {'required': False, 'type': 'int'},
        'type': {'choices': ['bridges', 'bonds', 'tunnels', 'ethernets',
                             'vlans', 'wifis'],
                 'required': True},
        'interface_id': {'required': True},
        'state': {'choices': ['present', 'absent'], 'required': True},
        'dhcp4': {'required': False, 'type': 'bool'},
        'dhcp6': {'required': False, 'type': 'bool'},
        'ipv6_privacy': {'required': False, 'type': 'bool'},
        'link_local': {'choices': ['ipv4', 'ipv6'],
                       'required': False},
        'critical': {'required': False,
                     'type': 'bool'},
        'dhcp_identifier': {'required': False},
        'accept_ra': {'required': False, 'type': 'bool'},
        'addresses': {'required': False,
                      'type': 'list'},
        'gateway4': {'required': False},
        'gateway6': {'required': False},
        'nameservers_search': {'required': False,
                               'type': 'list'},
        'nameservers_addresses': {'required': False,
                                  'type': 'list'},
        'macaddress': {'required': False},
        'mtu': {'required': False, 'type': 'int'},
        'optional': {'required': False, 'type': 'bool'},
        'optional_addresses': {'required': False, 'type': 'list'},
        'match_name': {'required': False},
        'match_macaddress': {'required': False},
        'match_driver': {'required': False},
        'set_name': {'required': False},
        'wakeonlan': {'required': False, 'type': 'bool'},
        'dhcp4_overrides_use_dns': {'required': False, 'type': 'bool'},
        'dhcp4_overrides_use_ntp': {'required': False, 'type': 'bool'},
        'dhcp4_overrides_use_hostname': {'required': False, 'type': 'bool'},
        'dhcp4_overrides_send_hostname': {'required': False, 'type': 'bool'},
        'dhcp4_overrides_hostname': {'required': False},
        'dhcp6_overrides_use_dns': {'required': False, 'type': 'bool'},
        'dhcp6_overrides_use_ntp': {'required': False, 'type': 'bool'},
        'dhcp6_overrides_use_hostname': {'required': False, 'type': 'bool'},
        'dhcp6_overrides_send_hostname': {'required': False, 'type': 'bool'},
        'dhcp6_overrides_hostname': {'required': False},
        'routes': {'required': False, 'type': 'list'},
        'routing_policy': {'required': False, 'type': 'list'},
        'auth_key_management': {'choices': ['none', 'psk', 'eap', '802.1x'],
                                'required': False},
        'auth_password': {'required': False},
        'auth_method': {'choices': ['tls', 'peap', 'ttls'], 'required': False},
        'auth_identity': {'required': False},
        'auth_anonymous_identity': {'required': False},
        'auth_ca_certificate': {'required': False},
        'auth_client_certificate': {'required': False},
        'auth_client_key': {'required': False},
        'auth_client_key_password': {'required': False},
        'interfaces': {'required': False, 'type': 'list'},
        'bonding_mode': {'choices': ['balance-rr', 'active-backup', 'balance-xor',
                                     'broadcast', '802.3ad', 'balance-tlb',
                                     'balance-alb'],
                         'required': False},
        'lacp_rate': {'choices': ['slow', 'fast'],
                      'required': False},
        'mii_monitor_interval': {'required': False, 'type': 'int'},
        'min_links': {'required': False, 'type': 'int'},
        'transmit_hash_policy': {'choices': ['layer2', 'layer3+4', 'layer2+3',
                                             'encap2+3', 'encap3+4'],
                                 'required': False},
        'ad_select': {'choices': ['stable', 'bandwidth', 'count'],
                      'required': False},
        'all_slaves_active': {'required': False, 'type': 'bool'},
        'arp_interval': {'required': False, 'type': 'int'},
        'arp_ip_targets': {'required': False, 'type': 'list'},
        'arp_validate': {'choices': ['none', 'active', 'backup', 'all'],
                         'required': False},
        'arp_all_targets': {'choices': ['any', 'all'], 'required': False},
        'up_delay': {'required': False, 'type': 'int'},
        'down_delay': {'required': False, 'type': 'int'},
        'fail_over_mac_policy': {'choices': ['none', 'active', 'follow'],
                                 'required': False},
        'gratuitous_arp': {'required': False, 'type': 'int'},
        'packets_per_slave': {'required': False, 'type': 'int'},
        'primary_reselect_policy': {'choices': ['always', 'better',
                                                'failure'],
                                    'required': False},
        'resend_igmp': {'required': False, 'type': 'int'},
        'primary': {'required': False},
        'learn_packet_interval': {'required': False, 'type': 'int'},
        'ageing_time': {'required': False, 'type': 'int'},
        'priority': {'required': False, 'type': 'int'},
        'port_priority': {'required': False, 'type': 'list'},
        'forward_delay': {'required': False, 'type': 'int'},
        'hello_time': {'required': False, 'type': 'int'},
        'max_age': {'required': False, 'type': 'int'},
        'path_cost': {'required': False, 'type': 'list'},
        'stp': {'required': False, 'type': 'bool'},
        'tunneling_mode': {'choices': ['sit', 'gre', 'ip6gre', 'ipip', 'ipip6',
                                       'ip6ip6', 'vti', 'vti6', 'gretap',
                                       'ip6gretap', 'isatap'],
                           'required': False},
        'local': {'required': False},
        'remote': {'required': False},
        'id': {'required': False, 'type': 'int'},
        'key': {'required': False},
        'keys_input_output': {'required': False, 'type': 'list'},
        'link': {'required': False},
        'access_points_ssid': {'required': False},
        'access_points_password': {'required': False},
        'access_points_mode': {'choices': ['infrastructure', 'ap', 'adhoc'],
                               'required': False}
    }

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    if not HAS_YAML:
        module.fail_json(msg='The PyYAML Python module is required')

    validate_args(module)

    NETPLAN_FILENAME = '{0}/{1}.yaml'.format(NETPLAN_PATH, module.params.get('filename'))

    # Alias to improve readability
    p_type = module.params.get('type')
    p_ifid = module.params.get('interface_id')

    if os.path.isfile(NETPLAN_FILENAME):
        with open(NETPLAN_FILENAME, 'r') as yamlfile:
            netplan_file_dict = yaml.load(yamlfile)
        netplan_module_dict = get_netplan_dict(module.params)

        # Add interface
        if module.params.get('state') == 'present':
            if netplan_file_dict == netplan_module_dict:
                module.exit_json(changed=False)
            else:
                new_file_dict = update_file_dict(netplan_module_dict, copy.deepcopy(netplan_file_dict))
                if netplan_file_dict == new_file_dict:
                    module.exit_json(changed=False)
                with open(NETPLAN_FILENAME, 'w') as yamlfile:
                    yaml.dump(new_file_dict, yamlfile, default_flow_style=False)
                module.run_command('netplan apply', check_rc=True)
                module.exit_json(changed=True)
        # Remove interface
        else:
            if not netplan_file_dict['network'].get(p_type):
                module.exit_json(changed=False)
            if not netplan_file_dict['network'][p_type].pop(p_ifid):
                module.exit_json(changed=False)
            else:
                # Verify if type key is None to remove from dict
                if not netplan_file_dict['network'].get(p_type):
                    netplan_file_dict['network'].pop(p_type)
                with open(NETPLAN_FILENAME, 'w') as yamlfile:
                    yaml.dump(netplan_file_dict, yamlfile, default_flow_style=False)
                module.run_command('netplan apply', check_rc=True)
                module.exit_json(changed=True)
    else:
        if module.params.get('state') == 'present':
            netplan_dict = get_netplan_dict(module.params)
            with open(NETPLAN_FILENAME, 'w') as yamlfile:
                yaml.dump(netplan_dict, yamlfile, default_flow_style=False)
            module.run_command('netplan apply', check_rc=True)
            module.exit_json(changed=True)
        else:
            module.fail_json(msg='Interface {0} can not be removed because {1} file does not exist'.format(p_ifid, NETPLAN_FILENAME))


if __name__ == '__main__':
    main()
