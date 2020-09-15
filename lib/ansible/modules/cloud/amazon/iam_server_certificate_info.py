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
short_description: Retrieve the information of a server certificate
description:
  - Retrieve the attributes of a server certificate
  - This module was called C(iam_server_certificate_facts) before Ansible 2.9. The usage did not change.
version_added: "2.2"
author: "Allen Sanabria (@linuxdynasty)"
requirements: [boto3, botocore]
options:
  name:
    description:
      - The name of the server certificate you are retrieving attributes for.
    required: true
    type: str
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Retrieve server certificate
- iam_server_certificate_info:
    name: production-cert
  register: server_cert

# Fail if the server certificate name was not found
- iam_server_certificate_info:
    name: production-cert
  register: server_cert
  failed_when: "{{ server_cert.results | length == 0 }}"
'''

RETURN = '''
server_certificate_id:
    description: The 21 character certificate id
    returned: success
    type: str
    sample: "ADWAJXWTZAXIPIMQHMJPO"
certificate_body:
    description: The asn1der encoded PEM string
    returned: success
    type: str
    sample: "-----BEGIN CERTIFICATE-----\nbunch of random data\n-----END CERTIFICATE-----"
server_certificate_name:
    description: The name of the server certificate
    returned: success
    type: str
    sample: "server-cert-name"
arn:
    description: The Amazon resource name of the server certificate
    returned: success
    type: str
    sample: "arn:aws:iam::911277865346:server-certificate/server-cert-name"
path:
    description: The path of the server certificate
    returned: success
    type: str
    sample: "/"
expiration:
    description: The date and time this server certificate will expire, in ISO 8601 format.
    returned: success
    type: str
    sample: "2017-06-15T12:00:00+00:00"
upload_date:
    description: The date and time this server certificate was uploaded, in ISO 8601 format.
    returned: success
    type: str
    sample: "2015-04-25T00:36:40+00:00"
'''


try:
    import boto3
    import botocore.exceptions
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, get_aws_connection_info


def get_server_certs(iam, name=None):
    """Retrieve the attributes of a server certificate if it exists or all certs.
    Args:
        iam (botocore.client.IAM): The boto3 iam instance.

    Kwargs:
        name (str): The name of the server certificate.

    Basic Usage:
        >>> import boto3
        >>> iam = boto3.client('iam')
        >>> name = "server-cert-name"
        >>> results = get_server_certs(iam, name)
        {
            "upload_date": "2015-04-25T00:36:40+00:00",
            "server_certificate_id": "ADWAJXWTZAXIPIMQHMJPO",
            "certificate_body": "-----BEGIN CERTIFICATE-----\nbunch of random data\n-----END CERTIFICATE-----",
            "server_certificate_name": "server-cert-name",
            "expiration": "2017-06-15T12:00:00+00:00",
            "path": "/",
            "arn": "arn:aws:iam::911277865346:server-certificate/server-cert-name"
        }
    """
    results = dict()
    try:
        if name:
            server_certs = [iam.get_server_certificate(ServerCertificateName=name)['ServerCertificate']]
        else:
            server_certs = iam.list_server_certificates()['ServerCertificateMetadataList']

        for server_cert in server_certs:
            if not name:
                server_cert = iam.get_server_certificate(ServerCertificateName=server_cert['ServerCertificateName'])['ServerCertificate']
            cert_md = server_cert['ServerCertificateMetadata']
            results[cert_md['ServerCertificateName']] = {
                'certificate_body': server_cert['CertificateBody'],
                'server_certificate_id': cert_md['ServerCertificateId'],
                'server_certificate_name': cert_md['ServerCertificateName'],
                'arn': cert_md['Arn'],
                'path': cert_md['Path'],
                'expiration': cert_md['Expiration'].isoformat(),
                'upload_date': cert_md['UploadDate'].isoformat(),
            }

    except botocore.exceptions.ClientError:
        pass

    return results


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        name=dict(type='str'),
    ))

    module = AnsibleModule(argument_spec=argument_spec,)
    if module._name == 'iam_server_certificate_facts':
        module.deprecate("The 'iam_server_certificate_facts' module has been renamed to 'iam_server_certificate_info'", version='2.13')

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        iam = boto3_conn(module, conn_type='client', resource='iam', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Boto3 Client Error - " + str(e.msg))

    cert_name = module.params.get('name')
    results = get_server_certs(iam, cert_name)
    module.exit_json(results=results)


if __name__ == '__main__':
    main()
