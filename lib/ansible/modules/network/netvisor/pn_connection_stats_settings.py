#!/usr/bin/python
""" PN CLI connection-stats-settings-modify """

# Copyright 2018 Pluribus Networks
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: pn_connection_stats_settings
author: "Pluribus Networks (devops@pluribusnetworks.com)"
version_added: "2.7"
short_description: CLI command to modify connection-stats-settings.
description:
  - C(modify): modify the settings for collecting statistical
               data about connections
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
    type: str
  state:
    description:
      - State the action to perform. Use 'update' to modify the
        connection-stats-settings.
    required: True
  pn_enable:
    description:
      - enable or disable collecting connections statistics
    required: false
    type: bool
  pn_connection_backup_enable:
    description:
      - enable backup for connection statistics collection
    required: false
    type: bool
  pn_client_server_stats_max_memory:
    description:
      - maximum memory for client server statistics
    required: false
    type: str
  pn_connection_stats_log_disk_space:
    description:
      - disk-space allocated for statistics (including rotated log files)
    required: false
    type: str
  pn_client_server_stats_log_enable:
    description:
      - enable or disable statistics
    required: false
    type: bool
  pn_service_stat_max_memory:
    description:
      - maximum memory allowed for service statistics
    required: false
    type: str
  pn_connection_stats_log_interval:
    description:
      - interval to collect statistics
    required: false
    type: str
  pn_fabric_connection_backup_interval:
    description:
      - backup interval for fabric connection statistics collection
    required: false
    type: str
  pn_connection_backup_interval:
    description:
      - backup interval for connection statistics collection
    required: false
    type: str
  pn_connection_stats_log_enable:
    description:
      - enable or disable statistics
    required: false
    type: bool
  pn_fabric_connection_max_memory:
    description:
      - maximum memory allowed for fabric connection statistics
    required: false
    type: str
  pn_fabric_connection_backup_enable:
    description:
      - enable backup for fabric connection statistics collection
    required: false
    type: bool
  pn_client_server_stats_log_disk_space:
    description:
      - disk-space allocated for statistics (including rotated log files)
    required: false
    type: str
  pn_connection_max_memory:
    description:
      - maximum memory allowed for connection statistics
    required: false
    type: str
  pn_connection_stats_max_memory:
    description:
      - maximum memory allowed for connection statistics
    required: false
    type: str
  pn_client_server_stats_log_interval:
    description:
      - interval to collect statistics
    required: false
    type: str
"""

EXAMPLES = """
- name: "Modify connection stats settings"
  pn_connection_stats_settings:
    pn_cliswitch: "sw01"
    state: "update"
    pn_enable: False
    pn_fabric_connection_max_memory: "1000"

- name: "Modify connection stats settings"
  pn_connection_stats_settings:
    pn_cliswitch: "sw01"
    state: "update"
    pn_enable: True
"""

RETURN = """
command:
  description: the CLI command run on the target node.
stdout:
  description: set of responses from the connection-stats-settings command.
  returned: always
  type: list
stderr:
  description: set of error responses from the connection-stats-settings
               command.
  returned: on error
  type: list
changed:
  description: indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

import shlex
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pn_nvos import pn_cli
from ansible.module_utils.pn_nvos import booleanArgs


def run_cli(module, cli):
    """
    This method executes the cli command on the target node(s) and returns the
    output. The module then exits based on the output.
    :param cli: the complete cli string to be executed on the target node(s).
    :param module: The Ansible module to fetch command
    """
    state = module.params['state']
    command = state_map[state]

    cmd = shlex.split(cli)
    result, out, err = module.run_command(cmd)

    remove_cmd = '/usr/bin/cli --quiet -e --no-login-prompt'

    # Response in JSON format
    if result != 0:
        module.exit_json(
            command=' '.join(cmd).replace(remove_cmd, ''),
            stderr=err.strip(),
            msg="%s operation failed" % command,
            changed=False
        )

    if out:
        module.exit_json(
            command=' '.join(cmd).replace(remove_cmd, ''),
            stdout=out.strip(),
            msg="%s operation completed" % command,
            changed=True
        )

    else:
        module.exit_json(
            command=' '.join(cmd).replace(remove_cmd, ''),
            msg="%s operation completed" % command,
            changed=True
        )


