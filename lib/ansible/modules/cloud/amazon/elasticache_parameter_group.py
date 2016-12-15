#!/usr/bin/python
# -*- coding: utf-8 -*-
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

DOCUMENTATION = """
---
module: elasticache_parameter_group
short_description: Manage elasticache parameter group
description:
  - Manage elasticache parameter group
  - Has the capabilities to create/destroy parameter group
version_added: "2.2"
author: "Aditya Kurniawan (@akurniawan)"
options:
  pg_family:
    description:
      - Family type for parameter groupo
    required: false
    choices: ['memcached1.4', 'redis2.6', 'redis2.8', 'redis3.2']
  pg_desc:
    description:
      - Description for parameter group
    required: false
    default: False
  pg_name:
    description:
      - Name for parameter groupo
    required: false
  pg_params:
    description:
      - List of parameters for elasticacheh parameter group (see example)
    required: True
  state:
    description:
      - Use C(present) to create and modify the cluster
      - or node inside the cluster
      - Use C(absent) to destroy the cluster or node inside the cluster
      - Use C(reboot) to reboot the cluster or node inside the cluster
    required: true
"""

EXAMPLES = """
- elasticache_parameter_group:
    state: "present"
    pg_name: "testing-pg"
    pg_desc: "testing parameter group"
    pg_family: "memcached1.4"
    pg_params:
      lru_maintainer: 1

- elasticache_parameter_group:
    state: "absent"
    pg_name: "testing-pg"
"""

try:
    import boto3
    import botocore
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

"""
Helper functions
"""


def get_es_client(params):
    """Get elasticache client"""
    session = boto3.Session(aws_access_key_id=params["aws_access_key"],
                            aws_secret_access_key=params["aws_secret_key"],
                            profile_name=params["profile"],
                            region_name=params["region"])
    cache = session.client("elasticache")

    return cache


def get_current_pg(es_client, module):
    """Check whether the cache cluster is already exist"""
    try:
        response = es_client.describe_cache_parameter_groups(
            CacheParameterGroupName=module.params.get("pg_name"))
        result = response["CacheParameterGroups"][0]
    except botocore.exceptions.ClientError as e:
        if "CacheParameterGroupNotFound" in e.message:
            result = None
        else:
            module.fail_json(msg=e.message)

    return result


def get_current_pg_params(es_client, module):
    """Get the current parameter group params, only the global
    params returned"""
    try:
        response = es_client.describe_cache_parameters(
            CacheParameterGroupName=module.params.get("pg_name"))
        param = response["Parameters"]
    except botocore.exceptions.ClientError as e:
        if "CacheParameterGroupNotFound" in e.message:
            param = None
        else:
            module.fail_json(msg=e.message)

    return param


def is_params_diff(before_params, after_params):
    """Check the difference between previous pg params and after
    changed params"""
    for bp in before_params:
        before_name = bp["ParameterName"]
        before_value = bp["ParameterValue"]
        if before_name in after_params:
            if str(before_value) != str(after_params[before_name]):
                return True
    return False


def convert_params_format(params):
    result = []
    for k, v in list(params.items()):
        result.append({
            "ParameterName": str(k),
            "ParameterValue": str(v)
        })

    return result


"""
Elasticache parameter groups module functionality
"""


def upsert_elasticache_pg(es_client, existing_pg, module):

    try:
        response = existing_pg
        changed = False
        if not existing_pg:
            response = es_client.create_cache_parameter_group(
                CacheParameterGroupName=module.params.get("pg_name"),
                CacheParameterGroupFamily=module.params.get("pg_family"),
                Description=module.params.get("pg_desc")
            )["CacheParameterGroup"]
            changed = True

        is_param_changes = False
        if module.params.get("pg_params"):
            response["params"] = get_current_pg_params(es_client, module)
            is_param_changes = is_params_diff(
                    response["params"], module.params.get("pg_params"))
            response = es_client.modify_cache_parameter_group(
                CacheParameterGroupName=module.params.get("pg_name"),
                ParameterNameValues=convert_params_format(
                    module.params.get("pg_params"))
            )
            if is_param_changes:
                changed = True
            response["params"] = dict([
                    (x["ParameterName"], x["ParameterValue"])
                    for x in get_current_pg_params(es_client, module)])
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=e.message)

    return response, changed


def remove_elasticache_pg(es_client, existing_pg, module):

    try:
        if existing_pg:
            response = es_client.delete_cache_parameter_group(
                CacheParameterGroupName=module.params.get("pg_name")
            )
            changed = True
        else:
            response = "Parameter Group doesn't exist, not doing anything"
            changed = False
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=e.message)

    return response, changed


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        pg_name=dict(required=True),
        pg_desc=dict(),
        pg_family=dict(choices=[
            "memcached1.4", "redis2.6", "redis2.8", "redis3.2"]),
        pg_params=dict(type="dict"),
        state=dict(required=True, choices=["absent", "present"])))

    module = AnsibleModule(
        argument_spec=argument_spec
    )

    if not HAS_BOTO:
        module.fail_json(msg="boto3 required for this module")

    state = module.params.get("state")
    es_client = get_es_client(module.params)
    existing_pg = get_current_pg(es_client, module)

    if state == "absent":
        response, changed = remove_elasticache_pg(
            es_client, existing_pg, module)
    elif state == "present":
        response, changed = upsert_elasticache_pg(
            es_client, existing_pg, module)

    if changed:
        module.exit_json(changed=True, parameter_groups=response)
    else:
        module.exit_json(changed=False, parameter_groups=response)

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == "__main__":
    main()
