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
module: ne_qos_diffserv_ba
version_added: "2.6"
short_description:  Mapping from the external priority to the internal priority for upstream traffic.
description:
    - Mapping from the external priority to the internal priority for upstream traffic.
options:
    dsName:
        description:
            - Name of a DiffServ domain.
              The value is a string of 1 to 48 characters.
        required: true
        default: null
    baType:
        description:
            - External priority type.
        required: true
        default: null
        choices=['8021p', 'ipDscp', 'mplsExp']
    baValue:
        description:
            - Internal priority to which the external priority is mapped.
            The value is an integer ranging from 0 to 63.
        required: true
        default: null
    serviceClass:
        description:
            - Service class.
        required: true
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
- name: ne_qos_diffserv_ba module test
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


  - name: Config Internal Priority Mapping
    ne_qos_diffserv_ba:
      dsName: test
      baType: 8021p
      baValue: 1
      serviceClass: be
      color: red
      operation: create
      provider: "{{ cli }}"

  - name: Undo Internal Priority Mapping
    ne_qos_diffserv_ba:
      behaviorName: test
      baType: 8021p
      baValue: 1
      operation: delete
      provider: "{{ cli }}"

  - name: Get all Internal Priority Mapping configurations in specified diffServ domain
    ne_qos_diffserv_ba:
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
        "baType": "8021p",
        "baValue": "1",
        "color": "red",
        "dsName": "test",
        "operation": "create",
        "serviceClass": "be"
    }
