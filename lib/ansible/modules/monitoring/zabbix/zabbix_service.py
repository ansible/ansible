#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, OVH SAS
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: zabbix_service
short_description: Create/update/delete Zabbix service
description:
    - Create/update/delete Zabbix service.
version_added: "2.10"
author:
    - "Emmanuel Riviere (@emriver)"
requirements:
    - "python >= 2.7"
    - "zabbix-api >= 0.5.4"
options:
    name:
        description:
            - Name of Zabbix service
        required: true
        type: str
    parent:
        description:
            - Name of Zabbix service parent
        required: false
        type: str
    sla:
        description:
            - Sla value (i.e 99.99), goodsla in Zabbix API
        required: false
        type: float
    calculate_sla:
        description:
            - If yes, calculate the SLA value for this service, showsla in Zabbix API
        required: false
        type: bool
    algorithm:
        description:
            - Algorithm used to calculate the sla
            - C(no), sla is not calculated
            - C(one_child), problem if at least one child has a problem
            - C(all_children), problem if all children have problems
        required: false
        type: str
        choices: ["no", "one_child", "all_children"]
        default: one_child
    trigger_name:
        description:
            - Name of trigger linked to the service
        required: false
        type: str
    trigger_host:
        description:
            - Name of host linked to the service
        required: false
        type: str
    state:
        description:
            - 'State: present - create/update service; absent - delete service'
        required: false
        choices: [present, absent]
        default: "present"
        type: str

extends_documentation_fragment:
    - zabbix
'''

EXAMPLES = '''
---
# Creates a new Zabbix service
- name: Manage services
  local_action:
        module: zabbix_service
        server_url: "https://192.168.1.1"
        login_user: username
        login_password: password
        name: apache2 service
        sla: 99.99
        calculate_sla: yes
        algorithm: one_child
        trigger_name: apache2 service status
        trigger_host: webserver01
        state: present
