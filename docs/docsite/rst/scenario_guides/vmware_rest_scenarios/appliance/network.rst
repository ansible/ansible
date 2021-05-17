.. _vmware-rest-appliance-network:


Network managment
*****************


IP configuration
================

You can also use Ansible to get and configure the network stack of the
VCSA.


Global network information
--------------------------

The appliance_networking_info exposes the state of the global network
configuration:

::

   - name: Get network information
     vmware.vmware_rest.appliance_networking_info:

response

::

   {
       "changed": false,
       "value": {
           "dns": {
               "hostname": "vcenter.test",
               "mode": "DHCP",
               "servers": [
                   "192.168.123.1"
               ]
           },
           "interfaces": {
               "nic0": {
                   "ipv4": {
                       "address": "192.168.123.8",
                       "configurable": true,
                       "default_gateway": "192.168.123.1",
                       "mode": "DHCP",
                       "prefix": 24
                   },
                   "mac": "52:54:00:c8:2b:a1",
                   "name": "nic0",
                   "status": "up"
               }
           },
           "vcenter_base_url": "https://vcenter.test:443"
       }
   }

And you can adjust the parameters with the appliance_networking
module.

::

   - name: Set network information
     vmware.vmware_rest.appliance_networking:
       ipv6_enabled: False

response

::

   {
       "changed": true,
       "id": null,
       "value": {}
   }


Network Interface configuration
-------------------------------

The appliance_networking_interfaces_info returns a list of the Network
Interface of the system:

::

   - name: Get a list of the network interfaces
     vmware.vmware_rest.appliance_networking_interfaces_info:

response

::

   {
       "changed": false,
       "value": [
           {
               "ipv4": {
                   "address": "192.168.123.8",
                   "configurable": true,
                   "default_gateway": "192.168.123.1",
                   "mode": "DHCP",
                   "prefix": 24
               },
               "mac": "52:54:00:c8:2b:a1",
               "name": "nic0",
               "status": "up"
           }
       ]
   }

You can also use the ``interface_name`` parameter to just focus on one
single entry:

::

   - name: Get details about one network interfaces
     vmware.vmware_rest.appliance_networking_interfaces_info:
       interface_name: nic0

response

::

   {
       "changed": false,
       "id": "nic0",
       "value": {
           "ipv4": {
               "address": "192.168.123.8",
               "configurable": true,
               "default_gateway": "192.168.123.1",
               "mode": "DHCP",
               "prefix": 24
           },
           "mac": "52:54:00:c8:2b:a1",
           "name": "nic0",
           "status": "up"
       }
   }

You can adjust the IPv4 network configuration of a NIC with with
appliance_networking_interfaces_ipv4:

::

   - name: Enforce the use of DHCP for nic0
     vmware.vmware_rest.appliance_networking_interfaces_ipv4:
       interface_name: nic0
       mode: DHCP

response

::

   {
       "changed": false,
       "value": {
           "address": "192.168.123.8",
           "configurable": true,
           "default_gateway": "192.168.123.1",
           "mode": "DHCP",
           "prefix": 24
       }
   }

The appliance_networking_interfaces_ipv6 and
appliance_networking_interfaces_ipv6_info allow you do the same with
IPv6.


DNS configuration
=================


The hostname configuration
--------------------------

The appliance_networking_dns_hostname_info module can be use to
retrieve the hostname of the VCSA:

::

   - name: Get the hostname configuration
     vmware.vmware_rest.appliance_networking_dns_hostname_info:

response

::

   {
       "changed": false,
       "value": "vcenter.test"
   }


The DNS servers
---------------

Use the appliance_networking_dns_servers_info to get DNS servers
currently in use:

::

   - name: Get the DNS servers
     vmware.vmware_rest.appliance_networking_dns_servers_info:
     ignore_errors: True  # May be failing because of the CI set-up

response

::

   {
       "changed": false,
       "value": {
           "mode": "dhcp",
           "servers": [
               "192.168.123.1"
           ]
       }
   }

The appliance_networking_dns_servers can be used to set a different
name server.

::

   - name: Set the DNS servers
     vmware.vmware_rest.appliance_networking_dns_servers:
       servers:
         - 192.168.123.1

response

::

   {
       "changed": false,
       "value": {
           "mode": "dhcp",
           "servers": [
               "192.168.123.1"
           ]
       }
   }

You can test a list of servers if you set ``state=test``:

