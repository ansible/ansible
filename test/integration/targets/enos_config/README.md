# Ansible Role: enos_config - Executes any Configuration command on switch and results are displayed.
---
<add role description below>

  Lenovo ENOS configurations use a simple block indent file syntax
  for segmenting configuration into sections.  This module provides
  an implementation for working with ENOS configuration sections in
  a deterministic way.

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

These are the various options the customer have in executing the enos_config modules:

Variable | Description
--- | ---
`lines`  | The ordered set of commands that should be configured in the section.  The commands must be the exact same commands as found in the device running-config.  Be sure to note the configuration command syntax as some commands are automatically modified by the device config parser.
`parents`  | The ordered set of parents that uniquely identify the section the commands should be checked against.  If the parents argument is omitted, the commands are checked against the set of top level or global commands.
`src`  | Specifies the source path to the file that contains the configuration or configuration template to load.  The path to the source file can either be the full path on the Ansible control host or a relative path from the playbook or role root directory.  This argument is mutually exclusive with I(lines), I(parents).
`before`  | The ordered set of commands to push on to the command stack if a change needs to be made.  This allows the playbook designer the opportunity to perform configuration commands prior to pushing any changes without affecting how the set of commands are matched against the system.
`after`  | The ordered set of commands to append to the end of the command stack if a change needs to be made.  Just like with I(before) this allows the playbook designer to append a set of commands to be executed after the command set.
`replace`  | Instructs the module on the way to perform the configuration on the device.  If the replace argument is set to I(line) then the modified lines are pushed to the device in configuration mode.  If the replace argument is set to I(block) then the entire command block is pushed to the device in configuration mode if any line is not correct.
`config`  | The module, by default, will connect to the remote device and retrieve the current running-config to use as a base for comparing against the contents of source.  There are times when it is not desirable to have the task get the current running-config for every task in a playbook.  The I(config) argument allows the implementer to pass in the configuration to use as the base config for comparison.
`backup`  |  This argument will cause the module to create a full backup of the current C(running-config) from the remote device before any changes are made.  The backup file is written to the C(backup) folder in the playbook root directory.  If the directory does not exist, it is created.
`match`  |Instructs the module on the way to perform the matching of the set of commands against the current device config. If match is set to I(line), commands are matched line by line. If match is set to I(strict), command lines are matched with respect to position.  If match is set to I(exact), command lines must be an equal match.  Finally, if match is set to I(none), the module will not attempt to compare the source configuration with the running configuration on the remote device.
`comment`  |  Allows a commit description to be specified to be included when the configuration is committed.  If the configuration is not changed or committed, this argument is ignored.
`admin`  |  Enters into administration configuration mode for making config changes to the device.


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
- enos_config.py - This module file will be located at lib/ansible/modules/network/enos/ of Ansible installation.
- enos.py - This module util file will be located at lib/ansible/module_utils/network/enos of Ansible installation.
- enos.py - This module plugin file will be located at lib/ansible/plugins/action of Ansible installation.
- enos_config.py - This module plugin file will be located at lib/ansible/plugins/action of Ansible installation.
- enos.py - This module plugin file will be located at lib/ansible/plugins/cliconf of Ansible installation.
- enos.py - This module plugin file will be located at lib/ansible/plugins/cliconf of Ansible installation.
- /etc/ansible/hosts - You must edit the */etc/ansible/hosts* file with the device information of the switches designated as leaf switches. You may refer to *cnos_command_sample_hosts* for a sample configuration.

Ansible keeps track of all network elements that it manages through a hosts file. Before the execution of a playbook, the hosts file must be set up.

Open the */etc/ansible/hosts* file with root privileges. Most of the file is commented out by using **#**. You can also comment out the entries you will be adding by using **#**. You need to copy the content of the hosts file for the role into the */etc/ansible/hosts* file. The sample hosts file for the role is located in the main directory.

```
[enos_config]
10.241.105.24    ansible_connection=network_cli ansible_network_os=enos ansible_ssh_user=<username> ansible_ssh_pass=<password>
```

**Note:** You need to change the IP addresses to fit your specific topology. You also need to change the `<username>` and `<password>` to the appropriate values used to log into the specific Lenovo network devices.


## Example Playbook
---
<add playbook samples below>

To execute an Ansible playbook, use the following command:

```
ansible-playbook enos_config_sample.yml -vvv
```

`-vvv` is an optional verbose command that helps identify what is happening during playbook execution. The playbook for each role is located in the main directory of the solution.

```
 - name: Module to  do some CLI Command configurations
   hosts: enos_config
   gather_facts: no
   connection: network_cli
   roles:
    - enos_config
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
