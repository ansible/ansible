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
module: zabbix_screen
short_description: Zabbix screen creates/updates/deletes
description:
    - This module allows you to create, modify and delete Zabbix screens and associated graph data.
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
            - Zabbix user name.
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
    timeout:
        description:
            - The timeout of API request (seconds).
        default: 10
    screens:
        description:
            - List of screens to be created/updated/deleted(see example).
            - If the screen(s) already been added, the screen(s) name won't be updated.
            - When creating or updating screen(s), C(screen_name), C(host_group) are required.
            - When deleting screen(s), the C(screen_name) is required.
            - 'The available states are: C(present) (default) and C(absent). If the screen(s) already exists, and the state is not C(absent), the screen(s) will just be updated as needed.'
        required: true
notes:
    - Too many concurrent updates to the same screen may cause Zabbix to return errors, see examples for a workaround if needed.
'''

EXAMPLES = '''
# Create/update a screen.
- name: Create a new screen or update an existing screen's items
  local_action:
    module: zabbix_screen
    server_url: http://monitor.example.com
    login_user: username
    login_password: password
    screens:
      - screen_name: ExampleScreen1
        host_group: Example group1
        state: present
        graph_names:
          - Example graph1
          - Example graph2
        graph_width: 200
        graph_height: 100

# Create/update multi-screen
- name: Create two of new screens or update the existing screens' items
  local_action:
    module: zabbix_screen
    server_url: http://monitor.example.com
    login_user: username
    login_password: password
    screens:
      - screen_name: ExampleScreen1
        host_group: Example group1
        state: present
        graph_names:
          - Example graph1
          - Example graph2
        graph_width: 200
        graph_height: 100
      - screen_name: ExampleScreen2
        host_group: Example group2
        state: present
        graph_names:
          - Example graph1
          - Example graph2
        graph_width: 200
        graph_height: 100

# Limit the Zabbix screen creations to one host since Zabbix can return an error when doing concurent updates
- name: Create a new screen or update an existing screen's items
  local_action:
    module: zabbix_screen
    server_url: http://monitor.example.com
    login_user: username
    login_password: password
    state: present
    screens:
      - screen_name: ExampleScreen
        host_group: Example group
        state: present
        graph_names:
          - Example graph1
          - Example graph2
        graph_width: 200
        graph_height: 100
  when: inventory_hostname==groups['group_name'][0]
