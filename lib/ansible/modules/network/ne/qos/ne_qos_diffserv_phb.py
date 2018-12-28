#!/usr/bin/python
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

from ansible.module_utils.network.ne.ne import get_nc_config, set_nc_config, execute_nc_action, ne_argument_spec, constr_leaf_value
from ansible.module_utils.basic import AnsibleModule
import collections
import re
ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: ne_qos_diffserv_phb
version_added: "2.6"
short_description:  Mapping from the internal priority to the external priority for downstream traffic.
description:
    - Mapping from the internal priority to the external priority for downstream traffic.
options:
    dsName:
        description:
            - Name of a DiffServ domain.
              The value is a string of 1 to 48 characters.
        required: true
        default: null
    phbType:
        description:
            - External priority type.
        required: false
        default: null
        choices=['8021p', 'ipDscp', 'mplsExp']
    phbValue:
        description:
            - External priority to which the internal priority is mapped.
            The value is an integer ranging from 0 to 63.
        required: false
        default: null
    serviceClass:
        description:
            - Service class.
        required: false
        default: null
        choices=['be', 'af1', 'af2', 'af3', 'af4', 'ef', 'cs6', 'cs7']
    color:
        description:
            - Color marked to the data flows after measurement.
        required: false
        default: null
        choices=['green', 'yellow', 'red']
    operation:
        description:
            - Operation type.
        required: false
        default: create
        choices: ['create', 'getconfig', 'delete']
'''

EXAMPLES = '''
- name: ne_qos_diffserv_phb module test
  hosts: ne_test
  connection: netconf
  gather_facts: no
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ ansible_user }}"
      password: "{{ ansible_ssh_pass }}"
      transport: cli


  tasks:


  - name: Config External Priority Mapping
    ne_qos_diffserv_phb:
      dsName: test
      baType: 8021p
      baValue: 1
      serviceClass: be
      color: red
      operation: create
      provider: "{{ cli }}"

  - name: Undo External Priority Mapping
    ne_qos_diffserv_phb:
      behaviorName: test
      baType: 8021p
      baValue: 1
      operation: delete
      provider: "{{ cli }}"

  - name: Get all External Priority Mapping configurations in specified diffServ domain
    ne_qos_diffserv_phb:
      behaviorName: test
      operation: getconfig
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample:  {
        "phbType": "8021p",
        "phbValue": "1",
        "color": "red",
        "dsName": "test",
        "operation": "create",
        "serviceClass": "be"
    }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample: [
        {
            "color": "green",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "0",
            "serviceClass": "be"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "0",
            "serviceClass": "be"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "0",
            "serviceClass": "be"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "1",
            "serviceClass": "af1"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "1",
            "serviceClass": "af1"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "1",
            "serviceClass": "af1"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "2",
            "serviceClass": "af2"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "2",
            "serviceClass": "af2"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "2",
            "serviceClass": "af2"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "3",
            "serviceClass": "af3"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "3",
            "serviceClass": "af3"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "3",
            "serviceClass": "af3"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "4",
            "serviceClass": "af4"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "4",
            "serviceClass": "af4"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "4",
            "serviceClass": "af4"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "5",
            "serviceClass": "ef"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "5",
            "serviceClass": "ef"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "5",
            "serviceClass": "ef"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "6",
            "serviceClass": "cs6"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "6",
            "serviceClass": "cs6"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "6",
            "serviceClass": "cs6"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "7",
            "serviceClass": "cs7"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "7",
            "serviceClass": "cs7"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "7",
            "serviceClass": "cs7"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "0",
            "serviceClass": "be"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "0",
            "serviceClass": "be"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "0",
            "serviceClass": "be"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "10",
            "serviceClass": "af1"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "12",
            "serviceClass": "af1"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "14",
            "serviceClass": "af1"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "18",
            "serviceClass": "af2"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "20",
            "serviceClass": "af2"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "22",
            "serviceClass": "af2"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "26",
            "serviceClass": "af3"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "28",
            "serviceClass": "af3"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "30",
            "serviceClass": "af3"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "34",
            "serviceClass": "af4"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "36",
            "serviceClass": "af4"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "38",
            "serviceClass": "af4"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "46",
            "serviceClass": "ef"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "46",
            "serviceClass": "ef"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "46",
            "serviceClass": "ef"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "48",
            "serviceClass": "cs6"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "48",
            "serviceClass": "cs6"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "48",
            "serviceClass": "cs6"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "56",
            "serviceClass": "cs7"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "56",
            "serviceClass": "cs7"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "56",
            "serviceClass": "cs7"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "0",
            "serviceClass": "be"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "0",
            "serviceClass": "be"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "0",
            "serviceClass": "be"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "1",
            "serviceClass": "af1"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "1",
            "serviceClass": "af1"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "1",
            "serviceClass": "af1"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "2",
            "serviceClass": "af2"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "2",
            "serviceClass": "af2"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "2",
            "serviceClass": "af2"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "3",
            "serviceClass": "af3"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "3",
            "serviceClass": "af3"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "3",
            "serviceClass": "af3"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "4",
            "serviceClass": "af4"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "4",
            "serviceClass": "af4"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "4",
            "serviceClass": "af4"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "5",
            "serviceClass": "ef"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "5",
            "serviceClass": "ef"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "5",
            "serviceClass": "ef"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "6",
            "serviceClass": "cs6"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "6",
            "serviceClass": "cs6"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "6",
            "serviceClass": "cs6"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "7",
            "serviceClass": "cs7"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "7",
            "serviceClass": "cs7"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "7",
            "serviceClass": "cs7"
        }
    ],

