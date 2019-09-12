#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vultr_server
short_description: Manages virtual servers on Vultr.
description:
  - Deploy, start, stop, update, restart, reinstall servers.
version_added: "2.5"
author: "René Moser (@resmo)"
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
      - Required if the server does not yet exist and is not restoring from a snapshot.
  snapshot:
    version_added: "2.8"
    description:
      - Name of snapshot to restore server from.
  firewall_group:
    description:
      - The firewall group to assign this server to.
  plan:
    description:
      - Plan to use for the server.
      - Required if the server does not yet exist.
  force:
    description:
      - Force stop/start the server if required to apply changes
      - Otherwise a running server will not be changed.
    type: bool
  notify_activate:
    description:
      - Whether to send an activation email when the server is ready or not.
      - Only considered on creation.
    type: bool
  private_network_enabled:
    description:
      - Whether to enable private networking or not.
    type: bool
  auto_backup_enabled:
    description:
      - Whether to enable automatic backups or not.
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
    choices: [ present, absent, restarted, reinstalled, started, stopped ]
extends_documentation_fragment: vultr
'''

EXAMPLES = '''
- name: create server
  local_action:
    module: vultr_server
    name: "{{ vultr_server_name }}"
    os: CentOS 7 x64
    plan: 1024 MB RAM,25 GB SSD,1.00 TB BW
    ssh_keys:
      - my_key
      - your_key
    region: Amsterdam
    state: present

- name: ensure a server is present and started
  local_action:
    module: vultr_server
    name: "{{ vultr_server_name }}"
    os: CentOS 7 x64
    plan: 1024 MB RAM,25 GB SSD,1.00 TB BW
    ssh_key: my_key
    region: Amsterdam
    state: started

- name: ensure a server is present and stopped
  local_action:
    module: vultr_server
    name: "{{ vultr_server_name }}"
    os: CentOS 7 x64
    plan: 1024 MB RAM,25 GB SSD,1.00 TB BW
    region: Amsterdam
    state: stopped

- name: ensure an existing server is stopped
  local_action:
    module: vultr_server
    name: "{{ vultr_server_name }}"
    state: stopped

- name: ensure an existing server is started
  local_action:
    module: vultr_server
    name: "{{ vultr_server_name }}"
    state: started

- name: ensure a server is absent
  local_action:
    module: vultr_server
    name: "{{ vultr_server_name }}"
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
vultr_server:
  description: Response from Vultr API with a few additions/modification
  returned: success
  type: complex
  contains:
    id:
      description: ID of the server
      returned: success
      type: str
      sample: 10194376
    name:
      description: Name (label) of the server
      returned: success
      type: str
      sample: "ansible-test-vm"
    plan:
      description: Plan used for the server
      returned: success
      type: str
      sample: "1024 MB RAM,25 GB SSD,1.00 TB BW"
    allowed_bandwidth_gb:
      description: Allowed bandwidth to use in GB
      returned: success
      type: int
      sample: 1000
    auto_backup_enabled:
      description: Whether automatic backups are enabled
      returned: success
      type: bool
      sample: false
    cost_per_month:
      description: Cost per month for the server
      returned: success
      type: float
      sample: 5.00
    current_bandwidth_gb:
      description: Current bandwidth used for the server
      returned: success
      type: int
      sample: 0
    date_created:
      description: Date when the server was created
      returned: success
      type: str
      sample: "2017-08-26 12:47:48"
    default_password:
      description: Password to login as root into the server
      returned: success
      type: str
      sample: "!p3EWYJm$qDWYaFr"
    disk:
      description: Information about the disk
      returned: success
      type: str
      sample: "Virtual 25 GB"
    v4_gateway:
      description: IPv4 gateway
      returned: success
      type: str
      sample: "45.32.232.1"
    internal_ip:
      description: Internal IP
      returned: success
      type: str
      sample: ""
    kvm_url:
      description: URL to the VNC
      returned: success
      type: str
      sample: "https://my.vultr.com/subs/vps/novnc/api.php?data=xyz"
    region:
      description: Region the server was deployed into
      returned: success
      type: str
      sample: "Amsterdam"
    v4_main_ip:
      description: Main IPv4
      returned: success
      type: str
      sample: "45.32.233.154"
    v4_netmask:
      description: Netmask IPv4
      returned: success
      type: str
      sample: "255.255.254.0"
    os:
      description: Operating system used for the server
      returned: success
      type: str
      sample: "CentOS 6 x64"
    firewall_group:
      description: Firewall group the server is assigned to
      returned: success and available
      type: str
      sample: "CentOS 6 x64"
    pending_charges:
      description: Pending charges
      returned: success
      type: float
      sample: 0.01
    power_status:
      description: Power status of the server
      returned: success
      type: str
      sample: "running"
    ram:
      description: Information about the RAM size
      returned: success
      type: str
      sample: "1024 MB"
    server_state:
      description: State about the server
      returned: success
      type: str
      sample: "ok"
    status:
      description: Status about the deployment of the server
      returned: success
      type: str
      sample: "active"
    tag:
      description: TBD
      returned: success
      type: str
      sample: ""
    v6_main_ip:
      description: Main IPv6
      returned: success
      type: str
      sample: ""
    v6_network:
      description: Network IPv6
      returned: success
      type: str
      sample: ""
    v6_network_size:
      description:  Network size IPv6
      returned: success
      type: str
      sample: ""
    v6_networks:
      description: Networks IPv6
      returned: success
      type: list
      sample: []
    vcpu_count:
      description: Virtual CPU count
      returned: success
      type: int
      sample: 1
