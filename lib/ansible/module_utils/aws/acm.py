# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Ansible Project
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
#     on behalf of Telstra Corporation Limited
#
# Common functionality to be used by the modules:
#   - acm

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

"""
Common Amazon Certificate Manager facts shared between modules
"""
import traceback
from ansible.module_utils.ec2 import get_aws_connection_info, boto3_conn
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, AWSRetry, HAS_BOTO3, boto3_tag_list_to_ansible_dict, ansible_dict_to_boto3_tag_list
from ansible.module_utils._text import to_bytes


try:
    import botocore
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # caught by imported HAS_BOTO3


class ACMServiceManager(object):
    """Handles ACM Facts Services"""

    def __init__(self, module):
        self.module = module

        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        self.client = module.client('acm')

    @AWSRetry.backoff(tries=5, delay=5, backoff=2.0, catch_extra_error_codes=['RequestInProgressException'])
    def delete_certificate_with_backoff(self, client, arn):
        client.delete_certificate(CertificateArn=arn)

    def delete_certificate(self, client, module, arn):
        module.debug("Attempting to delete certificate %s" % arn)
        try:
            self.delete_certificate_with_backoff(client, arn)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Couldn't delete certificate %s" % arn)
        module.debug("Successfully deleted certificate %s" % arn)

    @AWSRetry.backoff(tries=5, delay=5, backoff=2.0, catch_extra_error_codes=['RequestInProgressException'])
    def list_certificates_with_backoff(self, client, statuses=None):
        paginator = client.get_paginator('list_certificates')
        kwargs = dict()
        if statuses:
            kwargs['CertificateStatuses'] = statuses
        return paginator.paginate(**kwargs).build_full_result()['CertificateSummaryList']

    @AWSRetry.backoff(tries=5, delay=5, backoff=2.0, catch_extra_error_codes=['ResourceNotFoundException', 'RequestInProgressException'])
    def get_certificate_with_backoff(self, client, certificate_arn):
        response = client.get_certificate(CertificateArn=certificate_arn)
        # strip out response metadata
        return {'Certificate': response['Certificate'],
                'CertificateChain': response['CertificateChain']}

    @AWSRetry.backoff(tries=5, delay=5, backoff=2.0, catch_extra_error_codes=['ResourceNotFoundException', 'RequestInProgressException'])
    def describe_certificate_with_backoff(self, client, certificate_arn):
        return client.describe_certificate(CertificateArn=certificate_arn)['Certificate']

    @AWSRetry.backoff(tries=5, delay=5, backoff=2.0, catch_extra_error_codes=['ResourceNotFoundException', 'RequestInProgressException'])
    def list_certificate_tags_with_backoff(self, client, certificate_arn):
        return client.list_tags_for_certificate(CertificateArn=certificate_arn)['Tags']

    # Returns a list of certificates
    # if domain_name is specified, returns only certificates with that domain
    # if an ARN is specified, returns only that certificate
    # only_tags is a dict, e.g. {'key':'value'}. If specified this function will return
    # only certificates which contain all those tags (key exists, value matches).
    def get_certificates(self, client, module, domain_name=None, statuses=None, arn=None, only_tags=None):
        try:
            all_certificates = self.list_certificates_with_backoff(client=client, statuses=statuses)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Couldn't obtain certificates")
        if domain_name:
            certificates = [cert for cert in all_certificates
                            if cert['DomainName'] == domain_name]
        else:
            certificates = all_certificates

        if arn:
            # still return a list, not just one item
            certificates = [c for c in certificates if c['CertificateArn'] == arn]

        results = []
        for certificate in certificates:
            try:
                cert_data = self.describe_certificate_with_backoff(client, certificate['CertificateArn'])
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Couldn't obtain certificate metadata for domain %s" % certificate['DomainName'])

            # in some states, ACM resources do not have a corresponding cert
            if cert_data['Status'] not in ['PENDING_VALIDATION', 'VALIDATION_TIMED_OUT', 'FAILED']:
                try:
                    cert_data.update(self.get_certificate_with_backoff(client, certificate['CertificateArn']))
                except (BotoCoreError, ClientError, KeyError) as e:
                    module.fail_json_aws(e, msg="Couldn't obtain certificate data for domain %s" % certificate['DomainName'])
            cert_data = camel_dict_to_snake_dict(cert_data)
            try:
                tags = self.list_certificate_tags_with_backoff(client, certificate['CertificateArn'])
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Couldn't obtain tags for domain %s" % certificate['DomainName'])

            cert_data['tags'] = boto3_tag_list_to_ansible_dict(tags)
            results.append(cert_data)

        if only_tags:
            for tag_key in only_tags:
                try:
                    results = [c for c in results if ('tags' in c) and (tag_key in c['tags']) and (c['tags'][tag_key] == only_tags[tag_key])]
                except (TypeError, AttributeError) as e:
                    for c in results:
                        if 'tags' not in c:
                            module.debug("cert is %s" % str(c))
                    module.fail_json(msg="ACM tag filtering err", exception=e)

        return results

    # returns the domain name of a certificate (encoded in the public cert)
    # for a given ARN
    # A cert with that ARN must already exist
    def get_domain_of_cert(self, client, module, arn):
        if arn is None:
            module.fail(msg="Internal error with ACM domain fetching, no certificate ARN specified")
        try:
            cert_data = self.describe_certificate_with_backoff(client=client, certificate_arn=arn)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Couldn't obtain certificate data for arn %s" % arn)
        return cert_data['DomainName']

    @AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
    def import_certificate_with_backoff(self, client, certificate, private_key, certificate_chain, arn):
        if certificate_chain:
            if arn:
                ret = client.import_certificate(Certificate=to_bytes(certificate),
                                                PrivateKey=to_bytes(private_key),
                                                CertificateChain=to_bytes(certificate_chain),
                                                CertificateArn=arn)
            else:
                ret = client.import_certificate(Certificate=to_bytes(certificate),
                                                PrivateKey=to_bytes(private_key),
                                                CertificateChain=to_bytes(certificate_chain))
        else:
            if arn:
                ret = client.import_certificate(Certificate=to_bytes(certificate),
                                                PrivateKey=to_bytes(private_key),
                                                CertificateArn=arn)
            else:
                ret = client.import_certificate(Certificate=to_bytes(certificate),
                                                PrivateKey=to_bytes(private_key))
        return ret['CertificateArn']

    # Tags are a normal Ansible style dict
    # {'Key':'Value'}
    @AWSRetry.backoff(tries=5, delay=5, backoff=2.0, catch_extra_error_codes=['ResourceNotFoundException', 'RequestInProgressException'])
    def tag_certificate_with_backoff(self, client, arn, tags):
        aws_tags = ansible_dict_to_boto3_tag_list(tags)
        client.add_tags_to_certificate(CertificateArn=arn, Tags=aws_tags)

    def import_certificate(self, client, module, certificate, private_key, arn=None, certificate_chain=None, tags=None):

        original_arn = arn

        # upload cert
        try:
            arn = self.import_certificate_with_backoff(client, certificate, private_key, certificate_chain, arn)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Couldn't upload new certificate")

        if original_arn and (arn != original_arn):
            # I'm not sure whether the API guarentees that the ARN will not change
            # I'm failing just in case.
            # If I'm wrong, I'll catch it in the integration tests.
            module.fail_json(msg="ARN changed with ACM update, from %s to %s" % (original_arn, arn))

        # tag that cert
        try:
            self.tag_certificate_with_backoff(client, arn, tags)
        except (BotoCoreError, ClientError) as e:
            module.debug("Attempting to delete the cert we just created, arn=%s" % arn)
            try:
                self.delete_certificate_with_backoff(client, arn)
            except Exception as f:
                module.warn("Certificate %s exists, and is not tagged. So Ansible will not see it on the next run.")
                module.fail_json_aws(e, msg="Couldn't tag certificate %s, couldn't delete it either" % arn)
            module.fail_json_aws(e, msg="Couldn't tag certificate %s" % arn)

        return arn
