# Ansible Role: enos_command - Executes any CLI command on switch and results are displayed.
---
<add role description below>

 Sends arbitrary commands to an ENOS node and returns the results
 read from the device. The C(enos_command) module includes an
 argument that will cause the module to wait for a specific condition
 before returning or timing out if the condition is not met.

## Requirements
---
<add role requirements information below>

- Ansible version 2.4 or later ([Ansible installation documentation](http://docs.ansible.com/ansible/intro_installation.html))
- Lenovo switches running ENOS version 8.4.1.0 or later
- an SSH connection to the Lenovo switch (SSH must be enabled on the network device)


## Role Variables
---
<add role variables information below>
Available variables are listed below, along with description.

The following are mandatory inventory variables:

Variable | Description
--- | ---
`ansible_connection` | Has to be `network_cli`
`ansible_network_os` | Has to be `enos`
`ansible_ssh_user` | Specifies the username used to log into the switch
`ansible_ssh_pass` | Specifies the password used to log into the switch

These are the various options the customer have in executing the enos_command modules:

Variable | Description
--- | ---
`commands`  | List of commands to send to the remote device over the configured provider. The resulting output from the command is returned. If the I(wait_for) argument is provided, the module is not returned until the condition is satisfied or the number of retires as expired.
`wait_for`  | List of conditions to evaluate against the output of the command. The task will wait for each condition to be true before moving forward. If the conditional is not true within the configured number of retries, the task fails. See examples.
`match`  | The I(match) argument is used in conjunction with the I(wait_for) argument to specify the match policy.  Valid   values are C(all) or C(any).  If the value is set to C(all) then all conditionals in the wait_for must be satisfied.  If       the value is set to C(any) then only one of the values must be satisfied.
`retries`  | Specifies the number of retries a command should by tried before it is considered failed. The command is run on the target device every retry and evaluated against the I(wait_for) conditions.
`interval`  | Configures the interval in seconds to wait between retries of the command. If the command does not pass the specified conditions, the interval indicates how long to wait before trying the command again.

Need to specify these variables in vars/main.yml under variable `cli`

Variable | Description
--- | ---
`host`  | Has to be "{{ inventory_hostname }}"
`port`  | Has to be`22`
`username`  | User Name of switch
`password`  | Password of switch
`timeout`  | time out value for CLI
`authorize`  | Whether u have to enter enable mode for data collection.
`auth_pass`| Enable Password if required


## Dependencies
---
<add dependencies information below>

- username.iptables - Configures the firewall and blocks all ports except those needed for web server and SSH access.
- username.common - Performs common server configuration.
- enos_command.py - This module file will be located at lib/ansible/modules/network/enos/ of Ansible installation.
- enos.py - This module util file will be located at lib/ansible/module_utils/network/enos of Ansible installation.
- enos.py - This module plugin file will be located at lib/ansible/plugins/action of Ansible installation.
- enos.py - This module plugin file will be located at lib/ansible/plugins/cliconf of Ansible installation.
- enos.py - This module plugin file will be located at lib/ansible/plugins/cliconf of Ansible installation.
- /etc/ansible/hosts - You must edit the */etc/ansible/hosts* file with the device information of the switches designated as leaf switches. You may refer to *cnos_command_sample_hosts* for a sample configuration.

Ansible keeps track of all network elements that it manages through a hosts file. Before the execution of a playbook, the hosts file must be set up.

Open the */etc/ansible/hosts* file with root privileges. Most of the file is commented out by using **#**. You can also comment out the entries you will be adding by using **#**. You need to copy the content of the hosts file for the role into the */etc/ansible/hosts* file. The sample hosts file for the role is located in the main directory.

```
[enos_command]
10.241.105.24    ansible_connection=network_cli ansible_network_os=enos ansible_ssh_user=<username> ansible_ssh_pass=<password>
```

**Note:** You need to change the IP addresses to fit your specific topology. You also need to change the `<username>` and `<password>` to the appropriate values used to log into the specific Lenovo network devices.


## Example Playbook
---
<add playbook samples below>

To execute an Ansible playbook, use the following command:

```
ansible-playbook enos_command_sample.yml -vvv
```

`-vvv` is an optional verbose command that helps identify what is happening during playbook execution. The playbook for each role is located in the main directory of the solution.

```
 - name: Module to  do some CLI Command configurations
   hosts: enos_command
   gather_facts: no
   connection: network_cli
   roles:
    - enos_command
```

## License
---
<add license information below>
Copyright (C) 2017 Lenovo, Inc.

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, eithe
r version 3 of the License, or (at your option) any later version.

Ansible is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PU
RPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
