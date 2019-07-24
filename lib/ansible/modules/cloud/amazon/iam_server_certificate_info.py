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
module: iam_server_certificate_info
short_description: Retrieve the facts of a server certificate either based on name or path
description:
  - Retrieve the attributes of a server certificate
version_added: "2.2"
author: "Vijayanand (@vijayanandsharma)"
requirements: [boto3, botocore]
options:
  name:
    description:
      - The name of the server certificate you are retrieving attributes for. This argument is mutually exclusive with I(path)
    type: str
    required: false
  path:
    description:
      - The path to the server certificate you are retrieving attributes for. This argument is mutually exclusive with I(name)
    type: str
    required: false
    version_added: '2.9'
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Retrieve server certificate
- iam_server_certificate_info:
    name: production-cert
  register: server_cert
# Retrieve server certificates from a particular path
- iam_server_certificate_info:
    path: /company/servercerts
  register: server_cert
# Retrieve all server certificates
- iam_server_certificate_info:
  register: server_certs
# Fail if the server certificate name was not found
- iam_server_certificate_info:
    name: production-cert
  register: server_cert
  failed_when: "{{ server_cert.certificates | length == 0 }}"
'''

RETURN = '''
certificates:
    description: Returns an array of complex objects as described below.
    returned: success
    type: complex
    contains:
        certificate_body:
            description: The asn1der encoded PEM string
            returned: always
            type: str
            sample: "-----BEGIN CERTIFICATE-----\nbunch of random data\n-----END CERTIFICATE-----"
        certificate_chain:
            description: The asn1der encoded PEM string
            returned: always
            type: str
            sample: "-----BEGIN CERTIFICATE-----\nbunch of random data\n-----END CERTIFICATE-----"
        server_certificate_metadata:
            description: Returns an array of complex objects as described below.
            returned: always
            type: complex
            contains:
                server_certificate_id:
                    description: The 21 character certificate id
                    returned: always
                    type: str
                    sample: "ADWAJXWTZAXIPIMQHMJPO"
                server_certificate_name:
                    description: The name of the server certificate
                    returned: always
                    type: str
                    sample: "server-cert-name"
                arn:
                    description: The Amazon resource name of the server certificate
                    returned: always
                    type: str
                    sample: "arn:aws:iam::911277865346:server-certificate/server-cert-name"
                path:
                    description: The path of the server certificate
                    returned: always
                    type: str
                    sample: "/"
                expiration:
                    description: The date and time this server certificate will expire, in ISO 8601 format.
                    returned: always
                    type: str
                    sample: "2017-06-15T12:00:00+00:00"
                upload_date:
                    description: The date and time this server certificate was uploaded, in ISO 8601 format.
                    returned: always
                    type: str
                    sample: "2015-04-25T00:36:40+00:00"
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import AWSRetry, camel_dict_to_snake_dict

# Non-ansible imports
try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def list_iam_server_certificates_with_backoff(connection, path):
    paginator = connection.get_paginator('list_server_certificates')
    if path:
        return paginator.paginate(PathPrefix=path).build_full_result()
    else:
        return paginator.paginate().build_full_result()


def _get_server_certs(connection, module, name, path):
    """
    Get one or more IAM server certificates facts based on name or path. If not found, return None.

    :param connection: AWS boto3 glue connection
    :param module: Ansible module
    :param name: The name of the server certificate
    :param path: The path of the server certificate
    :return: IAM server certificates dict or None if not found
    """

    response = dict()
    response['certificates'] = []

    if name:
        try:
            response['certificates'].append(connection.get_server_certificate(ServerCertificateName=name)['ServerCertificate'])
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                return response['certificates']
            else:
                module.fail_json_aws(e, msg="The specified server certificates could not be found ")
        except botocore.exceptions.BotoCoreError as e:
            module.fail_json_aws(e, msg="The specified server certificates could not be found ")
    else:
        server_certs = list_iam_server_certificates_with_backoff(connection, path)['ServerCertificateMetadataList']

    if not name:
        for server_cert in server_certs:
            try:
                response['certificates'].append(
                    connection.get_server_certificate(ServerCertificateName=server_cert['ServerCertificateName'])['ServerCertificate'])
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchEntity':
                    continue

    return response['certificates']


def get_server_certs(connection, module):
    """Retrieve the attributes of a server certificate if it exists or all certs.
    Get one or more IAM server certificates facts based on name or ptah. As well as server certificates metadata list it will also
    get facts of the Certificates.

    :param connection: AWS boto3 iam connection
    :param module: Ansible module
    """

    list_of_server_certs = _get_server_certs(connection, module, module.params.get('name'), module.params.get('path'))

    # Snake case the certificates results
    list_of_snaked_server_certs = list()

    if list_of_server_certs:
        for server_cert in list_of_server_certs:
            list_of_snaked_server_certs.append(camel_dict_to_snake_dict(server_cert))

    module.exit_json(certificates=list_of_snaked_server_certs)


def main():
    argument_spec = (
        dict(
            name=dict(type='str'),
            path=dict(type='str')
        )
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              mutually_exclusive=[['name', 'path']])

    connection = module.client('iam')

    get_server_certs(connection, module)


if __name__ == '__main__':
    main()