existing:
    description: k/v pairs of existing switchport
    returned: always
    type: dict
    sample:  [
        {
            "baType": "8021p",
            "baValue": "0",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "8021p",
            "baValue": "1",
            "color": "red",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "8021p",
            "baValue": "2",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af2"
        },
        {
            "baType": "8021p",
            "baValue": "3",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af3"
        },
        {
            "baType": "8021p",
            "baValue": "4",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af4"
        },
        {
            "baType": "8021p",
            "baValue": "5",
            "color": "green",
            "dsName": "1",
            "serviceClass": "ef"
        },
        {
            "baType": "8021p",
            "baValue": "6",
            "color": "green",
            "dsName": "1",
            "serviceClass": "cs6"
        },
        {
            "baType": "8021p",
            "baValue": "7",
            "color": "green",
            "dsName": "1",
            "serviceClass": "cs7"
        },
        {
            "baType": "ipDscp",
            "baValue": "0",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "1",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "2",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "3",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "4",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "5",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "6",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "7",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "8",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af1"
        },
        {
            "baType": "ipDscp",
            "baValue": "9",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "10",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af1"
        },
        {
            "baType": "ipDscp",
            "baValue": "11",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "12",
            "color": "yellow",
            "dsName": "1",
            "serviceClass": "af1"
        },
        {
            "baType": "ipDscp",
            "baValue": "13",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "14",
            "color": "red",
            "dsName": "1",
            "serviceClass": "af1"
        },
        {
            "baType": "ipDscp",
            "baValue": "15",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "16",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af2"
        },
        {
            "baType": "ipDscp",
            "baValue": "17",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "18",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af2"
        },
        {
            "baType": "ipDscp",
            "baValue": "19",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "20",
            "color": "yellow",
            "dsName": "1",
            "serviceClass": "af2"
        },
        {
            "baType": "ipDscp",
            "baValue": "21",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "22",
            "color": "red",
            "dsName": "1",
            "serviceClass": "af2"
        },
        {
            "baType": "ipDscp",
            "baValue": "23",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "24",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af3"
        },
        {
            "baType": "ipDscp",
            "baValue": "25",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "26",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af3"
        },
        {
            "baType": "ipDscp",
            "baValue": "27",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "28",
            "color": "yellow",
            "dsName": "1",
            "serviceClass": "af3"
        },
        {
            "baType": "ipDscp",
            "baValue": "29",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "30",
            "color": "red",
            "dsName": "1",
            "serviceClass": "af3"
        },
        {
            "baType": "ipDscp",
            "baValue": "31",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "32",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af4"
        },
        {
            "baType": "ipDscp",
            "baValue": "33",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "34",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af4"
        },
        {
            "baType": "ipDscp",
            "baValue": "35",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "36",
            "color": "yellow",
            "dsName": "1",
            "serviceClass": "af4"
        },
        {
            "baType": "ipDscp",
            "baValue": "37",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "38",
            "color": "red",
            "dsName": "1",
            "serviceClass": "af4"
        },
        {
            "baType": "ipDscp",
            "baValue": "39",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "40",
            "color": "green",
            "dsName": "1",
            "serviceClass": "ef"
        },
        {
            "baType": "ipDscp",
            "baValue": "41",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "42",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "43",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "44",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "45",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "46",
            "color": "green",
            "dsName": "1",
            "serviceClass": "ef"
        },
        {
            "baType": "ipDscp",
            "baValue": "47",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "48",
            "color": "green",
            "dsName": "1",
            "serviceClass": "cs6"
        },
        {
            "baType": "ipDscp",
            "baValue": "49",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "50",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "51",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "52",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "53",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "54",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "55",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "56",
            "color": "green",
            "dsName": "1",
            "serviceClass": "cs7"
        },
        {
            "baType": "ipDscp",
            "baValue": "57",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "58",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "59",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "60",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "61",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "62",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "63",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "mplsExp",
            "baValue": "0",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "mplsExp",
            "baValue": "1",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af1"
        },
        {
            "baType": "mplsExp",
            "baValue": "2",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af2"
        },
        {
            "baType": "mplsExp",
            "baValue": "3",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af3"
        },
        {
            "baType": "mplsExp",
            "baValue": "4",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af4"
        },
        {
            "baType": "mplsExp",
            "baValue": "5",
            "color": "green",
            "dsName": "1",
            "serviceClass": "ef"
        },
        {
            "baType": "mplsExp",
            "baValue": "6",
            "color": "green",
            "dsName": "1",
            "serviceClass": "cs6"
        },
        {
            "baType": "mplsExp",
            "baValue": "7",
            "color": "green",
            "dsName": "1",
            "serviceClass": "cs7"
        }
    ],
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict
    sample: [
        {
            "baType": "8021p",
            "baValue": "0",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "8021p",
            "baValue": "1",
            "color": "red",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "8021p",
            "baValue": "2",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af2"
        },
        {
            "baType": "8021p",
            "baValue": "3",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af3"
        },
        {
            "baType": "8021p",
            "baValue": "4",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af4"
        },
        {
            "baType": "8021p",
            "baValue": "5",
            "color": "green",
            "dsName": "1",
            "serviceClass": "ef"
        },
        {
            "baType": "8021p",
            "baValue": "6",
            "color": "green",
            "dsName": "1",
            "serviceClass": "cs6"
        },
        {
            "baType": "8021p",
            "baValue": "7",
            "color": "green",
            "dsName": "1",
            "serviceClass": "cs7"
        },
        {
            "baType": "ipDscp",
            "baValue": "0",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "1",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "2",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "3",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "4",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "5",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "6",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "7",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "8",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af1"
        },
        {
            "baType": "ipDscp",
            "baValue": "9",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "10",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af1"
        },
        {
            "baType": "ipDscp",
            "baValue": "11",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "12",
            "color": "yellow",
            "dsName": "1",
            "serviceClass": "af1"
        },
        {
            "baType": "ipDscp",
            "baValue": "13",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "14",
            "color": "red",
            "dsName": "1",
            "serviceClass": "af1"
        },
        {
            "baType": "ipDscp",
            "baValue": "15",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "16",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af2"
        },
        {
            "baType": "ipDscp",
            "baValue": "17",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "18",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af2"
        },
        {
            "baType": "ipDscp",
            "baValue": "19",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "20",
            "color": "yellow",
            "dsName": "1",
            "serviceClass": "af2"
        },
        {
            "baType": "ipDscp",
            "baValue": "21",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "22",
            "color": "red",
            "dsName": "1",
            "serviceClass": "af2"
        },
        {
            "baType": "ipDscp",
            "baValue": "23",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "24",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af3"
        },
        {
            "baType": "ipDscp",
            "baValue": "25",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "26",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af3"
        },
        {
            "baType": "ipDscp",
            "baValue": "27",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "28",
            "color": "yellow",
            "dsName": "1",
            "serviceClass": "af3"
        },
        {
            "baType": "ipDscp",
            "baValue": "29",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "30",
            "color": "red",
            "dsName": "1",
            "serviceClass": "af3"
        },
        {
            "baType": "ipDscp",
            "baValue": "31",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "32",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af4"
        },
        {
            "baType": "ipDscp",
            "baValue": "33",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "34",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af4"
        },
        {
            "baType": "ipDscp",
            "baValue": "35",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "36",
            "color": "yellow",
            "dsName": "1",
            "serviceClass": "af4"
        },
        {
            "baType": "ipDscp",
            "baValue": "37",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "38",
            "color": "red",
            "dsName": "1",
            "serviceClass": "af4"
        },
        {
            "baType": "ipDscp",
            "baValue": "39",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "40",
            "color": "green",
            "dsName": "1",
            "serviceClass": "ef"
        },
        {
            "baType": "ipDscp",
            "baValue": "41",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "42",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "43",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "44",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "45",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "46",
            "color": "green",
            "dsName": "1",
            "serviceClass": "ef"
        },
        {
            "baType": "ipDscp",
            "baValue": "47",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "48",
            "color": "green",
            "dsName": "1",
            "serviceClass": "cs6"
        },
        {
            "baType": "ipDscp",
            "baValue": "49",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "50",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "51",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "52",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "53",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "54",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "55",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "56",
            "color": "green",
            "dsName": "1",
            "serviceClass": "cs7"
        },
        {
            "baType": "ipDscp",
            "baValue": "57",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "58",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "59",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "60",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "61",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "62",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "ipDscp",
            "baValue": "63",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "mplsExp",
            "baValue": "0",
            "color": "green",
            "dsName": "1",
            "serviceClass": "be"
        },
        {
            "baType": "mplsExp",
            "baValue": "1",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af1"
        },
        {
            "baType": "mplsExp",
            "baValue": "2",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af2"
        },
        {
            "baType": "mplsExp",
            "baValue": "3",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af3"
        },
        {
            "baType": "mplsExp",
            "baValue": "4",
            "color": "green",
            "dsName": "1",
            "serviceClass": "af4"
        },
        {
            "baType": "mplsExp",
            "baValue": "5",
            "color": "green",
            "dsName": "1",
            "serviceClass": "ef"
        },
        {
            "baType": "mplsExp",
            "baValue": "6",
            "color": "green",
            "dsName": "1",
            "serviceClass": "cs6"
        },
        {
            "baType": "mplsExp",
            "baValue": "7",
            "color": "green",
            "dsName": "1",
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
            <qosBas>
                <qosBa>
"""

MERGE_CLASS_TAIL = """
                </qosBa>
            </qosBas>
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
            <qosBas>
              <qosBa/>
            </qosBas>
        </qosDs>
    </qosDss>
</qos>
</filter>
"""


class QosDsBaCfg(object):
    """
     Manages VLAN resources and attributes
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # qosds config info
        self.dsName = self.module.params['dsName']
        self.baType = self.module.params['baType']
        self.baValue = self.module.params['baValue']
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
            if not self.baType:
                msg_para += " baType"
            if not self.baValue:
                msg_para += " baValue"
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
        conf_str = constr_leaf_value(conf_str, 'baType', self.baType)
        conf_str = constr_leaf_value(conf_str, 'baValue', self.baValue)
        if self.serviceClass:
            conf_str = constr_leaf_value(
                conf_str, 'serviceClass', self.serviceClass)
        if self.color:
            conf_str = constr_leaf_value(conf_str, 'color', self.color)
        if self.operation == 'delete':
            conf_str = conf_str.replace(
                '<qosBa>', '<qosBa xc:operation="delete">')
        conf_str += MERGE_CLASS_TAIL
        print('88888', conf_str)
        return conf_str

    def merge_dsba(self):

        conf_str = self.constuct_xml()

        print('55555', conf_str)
        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_IFCAR")

    def get_dsba(self):
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
                find_baType = re.findall(
                    r'.*<baType>(.*)</baType>.*\s*', xml_str_split[j])
                find_baValue = re.findall(
                    r'.*<baValue>(.*)</baValue>.*\s*', xml_str_split[j])
                find_serviceClass = re.findall(
                    r'.*<serviceClass>(.*)</serviceClass>.*\s*', xml_str_split[j])
                find_color = re.findall(
                    r'.*<color>(.*)</color>.*\s*', xml_str_split[j])
                if find_dsName and find_dsName[0] == self.dsName:
                    for i in range(len(find_baType)):
                        attr = dict()
                        attr['dsName'] = find_dsName[0]
                        attr['baType'] = find_baType[i]
                        attr['baValue'] = find_baValue[i]
                        attr['serviceClass'] = find_serviceClass[i]
                        attr['color'] = find_color[i]
                        output_msg_list.append(attr)

        return output_msg_list

    def undo_dsba(self):

        conf_str = self.constuct_xml()

        recv_xml = set_nc_config(self.module, conf_str)
        self.check_response(recv_xml, "CFG_DS")
        # self.changed = True

    def get_proposed(self):

        if self.dsName:
            self.proposed["dsName"] = self.dsName
        if self.baType:
            self.proposed["baType"] = self.baType
        if self.baValue:
            self.proposed["baValue"] = self.baValue
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

        dsbacfg_attr_exist = self.get_dsba()
        if dsbacfg_attr_exist:
            self.results["existing"] = dsbacfg_attr_exist

        if self.operation == 'create':
            self.merge_dsba()

        if self.operation == 'delete':
            self.undo_dsba()

        dsbacfg_attr_end_state = self.get_dsba()
        if dsbacfg_attr_end_state:
            self.results["end_state"] = dsbacfg_attr_end_state

        if self.operation != 'getconfig':
            self.results["changed"] = True
        self.results["proposed"] = self.proposed

        self.module.exit_json(**self.results)


def main():
    """ module main """

    argument_spec = dict(
        dsName=dict(required=False, type='str'),
        baType=dict(required=False, choices=['8021p', 'ipDscp', 'mplsExp']),
        baValue=dict(required=False, type='str'),
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
    NEWQosDsBaCfg = QosDsBaCfg(argument_spec)
    NEWQosDsBaCfg.work()


if __name__ == '__main__':
    main()
