#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Alexander Bulimov <lazywolf0@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: zabbix_maintenance
short_description: Create Zabbix maintenance windows
description:
    - This module will let you create Zabbix maintenance windows.
version_added: "1.8"
author: "Alexander Bulimov (@abulimov)"
requirements:
    - "python >= 2.6"
    - zabbix-api
options:
    state:
        description:
            - Create or remove a maintenance window. Maintenance window to remove is identified by name.
        default: present
        choices: [ "present", "absent" ]
    host_names:
        description:
            - Hosts to manage maintenance window for.
              Separate multiple hosts with commas.
              C(host_name) is an alias for C(host_names).
              B(Required) option when C(state) is I(present)
              and no C(host_groups) specified.
        aliases: [ "host_name" ]
    host_groups:
        description:
            - Host groups to manage maintenance window for.
              Separate multiple groups with commas.
              C(host_group) is an alias for C(host_groups).
              B(Required) option when C(state) is I(present)
              and no C(host_names) specified.
        aliases: [ "host_group" ]
    minutes:
        description:
            - Length of maintenance window in minutes.
        default: 10
    name:
        description:
            - Unique name of maintenance window.
        required: true
    desc:
        description:
            - Short description of maintenance window.
        required: true
        default: Created by Ansible
    collect_data:
        description:
            - Type of maintenance. With data collection, or without.
        type: bool
        default: 'yes'

extends_documentation_fragment:
    - zabbix

notes:
    - Useful for setting hosts in maintenance mode before big update,
      and removing maintenance window after update.
    - Module creates maintenance window from now() to now() + minutes,
      so if Zabbix server's time and host's time are not synchronized,
      you will get strange results.
    - Install required module with 'pip install zabbix-api' command.
'''

EXAMPLES = '''
- name: Create a named maintenance window for host www1 for 90 minutes
  zabbix_maintenance:
    name: Update of www1
    host_name: www1.example.com
    state: present
    minutes: 90
    server_url: https://monitoring.example.com
    login_user: ansible
    login_password: pAsSwOrD

- name: Create a named maintenance window for host www1 and host groups Office and Dev
  zabbix_maintenance:
    name: Update of www1
    host_name: www1.example.com
    host_groups:
      - Office
      - Dev
    state: present
    server_url: https://monitoring.example.com
    login_user: ansible
    login_password: pAsSwOrD

- name: Create a named maintenance window for hosts www1 and db1, without data collection.
  zabbix_maintenance:
    name: update
    host_names:
      - www1.example.com
      - db1.example.com
    state: present
    collect_data: False
    server_url: https://monitoring.example.com
    login_user: ansible
    login_password: pAsSwOrD

- name: Remove maintenance window by name
  zabbix_maintenance:
    name: Test1
    state: absent
    server_url: https://monitoring.example.com
    login_user: ansible
    login_password: pAsSwOrD
