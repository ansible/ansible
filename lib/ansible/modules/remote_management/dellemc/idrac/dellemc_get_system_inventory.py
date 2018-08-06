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


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: dellemc_get_system_inventory
short_description: Get the PowerEdge Server System Inventory.
version_added: "2.3"
description:
    - Get the PowerEdge Server System Inventory.
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

requirements:
    - "omsdk"
    - "python >= 2.7.5"
author: "Rajeev Arakkal (@rajeevarakkal)"

"""

EXAMPLES = """
---
- name: Get System Inventory
  dellemc_get_system_inventory:
    idrac_ip: "xx.xx.xx.xx"
    idrac_user: "xxxx"
    idrac_pwd: "xxxxxxxx"
"""

RETURNS = """
dest:
    description: Displays the Dell EMC PowerEdge Server System Inventory.
    returned: success
    type: string
"""


from ansible.module_utils.dellemc_idrac import iDRACConnection, logger
from ansible.module_utils.basic import AnsibleModule


# Get System Inventory
def run_get_system_inventory(idrac, module):
    logger.info(module.params['idrac_ip'] + ': STARTING: Get System Inventory Method')
    msg = {}
    msg['changed'] = False
    msg['failed'] = False
    err = False

    try:
        # idrac.use_redfish = True
        logger.info(
            module.params['idrac_ip'] + ': STARTING: Get System Inventory Method: Invoking OMSDK system view API')
        idrac.get_entityjson()
        msg['msg'] = idrac.get_json_device()
        logger.info(
            module.params['idrac_ip'] + ': FINISHED: Get System Inventory Method: Invoking OMSDK system view API')
    except Exception as e:
        logger.error(module.params['idrac_ip'] + ': EXCEPTION: Get System Inventory Method: ' + str(e))
        err = True
        msg['msg'] = "Error: %s" % str(e)
        msg['failed'] = True
    logger.info(module.params['idrac_ip'] + ': FINISHED: Get System Inventory Method')
    return msg, err


# Main
def main():
    module = AnsibleModule(
        argument_spec=dict(

            # iDRAC Handle
            idrac=dict(required=False, type='dict'),

            # iDRAC credentials
            idrac_ip=dict(required=True, type='str'),
            idrac_user=dict(required=True, type='str'),
            idrac_pwd=dict(required=True, type='str', no_log=True),
            idrac_port=dict(required=False, default=443)
        ),
        supports_check_mode=True)
    logger.info(module.params['idrac_ip'] + ': STARTING: Get System Inventory')
    # Connect to iDRAC
    logger.info(module.params['idrac_ip'] + ': CALLING: iDRAC Connection')
    idrac_conn = iDRACConnection(module)
    idrac = idrac_conn.connect()
    logger.info(module.params['idrac_ip'] + ': FINISHED: iDRAC Connection is successful')
    # Get System Inventory
    msg, err = run_get_system_inventory(idrac, module)

    # Disconnect from iDRAC
    idrac_conn.disconnect()

    if err:
        module.fail_json(**msg)
    module.exit_json(ansible_facts={idrac.ipaddr: {'SystemInventory': msg['msg']}})
    logger.info(module.params['idrac_ip'] + ': FINISHED: Get System Inventory')


if __name__ == '__main__':
    main()
