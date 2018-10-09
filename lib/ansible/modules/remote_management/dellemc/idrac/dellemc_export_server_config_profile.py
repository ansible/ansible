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
module: dellemc_export_server_config_profile
short_description: Export Server Configuration Profile (SCP) to a network share or to a local file.
version_added: "2.7"
description:
    - Export Server Configuration Profile.
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
    scp_components:
        required: False
        description: Specify the hardware component(s) configuration to be exported.
            - If C(ALL), the module will export all components configurations in SCP file.
            - If C(IDRAC),  the module will export iDRAC configuration in SCP file.
            - If C(BIOS),  the module will export BIOS configuration in SCP file.
            - If C(NIC),  the module will export NIC configuration in SCP file.
            - If C(RAID),  the module will export RAID configuration in SCP file.
        choices: ['ALL', 'IDRAC', 'BIOS', 'NIC', 'RAID']
        default: 'ALL'
    job_wait:
        required:  True
        description: Whether to wait for job completion or not.
        type: bool
    export_format:
        required:  False
        description: Specify the output file format.
        choices: ['JSON',  'XML']
        default: 'XML'
    export_use:
        required:  False
        description: Specify the type of server configuration profile (SCP) to be exported.
        choices: ['Default',  'Clone', 'Replace']
        default: 'Default'

requirements:
    - "omsdk"
    - "python >= 2.7.5"
author: "Rajeev Arakkal (@rajeevarakkal)"

"""

EXAMPLES = """
---
- name: Export Server Configuration Profile (SCP)
  dellemc_export_server_config_profile:
       idrac_ip:   "{{ idrac_ip }}"
       idrac_user: "{{ idrac_user }}"
       idrac_pwd:  "{{ idrac_pwd }}"
       share_name: "xx.xx.xx.xx:/share"
       share_pwd:  "{{ share_pwd }}"
       share_user: "{{ share_user }}"
       job_wait: True
       export_format:  "XML"
       export_use:     "Default"
"""

RETURNS = """
dest:
    description: Exports the server configuration profile to the provided network share or to the local path.
    returned: success
    type: string
    sample: /path/to/file.xml
"""


from ansible.module_utils.dellemc_idrac import iDRACConnection
from ansible.module_utils.basic import AnsibleModule
from omsdk.sdkfile import file_share_manager
from omsdk.sdkcreds import UserCredentials


def run_export_server_config_profile(idrac, module):
    """
    Export Server Configuration Profile to a network share

    Keyword arguments:
    idrac  -- iDRAC handle
    module -- Ansible module
    """
    from omdrivers.enums.iDRAC.iDRACEnums import SCPTargetEnum, ExportFormatEnum, ExportUseEnum

    msg = {}
    msg['changed'] = False
    msg['failed'] = False
    err = False

    try:
        if module.params['export_format'].lower() == 'JSON'.lower():
            export_format = ExportFormatEnum.JSON
            scp_file_name_format = "%ip_%Y%m%d_%H%M%S_scp.json"
        elif module.params['export_format'].lower() == 'XML'.lower():
            export_format = ExportFormatEnum.XML
            scp_file_name_format = "%ip_%Y%m%d_%H%M%S_scp.xml"

        myshare = file_share_manager.create_share_obj(share_path=module.params['share_name'],
                                                      creds=UserCredentials(module.params['share_user'],
                                                                            module.params['share_pwd']),
                                                      isFolder=True, )

        scp_file_name = myshare.new_file(scp_file_name_format)

        target = SCPTargetEnum.ALL

        if module.params['scp_components'] == 'IDRAC':
            target = SCPTargetEnum.IDRAC
        elif module.params['scp_components'] == 'BIOS':
            target = SCPTargetEnum.BIOS
        elif module.params['scp_components'] == 'NIC':
            target = SCPTargetEnum.NIC
        elif module.params['scp_components'] == 'RAID':
            target = SCPTargetEnum.RAID
        job_wait = module.params['job_wait']

        if module.params['export_use'].lower() == 'Default'.lower():
            export_use = ExportUseEnum.Default
        elif module.params['export_use'].lower() == 'Clone'.lower():
            export_use = ExportUseEnum.Clone
        elif module.params['export_use'].lower() == 'Replace'.lower():
            export_use = ExportUseEnum.Replace

        idrac.use_redfish = True
        msg['msg'] = idrac.config_mgr.scp_export(scp_file_name,
                                                 target=target,
                                                 export_format=export_format,
                                                 export_use=export_use,
                                                 job_wait=job_wait)
        if 'Status' in msg['msg'] and msg['msg']['Status'] != "Success":
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

            # iDRAC credentials
            idrac_ip=dict(required=True, type='str'),
            idrac_user=dict(required=True, type='str'),
            idrac_pwd=dict(required=True, type='str', no_log=True),
            idrac_port=dict(required=False, default=443, type='int'),

            # Export Destination
            share_name=dict(required=True, type='str'),
            share_pwd=dict(required=False, type='str', no_log=True),
            share_user=dict(required=False, type='str'),

            scp_components=dict(required=False,
                                choices=['ALL', 'IDRAC', 'BIOS', 'NIC', 'RAID'],
                                default='ALL'),
            job_wait=dict(required=True, type='bool'),
            export_format=dict(required=False, type='str',
                               choices=['JSON', 'XML'], default='XML'),
            export_use=dict(required=False, type='str',
                            choices=['Default', 'Clone', 'Replace'], default='Default')
        ),

        supports_check_mode=False)
    # Connect to iDRAC
    idrac_conn = iDRACConnection(module)
    idrac = idrac_conn.connect()

    # Export Server Configuration Profile
    msg, err = run_export_server_config_profile(idrac, module)

    # Disconnect from iDRAC
    idrac_conn.disconnect()

    if err:
        module.fail_json(**msg)
    module.exit_json(**msg)


if __name__ == '__main__':
    main()
