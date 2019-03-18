# (C) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: aws_resource_actions
    type: aggregate
    short_description: summarizes all "resource:actions" completed
    version_added: "2.8"
    description:
      - Ansible callback plugin for collecting the AWS actions completed by all boto3 modules using
        AnsibleAWSModule in a playbook. Botocore endpoint logs need to be enabled for those modules, which can
        be done easily by setting debug_botocore_endpoint_logs to True for group/aws using module_defaults.
    requirements:
      - whitelisting in configuration - see examples section below for details.
'''

EXAMPLES = '''
example: >
  To enable, add this to your ansible.cfg file in the defaults block
    [defaults]
    callback_whitelist = aws_resource_actions
sample output: >
#
# AWS ACTIONS: ['s3:PutBucketAcl', 's3:HeadObject', 's3:DeleteObject', 's3:PutObjectAcl', 's3:CreateMultipartUpload',
#               's3:DeleteBucket', 's3:GetObject', 's3:DeleteObjects', 's3:CreateBucket', 's3:CompleteMultipartUpload',
#               's3:ListObjectsV2', 's3:HeadBucket', 's3:UploadPart', 's3:PutObject']
#
sample output: >
#
# AWS ACTIONS: ['ec2:DescribeVpcAttribute', 'ec2:DescribeVpcClassicLink', 'ec2:ModifyVpcAttribute', 'ec2:CreateTags',
#               'sts:GetCallerIdentity', 'ec2:DescribeSecurityGroups', 'ec2:DescribeTags', 'ec2:DescribeVpcs', 'ec2:CreateVpc']
#
'''

from ansible.plugins.callback import CallbackBase
from ansible.module_utils._text import to_native


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.8
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'aws_resource_actions'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        self.aws_resource_actions = []
        super(CallbackModule, self).__init__()

    def extend_aws_resource_actions(self, result):
        if result.get('resource_actions'):
            self.aws_resource_actions.extend(result['resource_actions'])

    def runner_on_ok(self, host, res):
        self.extend_aws_resource_actions(res)

    def runner_on_failed(self, host, res, ignore_errors=False):
        self.extend_aws_resource_actions(res)

    def v2_runner_item_on_ok(self, result):
        self.extend_aws_resource_actions(result._result)

    def v2_runner_item_on_failed(self, result):
        self.extend_aws_resource_actions(result._result)

    def playbook_on_stats(self, stats):
        if self.aws_resource_actions:
            self.aws_resource_actions = sorted(list(to_native(action) for action in set(self.aws_resource_actions)))
            self._display.display("AWS ACTIONS: {0}".format(self.aws_resource_actions))
