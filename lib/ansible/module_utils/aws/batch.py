# Copyright (c) 2017 Ansible Project
#
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""
This module adds shared support for Batch modules.
"""

from ansible.module_utils.ec2 import get_aws_connection_info, boto3_conn, snake_dict_to_camel_dict

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass  # Handled by HAS_BOTO3


class AWSConnection(object):
    """
    Create the connection object and client objects as required.
    """

    def __init__(self, ansible_obj, resources, boto3=True):

        self.region, self.endpoint, aws_connect_kwargs = get_aws_connection_info(ansible_obj, boto3=boto3)

        self.resource_client = dict()
        if not resources:
            resources = ['batch']

        resources.append('iam')

        for resource in resources:
            aws_connect_kwargs.update(dict(region=self.region,
                                           endpoint=self.endpoint,
                                           conn_type='client',
                                           resource=resource
                                           ))
            self.resource_client[resource] = boto3_conn(ansible_obj, **aws_connect_kwargs)

        # if region is not provided, then get default profile/session region
        if not self.region:
            self.region = self.resource_client['batch'].meta.region_name

        # set account ID
        try:
            self.account_id = self.resource_client['iam'].get_user()['User']['Arn'].split(':')[4]
        except (ClientError, ValueError, KeyError, IndexError):
            self.account_id = ''

    def client(self, resource='batch'):
        return self.resource_client[resource]


def cc(key):
    """
    Changes python key into Camel case equivalent. For example, 'compute_environment_name' becomes
    'computeEnvironmentName'.

    :param key:
    :return:
    """
    components = key.split('_')
    return components[0] + "".join([token.capitalize() for token in components[1:]])


def set_api_params(module, module_params):
    """
    Sets module parameters to those expected by the boto3 API.
    :param module:
    :param module_params:
    :return:
    """
    api_params = dict((k, v) for k, v in dict(module.params).items() if k in module_params and v is not None)
    return snake_dict_to_camel_dict(api_params)
