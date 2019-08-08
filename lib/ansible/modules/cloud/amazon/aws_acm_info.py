#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

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
    type: str
  statuses:
    description:
      - Status to filter the certificate results
    choices: ['PENDING_VALIDATION', 'ISSUED', 'INACTIVE', 'EXPIRED', 'VALIDATION_TIMED_OUT', 'REVOKED', 'FAILED']
    type: list
    elements: str
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

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, get_aws_connection_info
from ansible.module_utils.aws.acm_facts import ACMFactsServiceManager

try:
    import botocore
except ImportError:
    pass  # caught by imported HAS_BOTO3



def main():
    argument_spec = dict(
          domain_name=dict(aliases=['name']),
          statuses=dict(type='list', choices=['PENDING_VALIDATION', 'ISSUED', 'INACTIVE', 'EXPIRED', 'VALIDATION_TIMED_OUT', 'REVOKED', 'FAILED']),
    )
    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    acm_facts = ACMFactsServiceManager(module)
    
    if module._name == 'aws_acm_facts':
        module.deprecate("The 'aws_acm_facts' module has been renamed to 'aws_acm_info'", version='2.13')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    client = boto3_conn(module, conn_type='client', resource='acm',
                        region=region, endpoint=ec2_url, **aws_connect_kwargs)

    certificates = acm_facts.get_certificates(client, module, domain_name=module.params['domain_name'], statuses=module.params['statuses'])
    module.exit_json(certificates=certificates)


if __name__ == '__main__':
    main()
