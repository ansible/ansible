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
# AWS ACTIONS: [u's3:PutBucketAcl', u's3:HeadObject', u's3:DeleteObject', u's3:PutObjectAcl', u's3:CreateMultipartUpload',
#               u's3:DeleteBucket', u's3:GetObject', u's3:DeleteObjects', u's3:CreateBucket', u's3:CompleteMultipartUpload',
#               u's3:ListObjectsV2', u's3:HeadBucket', u's3:UploadPart', u's3:PutObject']
#
sample output: >
#
# AWS ACTIONS: [u'ec2:DescribeVpcAttribute', u'ec2:DescribeVpcClassicLink', u'ec2:ModifyVpcAttribute', u'ec2:CreateTags',
#               u'sts:GetCallerIdentity', u'ec2:DescribeSecurityGroups', u'ec2:DescribeTags', u'ec2:DescribeVpcs', u'ec2:CreateVpc']
#
'''

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    """
    This callback module provides per-task timing, ongoing playbook elapsed time
    and ordered list of top 20 longest running tasks at end.
    """
    CALLBACK_VERSION = 2.8
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'aws_resource_actions'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        self.aws_resource_actions = []
        super(CallbackModule, self).__init__()

    def runner_on_ok(self, host, res):
        if res.get('resource_actions'):
            self.aws_resource_actions.extend(res['resource_actions'])

    def runner_on_failed(self, host, res, ignore_errors=False):
        if res.get('resource_actions'):
            self.aws_resource_actions.extend(res['resource_actions'])

    def v2_runner_item_on_ok(self, result):
        if result._result.get('resource_actions'):
            self.aws_resource_actions.extend(result._result['resource_actions'])

    def v2_runner_item_on_failed(self, result):
        if result._result.get('resource_actions'):
            self.aws_resource_actions.extend(result._result['resource_actions'])

    def playbook_on_stats(self, stats):
        if self.aws_resource_actions:
            self.aws_resource_actions = sorted(list(set(self.aws_resource_actions)))
            self._display.display("AWS ACTIONS: {0}".format(self.aws_resource_actions))
