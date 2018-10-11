# Ansible Role: cnos_image_sample - Switch firmware download from a remote server
---
<add role description below>

This role is an example of using the *cnos_image.py* Lenovo module in the context of CNOS switch configuration. This module allows you to work with switch firmware images. It provides a way to download a firmware image to a network device from a remote server using FTP, SFTP, TFTP, or SCP.

The first step is to create a directory from where the remote server can be reached. The next step is to provide the full file path of the image location. Authentication details required by the remote server must be provided as well.

By default, this method makes the newly downloaded firmware image the active image, which will be used by the switch during the next restart.

The results of the operation can be viewed in *results* directory.

For more details, see [Lenovo modules for Ansible: cnos_image](http://systemx.lenovofiles.com/help/index.jsp?topic=%2Fcom.lenovo.switchmgt.ansible.doc%2Fcnos_image.html&cp=0_3_1_0_4_2).


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
`imgType` | Specifies the firmware image type to be downloaded (**all** - both Uboot and OS images, **boot** - only the Uboot image, **os** - only the OS image, **onie** - ONIE image)
`protocol` | Specifies the protocol used by the network device to interact with the remote server from where to download the firmware image (**ftp** - FTP, **sftp** - SFTP, **tftp** - TFTP, **scp** - SCP)
`serverip` | Specifies the IP Address of the remote server from where the software image will be downloaded
`imgpath` | Specifies the full file path of the image located on the remote server (in case the relative path is used as the variable value, the root folder for the user of the server needs to be specified)
`serverusername` | Configures the username for the server relating to the protocol used
`serverpassword` | Configures the password for the server relating to the protocol used


## Dependencies
---
<add dependencies information below>

- username.iptables - Configures the firewall and blocks all ports except those needed for web server and SSH access.
- username.common - Performs common server configuration.
- cnos_image.py - This modules needs to be present in the *library* directory of the role.
- cnos.py - This module needs to be present in the PYTHONPATH environment variable set in the Ansible system.
- /etc/ansible/hosts - You must edit the */etc/ansible/hosts* file with the device information of the switches designated as leaf switches. You may refer to *cnos_image_sample_hosts* for a sample configuration.

Ansible keeps track of all network elements that it manages through a hosts file. Before the execution of a playbook, the hosts file must be set up.

Open the */etc/ansible/hosts* file with root privileges. Most of the file is commented out by using **#**. You can also comment out the entries you will be adding by using **#**. You need to copy the content of the hosts file for the role into the */etc/ansible/hosts* file. The sample hosts file for the role is located in the main directory.

```
[cnos_image_sample]
10.241.107.39   ansible_network_os=cnos ansible_ssh_user=<username> ansible_ssh_pass=<password> deviceType=g8272_cnos
10.241.107.40   ansible_network_os=cnos ansible_ssh_user=<username> ansible_ssh_pass=<password> deviceType=g8272_cnos
```
 
**Note:** You need to change the IP addresses to fit your specific topology. You also need to change the `<username>` and `<password>` to the appropriate values used to log into the specific Lenovo network devices.


## Example Playbook
---
<add playbook samples below>

To execute an Ansible playbook, use the following command:

```
ansible-playbook cnos_image_sample.yml -vvv
```

`-vvv` is an optional verbos command that helps identify what is happening during playbook execution. The playbook for each role is located in the main directory of the solution.

```
  - name: Module to  do image download
   hosts: cnos_image_sample
   gather_facts: no
   connection: local
   roles:
    - cnos_image_sample
```


## License
---
<add license information below>
Copyright (C) 2017 Lenovo, Inc.

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Ansible is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Ansible.  If not, see <http://www.gnu.org/licenses/>.