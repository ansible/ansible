#!/usr/bin/python
# -*- coding: utf-8 -*-

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

DOCUMENTATION = r'''
---
module: idrac_firmware
short_description: Firmware update from a repository on a network share (CIFS, NFS).
version_added: "2.8"
description:
    - Update the Firmware by connecting to a network share (either CIFS or NFS) that contains a catalog of
        available updates.
    - Network share should contain a valid repository of Update Packages (DUPs) and a catalog file describing the DUPs.
    - All applicable updates contained in the repository are applied to the system.
    - This feature is available only with iDRAC Enterprise License.
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
    share_name:
        description: CIFS or NFS Network share.
        type: str
        required: True
    share_user:
        description: Network share user in the format 'user@domain' or 'domain\\user' if user is
            part of a domain else 'user'. This option is mandatory for CIFS Network Share.
        type: str
    share_password:
        description: Network share user password. This option is mandatory for CIFS Network Share.
        type: str
    share_mnt:
        description: Local mount path of the network share with read-write permission for ansible user.
            This option is mandatory for Network Share.
        type: str
        required: True
    reboot:
        description: Whether to reboots after applying the updates or not.
        type: bool
        default: false
    job_wait:
        description: Whether to wait for job completion or not.
        type: bool
        default: true
    catalog_file_name:
        required: False
        description: Catalog file name relative to the I(share_name).
        type: str
        default: 'Catalog.xml'

requirements:
    - "omsdk"
    - "python >= 2.7.5"
author: "Rajeev Arakkal (@rajeevarakkal)"
'''

EXAMPLES = """
---
- name: Update firmware from repository on a Network Share
  idrac_firmware:
       idrac_ip: "192.168.0.1"
       idrac_user: "user_name"
       idrac_password: "user_password"
       share_name: "192.168.0.0:/share"
       share_user: "share_user_name"
       share_password: "share_user_pwd"
       share_mnt: "/mnt/share"
       reboot: True
       job_wait: True
       catalog_file_name: "Catalog.xml"
"""

RETURN = """
---
msg:
  type: str
  description: Over all firmware update status.
  returned: always
  sample: "Successfully updated the firmware."
update_status:
  type: dict
  description: Firmware Update job and progress details from the iDRAC.
  returned: success
  sample: {
        'InstanceID': 'JID_XXXXXXXXXXXX',
        'JobState': 'Completed',
        'Message': 'Job completed successfully.',
        'MessageId': 'REDXXX',
        'Name': 'Repository Update',
        'JobStartTime': 'NA',
        'Status': 'Success',
    }
"""


from ansible.module_utils.remote_management.dellemc.dellemc_idrac import iDRACConnection
from ansible.module_utils.basic import AnsibleModule
try:
    from omsdk.sdkcreds import UserCredentials
    from omsdk.sdkfile import FileOnShare
    HAS_OMSDK = True
except ImportError:
    HAS_OMSDK = False


def _validate_catalog_file(catalog_file_name):
    normilized_file_name = catalog_file_name.lower()
    if not normilized_file_name:
        raise ValueError('catalog_file_name should be a non-empty string.')
    elif not normilized_file_name.endswith("xml"):
        raise ValueError('catalog_file_name should be an XML file.')


def update_firmware(idrac, module):
    """Update firmware from a network share and return the job details."""
    msg = {}
    msg['changed'] = False
    msg['update_status'] = {}

    try:
        upd_share = FileOnShare(remote=module.params['share_name'] + "/" + module.params['catalog_file_name'],
                                mount_point=module.params['share_mnt'],
                                isFolder=False,
                                creds=UserCredentials(
                                    module.params['share_user'],
                                    module.params['share_password'])
                                )

        idrac.use_redfish = True
        if '12' in idrac.ServerGeneration or '13' in idrac.ServerGeneration:
            idrac.use_redfish = False

        apply_update = True
        msg['update_status'] = idrac.update_mgr.update_from_repo(upd_share,
                                                                 apply_update,
                                                                 module.params['reboot'],
                                                                 module.params['job_wait'])
    except RuntimeError as e:
        module.fail_json(msg=str(e))

    if "Status" in msg['update_status']:
        if msg['update_status']['Status'] == "Success":
            if module.params['job_wait']:
                msg['changed'] = True
        else:
            module.fail_json(msg='Failed to update firmware.', update_status=msg['update_status'])
    return msg


def main():
    module = AnsibleModule(
        argument_spec={
            "idrac_ip": {"required": True, "type": 'str'},
            "idrac_user": {"required": True, "type": 'str'},
            "idrac_password": {"required": True, "type": 'str', "no_log": True},
            "idrac_port": {"required": False, "default": 443, "type": 'int'},

            "share_name": {"required": True, "type": 'str'},
            "share_user": {"required": False, "type": 'str'},
            "share_password": {"required": False, "type": 'str', "no_log": True},
            "share_mnt": {"required": True, "type": 'str'},

            "catalog_file_name": {"required": False, "type": 'str', "default": "Catalog.xml"},
            "reboot": {"required": False, "type": 'bool', "default": False},
            "job_wait": {"required": False, "type": 'bool', "default": True},
        },

        supports_check_mode=False)

    try:
        # Validate the catalog file
        _validate_catalog_file(module.params['catalog_file_name'])
        # Connect to iDRAC and update firmware
        with iDRACConnection(module.params) as idrac:
            update_status = update_firmware(idrac, module)
    except (ImportError, ValueError, RuntimeError) as e:
        module.fail_json(msg=str(e))

    module.exit_json(msg='Successfully updated the firmware.', update_status=update_status)


if __name__ == '__main__':
    main()