'''


import atexit
import datetime
import time

try:
    from zabbix_api import ZabbixAPI
    HAS_ZABBIX_API = True
except ImportError:
    HAS_ZABBIX_API = False

from ansible.module_utils.basic import AnsibleModule


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
                "timeperiods": [{
                    "timeperiod_type": "0",
                    "start_date": str(start_time),
                    "period": str(period),
                }]
            }
        )
    # zabbix_api can call sys.exit() so we need to catch SystemExit here
    except (Exception, SystemExit) as e:
        return 1, None, str(e)
    return 0, None, None


def update_maintenance(zbx, maintenance_id, group_ids, host_ids, start_time, maintenance_type, period, desc):
    end_time = start_time + period
    try:
        zbx.maintenance.update(
            {
                "maintenanceid": maintenance_id,
                "groupids": group_ids,
                "hostids": host_ids,
                "maintenance_type": maintenance_type,
                "active_since": str(start_time),
                "active_till": str(end_time),
                "description": desc,
                "timeperiods": [{
                    "timeperiod_type": "0",
                    "start_date": str(start_time),
                    "period": str(period),
                }]
            }
        )
    # zabbix_api can call sys.exit() so we need to catch SystemExit here
    except (Exception, SystemExit) as e:
        return 1, None, str(e)
    return 0, None, None


def get_maintenance(zbx, name):
    try:
        maintenances = zbx.maintenance.get(
            {
                "filter":
                {
                    "name": name,
                },
                "selectGroups": "extend",
                "selectHosts": "extend"
            }
        )
    # zabbix_api can call sys.exit() so we need to catch SystemExit here
    except (Exception, SystemExit) as e:
        return 1, None, str(e)

    for maintenance in maintenances:
        maintenance["groupids"] = [group["groupid"] for group in maintenance["groups"]] if "groups" in maintenance else []
        maintenance["hostids"] = [host["hostid"] for host in maintenance["hosts"]] if "hosts" in maintenance else []
        return 0, maintenance, None

    return 0, None, None


def delete_maintenance(zbx, maintenance_id):
    try:
        zbx.maintenance.delete([maintenance_id])
    # zabbix_api can call sys.exit() so we need to catch SystemExit here
    except (Exception, SystemExit) as e:
        return 1, None, str(e)
    return 0, None, None


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
        # zabbix_api can call sys.exit() so we need to catch SystemExit here
        except (Exception, SystemExit) as e:
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
        # zabbix_api can call sys.exit() so we need to catch SystemExit here
        except (Exception, SystemExit) as e:
            return 1, None, str(e)

        if not result:
            return 1, None, "Host id for host %s not found" % host

        host_ids.append(result[0]["hostid"])

    return 0, host_ids, None


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=False, default='present', choices=['present', 'absent']),
            server_url=dict(type='str', required=True, default=None, aliases=['url']),
            host_names=dict(type='list', required=False, default=None, aliases=['host_name']),
            minutes=dict(type='int', required=False, default=10),
            host_groups=dict(type='list', required=False, default=None, aliases=['host_group']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False, default=None, no_log=True),
            name=dict(type='str', required=True),
            desc=dict(type='str', required=False, default="Created by Ansible"),
            collect_data=dict(type='bool', required=False, default=True),
            timeout=dict(type='int', default=10),
        ),
        supports_check_mode=True,
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg="Missing required zabbix-api module (check docs or install with: pip install zabbix-api)")

    host_names = module.params['host_names']
    host_groups = module.params['host_groups']
    state = module.params['state']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    validate_certs = module.params['validate_certs']
    minutes = module.params['minutes']
    name = module.params['name']
    desc = module.params['desc']
    server_url = module.params['server_url']
    collect_data = module.params['collect_data']
    timeout = module.params['timeout']

    if collect_data:
        maintenance_type = 0
    else:
        maintenance_type = 1

    try:
        zbx = ZabbixAPI(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password,
                        validate_certs=validate_certs)
        zbx.login(login_user, login_password)
        atexit.register(zbx.logout)
    # zabbix_api can call sys.exit() so we need to catch SystemExit here
    except (Exception, SystemExit) as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    changed = False

    if state == "present":

        if not host_names and not host_groups:
            module.fail_json(msg="At least one host_name or host_group must be defined for each created maintenance.")

        now = datetime.datetime.now().replace(second=0)
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

        (rc, maintenance, error) = get_maintenance(zbx, name)
        if rc != 0:
            module.fail_json(msg="Failed to check maintenance %s existence: %s" % (name, error))

        if maintenance and (
            sorted(group_ids) != sorted(maintenance["groupids"]) or
            sorted(host_ids) != sorted(maintenance["hostids"]) or
            str(maintenance_type) != maintenance["maintenance_type"] or
            str(int(start_time)) != maintenance["active_since"] or
            str(int(start_time + period)) != maintenance["active_till"]
        ):
            if module.check_mode:
                changed = True
            else:
                (rc, _, error) = update_maintenance(zbx, maintenance["maintenanceid"], group_ids, host_ids, start_time, maintenance_type, period, desc)
                if rc == 0:
                    changed = True
                else:
                    module.fail_json(msg="Failed to update maintenance: %s" % error)

        if not maintenance:
            if module.check_mode:
                changed = True
            else:
                (rc, _, error) = create_maintenance(zbx, group_ids, host_ids, start_time, maintenance_type, period, name, desc)
                if rc == 0:
                    changed = True
                else:
                    module.fail_json(msg="Failed to create maintenance: %s" % error)

    if state == "absent":

        (rc, maintenance, error) = get_maintenance(zbx, name)
        if rc != 0:
            module.fail_json(msg="Failed to check maintenance %s existence: %s" % (name, error))

        if maintenance:
            if module.check_mode:
                changed = True
            else:
                (rc, _, error) = delete_maintenance(zbx, maintenance["maintenanceid"])
                if rc == 0:
                    changed = True
                else:
                    module.fail_json(msg="Failed to remove maintenance: %s" % error)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
