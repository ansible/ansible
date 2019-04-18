#!/usr/bin/python

# Copyright: (c) 2019, Hiroyuki Wakabayashi <hiroyuki.wakabayashi@emc.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: emc_vplex_storagevolume
version_added: '2.9'
short_description: Create storage-volume on EMC VPLEX Storage Array
description:
- Create storage-volume with verification of existence
author:
- Hiroyuki Wakabayashi (@hwakabh)
options: {}
'''

EXAMPLES = r'''
- name: Create storage-volume on VPLEX
  emc_vplex_storagevolume:
    vplex_ip_address: 10.10.10.2
    vplex_username: service
    vplex_password: password
    vplex_serialnum: CKM00120900782
    volume_name: lun_name_backend
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.storage.emc.emc_vplex import VPLEX
from requests.exceptions import RequestException

import logging
import os

logger = logging.getLogger(__name__)


# storage-volumes
def rediscover_storage_array(vplex, array_name):
    logger.info('--- array re-discover of ' + array_name)
    uri = '/vplex/array+re-discover'
    data = '{\"args\":\"--cluster cluster-1 --array ' + array_name + ' --force\"}'
    response = vplex.https_post(urlsuffix=uri, data=data)
    return response


def get_storage_volume_info(vplex, name, is_all):
    if is_all:
        uri = '/vplex/clusters/cluster-1/storage-elements/storage-volumes/'
    else:
        uri = '/vplex/clusters/cluster-1/storage-elements/storage-volumes/' + name
    response = vplex.https_get(urlsuffix=uri)
    # logger.info(response)
    return response


def claim_storage_volume(vplex, volume_name, vpd_id):
    claim_uri = '/vplex/storage-volume+claim'
    claiming_data = '{\"args\":\"-n ' + volume_name + ' -d ' + vpd_id + ' -f\"}'
    response = vplex.https_post(urlsuffix=claim_uri, data=claiming_data)
    return response


def main():
    log_directory = "./logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    _detail_formatting = "%(asctime)s : %(name)s - %(levelname)s : %(message)s"
    logging.basicConfig(
        level=logging.DEBUG,
        format=_detail_formatting,
        filename=log_directory + "/ansible-vplex.log"
    )
    logging.getLogger("modules").setLevel(level=logging.DEBUG)
    console = logging.StreamHandler()
    console_formatter = logging.Formatter("%(asctime)s : %(message)s")
    console.setFormatter(console_formatter)
    console.setLevel(logging.INFO)
    logging.getLogger("modules").addHandler(console)

    logger = logging.getLogger(__name__)
    logging.getLogger(__name__).addHandler(console)

    argument_spec = {
        "vplex_ip_address": dict(type="str", required=True),
        "vplex_username": dict(type="str", required=True),
        "vplex_password": dict(type="str", required=True),
        "vplex_serialnum": dict(type="str", required=True),
        "volume_name": dict(type="str", required=True),
        "vpd_id": dict(type="str", required=True),
        "array_name": dict(type="str", required=True),
        "volume_name": dict(type="str", required=True)}

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    volume_name = module.params["volume_name"]
    array_name = module.params['array_name']
    vpd_id = module.params["vpd_id"]

    vplex = VPLEX(
        ip_address=module.params["vplex_ip_address"],
        username=module.params["vplex_username"],
        password=module.params["vplex_password"])

    # --- if S/N differs from expected, exit the program
    if not vplex.confirm_vplex_serial_number(expect_serial_number=serial_number):
        logger.error('Target system S/N and expected ones are different. Exit the module wihtout any operations.')
        module.exit_json(changed=False)
    # --- if same as expected, proceed to play

    # Check LUN on backend storage-array are exposed to VPLEX or not
    logger.info('Getting exposed storage-volumes on VPLEX')
    storage_volumes_list_all = vplex.https_get(urlsuffix='/vplex/clusters/cluster-1/storage-elements/storage-volumes')
    # --- if not, run array re-discover for claiming storage-volumes
    storage_volumes = []
    for storage_volume in storage_volumes_list_all['response']['context'][0]['children']:
        storage_volumes.append(storage_volume['name'])

    if vpd_id not in storage_volumes:
        logger.info('------- Execute array Re-discovery')
        try:
            rediscover_storage_array(vplex=vplex, array_name=array_name)
        except requests.exceptions.RequestException:
            logger.error('Failed to array re-discover...')
            module.exit_json(changed=False)

    # Check provided storage-volume name exists
    if volume_name in storage_volumes:
        logger.error('Name duplication occured. Provided storage-volume name [ ' + volume_name + ' ] have already configured on VPLEX.')
        logger.error('Please specify another storage-volume name in group_vars/all.yml and retry playbooks.')
        module.exit_json(changed=False)
    else:
        try:
            claim_storage_volume(vplex=vplex, volume_name=volume_name, vpd_id=vpd_id)
        except requests.exceptions.RequestException:
            logger.error('Failed to claim storage-volumes. Retry playbook after checking backend volumes and masking on FC-Switches.')
            module.exit_json(changed=False)
        else:
            logger.info('Successfully claim storage-volumes.')
            get_storage_volume_info(vplex=vplex, name=volume_name, is_all=False)
            module.exit_json(changed=True)


if __name__ == "__main__":
    main()
