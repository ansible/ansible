#!/usr/bin/python

# Copyright: (c) 2018, Loic BLOT (@nerzhul) <loic.blot@unix-experience.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# This module is sponsored by E.T.A.I. (www.etai.fr)

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
author: Loic Blot (@nerzhul) <loic.blot@unix-experience.fr>
options:
  gather_local_disks:
    description:
      - Gather local disks attached to the storage gateway.
    type: bool
    required: false
    default: true
  gather_tapes:
    description:
      - Gather tape information for storage gateways in tape mode.
    type: bool
    required: false
    default: true
  gather_file_shares:
    description:
      - Gather file share information for storage gateways in s3 mode.
    type: bool
    required: false
    default: true
  gather_volumes:
    description:
      - Gather volume information for storage gateways in iSCSI (cached & stored) modes.
    type: bool
    required: false
    default: true
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
      type: str
      sample: "arn:aws:storagegateway:eu-west-1:367709993819:gateway/sgw-9999F888"
    gateway_id:
      description: "Storage Gateway ID"
      returned: always
      type: str
      sample: "sgw-9999F888"
    gateway_name:
      description: "Storage Gateway friendly name"
      returned: always
      type: str
      sample: "my-sgw-01"
    gateway_operational_state:
      description: "Storage Gateway operational state"
      returned: always
      type: str
      sample: "ACTIVE"
    gateway_type:
      description: "Storage Gateway type"
      returned: always
      type: str
      sample: "FILE_S3"
    file_shares:
      description: "Storage gateway file shares"
      returned: when gateway_type == "FILE_S3"
      type: complex
      contains:
        file_share_arn:
          description: "File share ARN"
          returned: always
          type: str
          sample: "arn:aws:storagegateway:eu-west-1:399805793479:share/share-AF999C88"
        file_share_id:
          description: "File share ID"
          returned: always
          type: str
          sample: "share-AF999C88"
        file_share_status:
          description: "File share status"
          returned: always
          type: str
          sample: "AVAILABLE"
    tapes:
        description: "Storage Gateway tapes"
        returned: when gateway_type == "VTL"
        type: complex
        contains:
          tape_arn:
            description: "Tape ARN"
            returned: always
            type: str
            sample: "arn:aws:storagegateway:eu-west-1:399805793479:tape/tape-AF999C88"
          tape_barcode:
            description: "Tape ARN"
            returned: always
            type: str
            sample: "tape-AF999C88"
          tape_size_in_bytes:
            description: "Tape ARN"
            returned: always
            type: int
            sample: 555887569
          tape_status:
            description: "Tape ARN"
            returned: always
            type: str
            sample: "AVAILABLE"
    local_disks:
      description: "Storage gateway local disks"
      returned: always
      type: complex
      contains:
        disk_allocation_type:
          description: "Disk allocation type"
          returned: always
          type: str
          sample: "CACHE STORAGE"
        disk_id:
          description: "Disk ID on the system"
          returned: always
          type: str
          sample: "pci-0000:00:1f.0"
        disk_node:
          description: "Disk parent block device"
          returned: always
          type: str
          sample: "/dev/sdb"
        disk_path:
          description: "Disk path used for the cache"
          returned: always
          type: str
          sample: "/dev/nvme1n1"
        disk_size_in_bytes:
          description: "Disk size in bytes"
          returned: always
          type: int
          sample: 107374182400
        disk_status:
          description: "Disk status"
          returned: always
          type: str
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
from ansible.module_utils.ec2 import camel_dict_to_snake_dict

try:
    from botocore.exceptions import BotoCoreError, ClientError
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
            if self.module.params.get('gather_local_disks'):
                self.list_local_disks(gateway)
            # File share gateway
            if gateway["gateway_type"] == "FILE_S3" and self.module.params.get('gather_file_shares'):
                self.list_gateway_file_shares(gateway)
            # Volume tape gateway
            elif gateway["gateway_type"] == "VTL" and self.module.params.get('gather_tapes'):
                self.list_gateway_vtl(gateway)
            # iSCSI gateway
            elif gateway["gateway_type"] in ["CACHED", "STORED"] and self.module.params.get('gather_volumes'):
                self.list_gateway_volumes(gateway)

        self.module.exit_json(gateways=gateways)

    """
    List all storage gateways for the AWS endpoint.
    """
    def list_gateways(self):
        try:
            paginator = self.client.get_paginator('list_gateways')
            response = paginator.paginate(
                PaginationConfig={
                    'PageSize': 100,
                }
            ).build_full_result()

            gateways = []
            for gw in response["Gateways"]:
                gateways.append(camel_dict_to_snake_dict(gw))

            return gateways

        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg="Couldn't list storage gateways")

    """
    Read file share objects from AWS API response.
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
        try:
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
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg="Couldn't list gateway file shares")

    """
    List storage gateway local disks
    """
    def list_local_disks(self, gateway):
        try:
            gateway['local_disks'] = [camel_dict_to_snake_dict(disk) for disk in
                                      self.client.list_local_disks(GatewayARN=gateway["gateway_arn"])['Disks']]
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg="Couldn't list storage gateway local disks")

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
        try:
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
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg="Couldn't list storage gateway tapes")

    """
    List volumes attached to AWS storage gateway in CACHED or STORAGE mode
    """
    def list_gateway_volumes(self, gateway):
        try:
            paginator = self.client.get_paginator('list_volumes')
            response = paginator.paginate(
                GatewayARN=gateway["gateway_arn"],
                PaginationConfig={
                    'PageSize': 100,
                }
            ).build_full_result()

            gateway["volumes"] = []
            for volume in response["VolumeInfos"]:
                volume_obj = camel_dict_to_snake_dict(volume)
                if "gateway_arn" in volume_obj:
                    del volume_obj["gateway_arn"]
                if "gateway_id" in volume_obj:
                    del volume_obj["gateway_id"]

                gateway["volumes"].append(volume_obj)
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg="Couldn't list storage gateway volumes")


def main():
    argument_spec = dict(
        gather_local_disks=dict(type='bool', default=True),
        gather_tapes=dict(type='bool', default=True),
        gather_file_shares=dict(type='bool', default=True),
        gather_volumes=dict(type='bool', default=True)
    )

    module = AnsibleAWSModule(argument_spec=argument_spec)
    client = module.client('storagegateway')

    if client is None:  # this should never happen
        module.fail_json(msg='Unknown error, failed to create storagegateway client, no information from boto.')

    SGWFactsManager(client, module).fetch()


if __name__ == '__main__':
    main()
