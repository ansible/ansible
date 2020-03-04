#!/usr/bin/python
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: aws_acm
short_description: Upload and delete certificates in the AWS Certificate Manager service
description:
  - Import and delete certificates in Amazon Web Service's Certificate Manager (AWS ACM).
  - >
    This module does not currently interact with AWS-provided certificates.
    It currently only manages certificates provided to AWS by the user.
  - The ACM API allows users to upload multiple certificates for the same domain name,
    and even multiple identical certificates.
    This module attempts to restrict such freedoms, to be idempotent, as per the Ansible philosophy.
    It does this through applying AWS resource "Name" tags to ACM certificates.
  - >
    When I(state=present),
    if there is one certificate in ACM
    with a C(Name) tag equal to the C(name_tag) parameter,
    and an identical body and chain,
    this task will succeed without effect.
  - >
    When I(state=present),
    if there is one certificate in ACM
    a I(Name) tag equal to the I(name_tag) parameter,
    and a different body,
    this task will overwrite that certificate.
  - >
    When I(state=present),
    if there are multiple certificates in ACM
    with a I(Name) tag equal to the I(name_tag) parameter,
    this task will fail.
  - >
    When I(state=absent) and I(certificate_arn) is defined,
    this module will delete the ACM resource with that ARN if it exists in this region,
    and succeed without effect if it doesn't exist.
  - >
    When I(state=absent) and I(domain_name) is defined,
    this module will delete all ACM resources in this AWS region with a corresponding domain name.
    If there are none, it will succeed without effect.
  - >
    When I(state=absent) and I(certificate_arn) is not defined,
    and I(domain_name) is not defined,
    this module will delete all ACM resources in this AWS region with a corresponding I(Name) tag.
    If there are none, it will succeed without effect.
  - Note that this may not work properly with keys of size 4096 bits, due to a limitation of the ACM API.