def main():
    """ This section is for arguments parsing """

    global state_map
    state_map = dict(
        update='connection-stats-settings-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_enable=dict(required=False, type='bool'),
            pn_connection_backup_enable=dict(required=False, type='bool'),
            pn_client_server_stats_max_memory=dict(required=False, type='str'),
            pn_connection_stats_log_disk_space=dict(required=False,
                                                    type='str'),
            pn_client_server_stats_log_enable=dict(required=False,
                                                   type='bool'),
            pn_service_stat_max_memory=dict(required=False, type='str'),
            pn_connection_stats_log_interval=dict(required=False, type='str'),
            pn_fabric_connection_backup_interval=dict(required=False,
                                                      type='str'),
            pn_connection_backup_interval=dict(required=False, type='str'),
            pn_connection_stats_log_enable=dict(required=False, type='bool'),
            pn_fabric_connection_max_memory=dict(required=False, type='str'),
            pn_fabric_connection_backup_enable=dict(required=False,
                                                    type='bool'),
            pn_client_server_stats_log_disk_space=dict(required=False,
                                                       type='str'),
            pn_connection_max_memory=dict(required=False, type='str'),
            pn_connection_stats_max_memory=dict(required=False, type='str'),
            pn_client_server_stats_log_interval=dict(required=False,
                                                     type='str'),
        ),
        required_one_of=[['pn_enable', 'pn_connection_backup_enable',
                          'pn_client_server_stats_max_memory',
                          'pn_connection_stats_log_disk_space',
                          'pn_client_server_stats_log_enable',
                          'pn_service_stat_max_memory',
                          'pn_connection_stats_log_interval',
                          'pn_connection_backup_interval',
                          'pn_connection_stats_log_enable',
                          'pn_fabric_connection_max_memory',
                          'pn_fabric_connection_backup_enable',
                          'pn_client_server_stats_log_disk_space',
                          'pn_connection_max_memory',
                          'pn_connection_stats_max_memory',
                          'pn_client_server_stats_log_interval']]
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    enable = module.params['pn_enable']
    connection_backup_enable = module.params['pn_connection_backup_enable']
    client_server_stats_max_memory = module.params['pn_client_server_stats_max_memory']
    connection_stats_log_disk_space = module.params['pn_connection_stats_log_disk_space']
    client_server_stats_log_enable = module.params['pn_client_server_stats_log_enable']
    service_stat_max_memory = module.params['pn_service_stat_max_memory']
    connection_stats_log_interval = module.params['pn_connection_stats_log_interval']
    fabric_connection_backup_interval = module.params['pn_fabric_connection_backup_interval']
    connection_backup_interval = module.params['pn_connection_backup_interval']
    connection_stats_log_enable = module.params['pn_connection_stats_log_enable']
    fabric_connection_max_memory = module.params['pn_fabric_connection_max_memory']
    fabric_connection_backup_enable = module.params['pn_fabric_connection_backup_enable']
    client_server_stats_log_disk_space = module.params['pn_client_server_stats_log_disk_space']
    connection_max_memory = module.params['pn_connection_max_memory']
    connection_stats_max_memory = module.params['pn_connection_stats_max_memory']
    client_server_stats_log_interval = module.params['pn_client_server_stats_log_interval']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    if command == 'connection-stats-settings-modify':
        cli += ' %s ' % command

        cli += booleanArgs(enable, 'enable', 'disable')
        cli += booleanArgs(connection_backup_enable, 'connection-backup-enable', 'connection-backup-disable')
        cli += booleanArgs(client_server_stats_log_enable, 'client-server-stats-log-enable', 'client-server-stats-log-disable')
        cli += booleanArgs(connection_stats_log_enable, 'connection-stats-log-enable', 'connection-stats-log-disable')
        cli += booleanArgs(fabric_connection_backup_enable, 'fabric-connection-backup-enable', 'fabric-connection-backup-disable')

        if client_server_stats_max_memory:
            cli += ' client-server-stats-max-memory ' + client_server_stats_max_memory
        if connection_stats_log_disk_space:
            cli += ' connection-stats-log-disk-space ' + connection_stats_log_disk_space
        if service_stat_max_memory:
            cli += ' service-stat-max-memory ' + service_stat_max_memory
        if connection_stats_log_interval:
            cli += ' connection-stats-log-interval ' + connection_stats_log_interval
        if fabric_connection_backup_interval:
            cli += ' fabric-connection-backup-interval ' + fabric_connection_backup_interval
        if connection_backup_interval:
            cli += ' connection-backup-interval ' + connection_backup_interval
        if fabric_connection_max_memory:
            cli += ' fabric-connection-max-memory ' + fabric_connection_max_memory
        if client_server_stats_log_disk_space:
            cli += ' client-server-stats-log-disk-space ' + client_server_stats_log_disk_space
        if connection_max_memory:
            cli += ' connection-max-memory ' + connection_max_memory
        if connection_stats_max_memory:
            cli += ' connection-stats-max-memory ' + connection_stats_max_memory
        if client_server_stats_log_interval:
            cli += ' client-server-stats-log-interval ' + client_server_stats_log_interval

    run_cli(module, cli)


if __name__ == '__main__':
    main()