end_stat:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample: [
        {
            "color": "green",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "0",
            "serviceClass": "be"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "0",
            "serviceClass": "be"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "1",
            "serviceClass": "be"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "1",
            "serviceClass": "af1"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "1",
            "serviceClass": "af1"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "1",
            "serviceClass": "af1"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "2",
            "serviceClass": "af2"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "2",
            "serviceClass": "af2"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "2",
            "serviceClass": "af2"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "3",
            "serviceClass": "af3"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "3",
            "serviceClass": "af3"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "3",
            "serviceClass": "af3"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "4",
            "serviceClass": "af4"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "4",
            "serviceClass": "af4"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "4",
            "serviceClass": "af4"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "5",
            "serviceClass": "ef"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "5",
            "serviceClass": "ef"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "5",
            "serviceClass": "ef"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "6",
            "serviceClass": "cs6"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "6",
            "serviceClass": "cs6"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "6",
            "serviceClass": "cs6"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "7",
            "serviceClass": "cs7"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "7",
            "serviceClass": "cs7"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "8021p",
            "phbValue": "7",
            "serviceClass": "cs7"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "0",
            "serviceClass": "be"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "0",
            "serviceClass": "be"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "0",
            "serviceClass": "be"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "10",
            "serviceClass": "af1"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "12",
            "serviceClass": "af1"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "14",
            "serviceClass": "af1"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "18",
            "serviceClass": "af2"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "20",
            "serviceClass": "af2"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "22",
            "serviceClass": "af2"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "26",
            "serviceClass": "af3"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "28",
            "serviceClass": "af3"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "30",
            "serviceClass": "af3"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "34",
            "serviceClass": "af4"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "36",
            "serviceClass": "af4"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "38",
            "serviceClass": "af4"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "46",
            "serviceClass": "ef"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "46",
            "serviceClass": "ef"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "46",
            "serviceClass": "ef"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "48",
            "serviceClass": "cs6"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "48",
            "serviceClass": "cs6"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "48",
            "serviceClass": "cs6"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "56",
            "serviceClass": "cs7"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "56",
            "serviceClass": "cs7"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "ipDscp",
            "phbValue": "56",
            "serviceClass": "cs7"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "0",
            "serviceClass": "be"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "0",
            "serviceClass": "be"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "0",
            "serviceClass": "be"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "1",
            "serviceClass": "af1"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "1",
            "serviceClass": "af1"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "1",
            "serviceClass": "af1"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "2",
            "serviceClass": "af2"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "2",
            "serviceClass": "af2"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "2",
            "serviceClass": "af2"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "3",
            "serviceClass": "af3"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "3",
            "serviceClass": "af3"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "3",
            "serviceClass": "af3"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "4",
            "serviceClass": "af4"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "4",
            "serviceClass": "af4"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "4",
            "serviceClass": "af4"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "5",
            "serviceClass": "ef"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "5",
            "serviceClass": "ef"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "5",
            "serviceClass": "ef"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "6",
            "serviceClass": "cs6"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "6",
            "serviceClass": "cs6"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "6",
            "serviceClass": "cs6"
        },
        {
            "color": "green",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "7",
            "serviceClass": "cs7"
        },
        {
            "color": "yellow",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "7",
            "serviceClass": "cs7"
        },
        {
            "color": "red",
            "dsName": "1",
            "phbType": "mplsExp",
            "phbValue": "7",
            "serviceClass": "cs7"
        }
    ],

changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


MERGE_CLASS_HEALDER = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosDss>
        <qosDs>
            <dsName>%s</dsName>
            <qosPhbs>
                <qosPhb>
"""

MERGE_CLASS_TAIL = """
                </qosPhb>
            </qosPhbs>
        </qosDs>
    </qosDss>
</qos>
</config>
"""
CFGGET_CLASS = """
<filter type="subtree">
<qos xmlns="http://www.huawei.com/netconf/vrp/huawei-qos">
    <qosDss>
        <qosDs>
            <dsName></dsName>
            <dsId></dsId>
            <qosPhbs>
              <qosPhb/>
            </qosPhbs>
        </qosDs>
    </qosDss>
