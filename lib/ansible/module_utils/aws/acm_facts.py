# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
#
# Author:
#   - Matthew Davis <Matthew.Davis.2@team.telstra.com>
#
# Common functionality to be used by the modules:
#   - acm


"""
Common Amazon Certificate Manager facts shared between modules
"""
import traceback
from ansible.module_utils.ec2 import get_aws_connection_info, boto3_conn
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, AWSRetry, HAS_BOTO3, boto3_tag_list_to_ansible_dict

try:
    import botocore
except ImportError:
    pass


class ACMFactsServiceManager(object):
    """Handles ACM Facts Services"""

    def __init__(self, module):
        self.module = module

        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        self.client = boto3_conn(module, conn_type='client',
                                 resource='acm', region=region,
                                 endpoint=ec2_url, **aws_connect_kwargs)


    @AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
    def list_certificates_with_backoff(self, client, statuses=None):
        paginator = client.get_paginator('list_certificates')
        kwargs = dict()
        if statuses:
            kwargs['CertificateStatuses'] = statuses
        return paginator.paginate(**kwargs).build_full_result()['CertificateSummaryList']
    
    
    @AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
    def get_certificate_with_backoff(self, client, certificate_arn):
        response = client.get_certificate(CertificateArn=certificate_arn)
        # strip out response metadata
        return {'Certificate': response['Certificate'],
                'CertificateChain': response['CertificateChain']}
    
    
    @AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
    def describe_certificate_with_backoff(self, client, certificate_arn):
        return client.describe_certificate(CertificateArn=certificate_arn)['Certificate']
    
    
    @AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
    def list_certificate_tags_with_backoff(self, client, certificate_arn):
        return client.list_tags_for_certificate(CertificateArn=certificate_arn)['Tags']
    
    
    def get_certificates(self, client, module, domain_name=None, statuses=None):
        try:
            all_certificates = self.list_certificates_with_backoff(client, statuses)
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Couldn't obtain certificates",
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
        if domain_name:
            certificates = [cert for cert in all_certificates
                            if cert['DomainName'] == domain_name]
        else:
            certificates = all_certificates
    
        results = []
        for certificate in certificates:
            try:
                cert_data = self.describe_certificate_with_backoff(client, certificate['CertificateArn'])
            except botocore.exceptions.ClientError as e:
                module.fail_json(msg="Couldn't obtain certificate metadata for domain %s" % certificate['DomainName'],
                                 exception=traceback.format_exc(),
                                 **camel_dict_to_snake_dict(e.response))
            try:
                cert_data.update(self.get_certificate_with_backoff(client, certificate['CertificateArn']))
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] != "RequestInProgressException":
                    module.fail_json(msg="Couldn't obtain certificate data for domain %s" % certificate['DomainName'],
                                     exception=traceback.format_exc(),
                                     **camel_dict_to_snake_dict(e.response))
            cert_data = camel_dict_to_snake_dict(cert_data)
            try:
                tags = self.list_certificate_tags_with_backoff(client, certificate['CertificateArn'])
            except botocore.exceptions.ClientError as e:
                module.fail_json(msg="Couldn't obtain tags for domain %s" % certificate['DomainName'],
                                 exception=traceback.format_exc(),
                                 **camel_dict_to_snake_dict(e.response))
            cert_data['tags'] = boto3_tag_list_to_ansible_dict(tags)
            results.append(cert_data)
        return results
