#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013-2014, Epic Games, Inc.
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.
#

DOCUMENTATION = '''
---
module: zabbix_host
short_description: Zabbix host creates/updates/deletes
description:
   - This module allows you to create, modify and delete Zabbix host entries and associated group and template data.
version_added: "2.0"
author:
    - "(@cove)"
    - "Tony Minfei Ding"
    - "Harrison Gu (@harrisongu)"
requirements:
    - "python >= 2.6"
    - zabbix-api
options:
    server_url:
        description:
            - Url of Zabbix server, with protocol (http or https).
        required: true
        aliases: [ "url" ]
    login_user:
        description:
            - Zabbix user name, used to authenticate against the server.
        required: true
    login_password:
        description:
            - Zabbix user password.
        required: true
    http_login_user:
        description:
            - Basic Auth login
        required: false
        default: None
        version_added: "2.1"
    http_login_password:
        description:
            - Basic Auth password
        required: false
        default: None
        version_added: "2.1"
    host_name:
        description:
            - Name of the host in Zabbix.
            - host_name is the unique identifier used and cannot be updated using this module.
        required: true
    visible_name:
        description:
            - Visible name of the host in Zabbix.
        required: false
        version_added: '2.3'
    host_groups:
        description:
            - List of host groups the host is part of.
        required: false
    link_templates:
        description:
            - List of templates linked to the host.
        required: false
        default: None
    inventory_mode:
        description:
            - Configure the inventory mode.
        choices: ['automatic', 'manual', 'disabled']
        required: false
        default: None
        version_added: '2.1'
    status:
        description:
            - Monitoring status of the host.
        required: false
        choices: ['enabled', 'disabled']
        default: "enabled"
    state:
        description:
            - State of the host.
            - On C(present), it will create if host does not exist or update the host if the associated data is different.
            - On C(absent) will remove a host if it exists.
        required: false
        choices: ['present', 'absent']
        default: "present"
    timeout:
        description:
            - The timeout of API request (seconds).
        default: 10
    proxy:
        description:
            - The name of the Zabbix Proxy to be used
        default: None
    interfaces:
        description:
            - List of interfaces to be created for the host (see example below).
            - 'Available values are: dns, ip, main, port, type and useip.'
            - Please review the interface documentation for more information on the supported properties
            - 'https://www.zabbix.com/documentation/2.0/manual/appendix/api/hostinterface/definitions#host_interface'
        required: false
        default: []
    force:
        description:
            - Overwrite the host configuration, even if already present
        required: false
        default: "yes"
        choices: [ "yes", "no" ]
        version_added: "2.0"
'''

EXAMPLES = '''
- name: Create a new host or update an existing host's info
  local_action:
    module: zabbix_host
    server_url: http://monitor.example.com
    login_user: username
    login_password: password
    host_name: ExampleHost
    visible_name: ExampleName
    host_groups:
      - Example group1
      - Example group2
    link_templates:
      - Example template1
      - Example template2
    status: enabled
    state: present
    inventory_mode: automatic
    interfaces:
      - type: 1
        main: 1
        useip: 1
        ip: 10.xx.xx.xx
        dns: ""
        port: 10050
      - type: 4
        main: 1
        useip: 1
        ip: 10.xx.xx.xx
        dns: ""
        port: 12345
    proxy: a.zabbix.proxy
'''

import logging
import copy

try:
    from zabbix_api import ZabbixAPI, ZabbixAPISubClass

    HAS_ZABBIX_API = True
except ImportError:
    HAS_ZABBIX_API = False


# Extend the ZabbixAPI
# Since the zabbix-api python module too old (version 1.0, no higher version so far),
# it does not support the 'hostinterface' api calls,
# so we have to inherit the ZabbixAPI class to add 'hostinterface' support.
class ZabbixAPIExtends(ZabbixAPI):
    hostinterface = None

    def __init__(self, server, timeout, user, passwd, **kwargs):
        ZabbixAPI.__init__(self, server, timeout=timeout, user=user, passwd=passwd)
        self.hostinterface = ZabbixAPISubClass(self, dict({"prefix": "hostinterface"}, **kwargs))


