# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Lenovo, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Standard CNOS documentation fragment
    DOCUMENTATION = r'''
options:
    outputfile:
        description:
            - This specifies the file path where the output of each command
             execution is saved. Each command that is specified in the merged
             template file and each response from the device are saved here.
             Usually the location is the results folder, but you can
             choose another location based on your write permission.
        type: str
        required: true
        version_added: '2.3'
    host:
        description:
            - This is the variable used to search the hosts file at
             /etc/ansible/hosts and identify the IP address of the device on
             which the template is going to be applied. Usually the Ansible
             keyword {{ inventory_hostname }} is specified in the playbook as
             an abstraction of the group of network elements that need to be
             configured.
        type: str
        required: true
        version_added: '2.3'
    username:
        description:
            - Configures the username used to authenticate the connection to
             the remote device. The value of the username parameter is used to
             authenticate the SSH session. While generally the value should
             come from the inventory file, you can also specify it as a
             variable. This parameter is optional. If it is not specified, no
             default value will be used.
        type: str
        required: true
        version_added: '2.3'
    password:
        description:
            - Configures the password used to authenticate the connection to
             the remote device. The value of the password parameter is used to
             authenticate the SSH session. While generally the value should
             come from the inventory file, you can also specify it as a
             variable. This parameter is optional. If it is not specified, no
             default value will be used.
        type: str
        required: true
        version_added: '2.3'
    enablePassword:
        description:
            - Configures the password used to enter Global Configuration
             command mode on the switch. If the switch does not request this
             password, the parameter is ignored.While generally the value
             should come from the inventory file, you can also specify it as a
             variable. This parameter is optional. If it is not specified,
             no default value will be used.
        type: str
        version_added: '2.3'
    deviceType:
        description:
            - This specifies the type of device where the method is executed.
             The choices NE1072T,NE1032,NE1032T,NE10032,NE2572 are added
             since Ansible 2.4. The choice NE0152T is added since 2.8
        type: str
        required: true
        choices:
        - g8272_cnos
        - g8296_cnos
        - g8332_cnos
        - NE0152T
        - NE1072T
        - NE1032
        - NE1032T
        - NE10032
        - NE2572
        version_added: '2.3'
notes:
  - For more information on using Ansible to manage Lenovo Network devices see U(https://www.ansible.com/ansible-lenovo).
'''
