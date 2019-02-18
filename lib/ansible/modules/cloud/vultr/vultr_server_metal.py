#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2019, Nate River <vitikc@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: vultr_server_metal
short_description: Manages baremetal servers on Vultr.
description:
  - Deploy and destroy servers.
version_added: "2.8"
author: "Nate River (@vitikc)"
options:
  name:
    description:
      - Name of the server.
    required: true
    aliases: [ label ]
  hostname:
    description:
      - Hostname to assign to this server.
  os:
    description:
      - The operating system.
      - Required if the server does not yet exist.
  plan:
    description:
      - Plan to use for the server.
      - Required if the server does not yet exist.
  notify_activate:
    description:
      - Whether to send an activation email when the server is ready or not.
      - Only considered on creation.
    type: bool
  ipv6_enabled:
    description:
      - Whether to enable IPv6 or not.
    type: bool
  tag:
    description:
      - Tag for the server.
  user_data:
    description:
      - User data to be passed to the server.
  startup_script:
    description:
      - Name of the startup script to execute on boot.
      - Only considered while creating the server.
  ssh_keys:
    description:
      - List of SSH keys passed to the server on creation.
    aliases: [ ssh_key ]
  reserved_ip_v4:
    description:
      - IP address of the floating IP to use as the main IP of this server.
      - Only considered on creation.
  region:
    description:
      - Region the server is deployed into.
      - Required if the server does not yet exist.
  state:
    description:
      - State of the server.
    default: present
    choices: [ present, absent ]
extends_documentation_fragment: vultr
'''

EXAMPLES = '''
- name: create server
  local_action:
    module: vultr_server_metal
    name: "{{ vultr_server_metal_name }}"
    os: Debian 9 x64 (stretch)
    plan: 32768 MB RAM,2x 240 GB SSD,5.00 TB BW
    region: Amsterdam

- name: ensure a server is absent
  local_action:
    module: vultr_server_metal
    name: "{{ vultr_server_metal_name }}"
    state: absent
'''

RETURN = '''
---
vultr_api:
  description: Response from Vultr API with a few additions/modification
  returned: success
  type: complex
  contains:
    api_account:
      description: Account used in the ini file to select the key
      returned: success
      type: str
      sample: default
    api_timeout:
      description: Timeout used for the API requests
      returned: success
      type: int
      sample: 60
    api_retries:
      description: Amount of max retries for the API requests
      returned: success
      type: int
      sample: 5
    api_endpoint:
      description: Endpoint used for the API requests
      returned: success
      type: str
      sample: "https://api.vultr.com"
vultr_server_metal:
  description: Response from Vultr API with a few additions/modification
  returned: success
  type: complex
  contains:
    id:
      description: ID of the server
      returned: success
      type: str
      sample: 900000
    name:
      description: Name (label) of the server
      returned: success
      type: str
      sample: "ansible-test-baremetal"
    plan:
      description: Plan used for the server
      returned: success
      type: str
      sample: "32768 MB RAM,2x 240 GB SSD,5.00 TB BW"
    allowed_bandwidth_gb:
      description: Allowed bandwidth to use in GB
      returned: success
      type: int
      sample: 1000
    cost_per_month:
      description: Cost per month for the server
      returned: success
      type: float
      sample: 120.00
    current_bandwidth_gb:
      description: Current bandwidth used for the server
      returned: success
      type: int
      sample: 0
    date_created:
      description: Date when the server was created
      returned: success
      type: str
      sample: "2017-04-12 18:45:41"
    default_password:
      description: Password to login as root into the server
      returned: success
      type: str
      sample: "ab81u!ryranq"
    disk:
      description: Information about the disk
      returned: success
      type: str
      sample: "SSD 250 GB"
    v4_gateway:
      description: IPv4 gateway
      returned: success
      type: str
      sample: "203.0.113.1"
    internal_ip:
      description: Internal IP
      returned: success
      type: str
      sample: ""
    region:
      description: Region the server was deployed into
      returned: success
      type: str
      sample: "Amsterdam"
    v4_main_ip:
      description: Main IPv4
      returned: success
      type: str
      sample: "203.0.113.10"
    v4_netmask:
      description: Netmask IPv4
      returned: success
      type: str
      sample: "255.255.255.0"
    os:
      description: Operating system used for the server
      returned: success
      type: str
      sample: "Debian 9 x64"
    pending_charges:
      description: Pending charges
      returned: success
      type: float
      sample: 0.18
    ram:
      description: Information about the RAM size
      returned: success
      type: str
      sample: "32768 MB"
    status:
      description: Status about the deployment of the server
      returned: success
      type: str
      sample: "active"
    tag:
      description: Server tag
      returned: success
      type: str
      sample: "my tag"
    v6_main_ip:
      description: Main IPv6
      returned: success
      type: str
      sample: "2001:DB8:9000::100"
    v6_network:
      description: Network IPv6
      returned: success
      type: str
      sample: "2001:DB8:9000::"
    v6_network_size:
      description:  Network size IPv6
      returned: success
      type: int
      sample: 64
    v6_networks:
      description: Networks IPv6
      returned: success
      type: list
      sample: []