class Host(object):
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx

    # exist host
    def is_host_exist(self, host_name):
        result = self._zapi.host.get({'filter': {'host': host_name}})
        return result

    # check if host group exists
    def check_host_group_exist(self, group_names):
        for group_name in group_names:
            result = self._zapi.hostgroup.get({'filter': {'name': group_name}})
            if not result:
                self._module.fail_json(msg="Hostgroup not found: %s" % group_name)
        return True

    def get_template_ids(self, template_list):
        template_ids = []
        if template_list is None or len(template_list) == 0:
            return template_ids
        for template in template_list:
            template_list = self._zapi.template.get({'output': 'extend', 'filter': {'host': template}})
            if len(template_list) < 1:
                self._module.fail_json(msg="Template not found: %s" % template)
            else:
                template_id = template_list[0]['templateid']
                template_ids.append(template_id)
        return template_ids

    def add_host(self, host_name, group_ids, status, interfaces, proxy_id, visible_name):
        try:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            parameters = {'host': host_name, 'interfaces': interfaces, 'groups': group_ids, 'status': status}
            if proxy_id:
                parameters['proxy_hostid'] = proxy_id
            if visible_name:
                parameters['name'] = visible_name 
            host_list = self._zapi.host.create(parameters)
            if len(host_list) >= 1:
                return host_list['hostids'][0]
        except Exception as e:
            self._module.fail_json(msg="Failed to create host %s: %s" % (host_name, e))

    def update_host(self, host_name, group_ids, status, host_id, interfaces, exist_interface_list, proxy_id, visible_name):
        try:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            parameters = {'hostid': host_id, 'groups': group_ids, 'status': status}
            if proxy_id:
                parameters['proxy_hostid'] = proxy_id
            if visible_name:
                parameters['name'] = visible_name 
            self._zapi.host.update(parameters)
            interface_list_copy = exist_interface_list
            if interfaces:
                for interface in interfaces:
                    flag = False
                    interface_str = interface
                    for exist_interface in exist_interface_list:
                        interface_type = interface['type']
                        exist_interface_type = int(exist_interface['type'])
                        if interface_type == exist_interface_type:
                            # update
                            interface_str['interfaceid'] = exist_interface['interfaceid']
                            self._zapi.hostinterface.update(interface_str)
                            flag = True
                            interface_list_copy.remove(exist_interface)
                            break
                    if not flag:
                        # add
                        interface_str['hostid'] = host_id
                        self._zapi.hostinterface.create(interface_str)
                        # remove
                remove_interface_ids = []
                for remove_interface in interface_list_copy:
                    interface_id = remove_interface['interfaceid']
                    remove_interface_ids.append(interface_id)
                if len(remove_interface_ids) > 0:
                    self._zapi.hostinterface.delete(remove_interface_ids)
        except Exception as e:
            self._module.fail_json(msg="Failed to update host %s: %s" % (host_name, e))

    def delete_host(self, host_id, host_name):
        try:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            self._zapi.host.delete([host_id])
        except Exception as e:
            self._module.fail_json(msg="Failed to delete host %s: %s" % (host_name, e))

    # get host by host name
    def get_host_by_host_name(self, host_name):
        host_list = self._zapi.host.get({'output': 'extend', 'filter': {'host': [host_name]}})
        if len(host_list) < 1:
            self._module.fail_json(msg="Host not found: %s" % host_name)
        else:
            return host_list[0]

    # get proxyid by proxy name
    def get_proxyid_by_proxy_name(self, proxy_name):
        proxy_list = self._zapi.proxy.get({'output': 'extend', 'filter': {'host': [proxy_name]}})
        if len(proxy_list) < 1:
            self._module.fail_json(msg="Proxy not found: %s" % proxy_name)
        else:
            return proxy_list[0]['proxyid']

    # get group ids by group names
    def get_group_ids_by_group_names(self, group_names):
        group_ids = []
        if self.check_host_group_exist(group_names):
            group_list = self._zapi.hostgroup.get({'output': 'extend', 'filter': {'name': group_names}})
            for group in group_list:
                group_id = group['groupid']
                group_ids.append({'groupid': group_id})
        return group_ids

    # get host templates by host id
    def get_host_templates_by_host_id(self, host_id):
        template_ids = []
        template_list = self._zapi.template.get({'output': 'extend', 'hostids': host_id})
        for template in template_list:
            template_ids.append(template['templateid'])
        return template_ids

    # get host groups by host id
    def get_host_groups_by_host_id(self, host_id):
        exist_host_groups = []
        host_groups_list = self._zapi.hostgroup.get({'output': 'extend', 'hostids': host_id})

        if len(host_groups_list) >= 1:
            for host_groups_name in host_groups_list:
                exist_host_groups.append(host_groups_name['name'])
        return exist_host_groups

    # check the exist_interfaces whether it equals the interfaces or not
    def check_interface_properties(self, exist_interface_list, interfaces):
        interfaces_port_list = []

        if interfaces is not None:
            if len(interfaces) >= 1:
                for interface in interfaces:
                    interfaces_port_list.append(int(interface['port']))

        exist_interface_ports = []
        if len(exist_interface_list) >= 1:
            for exist_interface in exist_interface_list:
                exist_interface_ports.append(int(exist_interface['port']))

        if set(interfaces_port_list) != set(exist_interface_ports):
            return True

        for exist_interface in exist_interface_list:
            exit_interface_port = int(exist_interface['port'])
            for interface in interfaces:
                interface_port = int(interface['port'])
                if interface_port == exit_interface_port:
                    for key in interface.keys():
                        if str(exist_interface[key]) != str(interface[key]):
                            return True

        return False

    # get the status of host by host
    def get_host_status_by_host(self, host):
        return host['status']

    # check all the properties before link or clear template
    def check_all_properties(self, host_id, host_groups, status, interfaces, template_ids,
                             exist_interfaces, host, proxy_id, visible_name):
        # get the existing host's groups
        exist_host_groups = self.get_host_groups_by_host_id(host_id)
        if set(host_groups) != set(exist_host_groups):
            return True

        # get the existing status
        exist_status = self.get_host_status_by_host(host)
        if int(status) != int(exist_status):
            return True

        # check the exist_interfaces whether it equals the interfaces or not
        if self.check_interface_properties(exist_interfaces, interfaces):
            return True

        # get the existing templates
        exist_template_ids = self.get_host_templates_by_host_id(host_id)
        if set(list(template_ids)) != set(exist_template_ids):
            return True

        if host['proxy_hostid'] != proxy_id:
            return True
        
        if host['name'] != visible_name:
            return True
        
        return False

    # link or clear template of the host
    def link_or_clear_template(self, host_id, template_id_list):
        # get host's exist template ids
        exist_template_id_list = self.get_host_templates_by_host_id(host_id)

        exist_template_ids = set(exist_template_id_list)
        template_ids = set(template_id_list)
        template_id_list = list(template_ids)

        # get unlink and clear templates
        templates_clear = exist_template_ids.difference(template_ids)
        templates_clear_list = list(templates_clear)
        request_str = {'hostid': host_id, 'templates': template_id_list, 'templates_clear': templates_clear_list}
        try:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            self._zapi.host.update(request_str)
        except Exception as e:
            self._module.fail_json(msg="Failed to link template to host: %s" % e)

    # Update the host inventory_mode
    def update_inventory_mode(self, host_id, inventory_mode):

        # nothing was set, do nothing
        if not inventory_mode:
            return

        if inventory_mode == "automatic":
            inventory_mode = int(1)
        elif inventory_mode == "manual":
            inventory_mode = int(0)
        elif inventory_mode == "disabled":
            inventory_mode = int(-1)

        # watch for - https://support.zabbix.com/browse/ZBX-6033
        request_str = {'hostid': host_id, 'inventory_mode': inventory_mode}
        try:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            self._zapi.host.update(request_str)
        except Exception as e:
            self._module.fail_json(msg="Failed to set inventory_mode to host: %s" % e)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            host_name=dict(type='str', required=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False, default=None, no_log=True),
            host_groups=dict(type='list', required=False),
            link_templates=dict(type='list', required=False),
            status=dict(default="enabled", choices=['enabled', 'disabled']),
            state=dict(default="present", choices=['present', 'absent']),
            inventory_mode=dict(required=False, choices=['automatic', 'manual', 'disabled']),
            timeout=dict(type='int', default=10),
            interfaces=dict(type='list', required=False),
            force=dict(type='bool', default=True),
            proxy=dict(type='str', required=False),
            visible_name=dict(type='str', required=False)

        ),
        supports_check_mode=True
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg="Missing requried zabbix-api module (check docs or install with: pip install zabbix-api)")

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    host_name = module.params['host_name']
    visible_name = module.params['visible_name']
    host_groups = module.params['host_groups']
    link_templates = module.params['link_templates']
    inventory_mode = module.params['inventory_mode']
    status = module.params['status']
    state = module.params['state']
    timeout = module.params['timeout']
    interfaces = module.params['interfaces']
    force = module.params['force']
    proxy = module.params['proxy']

    # convert enabled to 0; disabled to 1
    status = 1 if status == "disabled" else 0

    zbx = None
    # login to zabbix
    try:
        zbx = ZabbixAPIExtends(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password)
        zbx.login(login_user, login_password)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    host = Host(module, zbx)

    template_ids = []
    if link_templates:
        template_ids = host.get_template_ids(link_templates)

    group_ids = []

    if host_groups:
        group_ids = host.get_group_ids_by_group_names(host_groups)

    ip = ""
    if interfaces:
        for interface in interfaces:
            if interface['type'] == 1:
                ip = interface['ip']

    # check if host exist
    is_host_exist = host.is_host_exist(host_name)

    if is_host_exist:
        # Use proxy specified, or set to None when updating host
        if proxy:
            proxy_id = host.get_proxyid_by_proxy_name(proxy)
        else:
            proxy_id = None

        # get host id by host name
        zabbix_host_obj = host.get_host_by_host_name(host_name)
        host_id = zabbix_host_obj['hostid']

        if state == "absent":
            # remove host
            host.delete_host(host_id, host_name)
            module.exit_json(changed=True, result="Successfully delete host %s" % host_name)
        else:
            if not group_ids:
                module.fail_json(msg="Specify at least one group for updating host '%s'." % host_name)

            if not force:
                module.fail_json(changed=False, result="Host present, Can't update configuration without force")

            # get exist host's interfaces
            exist_interfaces = host._zapi.hostinterface.get({'output': 'extend', 'hostids': host_id})
            exist_interfaces_copy = copy.deepcopy(exist_interfaces)

            # update host
            interfaces_len = len(interfaces) if interfaces else 0

            if len(exist_interfaces) > interfaces_len:
                if host.check_all_properties(host_id, host_groups, status, interfaces, template_ids,
                                             exist_interfaces, zabbix_host_obj, proxy_id, visible_name):
                    host.link_or_clear_template(host_id, template_ids)
                    host.update_host(host_name, group_ids, status, host_id,
                                     interfaces, exist_interfaces, proxy_id, visible_name)
                    module.exit_json(changed=True,
                                     result="Successfully update host %s (%s) and linked with template '%s'"
                                     % (host_name, ip, link_templates))
                else:
                    module.exit_json(changed=False)
            else:
                if host.check_all_properties(host_id, host_groups, status, interfaces, template_ids,
                                             exist_interfaces_copy, zabbix_host_obj, proxy_id, visible_name):
                    host.update_host(host_name, group_ids, status, host_id, interfaces, exist_interfaces, proxy_id, visible_name)
                    host.link_or_clear_template(host_id, template_ids)
                    host.update_inventory_mode(host_id, inventory_mode)
                    module.exit_json(changed=True,
                                     result="Successfully update host %s (%s) and linked with template '%s'"
                                     % (host_name, ip, link_templates))
                else:
                    module.exit_json(changed=False)
    else:
        if state == "absent":
            # the host is already deleted.
            module.exit_json(changed=False)

        # Use proxy specified, or set to 0 when adding new host
        if proxy:
            proxy_id = host.get_proxyid_by_proxy_name(proxy)
        else:
            proxy_id = 0

        if not group_ids:
            module.fail_json(msg="Specify at least one group for creating host '%s'." % host_name)

        if not interfaces or (interfaces and len(interfaces) == 0):
            module.fail_json(msg="Specify at least one interface for creating host '%s'." % host_name)

        # create host
        host_id = host.add_host(host_name, group_ids, status, interfaces, proxy_id, visible_name)
        host.link_or_clear_template(host_id, template_ids)
        host.update_inventory_mode(host_id, inventory_mode)
        module.exit_json(changed=True, result="Successfully added host %s (%s) and linked with template '%s'" % (
            host_name, ip, link_templates))

from ansible.module_utils.basic import *
main()
