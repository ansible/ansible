#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Christian Kotte <christian.kotte@gmx.de>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: vmware_vcenter_settings
short_description: Configures general settings on a vCenter server
description:
- This module can be used to configure the vCenter server general settings (except the statistics).
- The statistics can be configured with the module C(vmware_vcenter_statistics).
version_added: 2.8
author:
- Christian Kotte (@ckotte)
notes:
- Tested with vCenter Server Appliance (vCSA) 6.5 and 6.7
requirements:
- python >= 2.6
- PyVmomi
options:
    database:
        description:
            - The database settings for vCenter server.
            - 'Valid attributes are:'
            - '- C(max_connections) (int): Maximum connections. (default: 50)'
            - '- C(task_cleanup) (bool): Task cleanup. (default: true)'
            - '- C(task_retention) (int): Task retention (days). (default: 30)'
            - '- C(event_cleanup) (bool): Event cleanup. (default: true)'
            - '- C(event_retention) (int): Event retention (days). (default: 30)'
        type: dict
        default: {
            max_connections: 50,
            task_cleanup: True,
            task_retention: 30,
            event_cleanup: True,
            event_retention: 30,
        }
    runtime_settings:
        description:
            - The unique runtime settings for vCenter server.
            - 'Valid attributes are:'
            - '- C(unique_id) (int): vCenter server unique ID.'
            - '- C(managed_address) (str): vCenter server managed address.'
            - '- C(vcenter_server_name) (str): vCenter server name. (default: FQDN)'
        type: dict
    user_directory:
        description:
            - The user directory settings for the vCenter server installation.
            - 'Valid attributes are:'
            - '- C(timeout) (int): User directory timeout. (default: 60)'
            - '- C(query_limit) (bool): Query limit. (default: true)'
            - '- C(query_limit_size) (int): Query limit size. (default: 5000)'
            - '- C(validation) (bool): Mail Validation. (default: true)'
            - '- C(validation_period) (int): Validation period. (default: 1440)'
        type: dict
        default: {
            timeout: 60,
            query_limit: True,
            query_limit_size: 5000,
            validation: True,
            validation_period: 1440,
        }
    mail:
        description:
            - The settings vCenter server uses to send email alerts.
            - 'Valid attributes are:'
            - '- C(server) (str): Mail server'
            - '- C(sender) (str): Mail sender address'
        type: dict
    snmp_receivers:
        description:
            - SNMP trap destinations for vCenter server alerts.
            - 'Valid attributes are:'
            - '- C(snmp_receiver_1_url) (str): Primary Receiver ULR. (default: "localhost")'
            - '- C(snmp_receiver_1_enabled) (bool): Enable receiver. (default: True)'
            - '- C(snmp_receiver_1_port) (int): Receiver port. (default: 162)'
            - '- C(snmp_receiver_1_community) (str): Community string. (default: "public")'
            - '- C(snmp_receiver_2_url) (str): Receiver 2 ULR. (default: "")'
            - '- C(snmp_receiver_2_enabled) (bool): Enable receiver. (default: False)'
            - '- C(snmp_receiver_2_port) (int): Receiver port. (default: 162)'
            - '- C(snmp_receiver_2_community) (str): Community string. (default: "")'
            - '- C(snmp_receiver_3_url) (str): Receiver 3 ULR. (default: "")'
            - '- C(snmp_receiver_3_enabled) (bool): Enable receiver. (default: False)'
            - '- C(snmp_receiver_3_port) (int): Receiver port. (default: 162)'
            - '- C(snmp_receiver_3_community) (str): Community string. (default: "")'
            - '- C(snmp_receiver_4_url) (str): Receiver 4 ULR. (default: "")'
            - '- C(snmp_receiver_4_enabled) (bool): Enable receiver. (default: False)'
            - '- C(snmp_receiver_4_port) (int): Receiver port. (default: 162)'
            - '- C(snmp_receiver_4_community) (str): Community string. (default: "")'
        type: dict
        default: {
            snmp_receiver_1_url: 'localhost',
            snmp_receiver_1_enabled: True,
            snmp_receiver_1_port: 162,
            snmp_receiver_1_community: 'public',
            snmp_receiver_2_url: '',
            snmp_receiver_2_enabled: False,
            snmp_receiver_2_port: 162,
            snmp_receiver_2_community: '',
            snmp_receiver_3_url: '',
            snmp_receiver_3_enabled: False,
            snmp_receiver_3_port: 162,
            snmp_receiver_3_community: '',
            snmp_receiver_4_url: '',
            snmp_receiver_4_enabled: False,
            snmp_receiver_4_port: 162,
            snmp_receiver_4_community: '',
        }
    timeout_settings:
        description:
            - The vCenter server connection timeout for normal and long operations.
            - 'Valid attributes are:'
            - '- C(normal_operations) (int) (default: 30)'
            - '- C(long_operations) (int) (default: 120)'
        type: dict
        default: {
            normal_operations: 30,
            long_operations: 120,
        }
    logging_options:
        description:
            - The level of detail that vCenter server usesfor log files.
        type: str
        choices: ['none', 'error', 'warning', 'info', 'verbose', 'trivia']
        default: 'info'
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Configure vCenter general settings
  vmware_vcenter_settings:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    database:
      max_connections: 50
      task_cleanup: true
      task_retention: 30
      event_cleanup: true
      event_retention: 30
    runtime_settings:
      unique_id: 1
      managed_address: "{{ ansible_default_ipv4.address }}"
      vcenter_server_name: "{{ inventory_hostname }}"
    user_directory:
      timeout: 60
      query_limit: true
      query_limit_size: 5000
      validation: true
      validation_period: 1440
    mail:
      server: mail.example.com
      sender: vcenter@{{ inventory_hostname }}
    snmp_receivers:
      snmp_receiver_1_url: localhost
      snmp_receiver_1_enabled: true
      snmp_receiver_1_port: 162
      snmp_receiver_1_community: public
    timeout_settings:
      normal_operations: 30
      long_operations: 120
    logging_options: info
    validate_certs: no
  delegate_to: localhost
