#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'supported_by': 'community',
    'status': ['preview']
}


DOCUMENTATION = '''
---
version_added: "1.1"
author:
  - Naval Patel (@navalkp)
  - Prashant Bhosale (@prabhosa)
module: lxca_updatecomp
short_description: Custom module for lxca update components config utility
description:
  - This module update firmware of components on LXCA

options:

  lxca_action:
    description:
    - action performed on lxca, Used with following commands with option for lxca_action
        - "update_firmware, update_all_firmware_withpolicy
            (apply  Applies the associated firmware to the submitted components.
            power  Perform power action on selected endpoint.
            cancelApply Cancels the firmware update request to the selected components.)"
    choices:
      - None
      - apply
      - power
      - cancelApply

  mode:
    description:
      - "used with command update_firmware, update_all_firmware_withpolicy
        Indicates when to activate the update. This can be one of the following values."
      - "immediate - Uses Immediate Activaton mode when applying firmware updates to
                               the selected endpoints."
      - "delayed - Uses Delayed Activaton mode when applying firmware updates to the
                               selected endpoints."

    choices:
      - immediate
      - delayed
      - None

  server:
    description:
      - used with command update_firmware
      - "string of format uuid,mt or uuid,fixids,mt
                fixid: lnvgy_fw_imm2_tcoo15m-2.50_anyos_noarch
                Component name
                name: IMM2 (Backup)"

      - "Example '7C5E041E3CCA11E18B715CF3FC112D8A,IMM2 (Backup)' or
                '7C5E041E3CCA11E18B715CF3FC112D8A,lnvgy_fw_imm2_tcoo15m-2.50_anyos_noarch,IMM2 (Backup)'"

  storage:
    description:
      - used with command update_firmware
      - "string of format uuid,mt or uuid,fixids,mt
                fixid: lnvgy_fw_imm2_tcoo15m-2.50_anyos_noarch
                Component name
                name: IMM2 (Backup)"

      - "Example '7C5E041E3CCA11E18B715CF3FC112D8A,IMM2 (Backup)' or
                '7C5E041E3CCA11E18B715CF3FC112D8A,lnvgy_fw_imm2_tcoo15m-2.50_anyos_noarch,IMM2 (Backup)'"

  cmm:
    description:
      - used with command update_firmware
      - "string of format uuid,mt or uuid,fixids,mt
                fixid: lnvgy_fw_imm2_tcoo15m-2.50_anyos_noarch
                Component name
                name: IMM2 (Backup)"

      - "Example '7C5E041E3CCA11E18B715CF3FC112D8A,IMM2 (Backup)' or
                '7C5E041E3CCA11E18B715CF3FC112D8A,lnvgy_fw_imm2_tcoo15m-2.50_anyos_noarch,IMM2 (Backup)'"

  switch:
    description:
      - used with command update_firmware
      - "string of format uuid,mt or uuid,fixids,mt
                fixid: lnvgy_fw_imm2_tcoo15m-2.50_anyos_noarch
                Component name
                name: IMM2 (Backup)"

      - "Example '7C5E041E3CCA11E18B715CF3FC112D8A,IMM2 (Backup)' or
                '7C5E041E3CCA11E18B715CF3FC112D8A,lnvgy_fw_imm2_tcoo15m-2.50_anyos_noarch,IMM2 (Backup)'"

  uuid_list:
    description:
      - used with command update_all_firmware_withpolicy. Apply firmware to uuid in list
      - "example ['38D9D7DBCB713C12A210E60C74A0E931','00000000000010008000542AA2D3CB00']"

  command_options:
    description:
      options to perform updatecomp operation
    required: True
    choices:
      - update_firmware
      - update_firmware_all
      - update_firmware_query_status
      - update_firmware_query_comp

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = r'''
# Query Updatable components from LXCA
- name: get all updatable components
  lxca_updatecomp:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    command_options: update_firmware_query_comp

# Query Firmware Update Status
- name: get status of firmware update
  lxca_updatecomp:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    command_options: update_firmware_query_status

# apply firmware on given deivce
- name: Firmware update on given UUID
  lxca_updatecomp:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: apply
    mode: immediate
    server: '7C5E041E3CCA11E18B715CF3FC112D8A,IMM2 (Primary)'
    command_options: update_firmware

# Apply firmware update on list of UUID with compliance policy assigned
- name: apply firmware update to list of UUID
  lxca_updatecomp:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: apply
    mode: immediate
    uuid_list: ['38D9D7DBCB713C12A210E60C74A0E931','00000000000010008000542AA2D3CB00']
    command_options: update_firmware_all

# Apply firmware update on all updatable components with compliance policy assigned
# uuid_list will be empty
- name: apply firmware update on all updatalbe components
  lxca_updatecomp:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: apply
    mode: immediate
    uuid_list: []
    command_options: update_firmware_all


