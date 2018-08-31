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
from ansible.module_utils.remote_management.lxca_common import LXCAModuleBase
from pylxca import updatecomp
from pylxca import updatepolicy


class UpdatecompModule(LXCAModuleBase):
    '''
    This class fetch information about updatecomp in lxca
    '''

    SUCCESS_MSG = "Success %s result"

    def __init__(self):
        self.func_dict = {
            'update_firmware': self._update_firmware,
            'update_firmware_all': self._update_firmware_all,
            'update_firmware_query_status': self._update_firmware_query_status,
            'update_firmware_query_comp': self._update_firmware_query_comp,
        }
        args_spec = dict(
            command_options=dict(default=None, choices=list(self.func_dict)),
            lxca_action=dict(default=None, choices=['apply', 'cancelApply', 'power', None]),
            mode=dict(default=None, choices=[None, 'immediate', 'delayed']),
            server=dict(default=None),
            storage=dict(default=None),
            switch=dict(default=None),
            cmm=dict(default=None),
            uuid_list=dict(default=None, type=('list')),
        )
        super(UpdatecompModule, self).__init__(input_args_spec=args_spec)
        self._changed = False

    def execute_module(self):
        try:
            result = self.func_dict[self.module.params['command_options']]()
            return dict(changed=self._changed,
                        msg=self.SUCCESS_MSG % self.module.params['command_options'],
                        result=result)
        except Exception as exception:
            error_msg = '; '.join((e) for e in exception.args)
            self.module.fail_json(msg=error_msg, exception=traceback.format_exc())

    def _update_firmware(self):
        result = updatecomp(self.lxca_con,
                            self.module.params['mode'],
                            self.module.params['lxca_action'],
                            self.module.params['cmms'],
                            self.module.params['switch'],
                            self.module.params['server'],
                            self.module.params['storage'],)

        self._changed = True
        return result

    def _update_firmware_query_status(self):
        result = updatecomp(self.lxca_con, query="status")
        return result

    def _update_firmware_query_comp(self):
        result = updatecomp(self.lxca_con, query="components")
        return result

    def _transform_devicelist(self, devicelist, uuid_list):
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

    def _valid_compliance_policies(self, policy_list):
        uuid_list = []
        for comp_policy in policy_list:
            if 'uuid' in comp_policy.keys():
                if 'currentPolicy' in comp_policy.keys() and len(comp_policy['currentPolicy']) > 0:
                    uuid_list.append(comp_policy['uuid'])

        return uuid_list

    def _update_firmware_all(self):
        result = None
        try:
            rep = updatepolicy(self.lxca_con, info="NAMELIST")
            uuid_list = self._valid_compliance_policies(rep['policies'])
            if len(uuid_list) == 0:
                self.module.fail_json(msg="No policy assigned to any device")
                return result

            dev_uuid_list = []
            if 'uuid_list' in self.module.params:
                dev_uuid_list = self.module.params.get('uuid_list')
                if len(dev_uuid_list) > 0:
                    # getting common uuid of two list
                    uuid_list = list(set(dev_uuid_list).intersection(uuid_list))

            rep = updatecomp(self.lxca_con, query='components')
            ret_dev_list = rep['DeviceList']
            mod_dev_list = self._transform_devicelist(ret_dev_list, uuid_list)
            if len(mod_dev_list) == 0:
                self.module.fail_json(
                    msg="No updateable component with assigned policy found")
                return result

            result = updatecomp(self.lxca_con, mode=self.module.params.get(
                'mode'), action=self.module.params.get('lxca_action'), dev_list=mod_dev_list)
            self._changed = True
        except Exception as err:
            self.module.fail_json(msg="Error updating all device firmware " + str(err))
        return result


def main():
    UpdatecompModule().run()


if __name__ == '__main__':
    main()
