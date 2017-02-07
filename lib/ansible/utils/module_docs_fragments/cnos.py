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
            - This specifies the file path to which the output of each command execution is persisted. 
             Response from the device saved here. Usually the location is the results folder. 
             But your user can choose which ever path he has write permission. 
        required: true
        default: null
        version_added: 2.3
    host:
        description:
            - This is the variable which used to look into /etc/ansible/hosts file so that device IP addresses 
             on which this template has to be applied is identified. Usually we specify the ansible keyword {{ inventory_hostname }} 
             which we specify in the playbook which is an abstraction to the group of 
             network elements that need to be configured.
        required: true
        default: null
        version_added: 2.3
    username:
        description:
            - Configures the username to use to authenticate the connection to the remote device. The value of 
             username is used to authenticate the SSH session. The value has to come from inventory file ideally,
             you can even enter it as variable.
        required: true
        default: null
        version_added: 2.3
    password:
        description:
            - Configures the password to use to authenticate the connection to the remote device. 
             The value of password is used to authenticate the SSH session.The value has to come from inventory file ideally,
             you can even enter it as variable.
        required: true
        default: null
        version_added: 2.3
    enablePassword:
        description:
            - Inputs the enable password, in case its enables in the device. This get ignored if the device is not demanding an enable password. 
             The value of password is used to enter the congig mode.The default value is empty string. The value has to come from inventory file ideally,
             you can even enter it as variable.
        required: false
        default: null
        version_added: 2.3
    deviceType:
        description:
            - This specifies the type of device against which the image is downloaded. The value has to come from inventory file ideally,
             you can even enter it as variable.
        required: Yes
        default: null
        choices: [g8272_cnos,g8296_cnos,g8332_cnos]
        version_added: 2.3
'''