'''

RETURN = '''
---
'''

import atexit
import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib


try:
    from zabbix_api import ZabbixAPI, ZabbixAPIException
    HAS_ZABBIX_API = True
except ImportError:
    ZBX_IMP_ERR = traceback.format_exc()
    HAS_ZABBIX_API = False


class Service(object):
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx

    def get_service_ids(self, service_name):
        service_ids = []
        services = self._zapi.service.get({'filter': {'name': service_name}})
        for service in services:
            service_ids.append(service['serviceid'])
        return service_ids

    def delete_service(self, service_ids):
        if self._module.check_mode:
            self._module.exit_json(changed=True)
        self._zapi.service.delete(service_ids)

    def dump_services(self, service_ids):
        services = self._zapi.service.get({'output': 'extend', 'filter': {'serviceid': service_ids}, 'selectParent': '1'})
        return services

    def generate_service_config(self, name, parent, sla, calculate_sla, trigger_name, trigger_host, algorithm):
        algorithms = {'no': '0', 'one_child': '1', 'all_children': '2'}
        algorithm = algorithms[algorithm]

        if calculate_sla:
            calculate_sla = 1
        else:
            calculate_sla = 0

        # Zabbix api return when no trigger
        trigger_id = 0
        if trigger_host and trigger_name:
            # Retrieving the host to get the trigger
            hosts = self._zapi.host.get({'filter': {'host': trigger_host}})
            if not hosts:
                self._module.fail_json(msg="Target host %s not found" % trigger_host)
            host_id = hosts[0]['hostid']

            triggers = self._zapi.trigger.get({'filter': {'description': trigger_name}, 'hostids': [host_id]})
            if not triggers:
                self._module.fail_json(msg="Trigger %s not found on host %s" % (trigger_name, trigger_host))
            trigger_id = triggers[0]['triggerid']

        request = {
            'name': name,
            'algorithm': algorithm,
            'showsla': calculate_sla,
            'sortorder': 1,
            'goodsla': format(sla, '.4f'),  # Sla has 4 decimals
            'triggerid': trigger_id
        }

        if parent:
            parent_ids = self.get_service_ids(parent)
            if not parent_ids:
                self._module.fail_json(msg="Parent %s not found" % parent)
            request['parentid'] = parent_ids[0]
        return request

    def create_service(self, name, parent, sla, calculate_sla, trigger_name, trigger_host, algorithm):
        if self._module.check_mode:
            self._module.exit_json(changed=True)
        self._zapi.service.create(self.generate_service_config(name, parent, sla, calculate_sla, trigger_name, trigger_host, algorithm))

    def update_service(self, service_id, name, parent, sla, calculate_sla, trigger_name, trigger_host, algorithm):
        generated_config = self.generate_service_config(name, parent, sla, calculate_sla, trigger_name, trigger_host, algorithm)
        live_config = self.dump_services(service_id)[0]

        item_to_check = ['name', 'showsla', 'algorithm', 'triggerid', 'sortorder', 'goodsla']
        change = False
        for item in item_to_check:
            if str(generated_config[item]) != str(live_config[item]):
                change = True

        # In Zabbix 4.0
        # No parent returns : "parent": []
        # A parent returns : "parent": { "serviceid": 12 }
        if 'parentid' in generated_config:
            if 'serviceid' in live_config['parent']:
                if generated_config['parentid'] != live_config['parent']['serviceid']:
                    change = True
            else:
                change = True
        elif 'serviceid' in live_config['parent']:
            change = True

        if not change:
            self._module.exit_json(changed=False, msg="Service %s up to date" % name)

        if self._module.check_mode:
            self._module.exit_json(changed=True)
        generated_config['serviceid'] = service_id
        self._zapi.service.update(generated_config)
        self._module.exit_json(changed=True, msg="Service %s updated" % name)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False, default=None, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
            name=dict(type='str', required=True),
            parent=dict(type='str', required=False),
            sla=dict(type='float', required=False),
            calculate_sla=dict(type='bool', required=False, default=False),
            algorithm=dict(default='one_child', required=False, choices=['no', 'one_child', 'all_children']),
            trigger_name=dict(type='str', required=False),
            trigger_host=dict(type='str', required=False),
            state=dict(default="present", choices=['present', 'absent']),
            timeout=dict(type='int', default=10)
        ),
        supports_check_mode=True
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg=missing_required_lib('zabbix-api', url='https://pypi.org/project/zabbix-api/'), exception=ZBX_IMP_ERR)

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    validate_certs = module.params['validate_certs']
    name = module.params['name']
    parent = module.params['parent']
    sla = module.params['sla']
    calculate_sla = module.params['calculate_sla']
    algorithm = module.params['algorithm']
    trigger_name = module.params['trigger_name']
    trigger_host = module.params['trigger_host']
    state = module.params['state']
    timeout = module.params['timeout']

    zbx = None

    # Login to zabbix
    try:
        zbx = ZabbixAPI(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password, validate_certs=validate_certs)
        zbx.login(login_user, login_password)
        atexit.register(zbx.logout)
    except ZabbixAPIException as error:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % error)

    # Load service module
    service = Service(module, zbx)
    service_ids = service.get_service_ids(name)
    if service_ids:
        service_json = service.dump_services(service_ids)

    # Delete service
    if state == "absent":
        if not service_ids:
            module.exit_json(changed=False, msg="Service not found, no change: %s" % name)
        service.delete_service(service_ids)
        module.exit_json(changed=True, result="Successfully deleted service(s) %s" % name)

    elif state == "present":
        if (trigger_name and not trigger_host) or (trigger_host and not trigger_name):
            module.fail_json(msg="Specify either both trigger_host and trigger_name or none to create or update a service")
        # Does not exists going to create it
        if not service_ids:
            service.create_service(name, parent, sla, calculate_sla, trigger_name, trigger_host, algorithm)
            module.exit_json(changed=True, msg="Service %s created" % name)
        # Else we update it if needed
        else:
            service.update_service(service_ids[0], name, parent, sla, calculate_sla, trigger_name, trigger_host, algorithm)


if __name__ == '__main__':
    main()
