# Ansible Role: cnos_save_sample - Saving the switch running configuration
---
<add role description below>

This role is an example of using the *cnos_save.py* Lenovo module in the context of CNOS switch configuration. This module allows you to copy the running configuration of a switch over its startup configuration. It is recommended to use this module shortly after any major configuration changes so they persist after a switch restart.

The results of the operation can be viewed in *results* directory.

For more details, see [Lenovo modules for Ansible: cnos_save](http://systemx.lenovofiles.com/help/index.jsp?topic=%2Fcom.lenovo.switchmgt.ansible.doc%2Fcnos_save.html&cp=0_3_1_0_4_3).


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
`username` | Specifies the username used to log into the switch
`password` | Specifies the password used to log into the switch
`enablePassword` | Configures the password used to enter Global Configuration command mode on the switch (this is an optional parameter)
`hostname` | Searches the hosts file at */etc/ansible/hosts* and identifies the IP address of the switch on which the role is going to be applied
`deviceType` | Specifies the type of device from where the configuration will be backed up (**g8272_cnos** - G8272, **g8296_cnos** - G8296)


## Dependencies
---
<add dependencies information below>

- username.iptables - Configures the firewall and blocks all ports except those needed for web server and SSH access.
- username.common - Performs common server configuration.
- cnos_save.py - This modules needs to be present in the *library* directory of the role.
- cnos.py - This module needs to be present in the PYTHONPATH environment variable set in the Ansible system.
- /etc/ansible/hosts - You must edit the */etc/ansible/hosts* file with the device information of the switches designated as leaf switches. You may refer to *cnos_save_sample_hosts* for a sample configuration.

Ansible keeps track of all network elements that it manages through a hosts file. Before the execution of a playbook, the hosts file must be set up.

Open the */etc/ansible/hosts* file with root privileges. Most of the file is commented out by using **#**. You can also comment out the entries you will be adding by using **#**. You need to copy the content of the hosts file for the role into the */etc/ansible/hosts* file. The sample hosts file for the role is located in the main directory.

```
[cnos_save_sample]
10.241.107.39   username=<username> password=<password> deviceType=g8272_cnos
10.241.107.40   username=<username> password=<password> deviceType=g8272_cnos 
```
    
**Note:** You need to change the IP addresses to fit your specific topology. You also need to change the `<username>` and `<password>` to the appropriate values used to log into the specific Lenovo network devices.
 

## Example Playbook
---
<add playbook samples below>

To execute an Ansible playbook, use the following command:

```
ansible-playbook cnos_save_sample.yml -vvv
```

`-vvv` is an optional verbos command that helps identify what is happening during playbook execution. The playbook for each role is located in the main directory of the solution.

```
 - name: Module to  do save configurations
   hosts: cnos_save_sample
   gather_facts: no
   connection: local
   roles:
    - cnos_save_sample
```


## License
---
<add license information below>
Copyright (C) 2017 Lenovo, Inc.

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Ansible is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Ansible.  If not, see <http://www.gnu.org/licenses/>.