#!/usr/bin/python
# _*_ coding: utf-8 _*_

#
# Dell EMC OpenManage Ansible Modules
# Version 1.0
# Copyright (C) 2018 Dell Inc.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# All rights reserved. Dell, EMC, and other trademarks are trademarks of Dell Inc. or its subsidiaries.
# Other trademarks may be trademarks of their respective owners.
#


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: dellemc_import_server_config_profile
short_description: Import SCP from a network share or from a local file.
version_added: "2.7"
description:
    - Import a given Server Configuration Profile (SCP) file from a network share or from a local file.
options:
    idrac_ip:
        required: True
        description: iDRAC IP Address.
    idrac_user:
        required: True
        description: iDRAC username.
    idrac_pwd:
        required: True
        description: iDRAC user password.
    idrac_port:
        required: False
        description: iDRAC port.
        default: 443
    share_name:
        required: True
        description: Network share or a local path.
    share_user:
        required: False
        description: Network share user in the format 'user@domain' or 'domain\\user' if user is
            part of a domain else 'user'. This option is mandatory for CIFS Network Share.
    share_pwd:
        required: False
        description: Network share user password. This option is mandatory for CIFS Network Share.
    scp_file:
        required: True
        description: Server Configuration Profile file name.
    scp_components:
        required: False
        description:
            - If C(ALL),    this module will import all components configurations from SCP file.
            - If C(IDRAC),  this module will import iDRAC configuration from SCP file.
            - If C(BIOS),   this module will import BIOS configuration from SCP file.
            - If C(NIC),    this module will import NIC configuration from SCP file.
            - If C(RAID),   this module will import RAID configuration from SCP file.
        choices: ['ALL', 'IDRAC', 'BIOS', 'NIC', 'RAID']
        default: 'ALL'

    shutdown_type:
        required: False
        description:
            - If C(Graceful), it gracefully shuts down the server.
            - If C(Forced),  it forcefully shuts down the server.
            - If C(NoReboot), it does not reboot the server.
        choices: ['Graceful', 'Forced', 'NoReboot']
        default: 'Graceful'

    end_host_power_state:
        required: False
        description:
            - If C(On), End host power state is on.
            - If C(Off), End host power state is off.
        choices: ['On' ,'Off']
        default: 'On'

    job_wait:
        required:  True
        description: Whether to wait for job completion or not.
        type: bool

requirements:
    - "omsdk"
    - "python >= 2.7.5"
author: "Rajeev Arakkal (@rajeevarakkal)"

"""

EXAMPLES = """
---
- name: Import Server Configuration Profile
  dellemc_import_server_config_profile:
       idrac_ip:   "{{ idrac_ip }}"
       idrac_user: "{{ idrac_user }}"
       idrac_pwd:  "{{ idrac_pwd }}"
       share_name: "xx.xx.xx.xx:/share"
       share_user: "{{ share_user }}"
       share_pwd:  "{{ share_pwd }}"
       scp_file:   "scp_file.xml"
       scp_components: "ALL"
       job_wait: True
"""

RETURNS = """
dest:
    description: Imports SCP from a network share or from a local file.
    returned: success
    type: string
"""


from ansible.module_utils.dellemc_idrac import iDRACConnection
from ansible.module_utils.basic import AnsibleModule
from omsdk.sdkfile import file_share_manager
from omsdk.sdkcreds import UserCredentials
from omdrivers.enums.iDRAC.iDRACEnums import (SCPTargetEnum, EndHostPowerStateEnum,
                                              ShutdownTypeEnum)


def run_import_server_config_profile(idrac, module):
    """
    Import Server Configuration Profile from a network share

    Keyword arguments:
    idrac  -- iDRAC handle
    module -- Ansible module
    """
    msg = {}
    msg['changed'] = False
    msg['failed'] = False
    msg['msg'] = {}
    err = False

    try:
        myshare = file_share_manager.create_share_obj(
            share_path=module.params['share_name'] + "/" + module.params['scp_file'],
            creds=UserCredentials(module.params['share_user'],
                                  module.params['share_pwd']), isFolder=False, )
        # myshare.new_file(module.params['scp_file'])

        scp_components = SCPTargetEnum.ALL

        if module.params['scp_components'] == 'IDRAC':
            scp_components = SCPTargetEnum.IDRAC
        elif module.params['scp_components'] == 'BIOS':
            scp_components = SCPTargetEnum.BIOS
        elif module.params['scp_components'] == 'NIC':
            scp_components = SCPTargetEnum.NIC
        elif module.params['scp_components'] == 'RAID':
            scp_components = SCPTargetEnum.RAID
        job_wait = module.params['job_wait']

        end_host_power_state = EndHostPowerStateEnum.On
        if module.params['end_host_power_state'] == 'Off':
            end_host_power_state = EndHostPowerStateEnum.Off

        shutdown_type = ShutdownTypeEnum.Graceful
        if module.params['shutdown_type'] == 'Forced':
            shutdown_type = ShutdownTypeEnum.Forced
        elif module.params['shutdown_type'] == 'NoReboot':
            shutdown_type = ShutdownTypeEnum.NoReboot

        idrac.use_redfish = True
        msg['msg'] = idrac.config_mgr.scp_import(myshare,
                                                 target=scp_components, shutdown_type=shutdown_type,
                                                 end_host_power_state=end_host_power_state,
                                                 job_wait=job_wait)
        if "Status" in msg['msg']:
            if msg['msg']['Status'] == "Success":
                if module.params['job_wait'] is True:
                    msg['changed'] = True
                    if "Message" in msg['msg']:
                        if "No changes were applied" in msg['msg']['Message']:
                            msg['changed'] = False
            else:
                msg['failed'] = True

    except Exception as e:
        err = True
        msg['msg'] = "Error: %s" % str(e)
        msg['failed'] = True
    return msg, err


# Main
def main():
    module = AnsibleModule(
        argument_spec=dict(

            # iDRAC Credentials
            idrac_ip=dict(required=True, type='str'),
            idrac_user=dict(required=True, type='str'),
            idrac_pwd=dict(required=True, type='str', no_log=True),
            idrac_port=dict(required=False, default=443, type='int'),

            # Network File Share
            share_name=dict(required=True, type='str'),
            share_user=dict(required=False, type='str'),
            share_pwd=dict(required=False, type='str', no_log=True),
            scp_file=dict(required=True, type='str'),
            scp_components=dict(required=False,
                                choices=['ALL', 'IDRAC', 'BIOS', 'NIC', 'RAID'],
                                default='ALL'),
            shutdown_type=dict(required=False,
                               choices=['Graceful', 'Forced', 'NoReboot'],
                               default='Graceful'),
            end_host_power_state=dict(required=False,
                                      choices=['On', 'Off'],
                                      default='On'),
            job_wait=dict(required=True, type='bool')
        ),

        supports_check_mode=False)
    # Connect to iDRAC
    idrac_conn = iDRACConnection(module)
    idrac = idrac_conn.connect()
    msg, err = run_import_server_config_profile(idrac, module)

    # Disconnect from iDRAC
    idrac_conn.disconnect()

    if err:
        module.fail_json(**msg)
    module.exit_json(**msg)


if __name__ == '__main__':
    main()
