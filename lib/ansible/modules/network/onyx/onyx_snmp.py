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
module: onyx_snmp
version_added: "2.10"
author: "Sara-Touqan (@sarato)"
short_description: Manages SNMP general configurations on Mellanox ONYX network devices
description:
  - This module provides declarative management of SNMP
    on Mellanox ONYX network devices.
options:
  state_enabled:
    description:
      - Enables/Disables the state of the SNMP configuration.
    choices: ['yes', 'no']
    type: str
  contact_name:
    description:
      - Sets the SNMP contact name.
    type: str
  location:
    description:
      - Sets the SNMP location.
    type: str
  communities_enabled:
    description:
      - Enables/Disables community-based authentication on the system.
    choices: ['yes', 'no']
    type: str
  multi_communities_enabled:
    description:
      - Enables/Disables multiple communities to be configured.
    choices: ['yes', 'no']
    type: str
  snmp_communities:
    type: list
    description:
      - List of snmp communities
    suboptions:
      community_name:
        description:
          - Configures snmp community name.
        required: true
        type: str
      community_type:
        description:
          - Add this community as either a read-only or read-write community.
        choices: ['ro', 'rw']
        type: str
      delete:
        description:
             - Used to decide if you want to delete the given snmp community or not
        choices: ['yes', 'no']
        type: str
  notify_enabled:
    description:
      - Enables/Disables sending of SNMP notifications (traps and informs) from thee system.
    choices: ['yes', 'no']
    type: str
  notify_port:
    description:
      - Sets the default port to which notifications are sent.
    type: str
  notify_community:
    description:
      - Sets the default community for SNMP v1 and v2c notifications sent to hosts which do not have a community override set.
    type: str
  notify_send_test:
    description:
      -  Sends a test notification.
    type: str
  notify_event:
    description:
      - Specifys which events will be sent as SNMP notifications.
    type: str
  engine_id_reset:
    description:
      - Sets SNMPv3 engineID to node unique value.
    choices: ['yes', 'no']
    type: str
  snmp_permissions:
    type: list
    description:
      -  Allow SNMPSET requests for items in a MIB.
    suboptions:
      state_enabled:
        description:
          - Enables/Disables the request.
        required: true
        choices: ['yes','no']
        type: str
      permission type:
        description:
          - Configures the request type.
        choices: ['MELLANOX-CONFIG-DB-MIB', 'MELLANOX-EFM-MIB','MELLANOX-POWER-CYCLE','MELLANOX-SW-UPDATE','RFC1213-MIB']
        type: str
"""

EXAMPLES = """
- name: configure SNMP
   - onyx_snmp:
         state_enabled: yes
         contact_name: sara
         location: Nablus
         communities_enabled: no
         multi_communities_enabled: no
         notify_enabled: yes
         notify_port: 1
         notify_community: community_1
         notify_send_test: yes
         notify_event: temperature-too-high
         engine_id_reset: yes
         snmp_communities:
              - community_name: public
                community_type: ro
                delete: no
         snmp_permissions:
              - state_enabled: yes
                permission_type: MELLANOX-CONFIG-DB-MIB
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always.
  type: list
  sample:
    - snmp-server enable
    - no snmp-server enable
    - snmp-server location <location_name>
    - snmp-server contact <contact_name>
    - snmp-server enable communities
    - no snmp-server enable communities
    - snmp-server enable mult-communities
    - no snmp-server enable mult-communities
    - snmp-server enable notify
    - snmp-server notify port <port_number>
    - snmp-server notify community <community_name>
    - snmp-server notify send-test
    - snmp-server notify event <event_name>
    - snmp-server enable set-permission <permission_type>
    - no snmp-server enable set-permission <permission_type>
    - snmp-server community <community_name> <community_type>
    - no snmp-server community <community_name>.
    - snmp-server engineID reset.
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule
from ansible.module_utils.network.onyx.onyx import show_cmd


