# Ansible Role: cnos_ethernet_sample - Performs switch ethernet port configuration and state management
---
<add role description below>

This role is an example of using the *cnos_interface.py* Lenovo module in the context of CNOS switch configuration. This module allows you to work with interface related configurations. The operators used are overloaded to ensure control over switch interface configurations, such as ethernet ports, loopback interfaces, VLANs, and the management interface.

Apart from the regular device connection related attributes, there are seven interface arguments that will perform further configurations. They are *interfaceArg1*, *interfaceArg2*, *interfaceArg3*, *interfaceArg4*, *interfaceArg5*, *interfaceArg6*, and *interfaceArg7*.

The results of the operation can be viewed in *results* directory.

For more details, see [Lenovo modules for Ansible: cnos_interface](http://systemx.lenovofiles.com/help/index.jsp?topic=%2Fcom.lenovo.switchmgt.ansible.doc%2Fcnos_interface.html&cp=0_3_1_0_4_12).


## Requirements
---
<add role requirements information below>

- Ansible version 2.2 or later ([Ansible installation documentation](https://docs.ansible.com/ansible/intro_installation.html))
- Lenovo switches running CNOS version 10.2.1.0 or later
- an SSH connection to the Lenovo switch (SSH must be enabled on the network device)


## Role Variables
---
<add role variables information below>

Available variables are listed below, along with description.

The following are mandatory inventory variables:

Variable | Description
--- | ---
`username` | Specifies the username used to log into the switch
`password` | Specifies the password used to log into the switch
`enablePassword` | Configures the password used to enter Global Configuration command mode on the switch (this is an optional parameter)
`hostname` | Searches the hosts file at */etc/ansible/hosts* and identifies the IP address of the switch on which the role is going to be applied
`deviceType` | Specifies the type of device from where the configuration will be backed up (**g8272_cnos** - G8272, **g8296_cnos** - G8296)

The values of the variables used need to be modified to fit the specific scenario in which you are deploying the solution. To change the values of the variables, you need to visits the *vars* directory of each role and edit the *main.yml* file located there. The values stored in this file will be used by Ansible when the template is executed.

The syntax of *main.yml* file for variables is the following:

```
<template variable>:<value>
```

You will need to replace the `<value>` field with the value that suits your topology. The `<template variable>` fields are taken from the template and it is recommended that you leave them unchanged.

Variable | Description
--- | ---
`interfaceOption` | Specifies the type of the interface that will be configured (**ethernet** - ethernet port, **loopback** - loopback interface, **vlan** - VLAN, **mgmt** - management interface, **port-aggregation** - Link Aggregation Group)
`interfaceRange` | Specifies the interface range that will be configured
`interfaceArg1` | This is an overloaded BGP variable. Please refer to the [cnos_interface module documentation](http://ralfss28.labs.lenovo.com:5555/help/topic/com.lenovo.switchmgt.ansible.doc/cnos_interface.html?cp=0_3_1_0_2_12) for detailed information on usage. The values of these variables depend on the configuration context and the choices are the following: **aggregation-group**, **bfd**, **bridge-port**, **description**, **duplex**, **flowcontrol**, **ip**, **ipv6**, **lacp**, **lldp**, **load-interval**, **mac**, **mac-address**, **mac-learn**, **microburst-detection**, **mtu**, **service**, **service-policy**, **shutdown**, **snmp**, **spanning-tree**, **speed**, **storm-control**, **vlan**, **vrrp**, **port-aggregation**.
`interfaceArg2` | This is an overloaded BGP variable. Please refer to the [cnos_interface module documentation](http://ralfss28.labs.lenovo.com:5555/help/topic/com.lenovo.switchmgt.ansible.doc/cnos_interface.html?cp=0_3_1_0_2_12) for detailed information on usage. The values of these variables depend on the configuration context and the choices are the following: specify a LAG number, **authentication**, **echo**, **ipv4**, **ipv6**, **interval**, **neighbor**, **access**, **mode**, **trunk**, interface description, **auto**, **full**, **half**, **receive**, **send**, **access-group**, **arp**, **dhcp**, **port**, **port-unreachable**, **redirects**, **router**, **unreachables**, **address**, **link-local**, **port-priority**, **suspend-individual**, **timeout**, **transmit**, **trap-notification**, **tlv-select**, load interval delay, **counter**, name for the MAC access group, MAC address in XXXX.XXXX.XXXX format, threshold value, MTU in bytes, instance ID to map to the EVC, **input**, **output**, **copp-system-policy**, **type**, **bpdufilter**, **bpduguard**, **cost**, **enable**, **disable**, **guard**, **link-type**, **mst**, **port**, **port-priority**, **vlan**, **auto**, 1000, 10000, 40000, **broadcast**, **unicast**, **multicast**, **egress-only**, **destination-ip**, **destination-mac**, **destination-port**, **source-dest-ip**, **source-dest-mac**, **source-dest-port**, **source-interface**, **source-ip**, **source-mac**, **source-port**.
`interfaceArg3` | This is an overloaded BGP variable. Please refer to the [cnos_interface module documentation](http://ralfss28.labs.lenovo.com:5555/help/topic/com.lenovo.switchmgt.ansible.doc/cnos_interface.html?cp=0_3_1_0_2_12) for detailed information on usage. The values of these variables depend on the configuration context and the choices are the following: **active**, **passive**, **on**, **keyed-md5**, **keyed-sha1**, **meticulous-keyed-md5**, **meticulous-keyed-sha1**, **simple**, **authentication**, **echo**, **interval**, interval value, source IP address, **off**, ACL name, IP address of the ARP entry, **timeout**, **client**, **relay**, **area**, **multi-area**, **dhcp**, IPv6 address, IPv6 address of the DHCP Relay, Neighbor IPv6 address, LACP port priority, **long**, **short**, **link-aggregation**, **mac-phy-status**, **management-address**, **max-frame-size**, **port-description**, **port-protocol-vlan**, **port-vlan**, **power-mdi**, **protocol-identity**, **system-capabilities**, **system-description**, **system-name**, **vid-management**, **vlan-name**, counter for the load interval, name of the policy to attach, **all**, COPP class name to attach, **qos**, **queuing**, **enable**, **disable**, **auto**, port path cost, **loop**, **root**, **auto**, **point-to-point**, **shared**, MSTP instance range, port priority value, specify VLAN, allowed traffic level, **ipv6**, **source-interface**.
`interfaceArg4` | This is an overloaded BGP variable. Please refer to the [cnos_interface module documentation](http://ralfss28.labs.lenovo.com:5555/help/topic/com.lenovo.switchmgt.ansible.doc/cnos_interface.html?cp=0_3_1_0_2_12) for detailed information on usage. The values of these variables depend on the configuration context and the choices are the following: **key-chain**, **key-id**, **keyed-md5**, **keyed-sha1**, **meticulous-keyed-md5**, **meticulous-keyed-sha1**, **simple**, interval value, BFD minimum receive interval, destination IP address, **in**, **out**, MAC address in XXXX.XXXX.XXXX format, timeout value, **class-id**, **request**, IPv4 address of the DHCP Relay, OSPF area ID, **anycast**, **secondary**, **ethernet**, **vlan**, load interval delay, name of the QoS policy to attach, **input**, **output**, **cost**, **port-priority**.
`interfaceArg5` | This is an overloaded BGP variable. Please refer to the [cnos_interface module documentation](http://ralfss28.labs.lenovo.com:5555/help/topic/com.lenovo.switchmgt.ansible.doc/cnos_interface.html?cp=0_3_1_0_2_12) for detailed information on usage. The values of these variables depend on the configuration context and the choices are the following: name of the key chain, key ID, **key-chain**, **key-id**, BFD minimum receive interval, Hello multiplier value, **admin-down**, **multihop**, **non-persistent**, vendor class ID name, **bootfile-name**, **host-name**, **log-server**, **ntp-server**, **tftp-server-name**, specifiy ethernet port, specify VLAN, name of the QoS policy to attach, **auto**, port path cost, port priority value. 
`interfaceArg6` | This is an overloaded BGP variable. Please refer to the [cnos_interface module documentation](http://ralfss28.labs.lenovo.com:5555/help/topic/com.lenovo.switchmgt.ansible.doc/cnos_interface.html?cp=0_3_1_0_2_12) for detailed information on usage. The values of these variables depend on the configuration context and the choices are the following: authentication key string, name of the key chain, key ID, Hello multiplier value, **admin-down**, **non-persistent**.
`interfaceArg7` | This is an overloaded BGP variable. Please refer to the [cnos_interface module documentation](http://ralfss28.labs.lenovo.com:5555/help/topic/com.lenovo.switchmgt.ansible.doc/cnos_interface.html?cp=0_3_1_0_2_12) for detailed information on usage. The values of these variables depend on the configuration context and the choices are the following: authentication key string, **admin-down**.


## Dependencies
---
<add dependencies information below>

- username.iptables - Configures the firewall and blocks all ports except those needed for web server and SSH access.
- username.common - Performs common server configuration.
- cnos_interface.py - This modules needs to be present in the *library* directory of the role.
- cnos.py - This module needs to be present in the PYTHONPATH environment variable set in the Ansible system.
- /etc/ansible/hosts - You must edit the */etc/ansible/hosts* file with the device information of the switches designated as leaf switches. You may refer to *cnos_interface_sample_hosts* for a sample configuration.

Ansible keeps track of all network elements that it manages through a hosts file. Before the execution of a playbook, the hosts file must be set up.

Open the */etc/ansible/hosts* file with root privileges. Most of the file is commented out by using **#**. You can also comment out the entries you will be adding by using **#**. You need to copy the content of the hosts file for the role into the */etc/ansible/hosts* file. The sample hosts file for the role is located in the main directory.

```
[cnos_ethernet_sample]
10.241.107.39   username=<username> password=<password> deviceType=g8272_cnos
10.241.107.40   username=<username> password=<password> deviceType=g8272_cnos 
```
    
**Note:** You need to change the IP addresses to fit your specific topology. You also need to change the `<username>` and `<password>` to the appropriate values used to log into the specific Lenovo network devices.


## Example Playbook
---
<add playbook samples below>

To execute an Ansible playbook, use the following command:

```
ansible-playbook cnos_interface_sample.yml -vvv
```

`-vvv` is an optional verbos command that helps identify what is happening during playbook execution. The playbook for each role is located in the main directory of the solution.

```
 - name: Module to  do Interface Ethernet configurations
   hosts: cnos_ethernet_sample
   gather_facts: no
   connection: local
   roles:
    - cnos_ethernet_sample
```


## License
---
<add license information below>
Copyright (C) 2017 Lenovo, Inc.

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Ansible is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Ansible.  If not, see <http://www.gnu.org/licenses/>.