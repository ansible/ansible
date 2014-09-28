#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Alexander Bulimov <lazywolf0@gmail.com>
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


DOCUMENTATION = '''

module: zabbix_maintenance
short_description: Create Zabbix maintenance windows
description:
    - This module will let you create Zabbix maintenance windows.
version_added: "1.8"
author: Alexander Bulimov
requirements:
    - zabbix-api python module
options:
    state:
        description:
            - Create or remove a maintenance window.
        required: false
        default: present
        choices: [ "present", "absent" ]
    server_url:
        description:
            - Url of Zabbix server, with protocol (http or https).
              C(url) is an alias for C(server_url).
        required: true
        default: null
        aliases: [ "url" ]
    login_user:
        description:
            - Zabbix user name.
        required: true
        default: null
    login_password:
        description:
            - Zabbix user password.
        required: true
        default: null
    host_names:
        description:
            - Hosts to manage maintenance window for.
              Separate multiple hosts with commas.
              C(host_name) is an alias for C(host_names).
              B(Required) option when C(state) is I(present)
              and no C(host_groups) specified.
        required: false
        default: null
        aliases: [ "host_name" ]
    host_groups:
        description:
            - Host groups to manage maintenance window for.
              Separate multiple groups with commas.
              C(host_group) is an alias for C(host_groups).
              B(Required) option when C(state) is I(present)
              and no C(host_names) specified.
        required: false
        default: null
        aliases: [ "host_group" ]
    minutes:
        description:
            - Length of maintenance window in minutes.
        required: false
        default: 10
    name:
        description:
            - Unique name of maintenance window.
        required: true
        default: null
    desc:
        description:
            - Short description of maintenance window.
        required: true
        default: Created by Ansible
    collect_data:
        description:
            - Type of maintenance. With data collection, or without.
        required: false
        default: "true"
notes:
    - Useful for setting hosts in maintenance mode before big update,
      and removing maintenance window after update.
    - Module creates maintenance window from now() to now() + minutes,
      so if Zabbix server's time and host's time are not synchronized,
      you will get strange results.
    - Install required module with 'pip install zabbix-api' command.
    - Checks existance only by maintenance name.
'''

EXAMPLES = '''
# Create maintenance window named "Update of www1"
# for host www1.example.com for 90 minutes
- zabbix_maintenance: name="Update of www1"
                      host_name=www1.example.com
                      state=present
                      minutes=90
                      server_url=https://monitoring.example.com
                      login_user=ansible
                      login_password=pAsSwOrD

# Create maintenance window named "Mass update"
# for host www1.example.com and host groups Office and Dev
- zabbix_maintenance: name="Update of www1"
                      host_name=www1.example.com
                      host_groups=Office,Dev
                      state=present
                      server_url=https://monitoring.example.com
                      login_user=ansible
                      login_password=pAsSwOrD

# Create maintenance window named "update"
# for hosts www1.example.com and db1.example.com and without data collection.
- zabbix_maintenance: name=update
                      host_names=www1.example.com,db1.example.com
                      state=present
                      collect_data=false
                      server_url=https://monitoring.example.com
                      login_user=ansible
                      login_password=pAsSwOrD

# Remove maintenance window named "Test1"
- zabbix_maintenance: name=Test1
                      state=absent
                      server_url=https://monitoring.example.com
                      login_user=ansible
                      login_password=pAsSwOrD
'''

import datetime
import time

try:
    from zabbix_api import ZabbixAPI
    HAS_ZABBIX_API = True
except ImportError:
    HAS_ZABBIX_API = False


def create_maintenance(zbx, group_ids, host_ids, start_time, maintenance_type, period, name, desc):
    end_time = start_time + period
    try:
        zbx.maintenance.create(
            {
                "groupids": group_ids,
                "hostids": host_ids,
                "name": name,
                "maintenance_type": maintenance_type,
                "active_since": str(start_time),
                "active_till": str(end_time),
                "description": desc,
                "timeperiods":  [{
                    "timeperiod_type": "0",
                    "start_date": str(start_time),
                    "period": str(period),
                }]
            }
        )
    except BaseException as e:
        return 1, None, str(e)
    return 0, None, None


def get_maintenance_id(zbx, name):
    try:
        result = zbx.maintenance.get(
            {
                "filter":
                {
                    "name": name,
                }
            }
        )
    except BaseException as e:
        return 1, None, str(e)

    maintenance_ids = []
    for res in result:
        maintenance_ids.append(res["maintenanceid"])

    return 0, maintenance_ids, None


