#!/usr/bin/python

# (C) Copyright 2018 Hewlett Packard Enterprise Development LP
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 3 of the GNU General Public License as
# published by the Free Software Foundation.  Alternatively, at your
# choice, you may also redistribute it and/or modify it under the terms
# of the Apache License, version 2.0, available at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <https://www.gnu.org/licenses/>


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
author: "Farhan Nomani (nomani@hpe.com)"
description: "On HPE 3PAR - Create QoS Rule. - Delete QoS Rule. - Modify QoS
 Rule."
module: hpe3par_qos
options:
  bwmax_limit_kb:
    default: -1
    description:
      - "Bandwidth rate maximum limit in kilobytes per second."
    required: false
  bwmax_limit_op:
    choices:
      - ZERO
      - NOLIMIT
    description:
      - "When set to 1, the bandwidth maximum limit is 0. When set to 2, the
       bandwidth maximum limit is none (NoLimit).\n"
    required: false
  bwmin_goal_kb:
    default: -1
    description:
      - "Bandwidth rate minimum goal in kilobytes per second."
    required: false
  bwmin_goal_op:
    choices:
      - ZERO
      - NOLIMIT
    description:
      - "When set to 1, the bandwidth minimum goal is 0. When set to 2, the
       bandwidth minimum goal is none (NoLimit).\n"
    required: false
  default_latency:
    default: false
    description:
      - "If true, set latencyGoal to the default value. If false and the
       latencyGoal value is positive, then set the value. Default is false.\n"
    required: false
    type: bool
  enable:
    default: false
    description:
      - "If true, enable the QoS rule for the target object. If false, disable
       the QoS rule for the target object.\n"
    required: false
    type: bool
  iomax_limit:
    default: -1
    description:
      - "I/O-per-second maximum limit."
    required: false
  iomax_limit_op:
    choices:
      - ZERO
      - NOLIMIT
    description:
      - "When set to 1, the I/O maximum limit is 0. When set to 2, the I/O
       maximum limit is none (NoLimit).\n"
    required: false
  iomin_goal:
    default: -1
    description:
      - "I/O-per-second minimum goal."
    required: false
  iomin_goal_op:
    choices:
      - ZERO
      - NOLIMIT
    description:
      - "When set to 1, the I/O minimum goal is 0. When set to 2, the I/O
       minimum goal is none (NoLimit).\n"
    required: false
  latency_goal:
    description:
      - "Latency goal in milliseconds. Do not use with latencyGoaluSecs."
    required: false
  latency_goal_usecs:
    description:
      - "Latency goal in microseconds. Do not use with latencyGoal."
    required: false
  priority:
    choices:
      - LOW
      - NORMAL
      - HIGH
    default: LOW
    description:
      - "QoS priority."
    required: false
  qos_target_name:
    description:
      - "The name of the target object on which the new QoS rules will be
       created."
    required: true
  state:
    choices:
      - present
      - absent
      - modify
    description:
      - "Whether the specified QoS Rule should exist or not. State also
       provides actions to modify QoS Rule\n"
    required: true
  type:
    choices:
      - vvset
      - sys
    description:
      - "Type of QoS target."
    required: false
extends_documentation_fragment: hpe3par
short_description: "Manage HPE 3PAR QoS Rules"
version_added: "2.4"
'''

EXAMPLES = r'''
    - name: Create QoS
      hpe3par_qos:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=present
        qos_target_name="{{ qos_target_name }}"
        priority='NORMAL'
        bwmin_goal_kb="{{ bwmin_goal_kb }}"
        bwmax_limit_kb="{{ bwmax_limit_kb }}"
        iomin_goal_op="{{ iomin_goal_op }}"
        default_latency="{{ default_latency }}"
        enable="{{ enable }}"
        bwmin_goal_op="{{ bwmin_goal_op }}"
        bwmax_limit_op="{{ bwmax_limit_op }}"
        latency_goal_usecs="{{ latency_goal_usecs }}"
        type="{{ type }}"
        iomax_limit_op="{{ iomax_limit_op }}"

    - name: Modify QoS
      hpe3par_qos:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=modify
        qos_target_name="{{ qos_target_name }}"
        priority="{{ priority }}"
        bwmin_goal_kb="{{ bwmin_goal_kb }}"
        bwmax_limit_kb="{{ bwmax_limit_kb }}"
        iomin_goal_op="{{ iomin_goal_op }}"
        default_latency="{{ default_latency }}"
        enable="{{ enable }}"
        bwmin_goal_op="{{ bwmin_goal_op }}"
        bwmax_limit_op="{{ bwmax_limit_op }}"
        latency_goal_usecs="{{ latency_goal_usecs }}"
        type="{{ type }}"
        iomax_limit_op="{{ iomax_limit_op }}"

    - name: Delete QoS
      hpe3par_qos:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=absent
        qos_target_name="{{ qos_target_name }}"
        type="{{ type }}"
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from hpe3par_sdk import client


