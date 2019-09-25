# Ansible Role: cnos_conditional_command_sample - Executing a single CNOS command with respect to conditions specified in the inventory
---
<add role description below>

This role is an example of using the *cnos_conditional_command.py* Lenovo module in the context of CNOS switch configuration. This module allows you to modify the running configuration of a switch. It provides a way to execute a single CNOS command on a network device by evaluating the current running configuration and executing the command only if the specific settings have not been already configured.

The CNOS command is passed as an argument of the method.

This module functions the same as the *cnos_command.py* module. The only exception is that the following inventory variable can be specified: condition = &lt;flag string&gt;

When this inventory variable is specified as the variable of a task, the command is executed for the network element that matches the flag string.
Usually, commands are executed across a group of network devices. When there is a requirement to skip the execution of the command on one or more devices, it is recommended to use this module.

The results of the operation can be viewed in *results* directory.

For more details, see [Lenovo modules for Ansible: cnos_conditional_command](http://systemx.lenovofiles.com/help/index.jsp?topic=%2Fcom.lenovo.switchmgt.ansible.doc%2Fcnos_conditional_command.html&cp=0_3_1_0_4_9).


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
`condition` | If `condition=false` is specified in the inventory file against any device, the command execution is skipped for that device (**true**, **false**)

The values of the variables used need to be modified to fit the specific scenario in which you are deploying the solution. To change the values of the variables, you need to visits the *vars* directory of each role and edit the *main.yml* file located there. The values stored in this file will be used by Ansible when the template is executed.

The syntax of *main.yml* file for variables is the following:

```
<template variable>:<value>
```

You will need to replace the `<value>` field with the value that suits your topology. The `<template variable>` fields are taken from the template and it is recommended that you leave them unchanged.

Variable | Description
--- | ---
`flag` | If a task needs to be executed, the flag needs to be set the same as it is specified in the inventory for that device
`clicommand` | Specifies the CLI command as an attribute to this method



## Dependencies
---
<add dependencies information below>

- username.iptables - Configures the firewall and blocks all ports except those needed for web server and SSH access.
- username.common - Performs common server configuration.
- cnos_conditional_command.py - This modules needs to be present in the *library* directory of the role.
- cnos.py - This module needs to be present in the PYTHONPATH environment variable set in the Ansible system.
- /etc/ansible/hosts - You must edit the */etc/ansible/hosts* file with the device information of the switches designated as leaf switches. You may refer to *cnos_conditional_command_sample_hosts* for a sample configuration.

Ansible keeps track of all network elements that it manages through a hosts file. Before the execution of a playbook, the hosts file must be set up.

Open the */etc/ansible/hosts* file with root privileges. Most of the file is commented out by using **#**. You can also comment out the entries you will be adding by using **#**. You need to copy the content of the hosts file for the role into the */etc/ansible/hosts* file. The sample hosts file for the role is located in the main directory.

```
[cnos_conditional_command_sample]
10.241.107.39   ansible_network_os=cnos ansible_ssh_user=<username> ansible_ssh_pass=<password> deviceType=g8272_cnos condition=pass
10.241.107.40   ansible_network_os=cnos ansible_ssh_user=<username> ansible_ssh_pass=<password> deviceType=g8272_cnos
```

**Note:** You need to change the IP addresses to fit your specific topology. You also need to change the `<username>` and `<password>` to the appropriate values used to log into the specific Lenovo network devices.


## Example Playbook
---
<add playbook samples below>

To execute an Ansible playbook, use the following command:

```
ansible-playbook cnos_conditional_command_sample.yml -vvv
```

`-vvv` is an optional verbose command that helps identify what is happening during playbook execution. The playbook for each role is located in the main directory of the solution.

```
 - name: Module to  do some configurations
   hosts: cnos_conditional_command_sample
   gather_facts: no
   connection: local
   roles:
    - cnos_conditional_command_sample
```


## License
---
<add license information below>
Copyright (C) 2017 Lenovo, Inc.

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Ansible is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