'''

import traceback
from ansible.module_utils.basic import AnsibleModule
from pylxca import connect
from pylxca import disconnect
from pylxca import updatecomp
from pylxca import updatepolicy

SUCCESS_MSG = "Success %s result"
__changed__ = False


def _update_firmware(module, lxca_con):
    global __changed__
    result = updatecomp(lxca_con,
                        module.params['mode'],
                        module.params['lxca_action'],
                        module.params['cmms'],
                        module.params['switch'],
                        module.params['server'],
                        module.params['storage'],)

    __changed__ = True
    return result


def _update_firmware_query_status(module, lxca_con):
    result = updatecomp(lxca_con, query="status")
    return result


def _update_firmware_query_comp(module, lxca_con):
    result = updatecomp(lxca_con, query="components")
    return result


def _transform_devicelist(devicelist, uuid_list):
    ret_device_list = []
    for dev in devicelist:
        new_dict = {}
        for dev_type in dev.keys():  # SwitchList
            new_list = []
            for sw_dev in dev[dev_type]:
                if not sw_dev['UUID'] in uuid_list:
                    continue
                cm_list = []
                for cm_dev in sw_dev['Components']:
                    cm_list.append({'Component': cm_dev})
                sw_dev['Components'] = cm_list
                new_list.append(sw_dev)
            if len(new_list) > 0:
                new_dict[dev_type] = new_list
        if len(new_dict) > 0:
            ret_device_list.append(new_dict)
    return ret_device_list


def _valid_compliance_policies(policy_list):
    uuid_list = []
    for comp_policy in policy_list:
        if 'uuid' in comp_policy.keys():
            if 'currentPolicy' in comp_policy.keys() and len(comp_policy['currentPolicy']) > 0:
                uuid_list.append(comp_policy['uuid'])

    return uuid_list


def _update_firmware_all(module, lxca_con):
    global __changed__
    result = None
    try:
        rep = updatepolicy(lxca_con, info="NAMELIST")
        uuid_list = _valid_compliance_policies(rep['policies'])
        if len(uuid_list) == 0:
            module.fail_json(msg="No policy assigned to any device")
            return result

        dev_uuid_list = []
        if 'uuid_list' in module.params:
            dev_uuid_list = module.params.get('uuid_list')
            if len(dev_uuid_list) > 0:
                # getting common uuid of two list
                uuid_list = list(set(dev_uuid_list).intersection(uuid_list))

        rep = updatecomp(lxca_con, query='components')
        ret_dev_list = rep['DeviceList']
        mod_dev_list = _transform_devicelist(ret_dev_list, uuid_list)
        if len(mod_dev_list) == 0:
            module.fail_json(
                msg="No updateable component with assigned policy found")
            return result

        result = updatecomp(lxca_con, mode=module.params.get(
            'mode'), action=module.params.get('lxca_action'), dev_list=mod_dev_list)
        __changed__ = True
    except Exception as err:
        module.fail_json(msg="Error updating all device firmware " + str(err))
    return result


def setup_module_object():
    """
    this function merge argument spec and create ansible module object
    :return:
    """
    args_spec = dict(LXCA_COMMON_ARGS)
    args_spec.update(INPUT_ARG_SPEC)
    module = AnsibleModule(argument_spec=args_spec, supports_check_mode=False)

    return module


def setup_conn(module):
    """
    this function create connection to LXCA
    :param module:
    :return:  lxca connection
    """
    lxca_con = None
    try:
        lxca_con = connect(module.params['auth_url'],
                           module.params['login_user'],
                           module.params['login_password'],
                           module.params['noverify'], )
    except Exception as exception:
        error_msg = '; '.join((e) for e in exception.args)
        module.fail_json(msg=error_msg, exception=traceback.format_exc())
    return lxca_con


def validate_parameters(module):
    """
    validate parameters mostly it will be place holder
    :param module:
    """
    pass


FUNC_DICT = {
    'update_firmware': _update_firmware,
    'update_firmware_all': _update_firmware_all,
    'update_firmware_query_status': _update_firmware_query_status,
    'update_firmware_query_comp': _update_firmware_query_comp,
}


LXCA_COMMON_ARGS = dict(
    login_user=dict(required=True),
    login_password=dict(required=True, no_log=True),
    auth_url=dict(required=True),
    noverify=dict(default=True)
)


INPUT_ARG_SPEC = dict(
    command_options=dict(default=None, choices=['update_firmware',
                                                'update_firmware_all',
                                                'update_firmware_query_status',
                                                'update_firmware_query_comp']),
    lxca_action=dict(default=None, choices=['apply', 'cancelApply', 'power', None]),
    mode=dict(default=None, choices=[None, 'immediate', 'delayed']),
    server=dict(default=None),
    storage=dict(default=None),
    switch=dict(default=None),
    cmm=dict(default=None),
    uuid_list=dict(default=None, type=('list')),
)


def execute_module(module, lxca_con):
    """
    This function invoke commands
    :param module: Ansible module object
    :param lxca_con:  lxca connection object
    """
    try:
        result = FUNC_DICT[module.params['command_options']](module, lxca_con)
        disconnect(lxca_con)
        module.exit_json(changed=__changed__,
                         msg=SUCCESS_MSG % module.params['command_options'],
                         result=result)
    except Exception as exception:
        error_msg = '; '.join((e) for e in exception.args)
        disconnect(lxca_con)
        module.fail_json(msg=error_msg, exception=traceback.format_exc())


def run_tasks(module, lxca_con):
    """

    :param module: Ansible module object
    :param lxca_con:  lxca connection object
    """
    execute_module(module, lxca_con)


def main():
    module = setup_module_object()
    validate_parameters(module)
    lxca_con = setup_conn(module)
    run_tasks(module, lxca_con)


if __name__ == '__main__':
    main()