def create_qos_rule(
        client_obj,
        storage_system_username,
        storage_system_password,
        qos_target_name,
        type,
        priority,
        bwmin_goal_kb,
        bwmax_limit_kb,
        iomin_goal,
        iomax_limit,
        bwmin_goal_op,
        bwmax_limit_op,
        iomin_goal_op,
        iomax_limit_op,
        latency_goal,
        default_latency,
        enable,
        latency_goal_usecs):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "QoS creation failed. Storage system username or password is null",
            {})
    if qos_target_name is None:
        return (
            False,
            False,
            "QoS creation failed. qos_target_name is null",
            {})
    if len(qos_target_name) < 1 or len(qos_target_name) > 31:
        return (False, False, "QoS create failed. QoS target name must be atleast 1 character and more than 31 characters", {})
    if latency_goal is not None and latency_goal_usecs is not None:
        return (
            False,
            False,
            "Attributes latency_goal and latency_goal_usecs cannot be given \
at the same time for qos rules creation",
            {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        if not client_obj.qosRuleExists(qos_target_name, type):
            qos_rules = construct_qos_rules_map(
                bwmin_goal_kb,
                bwmax_limit_kb,
                iomin_goal,
                iomax_limit,
                latency_goal,
                default_latency,
                enable,
                latency_goal_usecs,
                priority,
                bwmin_goal_op,
                bwmax_limit_op,
                iomin_goal_op,
                iomax_limit_op)

            client_obj.createQoSRules(
                qos_target_name,
                qos_rules,
                target_type=client.HPE3ParClient.VVSET)
        else:
            return (True, False, "QoS already present", {})
    except Exception as e:
        return (False, False, "QoS creation failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Created QoS successfully.", {})


def modify_qos_rule(
        client_obj,
        storage_system_username,
        storage_system_password,
        qos_target_name,
        type,
        priority,
        bwmin_goal_kb,
        bwmax_limit_kb,
        iomin_goal,
        iomax_limit,
        bwmin_goal_op,
        bwmax_limit_op,
        iomin_goal_op,
        iomax_limit_op,
        latency_goal,
        default_latency,
        enable,
        latency_goal_usecs):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "QoS modification failed. Storage system username or password is \
null",
            {})
    if qos_target_name is None:
        return (
            False,
            False,
            "QoS modification failed. qos_target_name is null",
            {})
    if len(qos_target_name) < 1 or len(qos_target_name) > 31:
        return (False, False, "QoS create failed. QoS target name must be atleast 1 character and more than 31 characters", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        qos_rules = construct_qos_rules_map(
            bwmin_goal_kb,
            bwmax_limit_kb,
            iomin_goal,
            iomax_limit,
            latency_goal,
            default_latency,
            enable,
            latency_goal_usecs,
            priority,
            bwmin_goal_op,
            bwmax_limit_op,
            iomin_goal_op,
            iomax_limit_op)
        client_obj.modifyQoSRules(qos_target_name, qos_rules, type)
    except Exception as e:
        return (False, False, "QoS modification failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Modified QoS successfully.", {})


def delete_qos_rule(
        client_obj,
        storage_system_username,
        storage_system_password,
        qos_target_name,
        type):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "QoS deletion failed. Storage system username or password is null",
            {})
    if qos_target_name is None:
        return (
            False,
            False,
            "QoS deletion failed. qos_target_name is null",
            {})
    if len(qos_target_name) < 1 or len(qos_target_name) > 31:
        return (False, False, "QoS create failed. QoS target name must be atleast 1 character and more than 31 characters", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        if client_obj.qosRuleExists(qos_target_name, type):
            client_obj.login(storage_system_username, storage_system_password)
            client_obj.deleteQoSRules(qos_target_name, type)
        else:
            return (True, False, "QoS does not exist", {})
    except Exception as e:
        return (False, False, "QoS delete failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Deleted QoS successfully.", {})


def construct_qos_rules_map(
        bwmin_goal_kb,
        bwmax_limit_kb,
        iomin_goal,
        iomax_limit,
        latency_goal,
        default_latency,
        enable,
        latency_goal_usecs,
        priority,
        bwmin_goal_op,
        bwmax_limit_op,
        iomin_goal_op,
        iomax_limit_op):
    qos_rules = {
        'bwMinGoalKB': bwmin_goal_kb,
        'bwMaxLimitKB': bwmax_limit_kb,
        'ioMinGoal': iomin_goal,
        'ioMaxLimit': iomax_limit,
        'latencyGoal': latency_goal,
        'defaultLatency': default_latency,
        'enable': enable,
        'latencyGoaluSecs': latency_goal_usecs
    }
    if priority is not None:
        qos_rules['priority'] = getattr(
            client.HPE3ParClient.QOSPriority, priority)

    if bwmin_goal_op is not None:
        qos_rules['bwMinGoalOP'] = getattr(client.HPE3ParClient, bwmin_goal_op)

    if bwmax_limit_op is not None:
        qos_rules['bwMaxLimitOP'] = getattr(
            client.HPE3ParClient, bwmax_limit_op)

    if iomin_goal_op is not None:
        qos_rules['ioMinGoalOP'] = getattr(client.HPE3ParClient, iomin_goal_op)

    if iomax_limit_op is not None:
        qos_rules['ioMaxLimitOP'] = getattr(
            client.HPE3ParClient, iomax_limit_op)
    return qos_rules


def main():

    fields = {
        "state": {
            "required": True,
            "choices": ['present', 'absent', 'modify'],
            "type": 'str'
        },
        "storage_system_ip": {
            "required": True,
            "type": "str"
        },
        "storage_system_username": {
            "required": True,
            "type": "str",
            "no_log": True
        },
        "storage_system_password": {
            "required": True,
            "type": "str",
            "no_log": True
        },
        "qos_target_name": {
            "required": True,
            "type": "str"
        },
        "type": {
            "choices": ['vvset', 'sys'],
            "type": "str"
        },
        "priority": {
            "choices": ['LOW', 'NORMAL', 'HIGH'],
            "default": 'LOW',
            "type": "str"
        },
        "bwmin_goal_kb": {
            "type": "int",
            "default": -1
        },
        "bwmax_limit_kb": {
            "type": "int",
            "default": -1
        },
        "iomin_goal": {
            "type": "int",
            "default": -1
        },
        "iomax_limit": {
            "type": "int",
            "default": -1
        },
        "bwmin_goal_op": {
            "type": "str",
            "choices": ['ZERO', 'NOLIMIT']
        },
        "bwmax_limit_op": {
            "type": "str",
            "choices": ['ZERO', 'NOLIMIT']
        },
        "iomin_goal_op": {
            "type": "str",
            "choices": ['ZERO', 'NOLIMIT']
        },
        "iomax_limit_op": {
            "type": "str",
            "choices": ['ZERO', 'NOLIMIT']
        },
        "latency_goal": {
            "type": "int"
        },
        "default_latency": {
            "type": "bool",
            "default": False
        },
        "enable": {
            "type": "bool",
            "default": False
        },
        "latency_goal_usecs": {
            "type": "int"
        }
    }
    module = AnsibleModule(argument_spec=fields)

    storage_system_ip = module.params["storage_system_ip"]
    storage_system_username = module.params["storage_system_username"]
    storage_system_password = module.params["storage_system_password"]

    qos_target_name = module.params["qos_target_name"]
    type = module.params["type"]
    priority = module.params["priority"]
    bwmin_goal_kb = module.params["bwmin_goal_kb"]
    bwmax_limit_kb = module.params["bwmax_limit_kb"]
    iomin_goal = module.params["iomin_goal"]
    iomax_limit = module.params["iomax_limit"]
    bwmin_goal_op = module.params["bwmin_goal_op"]
    bwmax_limit_op = module.params["bwmax_limit_op"]
    iomin_goal_op = module.params["iomin_goal_op"]
    iomax_limit_op = module.params["iomax_limit_op"]
    latency_goal = module.params["latency_goal"]
    default_latency = module.params["default_latency"]
    enable = module.params["enable"]
    latency_goal_usecs = module.params["latency_goal_usecs"]

    wsapi_url = 'https://%s:8080/api/v1' % storage_system_ip
    client_obj = client.HPE3ParClient(wsapi_url)

    # States
    if module.params["state"] == "present":
        return_status, changed, msg, issue_attr_dict = create_qos_rule(
            client_obj, storage_system_username, storage_system_password,
            qos_target_name, type, priority, bwmin_goal_kb,
            bwmax_limit_kb, iomin_goal, iomax_limit, bwmin_goal_op,
            bwmax_limit_op, iomin_goal_op, iomax_limit_op, latency_goal,
            default_latency, enable, latency_goal_usecs)
    elif module.params["state"] == "modify":
        return_status, changed, msg, issue_attr_dict = modify_qos_rule(
            client_obj, storage_system_username, storage_system_password,
            qos_target_name, type, priority, bwmin_goal_kb,
            bwmax_limit_kb, iomin_goal, iomax_limit, bwmin_goal_op,
            bwmax_limit_op, iomin_goal_op, iomax_limit_op, latency_goal,
            default_latency, enable, latency_goal_usecs)
    elif module.params["state"] == "absent":
        return_status, changed, msg, issue_attr_dict = delete_qos_rule(
            client_obj, storage_system_username, storage_system_password,
            qos_target_name, type)
    if return_status:
        if issue_attr_dict:
            module.exit_json(changed=changed, msg=msg, issue=issue_attr_dict)
        else:
            module.exit_json(changed=changed, msg=msg)
    else:
        module.fail_json(msg=msg)


if __name__ == '__main__':
    main()
