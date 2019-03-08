#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''

'''

EXAMPLES = '''
'''

RETURN = '''
'''


from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code, get_boto3_client_method_parameters
from time import sleep

try:
    from botocore.exceptions import ClientError, BotoCoreError, WaiterError
except ImportError:
    pass  # caught by AnsibleAWSModule


def main():
    arg_spec = dict(
        state=dict(choices=['present', 'absent'],default='present'),

    )

    parameter_options(
        
    )