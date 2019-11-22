#!/usr/bin/python
# -*- coding: utf-8 -*-

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

"""
(c) 2017, Milan Ilic <milani@nordeus.com>

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Ansible is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
"""

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: one_service
short_description: Deploy and manage OpenNebula services
description:
  - Manage OpenNebula services
version_added: "2.6"
options:
  api_url:
    description:
      - URL of the OpenNebula OneFlow API server.
      - It is recommended to use HTTPS so that the username/password are not transferred over the network unencrypted.
      - If not set then the value of the ONEFLOW_URL environment variable is used.
  api_username:
    description:
      - Name of the user to login into the OpenNebula OneFlow API server. If not set then the value of the C(ONEFLOW_USERNAME) environment variable is used.
  api_password:
    description:
      - Password of the user to login into OpenNebula OneFlow API server. If not set then the value of the C(ONEFLOW_PASSWORD) environment variable is used.
  template_name:
    description:
      - Name of service template to use to create a new instance of a service
  template_id:
    description:
      - ID of a service template to use to create a new instance of a service
  service_id:
    description:
      - ID of a service instance that you would like to manage
  service_name:
    description:
      - Name of a service instance that you would like to manage
  unique:
    description:
      - Setting C(unique=yes) will make sure that there is only one service instance running with a name set with C(service_name) when
      - instantiating a service from a template specified with C(template_id)/C(template_name). Check examples below.
    type: bool
    default: no
  state:
    description:
      - C(present) - instantiate a service from a template specified with C(template_id)/C(template_name).
      - C(absent) - terminate an instance of a service specified with C(service_id)/C(service_name).
    choices: ["present", "absent"]
    default: present
  mode:
    description:
      - Set permission mode of a service instance in octet format, e.g. C(600) to give owner C(use) and C(manage) and nothing to group and others.
  owner_id:
    description:
      - ID of the user which will be set as the owner of the service
  group_id:
    description:
      - ID of the group which will be set as the group of the service
  wait:
    description:
      - Wait for the instance to reach RUNNING state after DEPLOYING or COOLDOWN state after SCALING
    type: bool
    default: no
  wait_timeout:
    description:
      - How long before wait gives up, in seconds
    default: 300
  custom_attrs:
    description:
      - Dictionary of key/value custom attributes which will be used when instantiating a new service.
    default: {}
  role:
    description:
      - Name of the role whose cardinality should be changed
  cardinality:
    description:
      - Number of VMs for the specified role
  force:
    description:
      - Force the new cardinality even if it is outside the limits
    type: bool
    default: no
author:
    - "Milan Ilic (@ilicmilan)"
'''

EXAMPLES = '''
# Instantiate a new service
- one_service:
    template_id: 90
  register: result

# Print service properties
- debug:
    msg: result

# Instantiate a new service with specified service_name, service group and mode
- one_service:
    template_name: 'app1_template'
    service_name: 'app1'
    group_id: 1
    mode: '660'

# Instantiate a new service with template_id and pass custom_attrs dict
- one_service:
    template_id: 90
    custom_attrs:
      public_network_id: 21
      private_network_id: 26

# Instantiate a new service 'foo' if the service doesn't already exist, otherwise do nothing
- one_service:
    template_id: 53
    service_name: 'foo'
    unique: yes

# Delete a service by ID
- one_service:
    service_id: 153
    state: absent

# Get service info
- one_service:
    service_id: 153
  register: service_info

# Change service owner, group and mode
- one_service:
    service_name: 'app2'
    owner_id: 34
    group_id: 113
    mode: '600'

# Instantiate service and wait for it to become RUNNING
-  one_service:
    template_id: 43
    service_name: 'foo1'

# Wait service to become RUNNING
- one_service:
    service_id: 112
    wait: yes

# Change role cardinality
- one_service:
    service_id: 153
    role: bar
    cardinality: 5

# Change role cardinality and wait for it to be applied
- one_service:
    service_id: 112
    role: foo
    cardinality: 7
    wait: yes
'''

RETURN = '''
service_id:
    description: service id
    type: int
    returned: success
    sample: 153
service_name:
    description: service name
    type: str
    returned: success
    sample: app1
group_id:
    description: service's group id
    type: int
    returned: success
    sample: 1
group_name:
    description: service's group name
    type: str
    returned: success
    sample: one-users
