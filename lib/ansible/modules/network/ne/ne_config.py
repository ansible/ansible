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


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---

module: ne_config
version_added: "2.4
author: "LiQingKai (@NetEngine-Ansible)"
short_description: Search or Manage Huawei Router configuration sections. 
description:
 - Huawei Router configurations use a simple block indent file syntax
    for segmenting configuration into sections.  This module provides
    an implementation for working with Router configuration sections in
    a deterministic way. This module works with CLI transports.
options:
  section:
    description:
      - This argument will send a command to get particular branch of the running configuration from the remote device
      the value should be a list of configuration  branch names like 'aaa' , 'bgp'...
    required: false
    default: null
  contain:
    description:
      - This argument will search configuration lines containing defined text
      the value should be a list of defined text
    required: false
    default: null
  backup:
    description:
        - This argument will cause the module to create a full backup of
        the current C(current-configuration) from the remote device before any
        changes are made.  The backup file is written to the C(backup)
        folder in the playbook root directory.  If the directory does not
        exist, it will be created.
        the value should be the cfg file name to save like 'snmp.cfg'
    required: false
    default: null
  backup_all:
    description:
        - This argument will cause the module to download all backups in remote device 
        to the local path of "local_file_path"
        If the directory does not exist, it will be created.
    required: false
    default: false
  transfer:
    description:
        - This argument will send a config configurations file to the remote device. 
        the value should be the local cfg file path like '/opt/snmp.cfg'
        Local flie must be exist
    required: false
    default: null
  delete:
    description:
      - This argument will send a command to delete particular configuration files from the remote device
      the value should be a list of cfg file names like 'snmp.cfg'
    required: false
    default: null
  replace:
    description:
      -  This argument will replace the current configuration to specified one with the cfg name of "replace" value
      the value should be a list of cfg file names like 'snmp.cfg'
    required: false
    default: null
  merge:
    description:
      -  This argument will  merge configuration files to the current configuration with the cfg name of "merge" value
      the value should be a cfg file name like 'snmp.cfg'
    required: false
    default: null
  rollback:
    description:
      -  This argument will rollback the current configuration to specified one with the specified mode
      the value should be a cfg file name like 'snmp.cfg' or commit-id like '1000000010'
      or label name like "new_label" or last rollback number like '2'
    required: false
    default: null 
  rollback_type:
    description:
      -  This argument will allow user to choose a rollback mode 
    required: false
    default: file
    choices: ['file', 'commit-id', 'label', 'last']
  local_file:
    description:
        - Local file path for backup file to save . Local directory must be exist.
        When there is 'transfer' not null in playbook,the 'local_file' should be required.
    required: false
    default: null
  local_file_path:
    description:
        - Local path for backup file to save . Local directory must exist.
        When there is 'backup' or 'backup_all' in playbook,the 'local_file_path' should be required.
    required: false
    default: null
  commit:
    description:
      - The commit argument instructs the module to save the
        current-configuration to saved-configuration.  This operation is performed
        after any changes are made to the current running config.  If
        no changes are made, the configuration is still saved to the
        startup config.  This option will always cause the module to
        return changed.
    required: false
    type: bool
    default: false
  trial:
    description:
      -  This argument will allow to delay confirmation of the commitment with a specified time
      the value should be a value of second between 60 and 3600
    required: false
    default: null

"""

EXAMPLES = """
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.