'''

try:
    from zabbix_api import ZabbixAPI, ZabbixAPISubClass
    from zabbix_api import ZabbixAPIException
    from zabbix_api import Already_Exists
    HAS_ZABBIX_API = True
except ImportError:
    HAS_ZABBIX_API = False


# Extend the ZabbixAPI
# Since the zabbix-api python module too old (version 1.0, and there's no higher version so far), it doesn't support the 'screenitem' api call,
# we have to inherit the ZabbixAPI class to add 'screenitem' support.
class ZabbixAPIExtends(ZabbixAPI):
    screenitem = None

    def __init__(self, server, timeout, user, passwd, **kwargs):
        ZabbixAPI.__init__(self, server, timeout=timeout, user=user, passwd=passwd)
        self.screenitem = ZabbixAPISubClass(self, dict({"prefix": "screenitem"}, **kwargs))


class Screen(object):
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx

    # get group id by group name
    def get_host_group_id(self, group_name):
        if group_name == "":
            self._module.fail_json(msg="group_name is required")
        hostGroup_list = self._zapi.hostgroup.get({'output': 'extend', 'filter': {'name': group_name}})
        if len(hostGroup_list) < 1:
            self._module.fail_json(msg="Host group not found: %s" % group_name)
        else:
            hostGroup_id = hostGroup_list[0]['groupid']
            return hostGroup_id

    # get monitored host_id by host_group_id
    def get_host_ids_by_group_id(self, group_id):
        host_list = self._zapi.host.get({'output': 'extend', 'groupids': group_id, 'monitored_hosts': 1})
        if len(host_list) < 1:
            self._module.fail_json(msg="No host in the group.")
        else:
            host_ids = []
            for i in host_list:
                host_id = i['hostid']
                host_ids.append(host_id)
            return host_ids

    # get screen
    def get_screen_id(self, screen_name):
        if screen_name == "":
            self._module.fail_json(msg="screen_name is required")
        try:
            screen_id_list = self._zapi.screen.get({'output': 'extend', 'search': {"name": screen_name}})
            if len(screen_id_list) >= 1:
                screen_id = screen_id_list[0]['screenid']
                return screen_id
            return None
        except Exception as e:
            self._module.fail_json(msg="Failed to get screen %s from Zabbix: %s" % (screen_name, e))

    # create screen
    def create_screen(self, screen_name, h_size, v_size):
        try:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            screen = self._zapi.screen.create({'name': screen_name, 'hsize': h_size, 'vsize': v_size})
            return screen['screenids'][0]
        except Exception as e:
            self._module.fail_json(msg="Failed to create screen %s: %s" % (screen_name, e))

    # update screen
    def update_screen(self, screen_id, screen_name, h_size, v_size):
        try:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            self._zapi.screen.update({'screenid': screen_id, 'hsize': h_size, 'vsize': v_size})
        except Exception as e:
            self._module.fail_json(msg="Failed to update screen %s: %s" % (screen_name, e))

    # delete screen
    def delete_screen(self, screen_id, screen_name):
        try:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            self._zapi.screen.delete([screen_id])
        except Exception as e:
            self._module.fail_json(msg="Failed to delete screen %s: %s" % (screen_name, e))

    # get graph ids
    def get_graph_ids(self, hosts, graph_name_list):
        graph_id_lists = []
        vsize = 1
        for host in hosts:
            graph_id_list = self.get_graphs_by_host_id(graph_name_list, host)
            size = len(graph_id_list)
            if size > 0:
                graph_id_lists.extend(graph_id_list)
                if vsize < size:
                    vsize = size
        return graph_id_lists, vsize

    #  getGraphs
    def get_graphs_by_host_id(self, graph_name_list, host_id):
        graph_ids = []
        for graph_name in graph_name_list:
            graphs_list = self._zapi.graph.get({'output': 'extend', 'search': {'name': graph_name}, 'hostids': host_id})
            graph_id_list = []
            if len(graphs_list) > 0:
                for graph in graphs_list:
                    graph_id = graph['graphid']
                    graph_id_list.append(graph_id)
            if len(graph_id_list) > 0:
                graph_ids.extend(graph_id_list)
        return graph_ids

    # get screen items
    def get_screen_items(self, screen_id):
        screen_item_list = self._zapi.screenitem.get({'output': 'extend', 'screenids': screen_id})
        return screen_item_list

    # delete screen items
    def delete_screen_items(self, screen_id, screen_item_id_list):
        try:
            if len(screen_item_id_list) == 0:
                return True
            screen_item_list = self.get_screen_items(screen_id)
            if len(screen_item_list) > 0:
                if self._module.check_mode:
                    self._module.exit_json(changed=True)
                self._zapi.screenitem.delete(screen_item_id_list)
                return True
            return False
        except ZabbixAPIException:
            pass

    # get screen's hsize and vsize
    def get_hsize_vsize(self, hosts, v_size):
        h_size = len(hosts)
        if h_size == 1:
            if v_size == 1:
                h_size = 1
            elif v_size in range(2, 9):
                h_size = 2
            else:
                h_size = 3
            v_size = (v_size - 1) / h_size + 1
        return h_size, v_size

    # create screen_items
    def create_screen_items(self, screen_id, hosts, graph_name_list, width, height, h_size):
        if len(hosts) < 4:
            if width is None or width < 0:
                width = 500
        else:
            if width is None or width < 0:
                width = 200
        if height is None or height < 0:
            height = 100

        try:
            # when there're only one host, only one row is not good.
            if len(hosts) == 1:
                graph_id_list = self.get_graphs_by_host_id(graph_name_list, hosts[0])
                for i, graph_id in enumerate(graph_id_list):
                    if graph_id is not None:
                        self._zapi.screenitem.create({'screenid': screen_id, 'resourcetype': 0, 'resourceid': graph_id,
                                                      'width': width, 'height': height,
                                                      'x': i % h_size, 'y': i / h_size, 'colspan': 1, 'rowspan': 1,
                                                      'elements': 0, 'valign': 0, 'halign': 0,
                                                      'style': 0, 'dynamic': 0, 'sort_triggers': 0})
            else:
                for i, host in enumerate(hosts):
                    graph_id_list = self.get_graphs_by_host_id(graph_name_list, host)
                    for j, graph_id in enumerate(graph_id_list):
                        if graph_id is not None:
                            self._zapi.screenitem.create({'screenid': screen_id, 'resourcetype': 0, 'resourceid': graph_id,
                                                          'width': width, 'height': height,
                                                          'x': i, 'y': j, 'colspan': 1, 'rowspan': 1,
                                                          'elements': 0, 'valign': 0, 'halign': 0,
                                                          'style': 0, 'dynamic': 0, 'sort_triggers': 0})
        except Already_Exists:
            pass


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False, default=None, no_log=True),
            timeout=dict(type='int', default=10),
            screens=dict(type='list', required=True)
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
    timeout = module.params['timeout']
    screens = module.params['screens']

    zbx = None
    # login to zabbix
    try:
        zbx = ZabbixAPIExtends(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password)
        zbx.login(login_user, login_password)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    screen = Screen(module, zbx)
    created_screens = []
    changed_screens = []
    deleted_screens = []

    for zabbix_screen in screens:
        screen_name = zabbix_screen['screen_name']
        screen_id = screen.get_screen_id(screen_name)
        state = "absent" if "state" in zabbix_screen and zabbix_screen['state'] == "absent" else "present"

        if state == "absent":
            if screen_id:
                screen_item_list = screen.get_screen_items(screen_id)
                screen_item_id_list = []
                for screen_item in screen_item_list:
                    screen_item_id = screen_item['screenitemid']
                    screen_item_id_list.append(screen_item_id)
                screen.delete_screen_items(screen_id, screen_item_id_list)
                screen.delete_screen(screen_id, screen_name)

                deleted_screens.append(screen_name)
        else:
            host_group = zabbix_screen['host_group']
            graph_names = zabbix_screen['graph_names']
            graph_width = None
            if 'graph_width' in zabbix_screen:
                graph_width = zabbix_screen['graph_width']
            graph_height = None
            if 'graph_height' in zabbix_screen:
                graph_height = zabbix_screen['graph_height']
            host_group_id = screen.get_host_group_id(host_group)
            hosts = screen.get_host_ids_by_group_id(host_group_id)

            screen_item_id_list = []
            resource_id_list = []

            graph_ids, v_size = screen.get_graph_ids(hosts, graph_names)
            h_size, v_size = screen.get_hsize_vsize(hosts, v_size)

            if not screen_id:
                # create screen
                screen_id = screen.create_screen(screen_name, h_size, v_size)
                screen.create_screen_items(screen_id, hosts, graph_names, graph_width, graph_height, h_size)
                created_screens.append(screen_name)
            else:
                screen_item_list = screen.get_screen_items(screen_id)

                for screen_item in screen_item_list:
                    screen_item_id = screen_item['screenitemid']
                    resource_id = screen_item['resourceid']
                    screen_item_id_list.append(screen_item_id)
                    resource_id_list.append(resource_id)

                # when the screen items changed, then update
                if graph_ids != resource_id_list:
                    deleted = screen.delete_screen_items(screen_id, screen_item_id_list)
                    if deleted:
                        screen.update_screen(screen_id, screen_name, h_size, v_size)
                        screen.create_screen_items(screen_id, hosts, graph_names, graph_width, graph_height, h_size)
                        changed_screens.append(screen_name)

    if created_screens and changed_screens:
        module.exit_json(changed=True, result="Successfully created screen(s): %s, and updated screen(s): %s" % (",".join(created_screens), ",".join(changed_screens)))
    elif created_screens:
        module.exit_json(changed=True, result="Successfully created screen(s): %s" % ",".join(created_screens))
    elif changed_screens:
        module.exit_json(changed=True, result="Successfully updated screen(s): %s" % ",".join(changed_screens))
    elif deleted_screens:
        module.exit_json(changed=True, result="Successfully deleted screen(s): %s" % ",".join(deleted_screens))
    else:
        module.exit_json(changed=False)

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