'''

import time
import base64
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text, to_bytes
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrServer(Vultr):

    def __init__(self, module):
        super(AnsibleVultrServer, self).__init__(module, "vultr_server")

        self.server = None
        self.returns = {
            'SUBID': dict(key='id'),
            'label': dict(key='name'),
            'date_created': dict(),
            'allowed_bandwidth_gb': dict(convert_to='int'),
            'auto_backups': dict(key='auto_backup_enabled', convert_to='bool'),
            'current_bandwidth_gb': dict(),
            'kvm_url': dict(),
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
            'power_status': dict(),
            'ram': dict(),
            'plan': dict(),
            'server_state': dict(),
            'status': dict(),
            'firewall_group': dict(),
            'tag': dict(),
            'v6_main_ip': dict(),
            'v6_network': dict(),
            'v6_network_size': dict(),
            'v6_networks': dict(),
            'vcpu_count': dict(convert_to='int'),
        }
        self.server_power_state = None

    def get_startup_script(self):
        return self.query_resource_by_key(
            key='name',
            value=self.module.params.get('startup_script'),
            resource='startupscript',
        )

    def get_os(self):
        if self.module.params.get('snapshot'):
            os_name = 'Snapshot'
        else:
            os_name = self.module.params.get('os')

        return self.query_resource_by_key(
            key='name',
            value=os_name,
            resource='os',
            use_cache=True
        )

    def get_snapshot(self):
        return self.query_resource_by_key(
            key='description',
            value=self.module.params.get('snapshot'),
            resource='snapshot',
            use_cache=True
        )

    def get_ssh_keys(self):
        ssh_key_names = self.module.params.get('ssh_keys')
        if not ssh_key_names:
            return []

        ssh_keys = []
        for ssh_key_name in ssh_key_names:
            ssh_key = self.query_resource_by_key(
                key='name',
                value=ssh_key_name,
                resource='sshkey',
                use_cache=True
            )
            if ssh_key:
                ssh_keys.append(ssh_key)
        return ssh_keys

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
            use_cache=True
        )

    def get_firewall_group(self):
        return self.query_resource_by_key(
            key='description',
            value=self.module.params.get('firewall_group'),
            resource='firewall',
            query_by='group_list'
        )

    def get_user_data(self):
        user_data = self.module.params.get('user_data')
        if user_data is not None:
            user_data = to_text(base64.b64encode(to_bytes(user_data)))
        return user_data

    def get_server_user_data(self, server):
        if not server or not server.get('SUBID'):
            return None

        user_data = self.api_query(path="/v1/server/get_user_data?SUBID=%s" % server.get('SUBID'))
        return user_data.get('userdata')

    def get_server(self, refresh=False):
        if self.server is None or refresh:
            self.server = None
            server_list = self.api_query(path="/v1/server/list")
            if server_list:
                for server_id, server_data in server_list.items():
                    if server_data.get('label') == self.module.params.get('name'):
                        self.server = server_data

                        plan = self.query_resource_by_key(
                            key='VPSPLANID',
                            value=server_data['VPSPLANID'],
                            resource='plans',
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

                        fwg_id = server_data.get('FIREWALLGROUPID')
                        fw = self.query_resource_by_key(
                            key='FIREWALLGROUPID',
                            value=server_data.get('FIREWALLGROUPID') if fwg_id and fwg_id != "0" else None,
                            resource='firewall',
                            query_by='group_list',
                            use_cache=True
                        )
                        self.server['firewall_group'] = fw.get('description')
        return self.server

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

        snapshot_restore = self.module.params.get('snapshot') is not None
        if snapshot_restore:
            required_params.remove('os')

        self.module.fail_on_missing_params(required_params=required_params)

        self.result['changed'] = True
        if not self.module.check_mode:
            data = {
                'DCID': self.get_region().get('DCID'),
                'VPSPLANID': self.get_plan().get('VPSPLANID'),
                'FIREWALLGROUPID': self.get_firewall_group().get('FIREWALLGROUPID'),
                'OSID': self.get_os().get('OSID'),
                'SNAPSHOTID': self.get_snapshot().get('SNAPSHOTID'),
                'label': self.module.params.get('name'),
                'hostname': self.module.params.get('hostname'),
                'SSHKEYID': ','.join([ssh_key['SSHKEYID'] for ssh_key in self.get_ssh_keys()]),
                'enable_ipv6': self.get_yes_or_no('ipv6_enabled'),
                'enable_private_network': self.get_yes_or_no('private_network_enabled'),
                'auto_backups': self.get_yes_or_no('auto_backup_enabled'),
                'notify_activate': self.get_yes_or_no('notify_activate'),
                'tag': self.module.params.get('tag'),
                'reserved_ip_v4': self.module.params.get('reserved_ip_v4'),
                'user_data': self.get_user_data(),
                'SCRIPTID': self.get_startup_script().get('SCRIPTID'),
            }
            self.api_query(
                path="/v1/server/create",
                method="POST",
                data=data
            )
            server = self._wait_for_state(key='status', state='active')
            server = self._wait_for_state(state='running', timeout=3600 if snapshot_restore else 60)
        return server

    def _update_auto_backups_setting(self, server, start_server):
        auto_backup_enabled_changed = self.switch_enable_disable(server, 'auto_backup_enabled', 'auto_backups')

        if auto_backup_enabled_changed:
            if auto_backup_enabled_changed == "enable" and server['auto_backups'] == 'disable':
                self.module.warn("Backups are disabled. Once disabled, backups can only be enabled again by customer support")
            else:
                server, warned = self._handle_power_status_for_update(server, start_server)
                if not warned:
                    self.result['changed'] = True
                    self.result['diff']['before']['auto_backup_enabled'] = server.get('auto_backups')
                    self.result['diff']['after']['auto_backup_enabled'] = self.get_yes_or_no('auto_backup_enabled')

                    if not self.module.check_mode:
                        data = {
                            'SUBID': server['SUBID']
                        }
                        self.api_query(
                            path="/v1/server/backup_%s" % auto_backup_enabled_changed,
                            method="POST",
                            data=data
                        )
        return server

    def _update_ipv6_setting(self, server, start_server):
        ipv6_enabled_changed = self.switch_enable_disable(server, 'ipv6_enabled', 'v6_main_ip')

        if ipv6_enabled_changed:
            if ipv6_enabled_changed == "disable":
                self.module.warn("The Vultr API does not allow to disable IPv6")
            else:
                server, warned = self._handle_power_status_for_update(server, start_server)
                if not warned:
                    self.result['changed'] = True
                    self.result['diff']['before']['ipv6_enabled'] = False
                    self.result['diff']['after']['ipv6_enabled'] = True

                    if not self.module.check_mode:
                        data = {
                            'SUBID': server['SUBID']
                        }
                        self.api_query(
                            path="/v1/server/ipv6_%s" % ipv6_enabled_changed,
                            method="POST",
                            data=data
                        )
                        server = self._wait_for_state(key='v6_main_ip')
        return server

    def _update_private_network_setting(self, server, start_server):
        private_network_enabled_changed = self.switch_enable_disable(server, 'private_network_enabled', 'internal_ip')
        if private_network_enabled_changed:
            if private_network_enabled_changed == "disable":
                self.module.warn("The Vultr API does not allow to disable private network")
            else:
                server, warned = self._handle_power_status_for_update(server, start_server)
                if not warned:
                    self.result['changed'] = True
                    self.result['diff']['before']['private_network_enabled'] = False
                    self.result['diff']['after']['private_network_enabled'] = True

                    if not self.module.check_mode:
                        data = {
                            'SUBID': server['SUBID']
                        }
                        self.api_query(
                            path="/v1/server/private_network_%s" % private_network_enabled_changed,
                            method="POST",
                            data=data
                        )
        return server

    def _update_plan_setting(self, server, start_server):
        plan = self.get_plan()
        plan_changed = True if plan and plan['VPSPLANID'] != server.get('VPSPLANID') else False
        if plan_changed:
            server, warned = self._handle_power_status_for_update(server, start_server)
            if not warned:
                self.result['changed'] = True
                self.result['diff']['before']['plan'] = server.get('plan')
                self.result['diff']['after']['plan'] = plan['name']

                if not self.module.check_mode:
                    data = {
                        'SUBID': server['SUBID'],
                        'VPSPLANID': plan['VPSPLANID'],
                    }
                    self.api_query(
                        path="/v1/server/upgrade_plan",
                        method="POST",
                        data=data
                    )
        return server

    def _handle_power_status_for_update(self, server, start_server):
        # Remember the power state before we handle any action
        if self.server_power_state is None:
            self.server_power_state = server['power_status']

        # A stopped server can be updated
        if self.server_power_state == "stopped":
            return server, False

        # A running server must be forced to update unless the wanted state is stopped
        elif self.module.params.get('force') or not start_server:
            warned = False
            if not self.module.check_mode:
                # Some update APIs would restart the VM, we handle the restart manually
                # by stopping the server and start it at the end of the changes
                server = self.stop_server(skip_results=True)

        # Warn the user that a running server won't get changed
        else:
            warned = True
            self.module.warn("Some changes won't be applied to running instances. " +
                             "Use force=true to allow the instance %s to be stopped/started." % server['label'])

        return server, warned

    def _update_server(self, server=None, start_server=True):
        # Wait for server to unlock if restoring
        if server.get('os').strip() == 'Snapshot':
            server = self._wait_for_state(key='server_status', state='ok', timeout=3600)

        # Update auto backups settings, stops server
        server = self._update_auto_backups_setting(server=server, start_server=start_server)

        # Update IPv6 settings, stops server
        server = self._update_ipv6_setting(server=server, start_server=start_server)

        # Update private network settings, stops server
        server = self._update_private_network_setting(server=server, start_server=start_server)

        # Update plan settings, stops server
        server = self._update_plan_setting(server=server, start_server=start_server)

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
                    path="/v1/server/set_user_data",
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
                    path="/v1/server/tag_set",
                    method="POST",
                    data=data
                )

        # Firewall group
        firewall_group = self.get_firewall_group()
        if firewall_group and firewall_group.get('description') != server.get('firewall_group'):
            self.result['changed'] = True
            self.result['diff']['before']['firewall_group'] = server.get('firewall_group')
            self.result['diff']['after']['firewall_group'] = firewall_group.get('description')

            if not self.module.check_mode:
                data = {
                    'SUBID': server['SUBID'],
                    'FIREWALLGROUPID': firewall_group.get('FIREWALLGROUPID'),
                }
                self.api_query(
                    path="/v1/server/firewall_group_set",
                    method="POST",
                    data=data
                )
        # Start server again if it was running before the changes
        if not self.module.check_mode:
            if self.server_power_state in ['starting', 'running'] and start_server:
                server = self.start_server(skip_results=True)

        server = self._wait_for_state(key='status', state='active')
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
                    path="/v1/server/destroy",
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

    def restart_server(self):
        self.result['changed'] = True
        server = self.get_server()
        if server:
            if not self.module.check_mode:
                data = {
                    'SUBID': server['SUBID']
                }
                self.api_query(
                    path="/v1/server/reboot",
                    method="POST",
                    data=data
                )
                server = self._wait_for_state(state='running')
        return server

    def reinstall_server(self):
        self.result['changed'] = True
        server = self.get_server()
        if server:
            if not self.module.check_mode:
                data = {
                    'SUBID': server['SUBID']
                }
                self.api_query(
                    path="/v1/server/reinstall",
                    method="POST",
                    data=data
                )
                server = self._wait_for_state(state='running')
        return server

    def _wait_for_state(self, key='power_status', state=None, timeout=60):
        time.sleep(1)
        server = self.get_server(refresh=True)
        for s in range(0, timeout):
            # Check for Truely if wanted state is None
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

    def start_server(self, skip_results=False):
        server = self.get_server()
        if server:
            if server['power_status'] == 'starting':
                server = self._wait_for_state(state='running')

            elif server['power_status'] != 'running':
                if not skip_results:
                    self.result['changed'] = True
                    self.result['diff']['before']['power_status'] = server['power_status']
                    self.result['diff']['after']['power_status'] = "running"
                if not self.module.check_mode:
                    data = {
                        'SUBID': server['SUBID']
                    }
                    self.api_query(
                        path="/v1/server/start",
                        method="POST",
                        data=data
                    )
                    server = self._wait_for_state(state='running')
        return server

    def stop_server(self, skip_results=False):
        server = self.get_server()
        if server and server['power_status'] != "stopped":
            if not skip_results:
                self.result['changed'] = True
                self.result['diff']['before']['power_status'] = server['power_status']
                self.result['diff']['after']['power_status'] = "stopped"
            if not self.module.check_mode:
                data = {
                    'SUBID': server['SUBID'],
                }
                self.api_query(
                    path="/v1/server/halt",
                    method="POST",
                    data=data
                )
                server = self._wait_for_state(state='stopped')
        return server


def main():
    argument_spec = vultr_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True, aliases=['label']),
        hostname=dict(),
        os=dict(),
        snapshot=dict(),
        plan=dict(),
        force=dict(type='bool', default=False),
        notify_activate=dict(type='bool', default=False),
        private_network_enabled=dict(type='bool'),
        auto_backup_enabled=dict(type='bool'),
        ipv6_enabled=dict(type='bool'),
        tag=dict(),
        reserved_ip_v4=dict(),
        firewall_group=dict(),
        startup_script=dict(),
        user_data=dict(),
        ssh_keys=dict(type='list', aliases=['ssh_key']),
        region=dict(),
        state=dict(choices=['present', 'absent', 'restarted', 'reinstalled', 'started', 'stopped'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    vultr_server = AnsibleVultrServer(module)
    if module.params.get('state') == "absent":
        server = vultr_server.absent_server()
    else:
        if module.params.get('state') == "started":
            server = vultr_server.present_server()
            server = vultr_server.start_server()
        elif module.params.get('state') == "stopped":
            server = vultr_server.present_server(start_server=False)
            server = vultr_server.stop_server()
        elif module.params.get('state') == "restarted":
            server = vultr_server.present_server()
            server = vultr_server.restart_server()
        elif module.params.get('state') == "reinstalled":
            server = vultr_server.reinstall_server()
        else:
            server = vultr_server.present_server()

    result = vultr_server.get_result(server)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
