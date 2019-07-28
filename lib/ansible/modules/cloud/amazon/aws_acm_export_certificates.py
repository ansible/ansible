#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: aws_acm_export_certificates
short_description: Exports a private certificate issued by a private certificate authority (CA) for use anywhere
description:
  - Exports a private certificate issued by a private certificate authority (CA) for use anywhere
version_added: "2.9"
author:
  - diodonfrost (@diodonfrost)
options:
  certificate_arn:
    description:
      - The Amazon Resource Name (ARN) of the issued certificate.
    type: str
    required: true
  passphrase:
    description:
      - Passphrase to associate with the encrypted exported private key.
    type: str
    required: true
extends_documentation_fragment:
    - aws
    - ec2
requirements:
    - boto3
    - botocore
    - python >= 2.6
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.
# Exporting a private certificate and private key (more details: https://docs.aws.amazon.com/acm/latest/userguide/gs-acm-export-private.html#export-cli)

- name: obtain specific privates certificate
  aws_acm_export_certificates:
    certificate_arn: "arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012"
    passphrase: secretpassword
  register: acm_certificate
'''

RETURN = '''
certificate:
    description: The base64 PEM-encoded certificate
    returned: always
    type: str
certificate_chain:
    description: The base64 PEM-encoded certificate chain. This does not include the certificate that you are exporting
    returned: always
    type: str
private_key:
    description: The encrypted private key associated with the public key in the certificate
    returned: always
    type: str
'''

import traceback

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (
    camel_dict_to_snake_dict,
    ec2_argument_spec,
)


try:
    from botocore.exceptions import ClientError, ParamValidationError
except ImportError:
    pass  # caught by imported AnsibleAWSModule


def export_acm_certificate(connection, module):
    params = {
        'CertificateArn': module.params.get('certificate_arn'),
        'Passphrase': module.params.get('passphrase')
    }

    kwargs = dict((k, v) for k, v in params.items() if v is not None)

    try:
        response = connection.export_certificate(**kwargs)
    except (ClientError, ParamValidationError) as error:
        module.fail_json_aws(error, msg="Couldn't obtain private certificate")

    module.exit_json(**camel_dict_to_snake_dict(response))


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'certificate_arn': dict(required=True),
            'passphrase': dict(required=True),
        },
        supports_check_mode=False,
    )

    connection = module.client('acm')
    export_acm_certificate(connection, module)


if __name__ == '__main__':
    main()
