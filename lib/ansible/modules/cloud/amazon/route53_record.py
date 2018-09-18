#!/usr/bin/python

# Copyright: (c) Ansible Project
# Copyright: (c) 2018, Shuang Wang <ooocamel@icloud.com>

# This code refactors the module route53.py of Ansible in order to support boto3.
# Name this module [route53_record] for the consistency with other route53_xxx modules.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: route53_record
version_added: "2.8"
author: Shuang Wang (@ptux)
short_description: Manages DNS records in Amazons Route53 service
description: Creates,deletes,updates,reads DNS records in Amazons Route53 service
requirements:
  - botocore
  - boto3
  - python >= 2.7
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
'''

RETURN = '''
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils._text import to_native
from ansible.module_utils.ec2 import (
    AWSRetry,
    boto3_conn,
    ec2_argument_spec,
    get_aws_connection_info,
    camel_dict_to_snake_dict,
    boto3_tag_list_to_ansible_dict,
    ansible_dict_to_boto3_filter_list,
    ansible_dict_to_boto3_tag_list,
    compare_aws_tags
)


class AWSRoute53Record(object):
    def __init__(self, module=None, results=None):
        self._module = module
        self._results = results
        self._connection = self._module.client('ec2')
        self._check_mode = self._module.check_mode
        self.warnings = []

    def _read_zone(self):
        pass

    def _create_record(self):
        pass

    def _read_record(self):
        pass

    def _update_record(self):
        pass

    def _delete_record(self):
        pass

    def ensure_present(self):
        pass

    def ensure_absent(self):
        pass

    def process(self):
        pass


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(aliases=['command'], choices=['present', 'absent', 'get', 'create', 'delete'], required=True),
        zone=dict(required=True),
        hosted_zone_id=dict(required=False, default=None),
        record=dict(required=True),
        ttl=dict(required=False, type='int', default=3600),
        type=dict(choices=['A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'CAA', 'NS', 'SOA'], required=True),
        alias=dict(required=False, type='bool'),
        alias_hosted_zone_id=dict(required=False),
        alias_evaluate_target_health=dict(required=False, type='bool', default=False),
        value=dict(required=False, type='list'),
        overwrite=dict(required=False, type='bool'),
        retry_interval=dict(required=False, default=500),
        private_zone=dict(required=False, type='bool', default=False),
        identifier=dict(required=False, default=None),
        weight=dict(required=False, type='int'),
        region=dict(required=False),
        health_check=dict(required=False),
        failover=dict(required=False, choices=['PRIMARY', 'SECONDARY']),
        vpc_id=dict(required=False),
        wait=dict(required=False, type='bool', default=False),
        wait_timeout=dict(required=False, type='int', default=300),
    ))

    # state=present, absent, create, delete THEN value is required
    required_if = [('state', 'present', ['value']), ('state', 'create', ['value'])]
    required_if.extend([('state', 'absent', ['value']), ('state', 'delete', ['value'])])

    # If alias is True then you must specify alias_hosted_zone as well
    required_together = [['alias', 'alias_hosted_zone_id']]

    # failover, region, and weight are mutually exclusive
    mutually_exclusive = [('failover', 'region', 'weight')]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    results = dict(changed=False)

    record_controller = AWSRoute53Record(module=module, results=results)
    record_controller.process()

    module.exit_json(**results)

if __name__ == '__main__':
    main()
