#!/usr/bin/python

import atexit
import datetime
import time
import traceback

try:
    from zabbix_api import ZabbixAPI
    HAS_ZABBIX_API = True
except ImportError:
    ZBX_IMP_ERR = traceback.format_exc()
    HAS_ZABBIX_API = False

from ansible.module_utils.basic import *

def get_trigger(zbx, host_names):
    try:
        triggers = zbx.trigger.get(
            {
                "filter":
                {
                    "host": host_names,
                },
                "search": "*TCP 10050*",
                "searchByAny": "true",
                "searchWildcardsEnabled": "true",
                "limit": "1",
                "selectGroups": "extend",
                "selectHosts": "extend",
                "expandDescription": "extend"
            }
        )
    # zabbix_api can call sys.exit() so we need to catch SystemExit here
    except (Exception, SystemExit) as e:
        return 1, None, str(e)

    return 0, triggers, None

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

def delete_trigger(zbx, trigger_id):
    try:
        zbx.trigger.delete([trigger_id])
    # zabbix_api can call sys.exit() so we need to catch SystemExit here
    except (Exception, SystemExit) as e:
        return 1, None, str(e)
    return 0, None, None

def update_trigger(zbx, trigger_id, trigger_status):
    try:
        triggers = zbx.trigger.update(
            {
                "triggerid": trigger_id,
                "status": trigger_status
            }
        )
    # zabbix_api can call sys.exit() so we need to catch SystemExit here
    except (Exception, SystemExit) as e:
        return 1, None, str(e)
        
    return 0, triggers, None

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
            timeout=dict(type='int', default=10),
            trigger_id=dict(type='int', default=0)
        ),
        supports_check_mode=True,
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg=missing_required_lib('zabbix-api', url='https://pypi.org/project/zabbix-api/'), exception=ZBX_IMP_ERR)

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
    timeout = module.params['timeout']
    trigger_id= module.params['trigger_id']

    try:
        zbx = ZabbixAPI(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password,
                        validate_certs=validate_certs)
        zbx.login(login_user, login_password)
        atexit.register(zbx.logout)
    # zabbix_api can call sys.exit() so we need to catch SystemExit here
    except (Exception, SystemExit) as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    changed = False
    #zbx_result = get_trigger(zbx, host_names)

    #(rc, trigger, error) = get_trigger(zbx, host_names)
    #if rc != 0:
    #    module.fail_json(msg="Failed to check trigger %s existence: %s" % (name, error))

    #module.exit_json(ok=False, hosts=host_names, result=zbx_result)
    if state == "present":
        trigger_status = 0
        if trigger_id != 0:
             (rc, trigger, error) = update_trigger(zbx, trigger_id, trigger_status)
             (rc, trigger, error) = get_trigger(zbx, host_names)

        else:
            rc = 0
            trigger = 0

    if state == "absent":
        trigger_status = 1
        if trigger_id != 0:
            (rc, trigger, error) = update_trigger(zbx, trigger_id, trigger_status)
        else:
            rc = 0
            trigger = 0

    if rc != 0:
        module.fail_json(msg="Failed to check trigger %s %s status: %s" % (name, trigger_id, trigger_status))

    module.exit_json(ok=False, hosts=host_names, result=trigger, trigger_status=trigger_status)


if __name__ == '__main__':
    main()