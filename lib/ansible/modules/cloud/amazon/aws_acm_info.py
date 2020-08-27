#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: aws_acm_info
short_description: Retrieve certificate information from AWS Certificate Manager service
description:
  - Retrieve information for ACM certificates
  - This module was called C(aws_acm_facts) before Ansible 2.9. The usage did not change.
version_added: "2.5"
options:
  domain_name:
    description:
      - The domain name of an ACM certificate to limit the search to
    aliases:
      - name
  statuses:
    description:
      - Status to filter the certificate results
    choices: ['PENDING_VALIDATION', 'ISSUED', 'INACTIVE', 'EXPIRED', 'VALIDATION_TIMED_OUT', 'REVOKED', 'FAILED']
requirements:
  - boto3
author:
  - Will Thames (@willthames)
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
- name: obtain all ACM certificates
  aws_acm_info:

- name: obtain all information for a single ACM certificate
  aws_acm_info:
    domain_name: "*.example_com"

- name: obtain all certificates pending validation
  aws_acm_info:
    statuses:
    - PENDING_VALIDATION
'''

RETURN = '''
certificates:
  description: A list of certificates
  returned: always
  type: complex
  contains:
    certificate:
      description: The ACM Certificate body
      returned: when certificate creation is complete
      sample: '-----BEGIN CERTIFICATE-----\\nMII.....-----END CERTIFICATE-----\\n'
      type: str
    certificate_arn:
      description: Certificate ARN
      returned: always
      sample: arn:aws:acm:ap-southeast-2:123456789012:certificate/abcd1234-abcd-1234-abcd-123456789abc
      type: str
    certificate_chain:
      description: Full certificate chain for the certificate
      returned: when certificate creation is complete
      sample: '-----BEGIN CERTIFICATE-----\\nMII...\\n-----END CERTIFICATE-----\\n-----BEGIN CERTIFICATE-----\\n...'
      type: str
    created_at:
      description: Date certificate was created
      returned: always
      sample: '2017-08-15T10:31:19+10:00'
      type: str
    domain_name:
      description: Domain name for the certificate
      returned: always
      sample: '*.example.com'
      type: str
    domain_validation_options:
      description: Options used by ACM to validate the certificate
      returned: when certificate type is AMAZON_ISSUED
      type: complex
      contains:
        domain_name:
          description: Fully qualified domain name of the certificate
          returned: always
          sample: example.com
          type: str
        validation_domain:
          description: The domain name ACM used to send validation emails
          returned: always
          sample: example.com
          type: str
        validation_emails:
          description: A list of email addresses that ACM used to send domain validation emails
          returned: always
          sample:
          - admin@example.com
          - postmaster@example.com
          type: list
        validation_status:
          description: Validation status of the domain
          returned: always
          sample: SUCCESS
          type: str
    failure_reason:
      description: Reason certificate request failed
      returned: only when certificate issuing failed
      type: str
      sample: NO_AVAILABLE_CONTACTS
    in_use_by:
      description: A list of ARNs for the AWS resources that are using the certificate.
      returned: always
      sample: []
      type: list
    issued_at:
      description: Date certificate was issued
      returned: always
      sample: '2017-01-01T00:00:00+10:00'
      type: str
    issuer:
      description: Issuer of the certificate
      returned: always
      sample: Amazon
      type: str
    key_algorithm:
      description: Algorithm used to generate the certificate
      returned: always
      sample: RSA-2048
      type: str
    not_after:
      description: Date after which the certificate is not valid
      returned: always
      sample: '2019-01-01T00:00:00+10:00'
      type: str
    not_before:
      description: Date before which the certificate is not valid
      returned: always
      sample: '2017-01-01T00:00:00+10:00'
      type: str
    renewal_summary:
      description: Information about managed renewal process
      returned: when certificate is issued by Amazon and a renewal has been started
      type: complex
      contains:
        domain_validation_options:
          description: Options used by ACM to validate the certificate
          returned: when certificate type is AMAZON_ISSUED
          type: complex
          contains:
            domain_name:
              description: Fully qualified domain name of the certificate
              returned: always
              sample: example.com
              type: str
            validation_domain:
              description: The domain name ACM used to send validation emails
              returned: always
              sample: example.com
              type: str
            validation_emails:
              description: A list of email addresses that ACM used to send domain validation emails
              returned: always
              sample:
              - admin@example.com
              - postmaster@example.com
              type: list
            validation_status:
              description: Validation status of the domain
              returned: always
              sample: SUCCESS
              type: str
        renewal_status:
          description: Status of the domain renewal
          returned: always
          sample: PENDING_AUTO_RENEWAL
          type: str
    revocation_reason:
      description: Reason for certificate revocation
      returned: when the certificate has been revoked
      sample: SUPERCEDED
      type: str
    revoked_at:
      description: Date certificate was revoked
      returned: when the certificate has been revoked
      sample: '2017-09-01T10:00:00+10:00'
      type: str
    serial:
      description: The serial number of the certificate
      returned: always
      sample: 00:01:02:03:04:05:06:07:08:09:0a:0b:0c:0d:0e:0f
      type: str
    signature_algorithm:
      description: Algorithm used to sign the certificate
      returned: always
      sample: SHA256WITHRSA
      type: str
    status:
      description: Status of the certificate in ACM
      returned: always
      sample: ISSUED
      type: str
    subject:
      description: The name of the entity that is associated with the public key contained in the certificate
      returned: always
      sample: CN=*.example.com
      type: str
    subject_alternative_names:
      description: Subject Alternative Names for the certificate
      returned: always
      sample:
      - '*.example.com'
      type: list
    tags:
      description: Tags associated with the certificate
      returned: always
      type: dict
      sample:
        Application: helloworld
        Environment: test
    type:
      description: The source of the certificate
      returned: always
      sample: AMAZON_ISSUED
      type: str
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, get_aws_connection_info
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, AWSRetry, HAS_BOTO3, boto3_tag_list_to_ansible_dict


