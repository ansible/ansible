#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: iam_cert_facts
short_description: Retrieves iam_cert details using AWS methods.
description:
    - Gets various details related to IAM cert, ARN, expiration, Certificates.
version_added: "2.4"
options:
  certificate_name:
    description:
      - The name of the server certificate you want to retrieve information about.
    required: False

  path_prefix:
    description:
      - The path prefix for filtering the results. http://docs.aws.amazon.com/cli/latest/reference/iam/list-server-certificates.html#options
    required: False


author: Julien Thebault (@Lujeni)
extends_documentation_fragment: aws
'''

EXAMPLES = '''
- name: List all server certificates
  iam_cert_facts:
  register: server_certificates

- name: Retrieve specific certificate
  iam_cert_facts:
      certificate_name: cookie

- name: List all server certificates with this path
  iam_cert_facts:
      path_prefix: /company/servercerts
'''

RETURN = '''
is_truncated:
    description: A flag that indicates whether there are more items to return.
    returned: always
    type: bool
    sample: false

response_metadata:
    description: Response metadata.
    returned: always
    type: dict
    sample: {"http_status_code": 200, "request_id": "9f6d-671298e72d8b"}

server_certificate_metadata_list:
    description: Metadata list.
    returned: always
    type: dict
    sample: http://boto3.readthedocs.io/en/latest/reference/services/iam.html#IAM.Client.list_server_certificates
'''

from traceback import format_exc

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (
    boto3_conn, ec2_argument_spec, get_aws_connection_info,
    camel_dict_to_snake_dict, HAS_BOTO3)

from botocore.exceptions import ClientError


def get_server_certificate(client, module, server_certificate_name):
    """ Retrieves information about the specified server certificate stored in IAM.
    """
    try:
        response = client.get_server_certificate(
            ServerCertificateName=server_certificate_name)
    except ClientError as e:
        client_error = camel_dict_to_snake_dict(e.response)
        if client_error['error']['code'] == 'NoSuchEntity':
            return client_error['error']
        else:
            raise
    except Exception as e:
        module.fail_json(msg="Unable to get server certificate :: %s" % str(e), exception=format_exc())
    return response


def list_server_certificates(client, module, path_prefix):
    """ Lists the server certificates stored in IAM that have the specified path prefix.
        If none exist, the action returns an empty list.
    """
    try:
        if path_prefix:
            response = client.list_server_certificates(PathPrefix=path_prefix)
        else:
            response = client.list_server_certificates()
    except Exception as e:
        module.fail_json(msg="Unable to get server certificates :: %s" % str(e), exception=format_exc())
    return response


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        certificate_name=dict(type='str', default=None),
        path_prefix=dict(type='str', default=None),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['certificate_name', 'path_prefix'],
        ],
        supports_check_mode=False,
    )

    if not HAS_BOTO3:
        module.fail_json(msg="boto3 is required")

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        iam_cert = boto3_conn(module, conn_type='client', resource='iam',
                              region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except Exception as e:
        module.fail_json(msg="Can't authorize connection - %s " % str(e), exception=format_exc())

    certificate_name = module.params['certificate_name']
    path_prefix = module.params['path_prefix']

    if certificate_name:
        results = get_server_certificate(
            client=iam_cert, module=module, server_certificate_name=certificate_name)
    else:
        results = list_server_certificates(client=iam_cert, module=module, path_prefix=path_prefix)

    module.exit_json(**camel_dict_to_snake_dict(results))

if __name__ == '__main__':
    main()
