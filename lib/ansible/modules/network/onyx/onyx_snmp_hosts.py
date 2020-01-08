#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: onyx_snmp_hosts
version_added: "2.10"
author: "Sara Touqan (@sarato)"
short_description: Configures SNMP host parameters
description:
  - This module provides declarative management of SNMP hosts protocol params
    on Mellanox ONYX network devices.
options:
  hosts:
    type: list
    description:
      - List of snmp hosts
    suboptions:
      name:
        description:
          - Specifies the name of the host.
        required: true
        type: str
      enabled:
        description:
          - Temporarily Enables/Disables sending of all notifications to this host.
        type: bool
      notification_type:
        description:
          - Configures the type of sending notification to the specified host.
        choices: ['trap', 'inform']
        type: str
      port:
        description:
             - Overrides default target port for this host.
        type: str
      version:
        description:
             -  Specifys SNMP version of informs to send.
        choices: ['1', '2c', '3']
        type: str
      user_name:
        description:
             - Specifys username for this inform sink.
        type: str
      auth_type:
        description:
             - Configures SNMP v3 security parameters, specifying passwords in a nother parameter (auth_password) (passwords are always stored encrypted).
        choices: ['md5', 'sha', 'sha224', 'sha256', 'sha384', 'sha512']
        type: str
      auth_password:
        description:
             - The password needed to configure the auth type.
        type: str
      privacy_type:
        description:
             -  Specifys SNMP v3 privacy settings for this user.
        choices: ['3des', 'aes-128', 'aes-192', 'aes-192-cfb', 'aes-256', 'aes-256-cfb', 'des']
        type: str
      privacy_password:
        description:
             - The password needed to configure the privacy type.
        type: str
      state:
        description:
             - Used to decide if you want to delete the specified host or not.
        choices: ['present' , 'absent']
        type: str
"""

EXAMPLES = """
- name: enables snmp host
  onyx_snmp_hosts:
      hosts:
       - name: 1.1.1.1
         enabled: true

- name: configures snmp host with version 2c
  onyx_snmp_hosts:
      hosts:
         - name: 2.3.2.4
           enabled: true
           notification_type: trap
           port: 66
           version: 2c

- name: configures snmp host with version 3 and configures it with user as sara
  onyx_snmp_hosts:
       hosts:
         - name: 2.3.2.4
           enabled: true
           notification_type: trap
           port: 66
           version: 3
           user_name: sara
           auth_type: sha
           auth_password: jnbdfijbdsf
           privacy_type: 3des
           privacy_password: nojfd8uherwiugfh

- name: deletes the snmp host
  onyx_snmp_hosts:
        hosts:
          - name: 2.3.2.4
            state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - snmp-server host <host_name> disable
    - no snmp-server host <host_name> disable
    - snmp-server host <host_name> informs port <port_number> version <version_number>
    - snmp-server host <host_name> traps port <port_number> version <version_number>
    - snmp-server host <host_name> informs port <port_number> version <version_number>  user <user_name> auth <auth_type>
                                                <auth_password> priv <privacy_type> <privacy_password>
    - snmp-server host <host_name> traps port <port_number> version <version_number>  user <user_name> auth <auth_type>
                                              <auth_password> priv <privacy_type> <privacy_password>
    - no snmp-server host <host_name>.
