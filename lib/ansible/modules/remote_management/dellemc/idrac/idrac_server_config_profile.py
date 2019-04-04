#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# Dell EMC OpenManage Ansible Modules
# Version 1.3
# Copyright (C) 2019 Dell Inc.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# All rights reserved. Dell, EMC, and other trademarks are trademarks of Dell Inc. or its subsidiaries.
# Other trademarks may be trademarks of their respective owners.
#


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: idrac_server_config_profile
short_description: Export or Import iDRAC Server Configuration Profile (SCP).
version_added: "2.8"
description:
  - Export the Server Configuration Profile (SCP) from the iDRAC or Import from a network share or a local file.
options:
  idrac_ip:
    description: iDRAC IP Address.
    type: str
    required: True
  idrac_user:
    description: iDRAC username.
    type: str
    required: True
  idrac_password:
    description: iDRAC user password.
    type: str
    required: True
  idrac_port:
    description: iDRAC port.
    type: int
    default: 443
  command:
    description:
      - If C(import), will perform SCP import operations.
      - If C(export), will perform SCP export operations.
    choices: ['import', 'export']
    default: 'export'
  job_wait:
    description: Whether to wait for job completion or not.
    type: bool
    required: True
  share_name:
    description: CIFS or NFS Network Share or a local path.
    type: str
    required: True
  share_user:
    description: Network share user in the format 'user@domain' or 'domain\\user' if user is
      part of a domain else 'user'. This option is mandatory for CIFS Network Share.
    type: str
  share_password:
    description: Network share user password. This option is mandatory for CIFS Network Share.
    type: str
  scp_file:
    description: Server Configuration Profile file name. This option is mandatory for C(import) command.
    type: str
  scp_components:
    description:
      - If C(ALL), this module will import all components configurations from SCP file.
      - If C(IDRAC), this module will import iDRAC configuration from SCP file.
      - If C(BIOS), this module will import BIOS configuration from SCP file.
      - If C(NIC), this module will import NIC configuration from SCP file.
      - If C(RAID), this module will import RAID configuration from SCP file.
    choices: ['ALL', 'IDRAC', 'BIOS', 'NIC', 'RAID']
    default: 'ALL'
  shutdown_type:
    description:
      - This option is applicable for C(import) command.
      - If C(Graceful), it gracefully shuts down the server.
      - If C(Forced),  it forcefully shuts down the server.
      - If C(NoReboot), it does not reboot the server.
    choices: ['Graceful', 'Forced', 'NoReboot']
    default: 'Graceful'
  end_host_power_state:
    description:
      - This option is applicable for C(import) command.
      - If C(On), End host power state is on.
      - If C(Off), End host power state is off.
    choices: ['On' ,'Off']
    default: 'On'
  export_format:
    description: Specify the output file format. This option is applicable for C(export) command.
    choices: ['JSON',  'XML']
    default: 'XML'
  export_use:
    description: Specify the type of server configuration profile (SCP) to be exported.
      This option is applicable for C(export) command.
    choices: ['Default',  'Clone', 'Replace']
    default: 'Default'

requirements:
  - "omsdk"
  - "python >= 2.7.5"
author: "Jagadeesh N V(@jagadeeshnv)"

'''

EXAMPLES = r'''
---
- name: Import Server Configuration Profile from a network share
  idrac_server_config_profile:
    idrac_ip: "192.168.0.1"
    idrac_user: "user_name"
    idrac_password: "user_password"
    command: "import"
    share_name: "192.168.0.2:/share"
    share_user: "share_user_name"
    share_password: "share_user_password"
    scp_file: "scp_filename.xml"
    scp_components: "ALL"
    job_wait: True

- name: Import Server Configuration Profile from a local path
  idrac_server_config_profile:
    idrac_ip: "192.168.0.1"
    idrac_user: "user_name"
    idrac_password: "user_password"
    command: "import"
    share_name: "/scp_folder"
    share_user: "share_user_name"
    share_password: "share_user_password"
    scp_file: "scp_filename.xml"
    scp_components: "ALL"
    job_wait: True

- name: Export Server Configuration Profile to a network share
  idrac_server_config_profile:
    idrac_ip: "192.168.0.1"
    idrac_user: "user_name"
    idrac_password: "user_password"
    share_name: "192.168.0.2:/share"
    share_user: "share_user_name"
    share_password: "share_user_password"
    job_wait: False

- name: Export Server Configuration Profile to a local path
  idrac_server_config_profile:
    idrac_ip: "192.168.0.1"
    idrac_user: "user_name"
    idrac_password: "user_password"
    share_name: "/scp_folder"
    share_user: "share_user_name"
    share_password: "share_user_password"
    job_wait: False
'''

RETURN = r'''
---
msg:
  type: str
  description: Status of the import or export SCP job.
  returned: always
  sample: "Successfully imported the Server Configuration Profile"