::

   - name: Test the DNS servers
     vmware.vmware_rest.appliance_networking_dns_servers:
       state: test
       servers:
         - var

response

::

   {
       "changed": false,
       "value": {
           "messages": [
               {
                   "message": "Failed to reach 'var'.",
                   "result": "failure"
               }
           ],
           "status": "red"
       }
   }


The search domain configuration
-------------------------------

The search domain configuration can be done with
appliance_networking_dns_domains and
appliance_networking_dns_domains_info. The second module returns a
list of domains:

::

   - name: Get DNS domains configuration
     vmware.vmware_rest.appliance_networking_dns_domains_info:

response

::

   {
       "changed": false,
       "value": [
           "foobar",
           "barfoo"
       ]
   }

There is two way to set the search domain. By default the value you
pass in ``domains`` will overwrite the existing domain:

::

   - name: Update the domain configuration
     vmware.vmware_rest.appliance_networking_dns_domains:
       domains:
         - foobar

response

::

   {
       "changed": true,
       "value": {}
   }

If you instead use the ``state=add`` parameter, the ``domain`` value
will complet the existing list of domains.

::

   - name: Add another domain configuration
     vmware.vmware_rest.appliance_networking_dns_domains:
       domain: barfoo
       state: add

response

::

   {
       "changed": false,
       "value": {}
   }


Firewall settings
=================

You can also configure the VCSA firewall. You can add new ruleset with
the appliance_networking_firewall_inbound module. In this example, we
reject all the traffic coming from the ``1.2.3.0/24`` subnet:

::

   - name: Set a firewall rule
     vmware.vmware_rest.appliance_networking_firewall_inbound:
       rules:
         - address: 1.2.3.0
           prefix: 24
           policy: REJECT

response

::

   {
       "changed": false,
       "value": [
           {
               "address": "1.2.3.0",
               "interface_name": "*",
               "policy": "REJECT",
               "prefix": 24
           }
       ]
   }

The appliance_networking_firewall_inbound_info module returns a list
of the inbound ruleset:

::

   - name: Get the firewall inbound configuration
     vmware.vmware_rest.appliance_networking_firewall_inbound_info:

response

::

   {
       "changed": false,
       "value": [
           {
               "address": "1.2.3.0",
               "interface_name": "*",
               "policy": "REJECT",
               "prefix": 24
           }
       ]
   }


HTTP proxy
==========

You can also configurre the VCSA to go through a HTTP proxy. The
collection provides a set of modules to configure the proxy server and
manage the noproxy filter.

In this example, we will set up a proxy and configure the ``noproxy``
for ``redhat.com`` and ``ansible.com``:

::

   - name: Set the HTTP proxy configuration
     vmware.vmware_rest.appliance_networking_proxy:
       enabled: true
       server: http://47.244.50.194
       port: 8081
       protocol: http
   - name: Set HTTP noproxy configuration
     vmware.vmware_rest.appliance_networking_noproxy:
       servers:
         - redhat.com
         - ansible.com

response

::

   {
       "changed": false,
       "value": {
           "enabled": false,
           "port": -1,
           "server": ""
       }
   }

::

   {
       "changed": true,
       "value": {}
   }

We can validate the configuration with the associated _info modules:

::

   - name: Get the HTTP proxy configuration
     vmware.vmware_rest.appliance_networking_proxy_info:
   - name: Get HTTP noproxy configuration
     vmware.vmware_rest.appliance_networking_noproxy_info:

response

::

   {
       "changed": false,
       "value": {
           "ftp": {
               "enabled": false,
               "port": -1,
               "server": ""
           },
           "http": {
               "enabled": false,
               "port": -1,
               "server": ""
           },
           "https": {
               "enabled": false,
               "port": -1,
               "server": ""
           }
       }
   }

::

   {
       "changed": false,
       "value": [
           "redhat.com",
           "ansible.com",
           "localhost",
           "127.0.0.1"
       ]
   }

And we finally reverse the configuration:

::

   - name: Delete the HTTP proxy configuration
     vmware.vmware_rest.appliance_networking_proxy:
       config: {}
       protocol: http
       state: absent
   - name: Remove the noproxy entries
     vmware.vmware_rest.appliance_networking_noproxy:
       servers: []

response

::

   {
       "changed": true,
       "value": {}
   }

::

   {
       "changed": true,
       "value": {}
   }