"""

import re

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.network.onyx.onyx import show_cmd
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule


class OnyxSNMPHostsModule(BaseOnyxModule):

    def init_module(self):
        """ initialize module
        """
        host_spec = dict(name=dict(required=True),
                         enabled=dict(type='bool'),
                         notification_type=dict(type='str', choices=['trap', 'inform']),
                         port=dict(type='str'),
                         version=dict(type='str', choices=['1', '2c', '3']),
                         user_name=dict(type='str'),
                         auth_type=dict(type='str', choices=['md5', 'sha', 'sha224', 'sha256', 'sha384', 'sha512']),
                         privacy_type=dict(type='str', choices=['3des', 'aes-128', 'aes-192', 'aes-192-cfb', 'aes-256', 'aes-256-cfb', 'des']),
                         privacy_password=dict(type='str', no_log=True),
                         auth_password=dict(type='str', no_log=True),
                         state=dict(type='str', choices=['present', 'absent'])
                         )
        element_spec = dict(
            hosts=dict(type='list', elements='dict', options=host_spec),
        )
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def validate_snmp_required_params(self):
        req_hosts = self._required_config.get("hosts")
        if req_hosts:
            for host in req_hosts:
                version = host.get('version')
                if version:
                    if version == '3':
                        if host.get('user_name') is None or host.get('auth_type') is None or host.get('auth_password') is None:
                            self._module.fail_json(msg='user_name, auth_type and auth_password are required when version number is 3.')

                if host.get('notification_type') is not None:
                    if host.get('version') is None or host.get('port') is None:
                        self._module.fail_json(msg='port and version are required when notification_type is provided.')

                if host.get('auth_type') is not None:
                    if host.get('auth_password') is None:
                        self._module.fail_json(msg='auth_password is required when auth_type is provided.')

                if host.get('privacy_type') is not None:
                    if host.get('privacy_password') is None:
                        self._module.fail_json(msg='privacy_password is required when privacy_type is provided.')

    def get_required_config(self):
        module_params = self._module.params
        self._required_config = dict(module_params)
        self.validate_param_values(self._required_config)
        self.validate_snmp_required_params()

    def _set_host_config(self, hosts_config):
        hosts = hosts_config.get('Notification sinks')
        if hosts[0].get('Lines'):
            self._current_config['current_hosts'] = dict()
            self._current_config['host_names'] = []
            return

        current_hosts = dict()
        host_names = []
        for host in hosts:
            host_info = dict()
            for host_name in host:
                host_names.append(host_name)
                enabled = True
                first_entry = host.get(host_name)[0]
                if first_entry:
                    if first_entry.get('Enabled') == 'no':
                        enabled = False
                    notification_type = first_entry.get('Notification type')
                    notification_type = notification_type.split()
                    host_info['notification_type'] = notification_type[2]
                    version = notification_type[1][1:]
                    host_info['port'] = first_entry.get('Port')
                    host_info['name'] = host_name
                    host_info['enabled'] = enabled
                    host_info['version'] = version
                    if first_entry.get('Community') is None:
                        if len(first_entry) == 8:
                            host_info['user_name'] = first_entry.get('Username')
                            host_info['auth_type'] = first_entry.get('Authentication type')
                            host_info['privacy_type'] = first_entry.get('Privacy type')
                        elif len(host.get(host_name)) == 2:
                            second_entry = host.get(host_name)[1]
                            host_info['user_name'] = second_entry.get('Username')
                            host_info['auth_type'] = second_entry.get('Authentication type')
                            host_info['privacy_type'] = second_entry.get('Privacy type')
                        else:
                            host_info['user_name'] = ''
                            host_info['auth_type'] = ''
                            host_info['privacy_type'] = ''
                    else:
                        host_info['user_name'] = ''
                        host_info['auth_type'] = ''
                        host_info['privacy_type'] = ''
                current_hosts[host_name] = host_info
        self._current_config['current_hosts'] = current_hosts
        self._current_config['host_names'] = host_names

    def _show_hosts_config(self):
        cmd = "show snmp host"
        return show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False)

    def load_current_config(self):
        self._current_config = dict()
        hosts_config = self._show_hosts_config()
        if hosts_config[1]:
            self._set_host_config(hosts_config[1])

    def generate_snmp_commands_with_current_config(self, host):
        host_id = host.get('name')
        host_notification_type = host.get('notification_type')
        host_enabled = host.get("enabled")
        host_port = host.get('port')
        host_version = host.get('version')
        host_username = host.get('user_name')
        host_auth_type = host.get('auth_type')
        host_auth_pass = host.get('auth_password')
        host_priv_type = host.get('privacy_type')
        host_priv_pass = host.get('privacy_password')
        present_state = host.get('state')
        current_hosts = self._current_config.get("current_hosts")
        current_entry = current_hosts.get(host_id)
        if present_state is not None:
            if present_state == 'absent':
                self._commands.append('no snmp-server host {0}' .format(host_id))
                return
        if host_enabled is not None:
            if current_entry.get('enabled') != host_enabled:
                if host_enabled is True:
                    self._commands.append('no snmp-server host {0} disable' .format(host_id))
                else:
                    self._commands.append('snmp-server host {0} disable' .format(host_id))
        if host_notification_type is not None:
            current_port = current_entry.get('port')
            current_version = current_entry.get('version')
            current_priv_type = current_entry.get('privacy_type')
            current_username = current_entry.get('user_name')
            current_auth_type = current_entry.get('auth_type')
            current_noti_type = current_entry.get('notification_type')
            if host_port is not None:
                if host_version is not None:
                    if host_version == '3':
                        if (host_priv_type is not None and host_priv_pass is not None):
                            if((current_noti_type != host_notification_type) or
                               ((current_port != host_port)) or
                               (current_version != host_version) or
                               (current_priv_type != host_priv_type) or
                               (current_username != host_username) or
                               (current_auth_type != host_auth_type)):
                                self._commands.append('snmp-server host {0} {1}s port {2} version {3} user {4} auth {5} {6} priv {7} {8}'
                                                      .format(host_id, host_notification_type, host_port,
                                                              host_version, host_username, host_auth_type, host_auth_pass,
                                                              host_priv_type, host_priv_pass))
                        else:
                            if((current_noti_type != host_notification_type) or
                               ((current_port != host_port)) or
                               (current_version != host_version) or
                               (current_username != host_username) or
                               (current_auth_type != host_auth_type)):
                                self._commands.append('snmp-server host {0} {1}s port {2} version {3} user {4} auth {5} {6}'
                                                      .format(host_id, host_notification_type,
                                                              host_port, host_version, host_username,
                                                              host_auth_type, host_auth_pass))
                    else:
                        if((current_noti_type != host_notification_type) or
                           ((current_port != host_port)) or
                           (current_version != host_version)):
                            self._commands.append('snmp-server host {0} {1}s port {2} version {3}'
                                                  .format(host_id, host_notification_type,
                                                          host_port, host_version))
                else:
                    if ((current_noti_type != host_notification_type) or
                       ((current_port != host_port))):
                        self._commands.append('snmp-server host {0} {1}s port {2}'
                                              .format(host_id, host_notification_type, host_port))
            else:
                if host_version is not None:
                    if host_version == '3':
                        if (host_priv_type is not None and host_priv_pass is not None):
                            if ((current_noti_type != host_notification_type) or
                               ((current_version != host_version)) or
                               (current_username != host_username) or
                               ((current_auth_type != host_auth_type)) or
                               (current_priv_type != host_priv_type)):
                                self._commands.append('snmp-server host {0} {1}s version {2} user {3} auth {4} {5} priv {6} {7}'
                                                      .format(host_id, host_notification_type, host_version, host_username,
                                                              host_auth_type, host_auth_pass, host_priv_type, host_priv_pass))

                        else:
                            if ((current_noti_type != host_notification_type) or
                               ((current_version != host_version)) or
                               (current_username != host_username) or
                               ((current_auth_type != host_auth_type))):
                                self._commands.append('snmp-server host {0} {1}s version {2} user {3} auth {4} {5}'
                                                      .format(host_id, host_notification_type,
                                                              host_version, host_username, host_auth_type, host_auth_pass))

                    else:
                        if ((current_noti_type != host_notification_type) or
                           ((current_version != host_version))):
                            self._commands.append('snmp-server host {0} {1}s version {2}' .format(host_id,
                                                  host_notification_type, host_version))

    def generate_snmp_commands_without_current_config(self, host):
        host_id = host.get('name')
        host_notification_type = host.get('notification_type')
        host_enabled = host.get("enabled")
        host_port = host.get('port')
        host_version = host.get('version')
        host_username = host.get('user_name')
        host_auth_type = host.get('auth_type')
        host_auth_pass = host.get('auth_password')
        host_priv_type = host.get('privacy_type')
        host_priv_pass = host.get('privacy_password')
        present_state = host.get('state')
        present_state = host.get('state')
        if present_state is not None:
            if present_state == 'absent':
                return
        if host_enabled is not None:
            if host_enabled is True:
                self._commands.append('no snmp-server host {0} disable' .format(host_id))
            else:
                self._commands.append('snmp-server host {0} disable' .format(host_id))

        if host_notification_type is not None:
            if host_port is not None:
                if host_version is not None:
                    if host_version == '3':
                        if (host_priv_type is not None and host_priv_pass is not None):
                            self._commands.append('snmp-server host {0} {1}s port {2} version {3} user {4} auth {5} {6} priv {7} {8}'
                                                  .format(host_id, host_notification_type, host_port, host_version, host_username,
                                                          host_auth_type, host_auth_pass, host_priv_type, host_priv_pass))
                        else:
                            self._commands.append('snmp-server host {0} {1}s port {2} version {3} user {4} auth {5} {6}'
                                                  .format(host_id, host_notification_type, host_port, host_version, host_username,
                                                          host_auth_type, host_auth_pass))
                    else:
                        self._commands.append('snmp-server host {0} {1}s port {2} version {3}' .format(host_id,
                                              host_notification_type, host_port, host_version))
                else:
                    self._commands.append('snmp-server host {0} {1}s port {2}' .format(host_id,
                                                                                       host_notification_type, host_port))
            else:
                if host_version is not None:
                    if host_version == '3':
                        if (host_priv_type is not None and host_priv_pass is not None):
                            self._commands.append('snmp-server host {0} {1}s version {2} user {3} auth {4} {5} priv {6} {7}'
                                                  .format(host_id, host_notification_type, host_version, host_username,
                                                          host_auth_type, host_auth_pass, host_priv_type, host_priv_pass))
                        else:
                            self._commands.append('snmp-server host {0} {1}s version {2} user {3} auth {4} {5}' .format(host_id,
                                                  host_notification_type, host_version, host_username,
                                                  host_auth_type, host_auth_pass))
                    else:
                        self._commands.append('snmp-server host {0} {1}s version {2}' .format(host_id,
                                              host_notification_type, host_version))

    def generate_commands(self):
        req_hosts = self._required_config.get("hosts")
        host_names = self._current_config.get("host_names")

        if req_hosts:
            for host in req_hosts:
                host_id = host.get('name')
                if host_id:
                    if host_names and (host_id in host_names):
                        self.generate_snmp_commands_with_current_config(host)
                    else:
                        self.generate_snmp_commands_without_current_config(host)


def main():
    """ main entry point for module execution
    """
    OnyxSNMPHostsModule.main()


if __name__ == '__main__':
    main()