scp_status:
  type: dict
  description: SCP operation job and progress details from the iDRAC.
  returned: success
  sample:
    {
      "Id": "JID_XXXXXXXXX",
      "JobState": "Completed",
      "JobType": "ImportConfiguration",
      "Message": "Successfully imported and applied Server Configuration Profile.",
      "MessageArgs": [],
      "MessageId": "XXX123",
      "Name": "Import Configuration",
      "PercentComplete": 100,
      "StartTime": "TIME_NOW",
      "Status": "Success",
      "TargetSettingsURI": null,
      "retval": true
    }
'''

import os
from ansible.module_utils.remote_management.dellemc.dellemc_idrac import iDRACConnection
from ansible.module_utils.basic import AnsibleModule
try:
    from omsdk.sdkfile import file_share_manager
    from omsdk.sdkcreds import UserCredentials
    from omdrivers.enums.iDRAC.iDRACEnums import (SCPTargetEnum, EndHostPowerStateEnum,
                                                  ShutdownTypeEnum, ExportFormatEnum, ExportUseEnum)
except ImportError:
    pass


def run_import_server_config_profile(idrac, module):
    """Import Server Configuration Profile from a network share."""
    target = SCPTargetEnum[module.params['scp_components']]
    job_wait = module.params['job_wait']
    end_host_power_state = EndHostPowerStateEnum[module.params['end_host_power_state']]
    shutdown_type = ShutdownTypeEnum[module.params['shutdown_type']]
    idrac.use_redfish = True

    try:
        myshare = file_share_manager.create_share_obj(
            share_path="{0}{1}{2}".format(module.params['share_name'], os.sep, module.params['scp_file']),
            creds=UserCredentials(module.params['share_user'],
                                  module.params['share_password']), isFolder=False)
        import_status = idrac.config_mgr.scp_import(myshare,
                                                    target=target, shutdown_type=shutdown_type,
                                                    end_host_power_state=end_host_power_state,
                                                    job_wait=job_wait)
        if not import_status or import_status.get('Status') != "Success":
            module.fail_json(msg='Failed to import scp.', scp_status=import_status)
    except RuntimeError as e:
        module.fail_json(msg=str(e))
    return import_status


def run_export_server_config_profile(idrac, module):
    """Export Server Configuration Profile to a network share."""
    export_format = ExportFormatEnum[module.params['export_format']]
    scp_file_name_format = "%ip_%Y%m%d_%H%M%S_scp.{0}".format(module.params['export_format'].lower())
    target = SCPTargetEnum[module.params['scp_components']]
    export_use = ExportUseEnum[module.params['export_use']]
    idrac.use_redfish = True

    try:
        myshare = file_share_manager.create_share_obj(share_path=module.params['share_name'],
                                                      creds=UserCredentials(module.params['share_user'],
                                                                            module.params['share_password']),
                                                      isFolder=True)
        scp_file_name = myshare.new_file(scp_file_name_format)
        export_status = idrac.config_mgr.scp_export(scp_file_name,
                                                    target=target,
                                                    export_format=export_format,
                                                    export_use=export_use,
                                                    job_wait=module.params['job_wait'])
        if not export_status or export_status.get('Status') != "Success":
            module.fail_json(msg='Failed to export scp.', scp_status=export_status)
    except RuntimeError as e:
        module.fail_json(msg=str(e))
    return export_status


def main():
    module = AnsibleModule(
        argument_spec={
            "idrac_ip": {"required": True, "type": 'str'},
            "idrac_user": {"required": True, "type": 'str'},
            "idrac_password": {"required": True, "type": 'str', "no_log": True},
            "idrac_port": {"required": False, "default": 443, "type": 'int'},

            "command": {"required": False, "type": 'str',
                        "choices": ['export', 'import'], "default": 'export'},
            "job_wait": {"required": True, "type": 'bool'},

            "share_name": {"required": True, "type": 'str'},
            "share_user": {"required": False, "type": 'str'},
            "share_password": {"required": False, "type": 'str', "no_log": True},
            "scp_components": {"required": False,
                               "choices": ['ALL', 'IDRAC', 'BIOS', 'NIC', 'RAID'],
                               "default": 'ALL'},

            "scp_file": {"required": False, "type": 'str'},
            "shutdown_type": {"required": False,
                              "choices": ['Graceful', 'Forced', 'NoReboot'],
                              "default": 'Graceful'},
            "end_host_power_state": {"required": False,
                                     "choices": ['On', 'Off'],
                                     "default": 'On'},

            "export_format": {"required": False, "type": 'str',
                              "choices": ['JSON', 'XML'], "default": 'XML'},
            "export_use": {"required": False, "type": 'str',
                           "choices": ['Default', 'Clone', 'Replace'], "default": 'Default'}
        },
        required_if=[
            ["command", "import", ["scp_file"]]
        ],
        supports_check_mode=False)

    try:
        changed = False
        with iDRACConnection(module.params) as idrac:
            command = module.params['command']
            if command == 'import':
                scp_status = run_import_server_config_profile(idrac, module)
                if "No changes were applied" not in scp_status.get('Message', ""):
                    changed = True
            else:
                scp_status = run_export_server_config_profile(idrac, module)
        module.exit_json(changed=changed, msg="Successfully {0}ed the Server Configuration Profile.".format(command),
                         scp_status=scp_status)
    except (ImportError, ValueError, RuntimeError) as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