'''

RETURN = r'''
results:
    description: metadata about vCenter settings
    returned: always
    type: dict
    sample: {
        "changed": false,
        "db_event_cleanup": true,
        "db_event_retention": 30,
        "db_max_connections": 50,
        "db_task_cleanup": true,
        "db_task_retention": 30,
        "directory_query_limit": true,
        "directory_query_limit_size": 5000,
        "directory_timeout": 60,
        "directory_validation": true,
        "directory_validation_period": 1440,
        "logging_options": "info",
        "mail_sender": "vcenter@vcenter01.example.com",
        "mail_server": "mail.example.com",
        "msg": "vCenter settings already configured properly",
        "runtime_managed_address": "192.168.1.10",
        "runtime_server_name": "vcenter01.example.com",
        "runtime_unique_id": 1,
        "timeout_long_operations": 120,
        "timeout_normal_operations": 30
    }
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec
from ansible.module_utils._text import to_native


class VmwareVcenterSettings(PyVmomi):
    """Manage settings for a vCenter server"""

    def __init__(self, module):
        super(VmwareVcenterSettings, self).__init__(module)

        if not self.is_vcenter():
            self.module.fail_json(msg="You have to connect to a vCenter server!")

    def ensure(self):
        """Manage settings for a vCenter server"""
        result = dict(changed=False, msg='')
        db_max_connections = self.params['database'].get('max_connections')
        db_task_cleanup = self.params['database'].get('task_cleanup')
        db_task_retention = self.params['database'].get('task_retention')
        db_event_cleanup = self.params['database'].get('event_cleanup')
        db_event_retention = self.params['database'].get('event_retention')
        runtime_unique_id = self.params['runtime_settings'].get('unique_id')
        runtime_managed_address = self.params['runtime_settings'].get('managed_address')
        runtime_server_name = self.params['runtime_settings'].get('vcenter_server_name')
        directory_timeout = self.params['user_directory'].get('timeout')
        directory_query_limit = self.params['user_directory'].get('query_limit')
        directory_query_limit_size = self.params['user_directory'].get('query_limit_size')
        directory_validation = self.params['user_directory'].get('validation')
        directory_validation_period = self.params['user_directory'].get('validation_period')
        mail_server = self.params['mail'].get('server')
        mail_sender = self.params['mail'].get('sender')
        snmp_receiver_1_url = self.params['snmp_receivers'].get('snmp_receiver_1_url')
        snmp_receiver_1_enabled = self.params['snmp_receivers'].get('snmp_receiver_1_enabled')
        snmp_receiver_1_port = self.params['snmp_receivers'].get('snmp_receiver_1_port')
        snmp_receiver_1_community = self.params['snmp_receivers'].get('snmp_receiver_1_community')
        snmp_receiver_2_url = self.params['snmp_receivers'].get('snmp_receiver_2_url')
        snmp_receiver_2_enabled = self.params['snmp_receivers'].get('snmp_receiver_2_enabled')
        snmp_receiver_2_port = self.params['snmp_receivers'].get('snmp_receiver_2_port')
        snmp_receiver_2_community = self.params['snmp_receivers'].get('snmp_receiver_2_community')
        snmp_receiver_3_url = self.params['snmp_receivers'].get('snmp_receiver_3_url')
        snmp_receiver_3_enabled = self.params['snmp_receivers'].get('snmp_receiver_3_enabled')
        snmp_receiver_3_port = self.params['snmp_receivers'].get('snmp_receiver_3_port')
        snmp_receiver_3_community = self.params['snmp_receivers'].get('snmp_receiver_3_community')
        snmp_receiver_4_url = self.params['snmp_receivers'].get('snmp_receiver_4_url')
        snmp_receiver_4_enabled = self.params['snmp_receivers'].get('snmp_receiver_4_enabled')
        snmp_receiver_4_port = self.params['snmp_receivers'].get('snmp_receiver_4_port')
        snmp_receiver_4_community = self.params['snmp_receivers'].get('snmp_receiver_4_community')
        timeout_normal_operations = self.params['timeout_settings'].get('normal_operations')
        timeout_long_operations = self.params['timeout_settings'].get('long_operations')
        logging_options = self.params.get('logging_options')
        changed = False
        changed_list = []

        # Check all general settings, except statistics
        result['db_max_connections'] = db_max_connections
        result['db_task_cleanup'] = db_task_cleanup
        result['db_task_retention'] = db_task_retention
        result['db_event_cleanup'] = db_event_cleanup
        result['db_event_retention'] = db_event_retention
        result['runtime_unique_id'] = runtime_unique_id
        result['runtime_managed_address'] = runtime_managed_address
        result['runtime_server_name'] = runtime_server_name
        result['directory_timeout'] = directory_timeout
        result['directory_query_limit'] = directory_query_limit
        result['directory_query_limit_size'] = directory_query_limit_size
        result['directory_validation'] = directory_validation
        result['directory_validation_period'] = directory_validation_period
        result['mail_server'] = mail_server
        result['mail_sender'] = mail_sender
        result['timeout_normal_operations'] = timeout_normal_operations
        result['timeout_long_operations'] = timeout_long_operations
        result['logging_options'] = logging_options
        change_option_list = []
        option_manager = self.content.setting
        for setting in option_manager.setting:
            # Database
            if setting.key == 'VirtualCenter.MaxDBConnection' and setting.value != db_max_connections:
                changed = True
                changed_list.append("DB max connections")
                result['db_max_connections_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='VirtualCenter.MaxDBConnection', value=db_max_connections)
                )
            if setting.key == 'task.maxAgeEnabled' and setting.value != db_task_cleanup:
                changed = True
                changed_list.append("DB task cleanup")
                result['db_task_cleanup_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='task.maxAgeEnabled', value=db_task_cleanup)
                )
            if setting.key == 'task.maxAge' and setting.value != db_task_retention:
                changed = True
                changed_list.append("DB task retention")
                result['db_task_retention_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='task.maxAge', value=db_task_retention)
                )
            if setting.key == 'event.maxAgeEnabled' and setting.value != db_event_cleanup:
                changed = True
                changed_list.append("DB event cleanup")
                result['db_event_cleanup_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='event.maxAgeEnabled', value=db_event_cleanup)
                )
            if setting.key == 'event.maxAge' and setting.value != db_event_retention:
                changed = True
                changed_list.append("DB event retention")
                result['db_event_retention_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='event.maxAge', value=db_event_retention)
                )
            # Runtime settings
            if setting.key == 'instance.id' and setting.value != runtime_unique_id:
                changed = True
                changed_list.append("Instance ID")
                result['runtime_unique_id_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='instance.id', value=runtime_unique_id)
                )
            if setting.key == 'VirtualCenter.ManagedIP' and setting.value != runtime_managed_address:
                changed = True
                changed_list.append("Managed IP")
                result['runtime_managed_address_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='VirtualCenter.ManagedIP', value=runtime_managed_address)
                )
            if setting.key == 'VirtualCenter.InstanceName' and setting.value != runtime_server_name:
                changed = True
                changed_list.append("Server name")
                result['runtime_server_name_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='VirtualCenter.InstanceName', value=runtime_server_name)
                )
            # User directory
            if setting.key == 'ads.timeout' and setting.value != directory_timeout:
                changed = True
                changed_list.append("Directory timeout")
                result['directory_timeout_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='ads.timeout', value=directory_timeout)
                )
            if setting.key == 'ads.maxFetchEnabled' and setting.value != directory_query_limit:
                changed = True
                changed_list.append("Query limit")
                result['directory_query_limit_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='ads.maxFetchEnabled', value=directory_query_limit)
                )
            if setting.key == 'ads.maxFetch' and setting.value != directory_query_limit_size:
                changed = True
                changed_list.append("Query limit size")
                result['directory_query_limit_size_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='ads.maxFetch', value=directory_query_limit_size)
                )
            if setting.key == 'ads.checkIntervalEnabled' and setting.value != directory_validation:
                changed = True
                changed_list.append("Validation")
                result['directory_validation_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='ads.checkIntervalEnabled', value=directory_validation)
                )
            if setting.key == 'ads.checkInterval' and setting.value != directory_validation_period:
                changed = True
                changed_list.append("Validation period")
                result['directory_validation_period_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='ads.checkInterval', value=directory_validation_period)
                )
            # Mail
            if setting.key == 'mail.smtp.server' and setting.value != mail_server:
                changed = True
                changed_list.append("Mail server")
                result['mail_server_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='mail.smtp.server', value=mail_server)
                )
            if setting.key == 'mail.sender' and setting.value != mail_sender:
                changed = True
                changed_list.append("Mail sender")
                result['mail_sender_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='mail.sender', value=mail_sender)
                )
            # SNMP receivers - SNMP receiver #1
            if setting.key == 'snmp.receiver.1.enabled' and setting.value != snmp_receiver_1_enabled:
                changed = True
                changed_list.append("SNMP-1-enabled")
                result['snmp_1_enabled_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='snmp.receiver.1.enabled', value=snmp_receiver_1_enabled)
                )
            if setting.key == 'snmp.receiver.1.name' and setting.value != snmp_receiver_1_url:
                changed = True
                changed_list.append("SNMP-1-name")
                result['snmp_1_url_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='snmp.receiver.1.name', value=snmp_receiver_1_url)
                )
            if setting.key == 'snmp.receiver.1.port' and setting.value != snmp_receiver_1_port:
                changed = True
                changed_list.append("SNMP-1-port")
                result['snmp_receiver_1_port_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='snmp.receiver.1.port', value=snmp_receiver_1_port)
                )
            if setting.key == 'snmp.receiver.1.community' and setting.value != snmp_receiver_1_community:
                changed = True
                changed_list.append("SNMP-1-community")
                result['snmp_1_community_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='snmp.receiver.1.community', value=snmp_receiver_1_community)
                )
            # SNMP receivers - SNMP receiver #2
            if setting.key == 'snmp.receiver.2.enabled' and setting.value != snmp_receiver_2_enabled:
                changed = True
                changed_list.append("SNMP-2-enabled")
                result['snmp_2_enabled_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='snmp.receiver.2.enabled', value=snmp_receiver_2_enabled)
                )
            if setting.key == 'snmp.receiver.2.name' and setting.value != snmp_receiver_2_url:
                changed = True
                changed_list.append("SNMP-2-name")
                result['snmp_2_url_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='snmp.receiver.2.name', value=snmp_receiver_2_url)
                )
            if setting.key == 'snmp.receiver.2.port' and setting.value != snmp_receiver_2_port:
                changed = True
                changed_list.append("SNMP-2-port")
                result['snmp_receiver_2_port_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='snmp.receiver.2.port', value=snmp_receiver_2_port)
                )
            if setting.key == 'snmp.receiver.2.community' and setting.value != snmp_receiver_2_community:
                changed = True
                changed_list.append("SNMP-2-community")
                result['snmp_2_community_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='snmp.receiver.2.community', value=snmp_receiver_2_community)
                )
            # SNMP receivers - SNMP receiver #3
            if setting.key == 'snmp.receiver.3.enabled' and setting.value != snmp_receiver_3_enabled:
                changed = True
                changed_list.append("SNMP-3-enabled")
                result['snmp_3_enabled_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='snmp.receiver.3.enabled', value=snmp_receiver_3_enabled)
                )
            if setting.key == 'snmp.receiver.3.name' and setting.value != snmp_receiver_3_url:
                changed = True
                changed_list.append("SNMP-3-name")
                result['snmp_3_url_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='snmp.receiver.3.name', value=snmp_receiver_3_url)
                )
            if setting.key == 'snmp.receiver.3.port' and setting.value != snmp_receiver_3_port:
                changed = True
                changed_list.append("SNMP-3-port")
                result['snmp_receiver_3_port_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='snmp.receiver.3.port', value=snmp_receiver_3_port)
                )
            if setting.key == 'snmp.receiver.3.community' and setting.value != snmp_receiver_3_community:
                changed = True
                changed_list.append("SNMP-3-community")
                result['snmp_3_community_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='snmp.receiver.3.community', value=snmp_receiver_3_community)
                )
            # SNMP receivers - SNMP receiver #4
            if setting.key == 'snmp.receiver.4.enabled' and setting.value != snmp_receiver_4_enabled:
                changed = True
                changed_list.append("SNMP-4-enabled")
                result['snmp_4_enabled_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='snmp.receiver.4.enabled', value=snmp_receiver_4_enabled)
                )
            if setting.key == 'snmp.receiver.4.name' and setting.value != snmp_receiver_4_url:
                changed = True
                changed_list.append("SNMP-4-name")
                result['snmp_4_url_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='snmp.receiver.4.name', value=snmp_receiver_4_url)
                )
            if setting.key == 'snmp.receiver.4.port' and setting.value != snmp_receiver_4_port:
                changed = True
                changed_list.append("SNMP-4-port")
                result['snmp_receiver_4_port_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='snmp.receiver.4.port', value=snmp_receiver_4_port)
                )
            if setting.key == 'snmp.receiver.4.community' and setting.value != snmp_receiver_4_community:
                changed = True
                changed_list.append("SNMP-4-community")
                result['snmp_4_community_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='snmp.receiver.4.community', value=snmp_receiver_4_community)
                )
            # Timeout settings
            if setting.key == 'client.timeout.normal' and setting.value != timeout_normal_operations:
                changed = True
                changed_list.append("Timeout normal")
                result['timeout_normal_operations_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='client.timeout.normal', value=timeout_normal_operations)
                )
            if setting.key == 'client.timeout.long' and setting.value != timeout_long_operations:
                changed = True
                changed_list.append("Timout long")
                result['timeout_long_operations_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='client.timeout.long', value=timeout_long_operations)
                )
            # Logging settings
            if setting.key == 'log.level' and setting.value != logging_options:
                changed = True
                changed_list.append("Logging")
                result['logging_options_previous'] = setting.value
                change_option_list.append(
                    vim.option.OptionValue(key='log.level', value=logging_options)
                )

        if changed:
            if self.module.check_mode:
                changed_suffix = ' would be changed'
            else:
                changed_suffix = ' changed'
            if len(changed_list) > 2:
                message = ', '.join(changed_list[:-1]) + ', and ' + str(changed_list[-1])
            elif len(changed_list) == 2:
                message = ' and '.join(changed_list)
            elif len(changed_list) == 1:
                message = changed_list[0]
            message += changed_suffix
            if not self.module.check_mode:
                try:
                    option_manager.UpdateOptions(changedValue=change_option_list)
                except (vmodl.fault.SystemError, vmodl.fault.InvalidArgument) as invalid_argument:
                    self.module.fail_json(
                        msg="Failed to update option(s) as one or more OptionValue contains an invalid value: %s" %
                        to_native(invalid_argument.msg)
                    )
                except vim.fault.InvalidName as invalid_name:
                    self.module.fail_json(
                        msg="Failed to update option(s) as one or more OptionValue objects refers to a "
                        "non-existent option : %s" % to_native(invalid_name.msg)
                    )
        else:
            message = "vCenter settings already configured properly"
        result['changed'] = changed
        result['msg'] = message

        self.module.exit_json(**result)


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        database=dict(
            type='dict',
            options=dict(
                max_connections=dict(type='int'),
                task_cleanup=dict(type='bool'),
                task_retention=dict(type='int'),
                event_cleanup=dict(type='bool'),
                event_retention=dict(type='int'),
            ),
            default=dict(
                max_connections=50,
                task_cleanup=True,
                task_retention=30,
                event_cleanup=True,
                event_retention=30,
            ),
        ),
        runtime_settings=dict(
            type='dict',
            options=dict(
                unique_id=dict(type='int'),
                managed_address=dict(type='str'),
                vcenter_server_name=dict(type='str'),
            ),
        ),
        user_directory=dict(
            type='dict',
            options=dict(
                timeout=dict(type='int'),
                query_limit=dict(type='bool'),
                query_limit_size=dict(type='int'),
                validation=dict(type='bool'),
                validation_period=dict(type='int'),
            ),
            default=dict(
                timeout=60,
                query_limit=True,
                query_limit_size=5000,
                validation=True,
                validation_period=1440,
            ),
        ),
        mail=dict(
            type='dict',
            options=dict(
                server=dict(type='str'),
                sender=dict(type='str'),
            ),
        ),
        snmp_receivers=dict(
            type='dict',
            options=dict(
                snmp_receiver_1_url=dict(type='str', default='localhost'),
                snmp_receiver_1_enabled=dict(type='bool', default=True),
                snmp_receiver_1_port=dict(type='int', default=162),
                snmp_receiver_1_community=dict(type='str', default='public'),
                snmp_receiver_2_url=dict(type='str', default=''),
                snmp_receiver_2_enabled=dict(type='bool', default=False),
                snmp_receiver_2_port=dict(type='int', default=162),
                snmp_receiver_2_community=dict(type='str', default=''),
                snmp_receiver_3_url=dict(type='str', default=''),
                snmp_receiver_3_enabled=dict(type='bool', default=False),
                snmp_receiver_3_port=dict(type='int', default=162),
                snmp_receiver_3_community=dict(type='str', default=''),
                snmp_receiver_4_url=dict(type='str', default=''),
                snmp_receiver_4_enabled=dict(type='bool', default=False),
                snmp_receiver_4_port=dict(type='int', default=162),
                snmp_receiver_4_community=dict(type='str', default=''),
            ),
            default=dict(
                snmp_receiver_1_url='localhost',
                snmp_receiver_1_enabled=True,
                snmp_receiver_1_port=162,
                snmp_receiver_1_community='public',
                snmp_receiver_2_url='',
                snmp_receiver_2_enabled=False,
                snmp_receiver_2_port=162,
                snmp_receiver_2_community='',
                snmp_receiver_3_url='',
                snmp_receiver_3_enabled=False,
                snmp_receiver_3_port=162,
                snmp_receiver_3_community='',
                snmp_receiver_4_url='',
                snmp_receiver_4_enabled=False,
                snmp_receiver_4_port=162,
                snmp_receiver_4_community='',
            ),
        ),
        timeout_settings=dict(
            type='dict',
            options=dict(
                normal_operations=dict(type='int'),
                long_operations=dict(type='int'),
            ),
            default=dict(
                normal_operations=30,
                long_operations=120,
            ),
        ),
        logging_options=dict(default='info', choices=['none', 'error', 'warning', 'info', 'verbose', 'trivia']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    host_snmp = VmwareVcenterSettings(module)
    host_snmp.ensure()


if __name__ == '__main__':
    main()