- name: NetEngine config test
  hosts: NetEngine
  connection: local
  gather_facts: no
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ username }}"
      password: "{{ password }}"
      transport: cli

  tasks:

  tasks:
  - name: "get particular branch of the running configuration"
    ne_config:
      section: aaa
      provider: "{{ cli }}"

  - name: "search configuration lines containing defined text"
    ne_config:
      contain: aaa
      provider: "{{ cli }}"
      
  - name: "backup current configuration from remote device to local"
    ne_config:
      backup: snmp.cfg
      local_file_path: /opt
      provider: "{{ cli }}"

  - name: "download all backups in remote device"
    ne_config:
      backup_all: yes
      local_file_path: /opt
      provider: "{{ cli }}"
      
  - name: "send specified cfg file to remote device"
    ne_config:
      transfer: send
      local_file: /opt/snmp.cfg
      provider: "{{ cli }}"

  - name: "delete specified cfg file in remote device"
    ne_config:
      delete: snmp.cfg
      provider: "{{ cli }}"
    
  - name: "delete specified cfg file in remote device"
    ne_config:
      delete: snmp.cfg
      provider: "{{ cli }}"

  - name: "replace the current configuration to specified one with cfg name"
    ne_config:
      replace: snmp.cfg
      provider: "{{ cli }}"
      
  - name: "merge configuration files to the current configuration with cfg name"
    ne_config:
      merge: snmp.cfg
      provider: "{{ cli }}" 
      
  - name: "rollback the current configuration with a specific mode"
    ne_config:
      rollback: snmp.cfg
      rollback_type: file
      provider: "{{ cli }}"  
      
  - name: "Configure any configuration and automatically saved"
    ne_config:
      lines:
        - system-view
        - sysname netengine
      commit: yes
      provider: "{{ cli }}" 
      
  - name: "allow to delay confirmation of the commitment with a specific time"
    ne_config:
      lines:
        - system-view
        - sysname netengine
      trial: 3600
      provider: "{{ cli }}"     
      
"""

RETURN = """
stdout:
  description: the set of responses from the commands
  returned: always
  type: list
  sample: ['...', '...']

stdout_lines:
  description: The value of stdout split into a list
  returned: always
  type: list
  sample: [['...', '...'], ['...'], ['...']]

failed_conditions:
  description: the conditionals that failed
  returned: failed
  type: list
  sample: ['...', '...']
