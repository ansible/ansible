#!/usr/bin/python
# Copyright (c) 2018 Loic BLOT <loic.blot@unix-experience.fr>
# This module is sponsored by E.T.A.I. (www.etai.fr)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: aws_sgw_facts
short_description: Fetch AWS Storage Gateway facts
description:
    - Fetch AWS Storage Gateway facts
version_added: "2.6"
requirements: [ boto3 ]
author: "Loic Blot <loic.blot@unix-experience.fr>"
extends_documentation_fragment:
    - aws
    - ec2
'''

RETURN = '''
gateways:
  description: list of gateway objects
  returned: always
  type: complex
  contains:
    gateway_arn:
      description: "Storage Gateway ARN"
      returned: always
      type: string
      sample: "arn:aws:storagegateway:eu-west-1:367709993819:gateway/sgw-9999F888"
    gateway_id:
      description: "Storage Gateway ID"
      returned: always
      type: string
      sample: "sgw-9999F888"
    gateway_name:
      description: "Storage Gateway friendly name"
      returned: always
      type: string
      sample: "my-sgw-01"
    gateway_operational_state:
      description: "Storage Gateway operational state"
      returned: always
      type: string
      sample: "ACTIVE"
    gateway_type:
      description: "Storage Gateway type"
      returned: always
      type: string
      sample: "FILE_S3"
    file_shares:
      description: "Storage gateway file shares"
      returned: when gateway_type == "FILE_S3"
      type: complex
      contains:
        file_share_arn:
          description: "File share ARN"
          returned: always
          type: string
          sample: "arn:aws:storagegateway:eu-west-1:399805793479:share/share-AF999C88"
        file_share_id:
          description: "File share ID"
          returned: always
          type: string
          sample: "share-AF999C88"
        file_share_status:
          description: "File share status"
          returned: always
          type: string
          sample: "AVAILABLE"
    tapes:
        description: "Storage Gateway tapes"
        returned: when gateway_type == "VTL"
        type: complex
        contains:
          tape_arn:
            description: "Tape ARN"
            returned: always
            type: string
            sample: "arn:aws:storagegateway:eu-west-1:399805793479:tape/tape-AF999C88"
          tape_barcode:
            description: "Tape ARN"
            returned: always
            type: string
            sample: "tape-AF999C88"
          tape_size_in_bytes:
            description: "Tape ARN"
            returned: always
            type: integer
            sample: 555887569
          tape_status:
            description: "Tape ARN"
            returned: always
            type: string
            sample: "AVAILABLE"
    local_disks:
      description: "Storage gateway local disks"
      returned: always
      type: complex
      contains:
        disk_allocation_type:
          description: "Disk allocation type"
          returned: always
          type: string
          sample: "CACHE STORAGE"
        disk_id:
          description: "Disk ID on the system"
          returned: always
          type: string
          sample: "pci-0000:00:1f.0"
        disk_node:
          description: "Disk parent block device"
          returned: always
          type: string
          sample: "/dev/sdb"
        disk_path:
          description: "Disk path used for the cache"
          returned: always
          type: string
          sample: "/dev/nvme1n1"
        disk_size_in_bytes:
          description: "Disk size in bytes"
          returned: always
          type: integer
          sample: 107374182400
        disk_status:
          description: "Disk status"
          returned: always
          type: string
          sample: "present"
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: "Get AWS storage gateway facts"
  aws_sgw_facts:

- name: "Get AWS storage gateway facts for region eu-west-3"
  aws_sgw_facts:
    region: eu-west-3
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (ec2_argument_spec, camel_dict_to_snake_dict)

try:
    import botocore
    from botocore.exceptions import ClientError
except ImportError:
    pass  # caught by imported HAS_BOTO3


