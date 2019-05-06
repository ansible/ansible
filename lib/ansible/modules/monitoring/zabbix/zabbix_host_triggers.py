#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) stephane.travassac@fr.clara.net
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

RETURN = '''
---
output:
    description: Host Zabbix Triggers in Json format
    returned: On success
    type: complex
    contains:
            triggers_ok:
                - comments: Raise an alert whenever there is no data received from the agent during
                    the given interval
                  description: 'Status {HOSTNAME}: server is unreachable'
                  error: ''
                  expression: "{13665}=1"
                  flags: '0'
                  lastchange: '1556112352'
                  priority: '4'
                  state: '0'
                  status: '0'
                  templateid: '13619'
                  triggerid: '14038'
                  type: '0'
                  url: ''
                  value: '0'
            triggers_problem:
                - comments: ''
                  description: 'Process: NTPd is down'
                  error: ''
                  expression: "{13667}=0"
                  flags: '0'
                  last_event:
                    acknowledged: '0'
                    acknowledges:
                    - alias: Admin
                      clock: '1556182269'
                      message: waiting customer action
                    clock: '1556182854'
                    eventid: '630'
                    value: '1'
                  lastchange: '1556182854'
                  priority: '4'
                  state: '0'
                  status: '0'
                  templateid: '13615'
                  triggerid: '14040'
                  type: '0'
                  url: ''
                  value: '1'
'''

DOCUMENTATION = '''
---
module: zabbix_host_triggers
short_description: Get all triggers about a Zabbix host
description:
   - This module allows you to see if a Zabbix host have no active alert to make actions on it.
     For this case use module Ansible 'fail' to exclude host in trouble.
   - Length of "triggers_ok" allow if template's triggers exist for Zabbix Host
version_added: "2.9"
author:
    - "Stéphane Travassac (@stravassac)"
requirements:
    - "python >= 2.7"
    - "zabbix-api"
    - "zabbix-api >= 0.5.3"
options:
    host_identifier:
        description:
            - Identifier of Zabbix Host
        default: hostname
        required: true
    host_id_type:
        description:
            - Type of host_identifier
        choices:
            - hostname
            - visible_name
            - hostid
        required: false
        default: hostname
    trigger_severity:
        description:
            - Zabbix severity for search filter
        default: average
        required: false
        choices:
            - not_classified
            - information
            - warning
            - average
            - high
            - disaster
    timeout:
        description:
            - timeout before fail
        default: 10
        required: false
        type: int
    validate_certs:
        description:
                - SSL validate certificate
        default: true
        required: true
        type: bool
extends_documentation_fragment:
    - zabbix
'''

EXAMPLES = '''
- name: exclude machine if alert active on it
  zabbix_host_triggers_problem:
      server_url: "{{ zabbix_url }}"
      login_user: "{{ lookup('env','ZABBIX_USER') }}"
      login_password: "{{ lookup('env','ZABBIX_PASSWORD') }}"
      host_identifier: "{{inventory_hostname}}"
      host_id_type: "hostname"
      timeout: 120
  register: zbx_host
  delegate_to: localhost
- fail:
    msg: "machine alert in zabbix"
  when: zbx_host['triggers_problem']|length > 0
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from zabbix_api import ZabbixAPI, ZabbixAPISubClass
    HAS_ZABBIX_API = True
except ImportError:
    HAS_ZABBIX_API = False


class Host(object):
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx

    def get_host(self, host_identifier, host_inventory, search_key):
        """ Get host by hostname|visible_name|hostid """
        host = self._zapi.host.get(
            {'output': 'extend', 'selectParentTemplates': ['name'], 'filter': {search_key: host_identifier},
             'selectInventory': host_inventory})
        if len(host) < 1:
            self._module.fail_json(msg="Host not found: %s" % host_identifier)
        else:
            return host[0]

    def get_triggers_by_host_id_in_problem_state(self, host_id, trigger_severity):
        """ Get triggers in problem state from a hostid"""
        # https://www.zabbix.com/documentation/3.4/manual/api/reference/trigger/get
        output = ['triggerids', 'description', 'priority']
        output = 'extend'
        triggers_list = self._zapi.trigger.get({'output': output, 'hostids': host_id,
                                                'min_severity': trigger_severity})
        return triggers_list

    def get_last_event_by_trigger_id(self, triggers_id):
        """ Get the last event from triggerid"""
        output = ['eventid', 'clock', 'acknowledged', 'value']
        select_acknowledges = ['clock', 'alias', 'message']
        event = self._zapi.event.get({'output': output, 'objectids': triggers_id,
                                      'select_acknowledges': select_acknowledges, "limit": 1, "sortfield": "clock",
                                      "sortorder": "DESC"})
        return event[0]


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False, default=None, no_log=True),
            host_identifier=dict(type='str', default='hostname', required=False),
            host_id_type=dict(
                default='hostname',
                type='str',
                choices=['hostname', 'visible_name', 'hostid']),
            trigger_severity=dict(
                type='str',
                required=False,
                default='average',
                choices=['not_classified', 'information', 'warning', 'average', 'high', 'disaster']),
            validate_certs=dict(type='bool', required=False, default=True),
            timeout=dict(type='int', default=10),

        ),
        supports_check_mode=True
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg="Missing required zabbix-api module (check docs or install with: pip install zabbix-api)")

    trigger_severity_map = {'not_classified': 0, 'information': 1, 'warning': 2, 'average': 3, 'high': 4, 'disaster': 5}
    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    validate_certs = module.params['validate_certs']
    host_id = module.params['host_identifier']
    host_id_type = module.params['host_id_type']
    trigger_severity = trigger_severity_map[module.params['trigger_severity']]
    timeout = module.params['timeout']

    host_inventory = 'hostid'
    zbx = None
    # login to zabbix
    try:
        zbx = ZabbixAPI(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password,
                        validate_certs=validate_certs)
        zbx.login(login_user, login_password)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    host = Host(module, zbx)

    if host_id_type == 'hostname':
        zabbix_host = host.get_host(host_id, host_inventory, 'host')
        host_id = zabbix_host['hostid']

    elif host_id_type == 'visible_name':
        zabbix_host = host.get_host(host_id, host_inventory, 'name')
        host_id = zabbix_host['hostid']

    elif host_id_type == 'hostid':
        ''' check hostid exist'''
        zabbix_host = host.get_host(host_id, host_inventory, 'hostid')

    else:
        module.exit_json(ok=False, host=[], result="No Host present")

    triggers = host.get_triggers_by_host_id_in_problem_state(host_id, trigger_severity)

    triggers_ok = []
    triggers_problem = []
    for trigger in triggers:
        # tGet last event for trigger with problem value = 1
        # https://www.zabbix.com/documentation/3.4/manual/api/reference/trigger/object
        if int(trigger['value']) == 1:
            event = host.get_last_event_by_trigger_id(trigger['triggerid'])
            trigger['last_event'] = event
            triggers_problem.append(trigger)
        else:
            triggers_ok.append(trigger)

    module.exit_json(ok=True, triggers_ok=triggers_ok, triggers_problem=triggers_problem)


if __name__ == '__main__':
    main()