"""
import os
import time
import paramiko
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ne.ne import ne_argument_spec
from ansible.module_utils.network.ne.ne import run_commands
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.six import string_types
from ansible.module_utils.network.common.utils import ComplexList
from ansible.module_utils.connection import ConnectionError

try:
    from scp import SCPClient
    HAS_SCP = True
except ImportError:
    HAS_SCP = False


def to_lines(stdout):
    lines = list()
    for item in stdout:
        if isinstance(item, string_types):
            item = str(item).split('\n')
        lines.append(item)
    return lines


def to_cli(obj):
    cmd = obj['command']
    return cmd


def parse_commands(module, command):
    transform = ComplexList(dict(
        command=dict(key=True),
        prompt=dict(),
        answer=dict()
    ), module)

    commands = transform(command)

    return commands


def delete_config(module):
    responses = list()
    cfg_names = module.params['delete']
    for cfg_name in cfg_names:
        del_cmd = "delete cfcard:/" + cfg_name
        command = dict()
        command['command'] = del_cmd
        command['prompt'] = "Y/N"
        command['answer'] = "Y"
        response = run_commands(module, to_list(command))
        responses.append(response)
        try:
            del_slave_cmd = "delete salve#card:/" + cfg_name
            command_slave = dict()
            command_slave['command'] = del_slave_cmd
            command_slave['prompt'] = "Y/N"
            command_slave['answer'] = "Y"
            response_slave = run_commands(module, to_list(command_slave))
            responses.append(response_slave)
        except ConnectionError:
            responses.append("salve#card is not running,no need to delete!")

    return responses


def search_section(module):
    responses = list()
    sections = module.params['section']
    for section in sections:
        search_cmd = "display current-configuration configuration " + section
        command = dict()
        command['command'] = search_cmd
        response = run_commands(module, to_list(command))
        responses.append(response)
    return responses


def search_contain(module):
    responses = list()
    contains = module.params['contain']
    for contain in contains:
        search_cmd = "display current-configuration  | include " + contain
        command = dict()
        command['command'] = search_cmd
        response = run_commands(module, to_list(command))
        responses.append(response)
    return responses


def backup_config(module):
    responses = list()
    cfg_name = module.params['backup']
    backup_cmd = "save " + cfg_name
    command = dict()
    command['command'] = backup_cmd
    command['prompt'] = "Y/N"
    command['answer'] = "Y"
    result = run_commands(module, to_list(command))
    responses.append(result)
    return responses


def merge_config(module):
    responses = list()
    cfg_name = module.params['merge']
    merge_cmd = "load configuration file " + cfg_name + " merge"
    command = dict()
    command['command'] = merge_cmd
    try:
        result_view = run_commands(module, parse_commands(module, ['system-view']))
        responses.append(result_view)
        result = run_commands(module, to_list(command))
        responses.append(result)
    except ConnectionError as exc:
        message = getattr(exc, 'err', exc)
        responses.append("load configuration complete with some errors! error message:".join(message))
    return responses


def replace_config(module):
    responses = list()
    cfg_name = module.params['replace']
    replace_cmd = "rollback configuration to file  " + cfg_name
    command = dict()
    command['command'] = replace_cmd
    command['prompt'] = "Y/N"
    command['answer'] = "Y"
    result = run_commands(module, to_list(command))
    responses.append(result)
    return responses


def rollback_config(module):
    responses = list()
    if module.params['rollback_type'] and module.params['rollback_type'] == 'file':
        rollback = module.params['rollback']
        rollback_cmd = "rollback configuration to file " + rollback
    elif module.params['rollback_type'] and module.params['rollback_type'] == 'commit-id':
        rollback = module.params['rollback']
        rollback_cmd = "rollback configuration to commit-id " + rollback
    elif module.params['rollback_type'] and module.params['rollback_type'] == 'label':
        rollback = module.params['rollback']
        rollback_cmd = "rollback configuration to label " + rollback
    elif module.params['rollback_type'] and module.params['rollback_type'] == 'last':
        rollback = module.params['rollback']
        rollback_cmd = "rollback configuration last " + rollback
    else:
        rollback = module.params['rollback']
        rollback_cmd = "rollback configuration to file " + rollback
    command = dict()
    command['command'] = rollback_cmd
    command['prompt'] = "Y/N"
    command['answer'] = "Y"
    result = run_commands(module, to_list(command))
    responses.append(result)
    return responses


class FileOperation(object):
    """File copy function class"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # file copy parameters
        self.local_file = self.module.params['local_file']
        self.local_file_path = self.module.params['local_file_path']
        self.backup = self.module.params['backup']
        self.file_system = 'cfcard:'
        if self.local_file_path is not None and not self.local_file_path.endswith("/"):
            self.local_file_path = self.local_file_path + "/"

        # state
        self.transfer_result = None
        self.changed = False

    def init_module(self):
        """Init module"""

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def local_file_exists(self):
        """Local file whether exists"""

        return os.path.isfile(self.local_file)

    def is_dir(self):
        """Local file whether exists"""

        return os.path.isdir(self.local_file_path)

    def transfer_file(self, dest):
        """Begin to transfer file by scp"""

        if not self.local_file_exists():
            self.module.fail_json(
                msg='Could not transfer file. Local file doesn\'t exist.')

        hostname = self.module.params['provider']['host']
        username = self.module.params['provider']['username']
        password = self.module.params['provider']['password']
        port = self.module.params['provider']['port']

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=hostname, username=username, password=password, port=port)
        full_remote_path = '{}{}'.format(self.file_system, dest)
        scp = SCPClient(ssh.get_transport())
        try:
            scp.put(self.local_file, full_remote_path)
        except:
            time.sleep(10)
            scp.close()
            self.module.fail_json(msg='Could not transfer file. There was an error '
                                      'during transfer. Please make sure the format of '
                                      'input parameters is right.')
        scp.close()
        return True

    def download_file(self, dest):
        """Begin to download file by scp"""

        hostname = self.module.params['provider']['host']
        username = self.module.params['provider']['username']
        password = self.module.params['provider']['password']
        port = self.module.params['provider']['port']

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=hostname, username=username, password=password, port=port)
        full_remote_file = '{}{}'.format(self.file_system, "/" + dest)
        scp = SCPClient(ssh.get_transport())

        try:
            scp.get(full_remote_file, self.local_file_path + dest)
        except:
            time.sleep(10)
            scp.close()
            self.module.fail_json(msg='Could not transfer file. There was an error '
                                      'during transfer. Please make sure the format of '
                                      'input parameters is right.')
        scp.close()
        return True

    def send_cfg(self):

        """Excute task """
        if not os.path.isfile(self.local_file):
            self.module.fail_json(
                msg="Local file {} not found".format(self.local_file))

        dest = '/' + os.path.basename(self.local_file)

        self.transfer_file(dest)
        self.transfer_result = 'The local file has been successfully transferred to the device.'

    def receive_cfg(self):
        """Excute task """
        if not self.is_dir():
            os.makedirs(self.local_file_path)

        self.download_file(self.backup)
        self.transfer_result = 'The local file has been successfully download to ansible server.'

    def backup_all(self):
        if not self.is_dir():
            os.makedirs(self.local_file_path)
        hostname = self.module.params['provider']['host']
        username = self.module.params['provider']['username']
        password = self.module.params['provider']['password']
        port = self.module.params['provider']['port']
        client = paramiko.Transport((hostname, port))
        client.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(client)
        files = sftp.listdir("/")
        for file_name in files:
            if ".cfg" in file_name:
                sftp.get("/" + file_name, self.local_file_path + file_name)

        client.close()
        self.transfer_result = 'The local file has been successfully download to ansible server.'