class SGWFactsManager(object):
    def __init__(self, client, module):
        self.client = client
        self.module = module
        self.name = self.module.params.get('name')

    def fetch(self):
        gateways = self.list_gateways()
        for gateway in gateways:
            self.list_local_disks(gateway)
            # File share gateway
            if gateway["gateway_type"] == "FILE_S3":
                self.list_gateway_file_shares(gateway)
            # Volume tape gateway
            elif gateway["gateway_type"] == "VTL":
                self.list_gateway_vtl(gateway)
            # iSCSI gateway
            elif gateway["gateway_type"] in ["CACHED", "STORED"]:
                self.list_gateway_volumes(gateway)

        self.module.exit_json(gateways=gateways)

    """
    Reads the storage gateway object API response.
    """
    @staticmethod
    def _read_gatewaylist_reponse(gateway_list, aws_response):
        for gw in aws_response["Gateways"]:
            gateway_list.append(camel_dict_to_snake_dict(gw))
        return aws_response["Marker"] if "Marker" in aws_response else None

    """
    List all storage gateways for the AWS endpoint.
    """
    def list_gateways(self):
        response = self.client.list_gateways(
            Limit=100
        )

        gateways = []
        marker = self._read_gatewaylist_reponse(gateways, response)

        while marker is not None:
            response = self.client.list_gateways(
                Limit=100,
                Marker=marker
            )
            marker = self._read_gatewaylist_reponse(gateways, response)

        return gateways

    """
    Read fileshare objects from AWS API response.
    Drop the gateway_arn attribute from response, as it will be duplicate with parent object.
    """
    @staticmethod
    def _read_gateway_fileshare_response(fileshares, aws_reponse):
        for share in aws_reponse["FileShareInfoList"]:
            share_obj = camel_dict_to_snake_dict(share)
            if "gateway_arn" in share_obj:
                del share_obj["gateway_arn"]
            fileshares.append(share_obj)

        return aws_reponse["NextMarker"] if "NextMarker" in aws_reponse else None

    """
    List file shares attached to AWS storage gateway when in S3 mode.
    """
    def list_gateway_file_shares(self, gateway):
        response = self.client.list_file_shares(
            GatewayARN=gateway["gateway_arn"],
            Limit=100
        )

        gateway["file_shares"] = []
        marker = self._read_gateway_fileshare_response(gateway["file_shares"], response)

        while marker is not None:
            response = self.client.list_file_shares(
                GatewayARN=gateway["gateway_arn"],
                Marker=marker,
                Limit=100
            )

            marker = self._read_gateway_fileshare_response(gateway["file_shares"], response)

    """
    List storage gateway local disks
    """
    def list_local_disks(self, gateway):
        gateway['local_disks'] = [camel_dict_to_snake_dict(disk) for disk in
                                  self.client.list_local_disks(GatewayARN=gateway["gateway_arn"])['Disks']]

    """
    Read tape objects from AWS API response.
    Drop the gateway_arn attribute from response, as it will be duplicate with parent object.
    """
    @staticmethod
    def _read_gateway_tape_response(tapes, aws_response):
        for tape in aws_response["TapeInfos"]:
            tape_obj = camel_dict_to_snake_dict(tape)
            if "gateway_arn" in tape_obj:
                del tape_obj["gateway_arn"]
            tapes.append(tape_obj)

        return aws_response["Marker"] if "Marker" in aws_response else None

    """
    List VTL & VTS attached to AWS storage gateway in VTL mode
    """
    def list_gateway_vtl(self, gateway):
        response = self.client.list_tapes(
            Limit=100
        )

        gateway["tapes"] = []
        marker = self._read_gateway_tape_response(gateway["tapes"], response)

        while marker is not None:
            response = self.client.list_tapes(
                Marker=marker,
                Limit=100
            )

            marker = self._read_gateway_tape_response(gateway["tapes"], response)

    """
    Read tape objects from AWS API response.
    Drop the gateway_arn & gateway_id attribute from response, as it will be duplicate
    with parent object.
    """
    @staticmethod
    def _read_gateway_volumes(volumes, aws_response):
        for volume in aws_response["VolumeInfos"]:
            volume_obj = camel_dict_to_snake_dict(volume)
            if "gateway_arn" in volume_obj:
                del volume_obj["gateway_arn"]
            if "gateway_id" in volume_obj:
                del volume_obj["gateway_id"]

            volume.append(volume_obj)
        return aws_response["Marker"] if "Marker" in aws_response else None

    """
    List volumes attached to AWS storage gateway in CACHED or STORAGE mode
    """
    def list_gateway_volumes(self, gateway):
        response = self.client.list_volumes(
            GatewayARN=gateway["gateway_arn"],
            Limit=100
        )

        gateway["volumes"] = []
        marker = self._read_gateway_volumes(gateway["volumes"], response)

        while marker is not None:
            response = self.client.list_volumes(
                GatewayARN=gateway["gateway_arn"],
                Marker=marker,
                Limit=100
            )

            marker = self._read_gateway_volumes(gateway["volumes"], response)


def main():
    argument_spec = ec2_argument_spec()

    module = AnsibleAWSModule(argument_spec=argument_spec)
    client = module.client('storagegateway')

    if client is None:  # this should never happen
        module.fail_json(msg='Unknown error, failed to create storagegateway client, no information from boto.')

    SGWFactsManager(client, module).fetch()


if __name__ == '__main__':
    main()