'''

import time
import base64
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text, to_bytes
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrServerMetal(Vultr):

    def __init__(self, module):
        super(AnsibleVultrServerMetal, self).__init__(module, "vultr_server_metal")

        self.server = None
        self.returns = {
            'SUBID': dict(key='id'),
            'label': dict(key='name'),
            'date_created': dict(),
            'allowed_bandwidth_gb': dict(convert_to='int'),
            'current_bandwidth_gb': dict(),
            'default_password': dict(),
            'internal_ip': dict(),
            'disk': dict(),
            'cost_per_month': dict(convert_to='float'),
            'location': dict(key='region'),
            'main_ip': dict(key='v4_main_ip'),
            'network_v4': dict(key='v4_network'),
            'gateway_v4': dict(key='v4_gateway'),
            'os': dict(),
            'pending_charges': dict(convert_to='float'),
            'ram': dict(),
            'plan': dict(),
            'status': dict(),
            'tag': dict(),
            'v6_main_ip': dict(),
            'v6_network': dict(),
            'v6_network_size': dict(),
            'v6_networks': dict(),
        }
        self.server_power_state = None

    def get_startup_script(self):
        return self.query_resource_by_key(
            key='name',
            value=self.module.params.get('startup_script'),
            resource='startupscript',
        )

    def get_os(self):
        return self.query_resource_by_key(
            key='name',
            value=self.module.params.get('os'),
            resource='os',
            use_cache=True
        )

    def get_ssh_key(self):
        return self.query_resource_by_key(
            key='name',
            value=self.module.params.get('ssh_key'),
            resource='sshkey',
            use_cache=True
        )

    def get_region(self):
        return self.query_resource_by_key(
            key='name',
            value=self.module.params.get('region'),
            resource='regions',
            use_cache=True
        )

    def get_plan(self):
        return self.query_resource_by_key(
            key='name',
            value=self.module.params.get('plan'),
            resource='plans',
            query_by='list_baremetal',
            use_cache=True
        )

    def get_user_data(self):
        user_data = self.module.params.get('user_data')
        if user_data is not None:
            user_data = to_text(base64.b64encode(to_bytes(user_data)))
        return user_data

    def get_server_user_data(self, server):
        if not server or not server.get('SUBID'):
            return None

        user_data = self.api_query(path="/v1/baremetal/get_user_data?SUBID=%s" % server.get('SUBID'))
        return user_data.get('userdata')

    def get_server(self, refresh=False):
        if self.server is None or refresh:
            self.server = None
            server_list = self.api_query(path="/v1/baremetal/list")
            if server_list:
                for server_id, server_data in server_list.items():
                    if server_data.get('label') == self.module.params.get('name'):
                        self.server = server_data

                        plan = self.query_resource_by_key(
                            key='METALPLANID',
                            value=server_data['METALPLANID'],
                            resource='plans',
                            query_by='list_baremetal',
                            use_cache=True
                        )
                        self.server['plan'] = plan.get('name')

                        os = self.query_resource_by_key(
                            key='OSID',
                            value=int(server_data['OSID']),
                            resource='os',
                            use_cache=True
                        )
                        self.server['os'] = os.get('name')
        return self.server

    def _wait_for_state(self, key='status', state=None):
        time.sleep(1)
        server = self.get_server(refresh=True)
        for s in range(0, 60):
            if state is None and server.get(key):
                break
            elif server.get(key) == state:
                break
            time.sleep(2)
            server = self.get_server(refresh=True)

        # Timed out
        else:
            if state is None:
                msg = "Wait for '%s' timed out" % key
            else:
                msg = "Wait for '%s' to get into state '%s' timed out" % (key, state)
            self.fail_json(msg=msg)
        return server

    def present_server(self, start_server=True):
        server = self.get_server()
        if not server:
            server = self._create_server(server=server)
        else:
            server = self._update_server(server=server, start_server=start_server)
        return server

    def _create_server(self, server=None):
        required_params = [
            'os',
            'plan',
            'region',
        ]
        self.module.fail_on_missing_params(required_params=required_params)

        self.result['changed'] = True
        if not self.module.check_mode:
            data = {
                'DCID': self.get_region().get('DCID'),
                'METALPLANID': self.get_plan().get('METALPLANID'),
                'OSID': self.get_os().get('OSID'),
                'label': self.module.params.get('name'),
                'hostname': self.module.params.get('hostname'),
                'SSHKEYID': self.get_ssh_key().get('SSHKEYID'),
                'enable_ipv6': self.get_yes_or_no('ipv6_enabled'),
                'notify_activate': self.get_yes_or_no('notify_activate'),
                'tag': self.module.params.get('tag'),
                'reserved_ip_v4': self.module.params.get('reserved_ip_v4'),
                'user_data': self.get_user_data(),
                'SCRIPTID': self.get_startup_script().get('SCRIPTID'),
            }
            self.api_query(
                path="/v1/baremetal/create",
                method="POST",
                data=data
            )
            server = self._wait_for_state(key='status', state='active')
        return server

    def _update_server(self, server=None, start_server=True):

        # Update plan settings
        # server = self._update_plan_setting(server=server, start_server=start_server)

        # User data
        user_data = self.get_user_data()
        server_user_data = self.get_server_user_data(server=server)
        if user_data is not None and user_data != server_user_data:
            self.result['changed'] = True
            self.result['diff']['before']['user_data'] = server_user_data
            self.result['diff']['after']['user_data'] = user_data

            if not self.module.check_mode:
                data = {
                    'SUBID': server['SUBID'],
                    'userdata': user_data,
                }
                self.api_query(
                    path="/v1/baremetal/set_user_data",
                    method="POST",
                    data=data
                )

        # Tags
        tag = self.module.params.get('tag')
        if tag is not None and tag != server.get('tag'):
            self.result['changed'] = True
            self.result['diff']['before']['tag'] = server.get('tag')
            self.result['diff']['after']['tag'] = tag

            if not self.module.check_mode:
                data = {
                    'SUBID': server['SUBID'],
                    'tag': tag,
                }
                self.api_query(
                    path="/v1/baremetal/tag_set",
                    method="POST",
                    data=data
                )
        return server

    def absent_server(self):
        server = self.get_server()
        if server:
            self.result['changed'] = True
            self.result['diff']['before']['id'] = server['SUBID']
            self.result['diff']['after']['id'] = ""
            if not self.module.check_mode:
                data = {
                    'SUBID': server['SUBID']
                }
                self.api_query(
                    path="/v1/baremetal/destroy",
                    method="POST",
                    data=data
                )
                for s in range(0, 60):
                    if server is not None:
                        break
                    time.sleep(2)
                    server = self.get_server(refresh=True)
                else:
                    self.fail_json(msg="Wait for server '%s' to get deleted timed out" % server['label'])
        return server


def main():
    argument_spec = vultr_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True, aliases=['label']),
        hostname=dict(),
        os=dict(),
        plan=dict(),
        notify_activate=dict(type='bool', default=False),
        ipv6_enabled=dict(type='bool'),
        tag=dict(),
        reserved_ip_v4=dict(),
        startup_script=dict(),
        user_data=dict(),
        ssh_keys=dict(type='list', aliases=['ssh_key']),
        region=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    vultr_server_metal = AnsibleVultrServerMetal(module)
    if module.params.get('state') == "absent":
        server = vultr_server_metal.absent_server()
    else:
        server = vultr_server_metal.present_server()

    result = vultr_server_metal.get_result(server)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