def main():
    """entry point for module execution
    """
    argument_spec = dict(
        transfer=dict(type='path'),
        delete=dict(type='list'),
        section=dict(type='list'),
        contain=dict(type='list'),
        replace=dict(type='str'),
        # config operations
        backup=dict(type='str'),
        backup_all=dict(type='bool', default=False),
        rollback_type=dict(default='file', choices=['file', 'commit-id', 'label', 'last']),
        rollback=dict(type='str'),
        merge=dict(type='str'),
        lines=dict(type='list'),
        commit=dict(type='bool', default=False),
        trial=dict(type='str'),
        local_file=dict(type='path'),
        local_file_path=dict(type='path')
    )

    argument_spec.update(ne_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)
    warnings = list()
    responselist = list()
    result = dict(changed=False, warnings=warnings)

    if module.params['transfer'] and str(module.params['transfer']) == 'send':
        file_operation_obj = FileOperation(argument_spec)
        file_operation_obj.send_cfg()

    if module.params['backup']:
        result_backup = backup_config(module)
        responselist.append(result_backup)
        file_operation_obj = FileOperation(argument_spec)
        file_operation_obj.receive_cfg()

    if module.params['backup_all']:
        file_operation_obj = FileOperation(argument_spec)
        file_operation_obj.backup_all()

    if module.params['section']:
        result_search_section = search_section(module)
        responselist.append(result_search_section)

    if module.params['contain']:
        result_search_contain = search_contain(module)
        responselist.append(result_search_contain)

    if module.params['delete']:
        result_delete = delete_config(module)
        responselist.append(result_delete)

    if module.params['merge']:
        result_merge = merge_config(module)
        responselist.append(result_merge)

    if module.params['replace']:
        result_replace = replace_config(module)
        responselist.append(result_replace)

    if module.params['rollback']:
        result_rollback = rollback_config(module)
        responselist.append(result_rollback)

    if module.params['lines']:
        commands = module.params['lines']
        result_command = run_commands(module, parse_commands(module, commands))
        responselist.append(result_command)

    if module.params['trial']:
        command = 'commit trial ' + module.params['trial']
        result_command = run_commands(module, parse_commands(module, [command]))
        responselist.append(result_command)
    elif module.params['commit']:
        command = 'commit'
        result_command = run_commands(module, parse_commands(module, [command]))
        responselist.append(result_command)

    result.update({
        'changed': True,
        'stdout': responselist,
        'stdout_lines': to_lines(responselist)
    })
    module.exit_json(**result)


if __name__ == '__main__':
    main()