try:
    import botocore
except ImportError:
    pass  # caught by imported HAS_BOTO3


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def list_certificates_with_backoff(client, statuses=None):
    paginator = client.get_paginator('list_certificates')
    kwargs = dict()
    if statuses:
        kwargs['CertificateStatuses'] = statuses
    return paginator.paginate(**kwargs).build_full_result()['CertificateSummaryList']


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_certificate_with_backoff(client, certificate_arn):
    response = client.get_certificate(CertificateArn=certificate_arn)
    # strip out response metadata
    return {'Certificate': response['Certificate'],
            'CertificateChain': response['CertificateChain']}


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def describe_certificate_with_backoff(client, certificate_arn):
    return client.describe_certificate(CertificateArn=certificate_arn)['Certificate']


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def list_certificate_tags_with_backoff(client, certificate_arn):
    return client.list_tags_for_certificate(CertificateArn=certificate_arn)['Tags']


def get_certificates(client, module, domain_name=None, statuses=None):
    try:
        all_certificates = list_certificates_with_backoff(client, statuses)
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
            cert_data = describe_certificate_with_backoff(client, certificate['CertificateArn'])
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Couldn't obtain certificate metadata for domain %s" % certificate['DomainName'],
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
        if cert_data['Status'] not in ['PENDING_VALIDATION', 'VALIDATION_TIMED_OUT', 'FAILED']:
            try:
                cert_data.update(get_certificate_with_backoff(client, certificate['CertificateArn']))
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] != "RequestInProgressException":
                    module.fail_json(msg="Couldn't obtain certificate data for domain %s" % certificate['DomainName'],
                                     exception=traceback.format_exc(),
                                     **camel_dict_to_snake_dict(e.response))
        cert_data = camel_dict_to_snake_dict(cert_data)
        try:
            tags = list_certificate_tags_with_backoff(client, certificate['CertificateArn'])
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Couldn't obtain tags for domain %s" % certificate['DomainName'],
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
        cert_data['tags'] = boto3_tag_list_to_ansible_dict(tags)
        results.append(cert_data)
    return results


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            domain_name=dict(aliases=['name']),
            statuses=dict(type='list', choices=['PENDING_VALIDATION', 'ISSUED', 'INACTIVE', 'EXPIRED', 'VALIDATION_TIMED_OUT', 'REVOKED', 'FAILED']),
        )
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    if module._name == 'aws_acm_facts':
        module.deprecate("The 'aws_acm_facts' module has been renamed to 'aws_acm_info'", version='2.13')

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 and botocore are required by this module')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    client = boto3_conn(module, conn_type='client', resource='acm',
                        region=region, endpoint=ec2_url, **aws_connect_kwargs)

    certificates = get_certificates(client, module, domain_name=module.params['domain_name'], statuses=module.params['statuses'])
    module.exit_json(certificates=certificates)


if __name__ == '__main__':
    main()