def delete_maintenance(zbx, maintenance_id):
    try:
        zbx.maintenance.delete(maintenance_id)
    except BaseException as e:
        return 1, None, str(e)
    return 0, None, None


def check_maintenance(zbx, name):
    try:
        result = zbx.maintenance.exists(
            {
                "name": name
            }
        )
    except BaseException as e:
        return 1, None, str(e)
    return 0, result, None


def get_group_ids(zbx, host_groups):
    group_ids = []
    for group in host_groups:
        try:
            result = zbx.hostgroup.get(
                {
                    "output": "extend",
                    "filter":
                    {
                        "name": group
                    }
                }
            )
        except BaseException as e:
            return 1, None, str(e)

        if not result:
            return 1, None, "Group id for group %s not found" % group

        group_ids.append(result[0]["groupid"])

    return 0, group_ids, None


def get_host_ids(zbx, host_names):
    host_ids = []
    for host in host_names:
        try:
            result = zbx.host.get(
                {
                    "output": "extend",
                    "filter":
                    {
                        "name": host
                    }
                }
            )
        except BaseException as e:
            return 1, None, str(e)

        if not result:
            return 1, None, "Host id for host %s not found" % host

        host_ids.append(result[0]["hostid"])

    return 0, host_ids, None


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=False, default='present', choices=['present', 'absent']),
            server_url=dict(required=True, default=None, aliases=['url']),
            host_names=dict(type='list', required=False, default=None, aliases=['host_name']),
            minutes=dict(type='int', required=False, default=10),
            host_groups=dict(type='list', required=False, default=None, aliases=['host_group']),
            login_user=dict(required=True, default=None),
            login_password=dict(required=True, default=None),
            name=dict(required=True, default=None),
            desc=dict(required=False, default="Created by Ansible"),
            collect_data=dict(type='bool', required=False, default=True),
        ),
        supports_check_mode=True,
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg="Missing requried zabbix-api module (check docs or install with: pip install zabbix-api)")

    host_names = module.params['host_names']
    host_groups = module.params['host_groups']
    state = module.params['state']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    minutes = module.params['minutes']
    name = module.params['name']
    desc = module.params['desc']
    server_url = module.params['server_url']
    collect_data = module.params['collect_data']
    if collect_data:
        maintenance_type = 0
    else:
        maintenance_type = 1

    try:
        zbx = ZabbixAPI(server_url)
        zbx.login(login_user, login_password)
    except BaseException as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    changed = False

    if state == "present":

        now = datetime.datetime.now()
        start_time = time.mktime(now.timetuple())
        period = 60 * int(minutes)  # N * 60 seconds

        if host_groups:
            (rc, group_ids, error) = get_group_ids(zbx, host_groups)
            if rc != 0:
                module.fail_json(msg="Failed to get group_ids: %s" % error)
        else:
            group_ids = []

        if host_names:
            (rc, host_ids, error) = get_host_ids(zbx, host_names)
            if rc != 0:
                module.fail_json(msg="Failed to get host_ids: %s" % error)
        else:
            host_ids = []

        (rc, exists, error) = check_maintenance(zbx, name)
        if rc != 0:
            module.fail_json(msg="Failed to check maintenance %s existance: %s" % (name, error))

        if not exists:
            if not host_names and not host_groups:
                module.fail_json(msg="At least one host_name or host_group must be defined for each created maintenance.")

            if module.check_mode:
                changed = True
            else:
                (rc, _, error) = create_maintenance(zbx, group_ids, host_ids, start_time, maintenance_type, period, name, desc)
                if rc == 0:
                    changed = True
                else:
                    module.fail_json(msg="Failed to create maintenance: %s" % error)

    if state == "absent":

        (rc, exists, error) = check_maintenance(zbx, name)
        if rc != 0:
            module.fail_json(msg="Failed to check maintenance %s existance: %s" % (name, error))

        if exists:
            (rc, maintenance, error) = get_maintenance_id(zbx, name)
            if rc != 0:
                module.fail_json(msg="Failed to get maintenance id: %s" % error)

            if maintenance:
                if module.check_mode:
                    changed = True
                else:
                    (rc, _, error) = delete_maintenance(zbx, maintenance)
                    if rc == 0:
                        changed = True
                    else:
                        module.fail_json(msg="Failed to remove maintenance: %s" % error)

    module.exit_json(changed=changed)

from ansible.module_utils.basic import *
main()
