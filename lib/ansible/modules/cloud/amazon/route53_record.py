#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Shuang Wang <ooocamel@icloud.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: route53_record
version_added: "2.8"
short_description: Manages DNS records in Amazons Route53 service
description: Creates,deletes,updates,reads DNS records in Amazons Route53 service
author: Shuang Wang (@ptux)

requirements:
  - botocore
  - boto3
  - python >= 2.6

options:
  state:
    description:
      - Specifies the state of the resource record.
    required: true
    choices: [ 'present', 'absent' ]
  hosted_zone_name:
    description:
      - The DNS zone to modify
    required: true
  hosted_zone_id:
    description:
      - The Hosted Zone ID of the DNS zone to modify
  record_set_name:
    description:
      - The full DNS record to create or delete
    required: true
  record_set_ttl:
    description:
      - The TTL(seconds) to give the new record
    type: int
    default: 3600
  record_set_type:
    description:
      - The type of DNS record to create
    required: true
    choices: [ 'A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'CAA', 'NS', 'SOA' ]
  record_set_value:
    description:
      - The new value when creating a DNS record.
  wait:
    description:
      - Wait until the changes have been replicated to all Amazon Route 53 DNS servers.
    type: bool
    default: 'no'
  wait_timeout:
    description:
      - How long to wait for the changes to be replicated, in seconds.
    default: 300

extends_documentation_fragment:
  - aws
  - ec2
'''

RETURN = '''
name:
    description: hosted zone name
    returned: when hosted zone exists
    type: string
    sample: "private.local."
'''

EXAMPLES = '''
# Add new.foo.com as an A record with 3 IPs and wait until the changes have been replicated
- route53_record:
      state: present
      zone: foo.com
      record: new.foo.com
      type: A
      ttl: 7200
      value: 1.1.1.1,2.2.2.2,3.3.3.3
      wait: yes
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

import time
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (
    AWSRetry,
    boto3_conn,
    boto_exception,
    ec2_argument_spec,
    get_aws_connection_info,
    snake_dict_to_camel_dict,
    camel_dict_to_snake_dict
)


class AWSRoute53Record(object):
    def __init__(self, module=None):
        self._module = module
        self._connection = self._module.client('route53')
        self._check_mode = self._module.check_mode

    def process(self):
        if self._module.params['state'] == 'present':
            results = self._ensure_present()
        elif self._module.params['state'] == 'absent':
            results = self._ensure_absent()

    def _ensure_present(self):
        results = dict(changed=False)
        record_exists = False
        return results

    def _ensure_absent(self):
        results = dict(changed=False)
        record_exists = False
        return results

    def _get_zone_id(self, hosted_zone_name=None):
        """gets a zone id by zone name"""
        hosted_zone_id = None
        if hosted_zone_name is not None:
            try:
                hosted_zones = self._connection.list_hosted_zones().get('HostedZones', [])
                for dic in hosted_zones:
                    if dic.get('Name').rstrip('.') == hosted_zone_name:
                        hosted_zone_id = dic.get('Id')
                if hosted_zone_id is None:
                    self._module.fail_json(msg="hosted zone name not exists: %s" % hosted_zone_name)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self._module.fail_json_aws(e, msg="couldn't get hosted zone id by hosted_zone_name")
        else:
            self._module.fail_json(msg="hosted zone name is requied.")
        return hosted_zone_id

    def _get_zone(self, hosted_zone_id=None):
        """gets a zone by id"""
        hosted_zone = None
        if hosted_zone_id is not None:
            try:
                hosted_zone = self._connection.get_hosted_zone(Id=hosted_zone_id)
                hosted_zone_name = hosted_zone['HostedZone']['Name'].rstrip('.')
                if not self._module.params['hosted_zone_name'] == hosted_zone_name:
                    self._module.fail_json(msg="hosted_zone_id not matches hosted_zone_name")
                if hosted_zone is None:
                    self._module.fail_json(msg="hosted zone id not exists: %s" % hosted_zone_id)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self._module.fail_json_aws(e, msg="couldn't get hosted zone by hosted_zone_id")
        else:
            self._module.fail_json(msg="hosted zone id is requied.")
        return hosted_zone

    def _get_record(self):
        #      self._connection.list_resource_record_sets(**kwargs)
        # Lists the resource record sets in a specified hosted zone.
        pass

    def _create_record(self):
        #      self._connection.change_resource_record_sets(**kwargs)
        pass

    def _update_record(self):
        pass

    def _delete_record(self):
        pass


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        hosted_zone_name=dict(required=True),
        hosted_zone_id=dict(required=False, default=None),
        record_set_name=dict(required=True),
        record_set_type=dict(choices=['A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'CAA', 'NS', 'SOA'], required=True),
        record_set_ttl=dict(required=False, type='int', default=3600),
        record_set_value=dict(required=False, type='list'),
        state=dict(choices=['present', 'absent'], required=True),
        wait=dict(required=False, type='bool', default=False),
        wait_timeout=dict(required=False, type='int', default=300)
    ))

    required_if = [('state', 'present', ['record_set_value']),
                   ('state', 'absent', ['record_set_value'])]
    ansible_aws_module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=required_if,
        supports_check_mode=True
    )
    results = dict(changed=False)
    aws_route53_record = AWSRoute53Record(module=ansible_aws_module)
    aws_route53_record.process()
    aws_route53_record.exit_json(**results)


if __name__ == '__main__':
    main()
