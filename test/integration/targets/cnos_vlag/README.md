# Ansible Role: cnos_vlag_sample - Switch vLAG configuration
---
<add role description below>

This role is an example of using the *cnos_vlag.py* Lenovo module in the context of CNOS switch configuration. This module allows you to work with virtual Link Aggregation Groups (vLAG) related configurations. The operators used are overloaded to ensure control over switch vLAG configurations.

Apart from the regular device connection related attributes, there are four vLAG arguments which are overloaded variables that will perform further configurations. They are *vlagArg1*, *vlagArg2*, *vlagArg3*, and *vlagArg4*.

The results of the operation can be viewed in *results* directory.

For more details, see [Lenovo modules for Ansible: cnos_vlag](http://systemx.lenovofiles.com/help/index.jsp?topic=%2Fcom.lenovo.switchmgt.ansible.doc%2Fcnos_vlag.html&cp=0_3_1_0_4_15).


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
`vlagArg1` | This is an overloaded BGP variable. Please refer to the [cnos_vlag module documentation](http://ralfss28.labs.lenovo.com:5555/help/topic/com.lenovo.switchmgt.ansible.doc/cnos_template.html?cp=0_3_1_0_2_10) for detailed information on usage. The values of these variables depend on the configuration context and the choices are the following: **enable**, **auto-recovery**, **config-consistency**, **isl**, **mac-address-table**, **peer-gateway**, **priority**, **startup-delay**, **tier-id**, **vrrp**, **instance**, **hlthchk**.
`vlagArg2` | This is an overloaded BGP variable. Please refer to the [cnos_vlag module documentation](http://ralfss28.labs.lenovo.com:5555/help/topic/com.lenovo.switchmgt.ansible.doc/cnos_template.html?cp=0_3_1_0_2_10) for detailed information on usage. The values of these variables depend on the configuration context and the choices are the following: auto-recovery interval, **disabled**, **strict**, port aggregation number, vLAG priority, delay time, vLAG tier ID value, vLAG instance number, **keepalive-attempts**, **keepalive-interval**, **retry-interval**, **peer-ip**.
`vlagArg3` | This is an overloaded BGP variable. Please refer to the [cnos_vlag module documentation](http://ralfss28.labs.lenovo.com:5555/help/topic/com.lenovo.switchmgt.ansible.doc/cnos_template.html?cp=0_3_1_0_2_10) for detailed information on usage. The values of these variables depend on the configuration context and the choices are the following: **enable**, **port-aggregation**, number of Keep Alive attempts, Keep Alive interval, retry interval, vLAG Health Check peer IP address.
`vlagArg4` | This is an overloaded BGP variable. Please refer to the [cnos_vlag module documentation](http://ralfss28.labs.lenovo.com:5555/help/topic/com.lenovo.switchmgt.ansible.doc/cnos_template.html?cp=0_3_1_0_2_10) for detailed information on usage. The values of these variables depend on the configuration context and the choices are the following: LAG Number, **default**, **management**.


## Dependencies
---
<add dependencies information below>

- username.iptables - Configures the firewall and blocks all ports except those needed for web server and SSH access.
- username.common - Performs common server configuration.
- cnos_vlag.py - This modules needs to be present in the *library* directory of the role.
- cnos.py - This module needs to be present in the PYTHONPATH environment variable set in the Ansible system.
- /etc/ansible/hosts - You must edit the */etc/ansible/hosts* file with the device information of the switches designated as leaf switches. You may refer to *cnos_vlag_sample_hosts* for a sample configuration.

Ansible keeps track of all network elements that it manages through a hosts file. Before the execution of a playbook, the hosts file must be set up.

Open the */etc/ansible/hosts* file with root privileges. Most of the file is commented out by using **#**. You can also comment out the entries you will be adding by using **#**. You need to copy the content of the hosts file for the role into the */etc/ansible/hosts* file. The sample hosts file for the role is located in the main directory.

```
[cnos_vlag_sample]
10.241.107.39   ansible_network_os=cnos ansible_ssh_user=<username> ansible_ssh_pass=<password> deviceType=g8272_cnos
10.241.107.40   ansible_network_os=cnos ansible_ssh_user=<username> ansible_ssh_pass=<password> deviceType=g8272_cnos
```
    
**Note:** You need to change the IP addresses to fit your specific topology. You also need to change the `<username>` and `<password>` to the appropriate values used to log into the specific Lenovo network devices.


## Example Playbook
---
<add playbook samples below>

To execute an Ansible playbook, use the following command:

```
ansible-playbook cnos_vlag_sample.yml -vvv
```

`-vvv` is an optional verbos command that helps identify what is happening during playbook execution. The playbook for each role is located in the main directory of the solution.

```
 - name: Module to  do VLAG configurations
   hosts: cnos_vlag_sample
   gather_facts: no
   connection: local
   roles:
    - cnos_vlag_sample
```


## License
---
<add license information below>
Copyright (C) 2017 Lenovo, Inc.

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Ansible is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