</qos>
</filter>
"""


class QosDsPhbCfg(object):
    """
     Manages VLAN resources and attributes
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # qosds config info
        self.dsName = self.module.params['dsName']
        self.phbType = self.module.params['phbType']
        self.phbValue = self.module.params['phbValue']
        self.serviceClass = self.module.params['serviceClass']
        self.color = self.module.params['color']
        self.operation = self.module.params['operation']

        self.proposed = dict()
        self.results = dict()
        self.results["existing"] = []
        self.results["end_state"] = []
        self.results["changed"] = False

    def init_module(self):
        """
        init ansilbe NetworkModule.
        """

        self.module = AnsibleModule(
            argument_spec=self.spec,
            supports_check_mode=True)

    def check_params(self):
        """Check all input params"""
        msg_para = ""
        if not self.dsName:
            msg_para += " dsName"
        if self.operation != "getconfig":
            if not self.phbType:
                msg_para += " phbType"
            if not self.phbValue:
                msg_para += " phbValue"
        if msg_para:
            self.module.fail_json(
                msg='Error: Please input the necessary element includes%s.' % msg_para)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def constuct_xml(self):

        conf_str = None
        conf_str = MERGE_CLASS_HEALDER % self.dsName
        conf_str = constr_leaf_value(conf_str, 'phbType', self.phbType)
        conf_str = constr_leaf_value(conf_str, 'phbValue', self.phbValue)
        if self.serviceClass:
            conf_str = constr_leaf_value(
                conf_str, 'serviceClass', self.serviceClass)
        if self.color:
            conf_str = constr_leaf_value(conf_str, 'color', self.color)
        if self.operation == 'delete':
            conf_str = conf_str.replace(
                '<qosPhb>', '<qosPhb xc:operation="delete">')
        conf_str += MERGE_CLASS_TAIL
        print('88888', conf_str)
        return conf_str

    def merge_dsphb(self):

        conf_str = self.constuct_xml()

        print('55555', conf_str)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")

    def get_dsphb(self):
        attr = dict()
        output_msg_list = list()
        output_msg = list()
        conf_str = CFGGET_CLASS
        xml_str = get_nc_config(self.module, conf_str)
        print('xml_str', xml_str)
        if "<data/>" in xml_str:
            return attr
        else:

            print('66666', xml_str)
            xml_str_split = re.split('</qosDs>', xml_str)
            print('77777', xml_str_split)
            for j in range(len(xml_str_split)):
                find_dsName = re.findall(
                    r'.*<dsName>(.*)</dsName>.*\s*', xml_str_split[j])
                find_phbType = re.findall(
                    r'.*<phbType>(.*)</phbType>.*\s*', xml_str_split[j])
                find_phbValue = re.findall(
                    r'.*<phbValue>(.*)</phbValue>.*\s*', xml_str_split[j])
                find_serviceClass = re.findall(
                    r'.*<serviceClass>(.*)</serviceClass>.*\s*', xml_str_split[j])
                find_color = re.findall(
                    r'.*<color>(.*)</color>.*\s*', xml_str_split[j])
                if find_dsName and find_dsName[0] == self.dsName:
                    for i in range(len(find_phbType)):
                        attr = dict()
                        attr['dsName'] = find_dsName[0]
                        attr['phbType'] = find_phbType[i]
                        attr['phbValue'] = find_phbValue[i]
                        attr['serviceClass'] = find_serviceClass[i]
                        attr['color'] = find_color[i]
                        output_msg_list.append(attr)

        return output_msg_list

    def undo_dsphb(self):

        conf_str = self.constuct_xml()

        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_DS")
        # self.changed = True

    def get_proposed(self):

        if self.dsName:
            self.proposed["dsName"] = self.dsName
        if self.phbType:
            self.proposed["phbType"] = self.phbType
        if self.phbValue:
            self.proposed["phbValue"] = self.phbValue
        if self.serviceClass:
            self.proposed["serviceClass"] = self.serviceClass
        if self.color:
            self.proposed["color"] = self.color
        if self.operation:
            self.proposed["operation"] = self.operation

    def work(self):
        """
        worker.
        """
        self.check_params()
        self.get_proposed()

        dsphbcfg_attr_exist = self.get_dsphb()
        if dsphbcfg_attr_exist:
            self.results["existing"] = dsphbcfg_attr_exist

        if self.operation == 'create':
            self.merge_dsphb()

        if self.operation == 'delete':
            self.undo_dsphb()

        dsphbcfg_attr_end_state = self.get_dsphb()
        if dsphbcfg_attr_end_state:
            self.results["end_state"] = dsphbcfg_attr_end_state

        if self.operation != 'getconfig':
            self.results["changed"] = True
        self.results["proposed"] = self.proposed

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        dsName=dict(required=False, type='str'),
        phbType=dict(required=False, choices=['8021p', 'ipDscp', 'mplsExp']),
        phbValue=dict(required=False, type='str'),
        serviceClass=dict(
            required=False,
            choices=[
                'be',
                'af1',
                'af2',
                'af3',
                'af4',
                'ef',
                'cs6',
                'cs7']),
        color=dict(required=False, choices=['green', 'yellow', 'red']),
        operation=dict(
            required=False,
            choices=[
                'create',
                'getconfig',
                'delete'],
            default='create'),
    )

    argument_spec.update(ne_argument_spec)
    NEWQosDsPhbCfg = QosDsPhbCfg(argument_spec)
    NEWQosDsPhbCfg.work()


if __name__ == '__main__':
    main()