version_added: "2.10"
options:
  certificate:
    description:
      - The body of the PEM encoded public certificate.
      - Required when I(state) is not C(absent).
      - If your certificate is in a file, use C(lookup('file', 'path/to/cert.pem')).
    type: str

  certificate_arn:
    description:
      - The ARN of a certificate in ACM to delete
      - Ignored when I(state=present).
      - If I(state=absent), you must provide one of I(certificate_arn), I(domain_name) or I(name_tag).
      - >
        If I(state=absent) and no resource exists with this ARN in this region,
        the task will succeed with no effect.
      - >
        If I(state=absent) and the corresponding resource exists in a different region,
        this task may report success without deleting that resource.
    type: str
    aliases: [arn]

  certificate_chain:
    description:
      - The body of the PEM encoded chain for your certificate.
      - If your certificate chain is in a file, use C(lookup('file', 'path/to/chain.pem')).
      - Ignored when I(state=absent)
    type: str

  domain_name:
    description:
      - The domain name of the certificate.
      - >
        If I(state=absent) and I(domain_name) is specified,
        this task will delete all ACM certificates with this domain.
      - Exactly one of I(domain_name), I(name_tag)  and I(certificate_arn) must be provided.
      - >
        If I(state=present) this must not be specified.
        (Since the domain name is encoded within the public certificate's body.)
    type: str
    aliases: [domain]

  name_tag:
    description:
      - The unique identifier for tagging resources using AWS tags, with key I(Name).
      - This can be any set of characters accepted by AWS for tag values.
      - >
        This is to ensure Ansible can treat certificates idempotently,
        even though the ACM API allows duplicate certificates.
      - If I(state=preset), this must be specified.
      - >
        If I(state=absent), you must provide exactly one of
        I(certificate_arn), I(domain_name) or I(name_tag).
    type: str
    aliases: [name]

  private_key:
    description:
      - The body of the PEM encoded private key.
      - Required when I(state=present).
      - Ignored when I(state=absent).
      - If your private key is in a file, use C(lookup('file', 'path/to/key.pem')).
    type: str

  state:
    description:
      - >
        If I(state=present), the specified public certificate and private key
        will be uploaded, with I(Name) tag equal to I(name_tag).
      - >
        If I(state=absent), any certificates in this region
        with a corresponding I(domain_name), I(name_tag) or I(certificate_arn)
        will be deleted.
    choices: [present, absent]
    default: present
    type: str
requirements:
  - boto3
author:
  - Matthew Davis (@matt-telstra) on behalf of Telstra Corporation Limited
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''

- name: upload a self-signed certificate
  aws_acm:
    certificate: "{{ lookup('file', 'cert.pem' ) }}"
    privateKey: "{{ lookup('file', 'key.pem' ) }}"
    name_tag: my_cert # to be applied through an AWS tag as  "Name":"my_cert"
    region: ap-southeast-2 # AWS region

- name: create/update a certificate with a chain
  aws_acm:
    certificate: "{{ lookup('file', 'cert.pem' ) }}"
    privateKey: "{{ lookup('file', 'key.pem' ) }}"
    name_tag: my_cert
    certificate_chain: "{{ lookup('file', 'chain.pem' ) }}"
    state: present
    region: ap-southeast-2
  register: cert_create

- name: print ARN of cert we just created
  debug:
    var: cert_create.certificate.arn

- name: delete the cert we just created
  aws_acm:
    name_tag: my_cert
    state: absent
    region: ap-southeast-2

- name: delete a certificate with a particular ARN
  aws_acm:
    certificate_arn: "arn:aws:acm:ap-southeast-2:123456789012:certificate/01234567-abcd-abcd-abcd-012345678901"
    state: absent
    region: ap-southeast-2

- name: delete all certificates with a particular domain name
  aws_acm:
    domain_name: acm.ansible.com
    state: absent
    region: ap-southeast-2

'''

RETURN = '''
certificate:
  description: Information about the certificate which was uploaded
  type: complex
  returned: when I(state=present)
  contains:
    arn:
      description: The ARN of the certificate in ACM
      type: str
      returned: when I(state=present)
      sample: "arn:aws:acm:ap-southeast-2:123456789012:certificate/01234567-abcd-abcd-abcd-012345678901"
    domain_name:
      description: The domain name encoded within the public certificate
      type: str
      returned: when I(state=present)
      sample: acm.ansible.com
arns:
  description: A list of the ARNs of the certificates in ACM which were deleted
  type: list
  elements: str
  returned: when I(state=absent)
  sample:
   - "arn:aws:acm:ap-southeast-2:123456789012:certificate/01234567-abcd-abcd-abcd-012345678901"
'''


from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.aws.acm import ACMServiceManager
from ansible.module_utils._text import to_text
import base64
import re  # regex library


# Takes in two text arguments
# Each a PEM encoded certificate
# Or a chain of PEM encoded certificates
# May include some lines between each chain in the cert, e.g. "Subject: ..."
# Returns True iff the chains/certs are functionally identical (including chain order)
def chain_compare(module, a, b):

    chain_a_pem = pem_chain_split(module, a)
    chain_b_pem = pem_chain_split(module, b)

    if len(chain_a_pem) != len(chain_b_pem):
        return False

    # Chain length is the same
    for (ca, cb) in zip(chain_a_pem, chain_b_pem):
        der_a = PEM_body_to_DER(module, ca)
        der_b = PEM_body_to_DER(module, cb)
        if der_a != der_b:
            return False

    return True


# Takes in PEM encoded data with no headers
# returns equivilent DER as byte array
def PEM_body_to_DER(module, pem):
    try:
        der = base64.b64decode(to_text(pem))
    except (ValueError, TypeError) as e:
        module.fail_json_aws(e, msg="Unable to decode certificate chain")
    return der


# Store this globally to avoid repeated recompilation
pem_chain_split_regex = re.compile(r"------?BEGIN [A-Z0-9. ]*CERTIFICATE------?([a-zA-Z0-9\+\/=\s]+)------?END [A-Z0-9. ]*CERTIFICATE------?")


# Use regex to split up a chain or single cert into an array of base64 encoded data
# Using "-----BEGIN CERTIFICATE-----" and "----END CERTIFICATE----"
# Noting that some chains have non-pem data in between each cert
# This function returns only what's between the headers, excluding the headers
def pem_chain_split(module, pem):

    pem_arr = re.findall(pem_chain_split_regex, to_text(pem))

    if len(pem_arr) == 0:
        # This happens if the regex doesn't match at all
        module.fail_json(msg="Unable to split certificate chain. Possibly zero-length chain?")

    return pem_arr


def main():
    argument_spec = dict(
        certificate=dict(),
        certificate_arn=dict(aliases=['arn']),
        certificate_chain=dict(),
        domain_name=dict(aliases=['domain']),
        name_tag=dict(aliases=['name']),
        private_key=dict(no_log=True),
        state=dict(default='present', choices=['present', 'absent'])
    )
    required_if = [
        ['state', 'present', ['certificate', 'name_tag', 'private_key']],
    ]
    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True, required_if=required_if)
    acm = ACMServiceManager(module)

    # Check argument requirements
    if module.params['state'] == 'present':
        if module.params['certificate_arn']:
            module.fail_json(msg="Parameter 'certificate_arn' is only valid if parameter 'state' is specified as 'absent'")
    else:  # absent
        # exactly one of these should be specified
        absent_args = ['certificate_arn', 'domain_name', 'name_tag']
        if sum([(module.params[a] is not None) for a in absent_args]) != 1:
            for a in absent_args:
                module.debug("%s is %s" % (a, module.params[a]))
            module.fail_json(msg="If 'state' is specified as 'absent' then exactly one of 'name_tag', certificate_arn' or 'domain_name' must be specified")

    if module.params['name_tag']:
        tags = dict(Name=module.params['name_tag'])
    else:
        tags = None

    client = module.client('acm')

    # fetch the list of certificates currently in ACM
    certificates = acm.get_certificates(client=client,
                                        module=module,
                                        domain_name=module.params['domain_name'],
                                        arn=module.params['certificate_arn'],
                                        only_tags=tags)

    module.debug("Found %d corresponding certificates in ACM" % len(certificates))

    if module.params['state'] == 'present':
        if len(certificates) > 1:
            msg = "More than one certificate with Name=%s exists in ACM in this region" % module.params['name_tag']
            module.fail_json(msg=msg, certificates=certificates)
        elif len(certificates) == 1:
            # update the existing certificate
            module.debug("Existing certificate found in ACM")
            old_cert = certificates[0]  # existing cert in ACM
            if ('tags' not in old_cert) or ('Name' not in old_cert['tags']) or (old_cert['tags']['Name'] != module.params['name_tag']):
                # shouldn't happen
                module.fail_json(msg="Internal error, unsure which certificate to update", certificate=old_cert)

            if 'certificate' not in old_cert:
                # shouldn't happen
                module.fail_json(msg="Internal error, unsure what the existing cert in ACM is", certificate=old_cert)

            # Are the existing certificate in ACM and the local certificate the same?
            same = True
            same &= chain_compare(module, old_cert['certificate'], module.params['certificate'])
            if module.params['certificate_chain']:
                # Need to test this
                # not sure if Amazon appends the cert itself to the chain when self-signed
                same &= chain_compare(module, old_cert['certificate_chain'], module.params['certificate_chain'])
            else:
                # When there is no chain with a cert
                # it seems Amazon returns the cert itself as the chain
                same &= chain_compare(module, old_cert['certificate_chain'], module.params['certificate'])

            if same:
                module.debug("Existing certificate in ACM is the same, doing nothing")
                domain = acm.get_domain_of_cert(client=client, module=module, arn=old_cert['certificate_arn'])
                module.exit_json(certificate=dict(domain_name=domain, arn=old_cert['certificate_arn']), changed=False)
            else:
                module.debug("Existing certificate in ACM is different, overwriting")

                # update cert in ACM
                arn = acm.import_certificate(client, module,
                                             certificate=module.params['certificate'],
                                             private_key=module.params['private_key'],
                                             certificate_chain=module.params['certificate_chain'],
                                             arn=old_cert['certificate_arn'],
                                             tags=tags)
                domain = acm.get_domain_of_cert(client=client, module=module, arn=arn)
                module.exit_json(certificate=dict(domain_name=domain, arn=arn), changed=True)
        else:  # len(certificates) == 0
            module.debug("No certificate in ACM. Creating new one.")
            arn = acm.import_certificate(client=client,
                                         module=module,
                                         certificate=module.params['certificate'],
                                         private_key=module.params['private_key'],
                                         certificate_chain=module.params['certificate_chain'],
                                         tags=tags)
            domain = acm.get_domain_of_cert(client=client, module=module, arn=arn)

            module.exit_json(certificate=dict(domain_name=domain, arn=arn), changed=True)

    else:  # state == absent
        for cert in certificates:
            acm.delete_certificate(client, module, cert['certificate_arn'])
        module.exit_json(arns=[cert['certificate_arn'] for cert in certificates],
                         changed=(len(certificates) > 0))


if __name__ == '__main__':
    # tests()
    main()
