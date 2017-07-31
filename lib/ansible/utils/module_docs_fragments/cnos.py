# Copyright (C) 2017 Lenovo, Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#


class ModuleDocFragment(object):
    # Standard CNOS documentation fragment
    DOCUMENTATION = '''
options:
    outputfile:
        description:
            - This specifies the file path where the output of each command
             execution is saved. Each command that is specified in the merged
             template file and each response from the device are saved here.
             Usually the location is the results folder, but you can
             choose another location based on your write permission.
        required: true
        default: Null
        version_added: 2.3
    host:
        description:
            - This is the variable used to search the hosts file at
             /etc/ansible/hosts and identify the IP address of the device on
             which the template is going to be applied. Usually the Ansible
             keyword {{ inventory_hostname }} is specified in the playbook as
             an abstraction of the group of network elements that need to be
             configured.
        required: true
        default: Null
        version_added: 2.3
    username:
        description:
            - Configures the username used to authenticate the connection to
             the remote device. The value of the username parameter is used to
             authenticate the SSH session. While generally the value should
             come from the inventory file, you can also specify it as a
             variable. This parameter is optional. If it is not specified, no
             default value will be used.
        required: true
        default: Null
        version_added: 2.3
    password:
        description:
            - Configures the password used to authenticate the connection to
             the remote device. The value of the password parameter is used to
             authenticate the SSH session. While generally the value should
             come from the inventory file, you can also specify it as a
             variable. This parameter is optional. If it is not specified, no
             default value will be used.
        required: true
        default: Null
        version_added: 2.3
    enablePassword:
        description:
            - Configures the password used to enter Global Configuration
             command mode on the switch. If the switch does not request this
             password, the parameter is ignored.While generally the value
             should come from the inventory file, you can also specify it as a
             variable. This parameter is optional. If it is not specified,
             no default value will be used.
        required: false
        default: Null
        version_added: 2.3
    deviceType:
        description:
            - This specifies the type of device where the method is executed.
             The choices NE1072T,NE1032,NE1032T,NE10032,
             NE2572 are added since version 2.4
        required: Yes
        default: null
        choices: [g8272_cnos,g8296_cnos,g8332_cnos,NE1072T,NE1032,
         NE1032T,NE10032,NE2572]
        version_added: 2.3
'''