owner_id:
    description: service's owner id
    type: int
    returned: success
    sample: 143
owner_name:
    description: service's owner name
    type: str
    returned: success
    sample: ansible-test
state:
    description: state of service instance
    type: str
    returned: success
    sample: RUNNING
mode:
    description: service's mode
    type: int
    returned: success
    sample: 660
roles:
    description: list of dictionaries of roles, each role is described by name, cardinality, state and nodes ids
    type: list
    returned: success
    sample: '[{"cardinality": 1,"name": "foo","state": "RUNNING","ids": [ 123, 456 ]},
              {"cardinality": 2,"name": "bar","state": "RUNNING", "ids": [ 452, 567, 746 ]}]'
'''

import os
import sys
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url

STATES = ("PENDING", "DEPLOYING", "RUNNING", "UNDEPLOYING", "WARNING", "DONE",
          "FAILED_UNDEPLOYING", "FAILED_DEPLOYING", "SCALING", "FAILED_SCALING", "COOLDOWN")


def get_all_templates(module, auth):
    try:
        all_templates = open_url(url=(auth.url + "/service_template"), method="GET", force_basic_auth=True, url_username=auth.user, url_password=auth.password)
    except Exception as e:
        module.fail_json(msg=str(e))

    return module.from_json(all_templates.read())


def get_template(module, auth, pred):
    all_templates_dict = get_all_templates(module, auth)

    found = 0
    found_template = None
    template_name = ''

    if "DOCUMENT_POOL" in all_templates_dict and "DOCUMENT" in all_templates_dict["DOCUMENT_POOL"]:
        for template in all_templates_dict["DOCUMENT_POOL"]["DOCUMENT"]:
            if pred(template):
                found = found + 1
                found_template = template
                template_name = template["NAME"]

    if found <= 0:
        return None
    elif found > 1:
        module.fail_json(msg="There is no template with unique name: " + template_name)
    else:
        return found_template


def get_all_services(module, auth):
    try:
        response = open_url(auth.url + "/service", method="GET", force_basic_auth=True, url_username=auth.user, url_password=auth.password)
    except Exception as e:
        module.fail_json(msg=str(e))

    return module.from_json(response.read())


def get_service(module, auth, pred):
    all_services_dict = get_all_services(module, auth)

    found = 0
    found_service = None
    service_name = ''

    if "DOCUMENT_POOL" in all_services_dict and "DOCUMENT" in all_services_dict["DOCUMENT_POOL"]:
        for service in all_services_dict["DOCUMENT_POOL"]["DOCUMENT"]:
            if pred(service):
                found = found + 1
                found_service = service
                service_name = service["NAME"]

    # fail if there are more services with same name
    if found > 1:
        module.fail_json(msg="There are multiple services with a name: '" +
                         service_name + "'. You have to use a unique service name or use 'service_id' instead.")
    elif found <= 0:
        return None
    else:
        return found_service


def get_service_by_id(module, auth, service_id):
    return get_service(module, auth, lambda service: (int(service["ID"]) == int(service_id))) if service_id else None


def get_service_by_name(module, auth, service_name):
    return get_service(module, auth, lambda service: (service["NAME"] == service_name))


def get_service_info(module, auth, service):

    result = {
        "service_id": int(service["ID"]),
        "service_name": service["NAME"],
        "group_id": int(service["GID"]),
        "group_name": service["GNAME"],
        "owner_id": int(service["UID"]),
        "owner_name": service["UNAME"],
        "state": STATES[service["TEMPLATE"]["BODY"]["state"]]
    }

    roles_status = service["TEMPLATE"]["BODY"]["roles"]
    roles = []
    for role in roles_status:
        nodes_ids = []
        if "nodes" in role:
            for node in role["nodes"]:
                nodes_ids.append(node["deploy_id"])
        roles.append({"name": role["name"], "cardinality": role["cardinality"], "state": STATES[int(role["state"])], "ids": nodes_ids})

    result["roles"] = roles
    result["mode"] = int(parse_service_permissions(service))

    return result


def create_service(module, auth, template_id, service_name, custom_attrs, unique, wait, wait_timeout):
    # make sure that the values in custom_attrs dict are strings
    custom_attrs_with_str = dict((k, str(v)) for k, v in custom_attrs.items())

    data = {
        "action": {
            "perform": "instantiate",
            "params": {
                "merge_template": {
                    "custom_attrs_values": custom_attrs_with_str,
                    "name": service_name
                }
            }
        }
    }

    try:
        response = open_url(auth.url + "/service_template/" + str(template_id) + "/action", method="POST",
                            data=module.jsonify(data), force_basic_auth=True, url_username=auth.user, url_password=auth.password)
    except Exception as e:
        module.fail_json(msg=str(e))

    service_result = module.from_json(response.read())["DOCUMENT"]

    return service_result


def wait_for_service_to_become_ready(module, auth, service_id, wait_timeout):
    import time
    start_time = time.time()

    while (time.time() - start_time) < wait_timeout:
        try:
            status_result = open_url(auth.url + "/service/" + str(service_id), method="GET",
                                     force_basic_auth=True, url_username=auth.user, url_password=auth.password)
        except Exception as e:
            module.fail_json(msg="Request for service status has failed. Error message: " + str(e))

        status_result = module.from_json(status_result.read())
        service_state = status_result["DOCUMENT"]["TEMPLATE"]["BODY"]["state"]

        if service_state in [STATES.index("RUNNING"), STATES.index("COOLDOWN")]:
            return status_result["DOCUMENT"]
        elif service_state not in [STATES.index("PENDING"), STATES.index("DEPLOYING"), STATES.index("SCALING")]:
            log_message = ''
            for log_info in status_result["DOCUMENT"]["TEMPLATE"]["BODY"]["log"]:
                if log_info["severity"] == "E":
                    log_message = log_message + log_info["message"]
                    break

            module.fail_json(msg="Deploying is unsuccessful. Service state: " + STATES[service_state] + ". Error message: " + log_message)

        time.sleep(1)

    module.fail_json(msg="Wait timeout has expired")


def change_service_permissions(module, auth, service_id, permissions):

    data = {
        "action": {
            "perform": "chmod",
            "params": {"octet": permissions}
        }
    }

    try:
        status_result = open_url(auth.url + "/service/" + str(service_id) + "/action", method="POST", force_basic_auth=True,
                                 url_username=auth.user, url_password=auth.password, data=module.jsonify(data))
    except Exception as e:
        module.fail_json(msg=str(e))


def change_service_owner(module, auth, service_id, owner_id):
    data = {
        "action": {
            "perform": "chown",
            "params": {"owner_id": owner_id}
        }
    }

    try:
        status_result = open_url(auth.url + "/service/" + str(service_id) + "/action", method="POST", force_basic_auth=True,
                                 url_username=auth.user, url_password=auth.password, data=module.jsonify(data))
    except Exception as e:
        module.fail_json(msg=str(e))


def change_service_group(module, auth, service_id, group_id):

    data = {
        "action": {
            "perform": "chgrp",
            "params": {"group_id": group_id}
        }
    }

    try:
        status_result = open_url(auth.url + "/service/" + str(service_id) + "/action", method="POST", force_basic_auth=True,
                                 url_username=auth.user, url_password=auth.password, data=module.jsonify(data))
    except Exception as e:
        module.fail_json(msg=str(e))


def change_role_cardinality(module, auth, service_id, role, cardinality, force):

    data = {
        "cardinality": cardinality,
        "force": force
    }

    try:
        status_result = open_url(auth.url + "/service/" + str(service_id) + "/role/" + role, method="PUT",
                                 force_basic_auth=True, url_username=auth.user, url_password=auth.password, data=module.jsonify(data))
    except Exception as e:
        module.fail_json(msg=str(e))

    if status_result.getcode() != 204:
        module.fail_json(msg="Failed to change cardinality for role: " + role + ". Return code: " + str(status_result.getcode()))


def check_change_service_owner(module, service, owner_id):
    old_owner_id = int(service["UID"])

    return old_owner_id != owner_id


def check_change_service_group(module, service, group_id):
    old_group_id = int(service["GID"])

    return old_group_id != group_id


def parse_service_permissions(service):
    perm_dict = service["PERMISSIONS"]
    '''
    This is the structure of the 'PERMISSIONS' dictionary:

   "PERMISSIONS": {
                      "OWNER_U": "1",
                      "OWNER_M": "1",
                      "OWNER_A": "0",
                      "GROUP_U": "0",
                      "GROUP_M": "0",
                      "GROUP_A": "0",
                      "OTHER_U": "0",
                      "OTHER_M": "0",
                      "OTHER_A": "0"
                    }
    '''

    owner_octal = int(perm_dict["OWNER_U"]) * 4 + int(perm_dict["OWNER_M"]) * 2 + int(perm_dict["OWNER_A"])
    group_octal = int(perm_dict["GROUP_U"]) * 4 + int(perm_dict["GROUP_M"]) * 2 + int(perm_dict["GROUP_A"])
    other_octal = int(perm_dict["OTHER_U"]) * 4 + int(perm_dict["OTHER_M"]) * 2 + int(perm_dict["OTHER_A"])

    permissions = str(owner_octal) + str(group_octal) + str(other_octal)

    return permissions


def check_change_service_permissions(module, service, permissions):
    old_permissions = parse_service_permissions(service)

    return old_permissions != permissions


def check_change_role_cardinality(module, service, role_name, cardinality):
    roles_list = service["TEMPLATE"]["BODY"]["roles"]

    for role in roles_list:
        if role["name"] == role_name:
            return int(role["cardinality"]) != cardinality

    module.fail_json(msg="There is no role with name: " + role_name)


def create_service_and_operation(module, auth, template_id, service_name, owner_id, group_id, permissions, custom_attrs, unique, wait, wait_timeout):
    if not service_name:
        service_name = ''
    changed = False
    service = None

    if unique:
        service = get_service_by_name(module, auth, service_name)

    if not service:
        if not module.check_mode:
            service = create_service(module, auth, template_id, service_name, custom_attrs, unique, wait, wait_timeout)
        changed = True

    # if check_mode=true and there would be changes, service doesn't exist and we can not get it
    if module.check_mode and changed:
        return {"changed": True}

    result = service_operation(module, auth, owner_id=owner_id, group_id=group_id, wait=wait,
                               wait_timeout=wait_timeout, permissions=permissions, service=service)

    if result["changed"]:
        changed = True

    result["changed"] = changed

    return result


def service_operation(module, auth, service_id=None, owner_id=None, group_id=None, permissions=None,
                      role=None, cardinality=None, force=None, wait=False, wait_timeout=None, service=None):

    changed = False

    if not service:
        service = get_service_by_id(module, auth, service_id)
    else:
        service_id = service["ID"]

    if not service:
        module.fail_json(msg="There is no service with id: " + str(service_id))

    if owner_id:
        if check_change_service_owner(module, service, owner_id):
            if not module.check_mode:
                change_service_owner(module, auth, service_id, owner_id)
            changed = True
    if group_id:
        if check_change_service_group(module, service, group_id):
            if not module.check_mode:
                change_service_group(module, auth, service_id, group_id)
            changed = True
    if permissions:
        if check_change_service_permissions(module, service, permissions):
            if not module.check_mode:
                change_service_permissions(module, auth, service_id, permissions)
            changed = True

    if role:
        if check_change_role_cardinality(module, service, role, cardinality):
            if not module.check_mode:
                change_role_cardinality(module, auth, service_id, role, cardinality, force)
            changed = True

    if wait and not module.check_mode:
        service = wait_for_service_to_become_ready(module, auth, service_id, wait_timeout)

    # if something has changed, fetch service info again
    if changed:
        service = get_service_by_id(module, auth, service_id)

    service_info = get_service_info(module, auth, service)
    service_info["changed"] = changed

    return service_info


def delete_service(module, auth, service_id):
    service = get_service_by_id(module, auth, service_id)
    if not service:
        return {"changed": False}

    service_info = get_service_info(module, auth, service)

    service_info["changed"] = True

    if module.check_mode:
        return service_info

    try:
        result = open_url(auth.url + '/service/' + str(service_id), method="DELETE", force_basic_auth=True, url_username=auth.user, url_password=auth.password)
    except Exception as e:
        module.fail_json(msg="Service deletion has failed. Error message: " + str(e))

    return service_info


def get_template_by_name(module, auth, template_name):
    return get_template(module, auth, lambda template: (template["NAME"] == template_name))


def get_template_by_id(module, auth, template_id):
    return get_template(module, auth, lambda template: (int(template["ID"]) == int(template_id))) if template_id else None


def get_template_id(module, auth, requested_id, requested_name):
    template = get_template_by_id(module, auth, requested_id) if requested_id else get_template_by_name(module, auth, requested_name)

    if template:
        return template["ID"]

    return None


def get_service_id_by_name(module, auth, service_name):
    service = get_service_by_name(module, auth, service_name)

    if service:
        return service["ID"]

    return None


def get_connection_info(module):

    url = module.params.get('api_url')
    username = module.params.get('api_username')
    password = module.params.get('api_password')

    if not url:
        url = os.environ.get('ONEFLOW_URL')

    if not username:
        username = os.environ.get('ONEFLOW_USERNAME')

    if not password:
        password = os.environ.get('ONEFLOW_PASSWORD')

    if not(url and username and password):
        module.fail_json(msg="One or more connection parameters (api_url, api_username, api_password) were not specified")
    from collections import namedtuple

    auth_params = namedtuple('auth', ('url', 'user', 'password'))

    return auth_params(url=url, user=username, password=password)


def main():
    fields = {
        "api_url": {"required": False, "type": "str"},
        "api_username": {"required": False, "type": "str"},
        "api_password": {"required": False, "type": "str", "no_log": True},
        "service_name": {"required": False, "type": "str"},
        "service_id": {"required": False, "type": "int"},
        "template_name": {"required": False, "type": "str"},
        "template_id": {"required": False, "type": "int"},
        "state": {
            "default": "present",
            "choices": ['present', 'absent'],
            "type": "str"
        },
        "mode": {"required": False, "type": "str"},
        "owner_id": {"required": False, "type": "int"},
        "group_id": {"required": False, "type": "int"},
        "unique": {"default": False, "type": "bool"},
        "wait": {"default": False, "type": "bool"},
        "wait_timeout": {"default": 300, "type": "int"},
        "custom_attrs": {"default": {}, "type": "dict"},
        "role": {"required": False, "type": "str"},
        "cardinality": {"required": False, "type": "int"},
        "force": {"default": False, "type": "bool"}
    }

    module = AnsibleModule(argument_spec=fields,
                           mutually_exclusive=[
                               ['template_id', 'template_name', 'service_id'],
                               ['service_id', 'service_name'],
                               ['template_id', 'template_name', 'role'],
                               ['template_id', 'template_name', 'cardinality'],
                               ['service_id', 'custom_attrs']
                           ],
                           required_together=[['role', 'cardinality']],
                           supports_check_mode=True)

    auth = get_connection_info(module)
    params = module.params
    service_name = params.get('service_name')
    service_id = params.get('service_id')

    requested_template_id = params.get('template_id')
    requested_template_name = params.get('template_name')
    state = params.get('state')
    permissions = params.get('mode')
    owner_id = params.get('owner_id')
    group_id = params.get('group_id')
    unique = params.get('unique')
    wait = params.get('wait')
    wait_timeout = params.get('wait_timeout')
    custom_attrs = params.get('custom_attrs')
    role = params.get('role')
    cardinality = params.get('cardinality')
    force = params.get('force')

    template_id = None

    if requested_template_id or requested_template_name:
        template_id = get_template_id(module, auth, requested_template_id, requested_template_name)
        if not template_id:
            if requested_template_id:
                module.fail_json(msg="There is no template with template_id: " + str(requested_template_id))
            elif requested_template_name:
                module.fail_json(msg="There is no template with name: " + requested_template_name)

    if unique and not service_name:
        module.fail_json(msg="You cannot use unique without passing service_name!")

    if template_id and state == 'absent':
        module.fail_json(msg="State absent is not valid for template")

    if template_id and state == 'present':  # Instantiate a service
        result = create_service_and_operation(module, auth, template_id, service_name, owner_id,
                                              group_id, permissions, custom_attrs, unique, wait, wait_timeout)
    else:
        if not (service_id or service_name):
            module.fail_json(msg="To manage the service at least the service id or service name should be specified!")
        if custom_attrs:
            module.fail_json(msg="You can only set custom_attrs when instantiate service!")

        if not service_id:
            service_id = get_service_id_by_name(module, auth, service_name)
        # The task should be failed when we want to manage a non-existent service identified by its name
        if not service_id and state == 'present':
            module.fail_json(msg="There is no service with name: " + service_name)

        if state == 'absent':
            result = delete_service(module, auth, service_id)
        else:
            result = service_operation(module, auth, service_id, owner_id, group_id, permissions, role, cardinality, force, wait, wait_timeout)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