class OnyxSNMPModule(BaseOnyxModule):

    def init_module(self):
        """ module initialization
        """

        community_spec = dict(community_name=dict(required=True),
                              community_type=dict(choices=['ro', 'rw']),
                              delete=dict(choices=['yes', 'no']))

        snmp_permission_spec = dict(state_enabled=dict(choices=['yes', 'no'], required=True),
                                    permission_type=dict(choices=['MELLANOX-CONFIG-DB-MIB', 'MELLANOX-EFM-MIB', 'MELLANOX-POWER-CYCLE',
                                                                  'MELLANOX-SW-UPDATE', 'RFC1213-MIB']))

        event_choices = ['asic-chip-down', 'dcbx-pfc-port-oper-state-trap', 'insufficient-power', 'mstp-new-bridge-root',
                         'ospf-lsdb-approaching-overflow', 'sm-stop', 'user-logout', 'cli-line-executed', 'dcbx-pfc-port-peer-state-trap',
                         'interface-down', 'mstp-new-root-port', 'ospf-lsdb-overflow', 'snmp-authtrap', 'xstp-new-root-bridge',
                         'cpu-util-high', 'disk-io-high', 'interface-up', 'mstp-topology-change', 'ospf-nbr-state-change',
                         'temperature-too-high', 'xstp-root-port-change', 'dcbx-ets-module-state-change', 'disk-space-low',
                         'internal-bus-error', 'netusage-high', 'paging-high', 'topology_change', 'xstp-topology-change',
                         'dcbx-ets-port-admin-state-trap', 'entity-state-change', 'internal-link-speed-mismatch', 'new_root',
                         'power-redundancy-mismatch', 'unexpected-cluster-join', 'dcbx-ets-port-oper-state-trap', 'expected-shutdown',
                         'liveness-failure', 'ospf-auth-fail', 'process-crash', 'unexpected-cluster-leave', 'dcbx-ets-port-peer-state-trap',
                         'health-module-status', 'low-power', 'ospf-config-error', 'process-exit', 'unexpected-cluster-size',
                         'dcbx-pfc-module-state-change', 'insufficient-fans', 'low-power-recover', 'ospf-if-rx-bad-packet',
                         'sm-restart', 'unexpected-shutdown', 'dcbx-pfc-port-admin-state-trap', 'insufficient-fans-recover', 'memusage-high',
                         'ospf-if-state-change', 'sm-start', 'user-login']
        element_spec = dict(
            state_enabled=dict(choices=['yes', 'no']),
            contact_name=dict(type='str'),
            location=dict(type='str'),
            communities_enabled=dict(choices=['yes', 'no']),
            multi_communities_enabled=dict(choices=['yes', 'no']),
            snmp_communities=dict(type='list', elements='dict', options=community_spec),
            notify_enabled=dict(choices=['yes', 'no']),
            notify_port=dict(type='str'),
            notify_community=dict(type='str'),
            notify_send_test=dict(type='str', choices=['yes']),
            notify_event=dict(type='str', choices=event_choices),
            engine_id_reset=dict(choices=['yes', 'no']),
            snmp_permissions=dict(type='list', elements='dict', options=snmp_permission_spec)
        )
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def get_required_config(self):
        module_params = self._module.params
        self._required_config = dict(module_params)
        self.validate_param_values(self._required_config)

    def _show_snmp_config(self):
        show_cmds = []
        cmd = "show snmp"
        show_cmds.append(show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False))
        cmd = "show running-config | include snmp"
        show_cmds.append(show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False))
        return show_cmds

    def _set_snmp_config(self, all_snmp_config):
        ro_communities_list = []
        rw_communities_list = []
        snmp_config = all_snmp_config[0]
        if not snmp_config:
            return
        self._current_config['state_enabled'] = snmp_config.get("SNMP enabled")
        self._current_config['contact_name'] = snmp_config.get("System contact")
        self._current_config['location'] = snmp_config.get("System location")
        if snmp_config.get("Read-only community"):
            ro_arr = snmp_config.get("Read-only community").split(' ')
            rw_arr = snmp_config.get("Read-write community").split(' ')
            ro_communities_list = ro_arr[0]
            rw_communities_list = rw_arr[0]
            if (len(ro_arr) == 2):
                self._current_config['communities_enabled'] = "no"
            else:
                self._current_config['communities_enabled'] = "yes"
        else:
            read_only_communities = all_snmp_config[1]
            read_write_communities = all_snmp_config[2]
            if not read_only_communities:
                return
            if read_only_communities.get("Read-only communities"):
                self._current_config['communities_enabled'] = "yes"
                ro_communities_list = read_only_communities.get("Read-only communities")[0].get("Lines")
            else:
                self._current_config['communities_enabled'] = "no"
                if read_only_communities.get("Read-only communities (DISABLED)"):
                    ro_communities_list = read_only_communities.get("Read-only communities (DISABLED)")[0].get("Lines")
            if not read_write_communities:
                return
            if read_write_communities.get("Read-write communities"):
                self._current_config['communities_enabled'] = "yes"
                rw_communities_list = read_write_communities.get("Read-write communities")[0].get("Lines")
            else:
                self._current_config['communities_enabled'] = "no"
                if read_write_communities.get("Read-write communities (DISABLED)"):
                    rw_communities_list = read_write_communities.get("Read-write communities (DISABLED)")[0].get("Lines")
        self._current_config['ro_communities_list'] = ro_communities_list
        self._current_config['rw_communities_list'] = rw_communities_list

    def _set_snmp_running_config(self, snmp_running_config):
        self._current_config['multi_comm_enabled'] = 'yes'
        self._current_config['notify_enabled'] = 'yes'
        curr_config_arr = []
        snmp_lines = snmp_running_config.get('Lines')
        for runn_config in snmp_lines:
            curr_config_arr.append(runn_config.strip())
        if 'no snmp-server enable mult-communities' in snmp_lines:
            self._current_config['multi_comm_enabled'] = 'no'
        if 'no snmp-server enable notify' in snmp_lines:
            self._current_config['notify_enabled'] = 'no'
        self._current_config['snmp_running_config'] = curr_config_arr

    def load_current_config(self):
        self._current_config = dict()
        snmp_config = self._show_snmp_config()
        if snmp_config[0]:
            self._set_snmp_config(snmp_config[0])
        if snmp_config[1]:
            self._set_snmp_running_config(snmp_config[1])

    def generate_commands(self):
        current_state = self._current_config.get("state_enabled")
        state = current_state
        if self._required_config.get("state_enabled"):
            state = self._required_config.get("state_enabled")
        if state is not None:
            if current_state != state:
                if (state == 'yes'):
                    self._commands.append('snmp-server enable')
                else:
                    self._commands.append('no snmp-server enable')

        if self._required_config.get("contact_name"):
            contact_name = self._required_config.get("contact_name")
            current_contact_name = self._current_config.get("contact_name")
            if contact_name is not None:
                if current_contact_name != contact_name:
                    self._commands.append('snmp-server contact {0}' .format(contact_name))

        if self._required_config.get("location"):
            location = self._required_config.get("location")
            current_location = self._current_config.get("location")
            if location is not None:
                if current_location != location:
                    self._commands.append('snmp-server location {0}' .format(location))

        if self._required_config.get("communities_enabled"):
            communities_enabled = self._required_config.get("communities_enabled")
            current_communities_enabled = self._current_config.get("communities_enabled")
            if communities_enabled is not None:
                if current_communities_enabled != communities_enabled:
                    if communities_enabled == "yes":
                        self._commands.append('snmp-server enable communities')
                    else:
                        self._commands.append('no snmp-server enable communities')

        ro_communities = self._current_config.get("ro_communities_list")
        rw_communities = self._current_config.get("rw_communities_list")
        if self._required_config.get("snmp_communities"):
            snmp_communities = self._required_config.get("snmp_communities")
            if snmp_communities is not None:
                for community in snmp_communities:
                    if community.get("delete"):
                        if community.get("delete") == 'yes':
                            self._commands.append('no snmp-server community {0}' .format(community.get("community_name")))
                            continue
                    if community.get("community_type"):
                        if community.get("community_type") == 'ro':
                            if community.get("community_name") not in ro_communities:
                                self._commands.append('snmp-server community {0} {1}' .format(community.get("community_name"),
                                                                                              community.get("community_type")))
                        else:
                            if community.get("community_name") not in rw_communities:
                                self._commands.append('snmp-server community {0} {1}' .format(community.get("community_name"),
                                                                                              community.get("community_type")))
                    else:
                        if community.get("community_name") not in ro_communities:
                            self._commands.append('snmp-server community {0}' .format(community.get("community_name")))

        if self._required_config.get("engine_id_reset"):
            engine_id_reset = self._required_config.get("engine_id_reset")
            if engine_id_reset is not None:
                if engine_id_reset == 'yes':
                    self._commands.append('snmp-server engineID reset')

        current_multi_comm_state = self._current_config.get("multi_comm_enabled")
        if self._required_config.get("multi_communities_enabled"):
            multi_communities_enabled = self._required_config.get("multi_communities_enabled")
            if multi_communities_enabled is not None:
                if current_multi_comm_state != multi_communities_enabled:
                    if multi_communities_enabled == 'yes':
                        self._commands.append('snmp-server enable mult-communities')
                    else:
                        self._commands.append('no snmp-server enable mult-communities')

        if self._required_config.get("notify_enabled"):
            notify_enabled = self._required_config.get("notify_enabled")
            current_notify_state = self._current_config.get("notify_enabled")
            if notify_enabled is not None:
                if current_notify_state != notify_enabled:
                    if notify_enabled == 'yes':
                        self._commands.append('snmp-server enable notify')
                    else:
                        self._commands.append('no snmp-server enable notify')

        if self._required_config.get("snmp_permissions"):
            snmp_permissions = self._required_config.get("snmp_permissions")
            if snmp_permissions is not None:
                for permission in snmp_permissions:
                    if permission.get('state_enabled') == 'yes':
                        self._commands.append('snmp-server enable set-permission {0}' .format(permission.get('permission_type')))
                    else:
                        self._commands.append('no snmp-server enable set-permission {0}' .format(permission.get('permission_type')))

        snmp_running_config = self._current_config.get("snmp_running_config")
        if self._required_config.get("notify_port"):
            notify_port = self._required_config.get("notify_port")
            if notify_port is not None:
                notified_cmd = 'snmp-server notify port {0}' .format(notify_port)
                if notified_cmd not in snmp_running_config:
                    self._commands.append('snmp-server notify port {0}' .format(notify_port))

        if self._required_config.get("notify_community"):
            notify_community = self._required_config.get("notify_community")
            if notify_community is not None:
                notified_cmd = 'snmp-server notify community {0}' .format(notify_community)
                if notified_cmd not in snmp_running_config:
                    self._commands.append('snmp-server notify community {0}' .format(notify_community))

        if self._required_config.get("notify_send_test"):
            notify_send_test = self._required_config.get("notify_send_test")
            if notify_send_test is not None:
                self._commands.append('snmp-server notify send-test')

        if self._required_config.get("notify_event"):
            notify_event = self._required_config.get("notify_event")
            if notify_event is not None:
                self._commands.append('snmp-server notify event {0}' .format(notify_event))


def main():
    """ main entry point for module execution
    """
    OnyxSNMPModule.main()


if __name__ == '__main__':
    main()
