# Ansible Role: cnos_bgp_sample - CNOS Switch BGP Configuration
---
<add role description below>

This role is an example of using the *cnos_bgp.py* Lenovo module in the context of CNOS switch configuration. This module allows you to work with Border Gateway Protocol (BGP) related configurations. The operators used are overloaded to ensure control over switch BGP configurations. This module is invoked using method with *asNumber* as one of its arguments.

The first level of the BGP configuration allows to set up an AS number, with the following attributes going into various configuration operations under the context of BGP. After passing this level, there are eight BGP arguments that will perform further configurations. They are *bgpArg1*, *bgpArg2*, *bgpArg3*, *bgpArg4*, *bgpArg5*, *bgpArg6*, *bgpArg7*, and *bgpArg8*.

The results of the operation can be viewed in *results* directory.

For more details, see [Lenovo modules for Ansible: cnos_bgp](http://systemx.lenovofiles.com/help/index.jsp?topic=%2Fcom.lenovo.switchmgt.ansible.doc%2Fcnos_bgp.html&cp=0_3_1_0_4_16).


## Requirements
---
<add role requirements information below>

- Ansible version 2.2 or later ([Ansible installation documentation](http://docs.ansible.com/ansible/intro_installation.html))
- Lenovo switches running CNOS version 10.2.1.0 or later
- an SSH connection to the Lenovo switch (SSH must be enabled on the network device)


## Role Variables
---
<add role variables information below>

Available variables are listed below, along with description.

The following are mandatory inventory variables:

Variable | Description
--- | ---
`ansible_connection` | Has to be `network_cli`
`ansible_network_os` | Has to be `cnos`
`ansible_ssh_user` | Specifies the username used to log into the switch
`ansible_ssh_pass` | Specifies the password used to log into the switch
`enablePassword` | Configures the password used to enter Global Configuration command mode on the switch (this is an optional parameter)
`hostname` | Searches the hosts file at */etc/ansible/hosts* and identifies the IP address of the switch on which the role is going to be applied
`deviceType` | Specifies the type of device from where the configuration will be backed up (**g8272_cnos** - G8272, **g8296_cnos** - G8296, **g8332_cnos** - G8332, **NE10032** - NE10032, **NE1072T** - NE1072T, **NE1032** - NE1032, **NE1032T** - NE1032T, **NE2572** - NE2572, **NE0152T** - NE0152T)

The values of the variables used need to be modified to fit the specific scenario in which you are deploying the solution. To change the values of the variables, you need to visits the *vars* directory of each role and edit the *main.yml* file located there. The values stored in this file will be used by Ansible when the template is executed.

The syntax of *main.yml* file for variables is the following:

```
<template variable>:<value>
```

You will need to replace the `<value>` field with the value that suits your topology. The `<template variable>` fields are taken from the template and it is recommended that you leave them unchanged.

Variable | Description
--- | ---
`asNum` | Specifies the AS number
`bgpArg1` | This is an overloaded BGP variable. Please refer to the [cnos_bgp module documentation](http://ralfss28.labs.lenovo.com:5555/help/topic/com.lenovo.switchmgt.ansible.doc/cnos_bgp.html?cp=0_3_1_0_2_13) for detailed information on usage. The values of these variables depend on the configuration context and the choices are the following: **address-family**, **bestpath**, **bgp**, **cluster-id**, **confederation**, **enforce-first-as**, **fast-external-failover**, **graceful-restart**, **graceful-restart-helper**, **log-neighbor-changes**, **maxas-limit**, **neighbor**, **router-id**, **shutdown**, **synchronization**, **timers**, **vrf**.
`bgpArg2` | This is an overloaded BGP variable. Please refer to the [cnos_bgp module documentation](http://ralfss28.labs.lenovo.com:5555/help/topic/com.lenovo.switchmgt.ansible.doc/cnos_bgp.html?cp=0_3_1_0_2_13) for detailed information on usage. The values of these variables depend on the configuration context and the choices are the following: **ipv4**, **ipv6**, **always-compare-med**, **compare-confed-aspath**, **compare-routerid**, **dont-compare-originator-id**, **tie-break-on-age**, **as-path**, **med**, number of times to prepend the local AS, Route Reflector Cluster ID as a 32 bit quantity or in IP address format, **identifier**, **peers**, delay value, number of autonomous systems in the AS-path attribute, neighbor address, neighbor prefix, manually configured router identifier, keepalive interval.
`bgpArg3` | This is an overloaded BGP variable. Please refer to the [cnos_bgp module documentation](http://ralfss28.labs.lenovo.com:5555/help/topic/com.lenovo.switchmgt.ansible.doc/cnos_bgp.html?cp=0_3_1_0_2_13) for detailed information on usage. The values of these variables depend on the configuration context and the choices are the following: **aggregate-address**, **client-to-client**, **dampening**, **distance**, **maximum-paths**, **network**, **nexthop**, **redistribute**, **save**, **synchronization**, **ignore**, **multipath-relax**, **confed**, **missing-as-worst**, **non-deterministic**, **remove-recv-med**, **remove-send-med**, set routing domain confederation AS, AS number.
`bgpArg4` | This is an overloaded BGP variable. Please refer to the [cnos_bgp module documentation](http://ralfss28.labs.lenovo.com:5555/help/topic/com.lenovo.switchmgt.ansible.doc/cnos_bgp.html?cp=0_3_1_0_2_13) for detailed information on usage. The values of these variables depend on the configuration context and the choices are the following: IP address/prefix length, **route-map**, time after which a penalty is decreased by half, administrative distance to routes outside the AS, **ebgp**, **ibgp**, **synchronization**, IP address, delay value, **direct**, **ospf**, **static**, **memory**.
`bgpArg5` | This is an overloaded BGP variable. Please refer to the [cnos_bgp module documentation](http://ralfss28.labs.lenovo.com:5555/help/topic/com.lenovo.switchmgt.ansible.doc/cnos_bgp.html?cp=0_3_1_0_2_13) for detailed information on usage. The values of these variables depend on the configuration context and the choices are the following: **as-set**, **summary-only**, name of the route map that controls where BGP route dampening is enabled, value to start reusing a route, administrative distance to routes inside the AS, value for maximum path numbers, **backdoor**, **mask**, **route-map**.
`bgpArg6` | This is an overloaded BGP variable. Please refer to the [cnos_bgp module documentation](http://ralfss28.labs.lenovo.com:5555/help/topic/com.lenovo.switchmgt.ansible.doc/cnos_bgp.html?cp=0_3_1_0_2_13) for detailed information on usage. The values of these variables depend on the configuration context and the choices are the following: **summary-only**, **as-set**, value to start suppressing a route, administrative distance for local routes, IP subnet address mask, name of the route map.
`bgpArg7` | This is an overloaded BGP variable. Please refer to the [cnos_bgp module documentation](http://ralfss28.labs.lenovo.com:5555/help/topic/com.lenovo.switchmgt.ansible.doc/cnos_bgp.html?cp=0_3_1_0_2_13) for detailed information on usage. The values of these variables depend on the configuration context and the choices are the following: maximum duration to suppress a stable route, **route-map**, **backdoor**.
'bgpArg8' | This is an overloaded BGP variable. Please refer to the [cnos_bgp module documentation](http://ralfss28.labs.lenovo.com:5555/help/topic/com.lenovo.switchmgt.ansible.doc/cnos_bgp.html?cp=0_3_1_0_2_13) for detailed information on usage. The values of these variables depend on the configuration context and the choices are the following: time after which an unreachable route's penalty is decreased by half, **backdoor**.

## Dependencies
---
<add dependencies information below>

- username.iptables - Configures the firewall and blocks all ports except those needed for web server and SSH access.
- username.common - Performs common server configuration.
- cnos_bgp.py - This modules needs to be present in the *library* directory of the role.
- cnos.py - This module needs to be present in the PYTHONPATH environment variable set in the Ansible system.
- /etc/ansible/hosts - You must edit the */etc/ansible/hosts* file with the device information of the switches designated as leaf switches. You may refer to *cnos_bgp_sample_hosts* for a sample configuration.

Ansible keeps track of all network elements that it manages through a hosts file. Before the execution of a playbook, the hosts file must be set up.

Open the */etc/ansible/hosts* file with root privileges. Most of the file is commented out by using **#**. You can also comment out the entries you will be adding by using **#**. You need to copy the content of the hosts file for the role into the */etc/ansible/hosts* file. The sample hosts file for the role is located in the main directory.

```
[cnos_bgp_sample]
10.241.107.39   ansible_network_os=cnos ansible_ssh_user=<username> ansible_ssh_pass=<password> deviceType=g8272_cnos
10.241.107.40   ansible_network_os=cnos ansible_ssh_user=<username> ansible_ssh_pass=<password> deviceType=g8272_cnos
```

**Note:** You need to change the IP addresses to fit your specific topology. You also need to change the `<username>` and `<password>` to the appropriate values used to log into the specific Lenovo network devices.


## Example Playbook
---
<add playbook samples below>

To execute an Ansible playbook, use the following command:

```
ansible-playbook cnos_bgp_sample.yml -vvv
```

`-vvv` is an optional verbose command that helps identify what is happening during playbook execution. The playbook for each role is located in the main directory of the solution.

```
- name: Module to do BGP configuration
   hosts: cnos_bgp_sample
   gather_facts: no
   connection: local
   roles:
    - cnos_bgp_sample
```


## License
---
<add license information below>
Copyright (C) 2017 Lenovo, Inc.

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Ansible is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
