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

- name: obtain specific privates certificates
  aws_acm_export_certificates:
    certificate_arn: "arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012"
    passphrase: secretpassword
  register: acm_certificates
'''

RETURN = '''
certificates:
    description: The list of certificates and private key returned by the AWS Certificate Manager
    returned: always
    type: dict
    sample:
      certificate: XXXXXXXXXXXXXXXXXXXX
      certificate_chain: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
      private_key: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
'''


from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (
    boto3_conn,
    ec2_argument_spec,
    get_aws_connection_info,
    HAS_BOTO3
)


try:
    from botocore.exceptions import ClientError, ParamValidationError
except ImportError:
    pass  # caught by imported AnsibleAWSModule


def camel_dict_to_snake_dict(acm_certificates):
    certificate = acm_certificates.get('Certificate', None)
    certificate_chain = acm_certificates.get('CertificateChain', None)
    private_key = acm_certificates.get('PrivateKey', None)
    return {
        'certificate': certificate,
        'certificate_chain': certificate_chain,
        'private_key': private_key
    }


def export_acm_certificates(connection, module):
    params = {
        'CertificateArn': module.params.get('certificate_arn'),
        'Passphrase': module.params.get('passphrase')
    }

    kwargs = dict((k, v) for k, v in params.items() if v is not None)

    try:
        response = connection.export_certificate(**kwargs)
    except (ClientError, ParamValidationError) as e:
        module.fail_json_aws(e)

    module.exit_json(certificates=camel_dict_to_snake_dict(response))


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            certificate_arn=dict(type='str', required=True),
            passphrase=dict(type='str', required=True)
        )
    )

    module = AnsibleAWSModule(argument_spec=argument_spec)
    connection = module.client('acm')

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 and botocore are required.')

    export_acm_certificates(connection, module)


if __name__ == '__main__':
    main()
