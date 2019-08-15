#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
# Copyright 2019 Fortinet, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_facts
version_added: "2.9"
short_description: Get facts about fortios devices.
description:
  - Collects facts from network devices running the fortios operating
    system. This module places the facts gathered in the fact tree keyed by the
    respective resource name.  The facts module will always collect a
    base set of facts from the device and can enable or disable
    collection of additional facts.
author:
    - Miguel Angel Munoz (@mamunozgonzalez)
    - Nicolas Thomas (@thomnico)
    - Don Yao (@fortinetps)
notes:
    - Requires fortiosapi library developed by Fortinet
    - Run as a local_action in your playbook
requirements:
    - fortiosapi>=0.9.8
options:
    host:
        description:
            - FortiOS or FortiGate IP address.
        type: str
        required: true
    username:
        description:
            - FortiOS or FortiGate username.
        type: str
        required: true
    password:
        description:
            - FortiOS or FortiGate password.
        type: str
        default: ""
        required: true
    vdom:
        description:
            - Virtual domain, among those defined previously. A vdom is a
              virtual instance of the FortiGate that can be configured and
              used as a different unit.
        type: str
        default: root
        required: false
    https:
        description:
            - Indicates if the requests towards FortiGate must use HTTPS protocol.
        type: bool
        default: true
        required: false
    ssl_verify:
        description:
            - Ensures FortiGate certificate must be verified by a proper CA.
        type: bool
        default: false
        required: false
    gather_subset:
        description:
            - When supplied, this argument will restrict the facts collected
            to a given subset.  Possible values for this argument include
            all, hardware, config, and interfaces.  Can specify a list of
            values to include a larger subset.
      type: list
      default:
          - "system_status_select"
      required: false

'''

EXAMPLES = '''
- hosts: localhost
  vars:
    host: "192.168.122.40"
    username: "admin"
    password: ""
    vdom: "root"
    ssl_verify: "False"

  tasks:
  - name: gather system status and system interface facts
    fortios_facts:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      gather_subset:
        - "system_status_select"
        - "system_interface_select"
  '''

RETURN = '''
build:
  description: Build number of the fortigate image
  returned: always
  type: str
  sample: '1547'
http_method:
  description: Last method used to provision the content into FortiGate
  returned: always
  type: str
  sample: 'GET'
name:
  description: Name of the table used to fulfill the request
  returned: always
  type: str
  sample: "firmware"
path:
  description: Path of the table used to fulfill the request
  returned: always
  type: str
  sample: "system"
revision:
  description: Internal revision number
  returned: always
  type: str
  sample: "17.0.2.10658"
serial:
  description: Serial number of the unit
  returned: always
  type: str
  sample: "FGVMEVYYQT3AB5352"
status:
  description: Indication of the operation's result
  returned: always
  type: str
  sample: "success"
vdom:
  description: Virtual domain used
  returned: always
  type: str
  sample: "root"
version:
  description: Version of the FortiGate
  returned: always
  type: str
  sample: "v5.6.3"
ansible_facts:
  description: The list of fact subsets collected from the device
  returned: always
  type: list
# system
fortios_system_status:
  description: The fortios basic system status information running on the remote device
  returned: always
  type: dict

'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG
from ansible.module_utils.six import iteritems


class Factbase(object):
    def __init__(self, module, fos, uri=None):
        self.module = module
        self.fos = fos
        self.uri = uri
        self.facts = dict()


FACT_SYSTEM_SUBSETS = frozenset([
    'system_current-admins_select',
    'system_firmware_select',
    'system_fortimanager_status',
    'system_ha-checksums_select',
    'system_interface_select',
    'system_status_select',
    'system_time_select',
])


class System(Factbase):
    def populate_facts(self):
        fos = self.fos
        vdom = self.module.params['vdom']
        if self.uri.startswith(tuple(FACT_SYSTEM_SUBSETS)):
            resp = fos.monitor('system', self.uri[len('system_'):].replace('_', '/'), vdom=vdom)
            self.facts.update({self.uri: resp})


FACT_SUBSETS = dict(
    system=System,
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())


def login(data, fos):
    host = data['host']
    username = data['username']
    password = data['password']
    ssl_verify = data['ssl_verify']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password, verify=ssl_verify)


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": True, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "ssl_verify": {"required": False, "type": "bool", "default": False},
        'gather_subset': {"required": False, "type": "list", "default": ['system_status_select']}
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)

    legacy_mode = 'host' in module.params and module.params['host'] is not None and \
                  'username' in module.params and module.params['username'] is not None and \
                  'password' in module.params and module.params['password'] is not None

    # for now only support local connection mode
    if not legacy_mode:
        module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        gather_subset = module.params['gather_subset']

        runable_subsets = set()

        for subset in gather_subset:
            if not subset.startswith(tuple(VALID_SUBSETS)):
                module.fail_json(msg='Subset must be one of [%s], got %s' %
                                 (', '.join(VALID_SUBSETS), subset))

            for valid_subset in VALID_SUBSETS:
                if subset.startswith(valid_subset):
                    runable_subsets.add((subset, valid_subset))

        if not runable_subsets:
            runable_subsets.update(VALID_SUBSETS)

        facts = dict()
        facts['gather_subset'] = list(runable_subsets)

        instances = list()

        for (subset, valid_subset) in runable_subsets:
            instances.append(FACT_SUBSETS[valid_subset](module, fos, subset))

        # Populate facts for instances
        for inst in instances:
            inst.populate_facts()
            facts.update(inst.facts)

        fos.logout()

        module.exit_json(ansible_facts=facts)


if __name__ == '__main__':
    main()
