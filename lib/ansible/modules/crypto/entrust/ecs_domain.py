#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2019 Entrust Datacard Corporation.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ecs_domain
author:
    - Chris Trufan (@ctrufan)
version_added: '2.10'
short_description: Request validation of a domain with the Entrust Certificate Services (ECS) API.
description:
    - Request validation or re-validation of a domain with the Entrust Certificate Services (ECS) API.
    - Requires credentials for the L(Entrust Certificate Services,https://www.entrustdatacard.com/products/categories/ssl-certificates) (ECS) API.
    - In the case of validation modes that require action on returned data (C(FILE) and C(DNS)) module will return the data needed to validate.
    - For C(validation_method=DNS), the returned DNS value must be present at the location specified by return parameter I(location).
notes:
    - There is a small delay (typically about 5 seconds, but as long as 30) before obtaining the random values when requesting a validation.
      Be aware of that if doing bulk domain requests.
options:
    client_id:
        description:
            - The client ID to request the domain be associated with.
            - If no client ID is specified, the domain will be added under the primary client with ID of 1.
        type: int
        default: 1
    force:
        description:
            - Force a reverification regardless of state of current domain.
            - This can be used to change the state of an in process verification.
        type: bool
        default: false
    domain_name:
        description:
            - The domain name to be verified or reverified.
        type: str
        required: true
    verification_method:
        description:
            - The verification method to be used to prove control of the domain.
            - If C(verification_method=EMAIL), the value I(verification_email) is required, and no values are returned for I(verification_content) and
              I(verification_location). An email will be sent to the address in I(verification_email) with instructions on how to verify control of the domain.
            - If C(verification_method=DNS), the value I(DNS_contents) must be stored in location I(DNS_location), with a DNS record type of
              I(verification_DNS_record_type). To prove domain ownership, update your DNS records so the text string returned by I(DNS_contents) is available at
              I(DNS_location).
            - If C(verification_method=WEB_SERVER), the contents of return value I(file_contents) must be made available on a web server accessible at location
              I(file_location).
            - If C(verification_method=MANUAL), the domain will be validated with a manual process. This is not recommended.
        type: str
        choices: [ 'DNS', 'EMAIL', 'MANUAL', 'WEB_SERVER']
        required: true
    verification_email:
        description:
            - email address to be used to verify domain ownership.
            - 'email address must be either an email address present in the WHOIS data for I(domain_name), or one of the following constructed emails:
              admin@I(domain_name)), administrator@I(domain_name), webmaster@I(domain_name), hostmaster@I(domain_name), postmaster@I(domain_name)'
            - To verify domain ownership, domain owner must follow the instructions in the email they receive.
            - Required if C(verification_method=EMAIL)
            - Only allowed if C(verification_method=EMAIL)
        type: str
    ov_remaining_days:
        description:
            - The number of days the domain must have left being valid for OV eligibility, if it is already a validated domain. I(ov_days_remaining) is
              less than I(ov_remaining_days), a new validation will be requested using I(validation_method).
        type: int
        default: 60
    ev_remaining_days:
        description:
            - The number of days the domain must have left being valid for EV eligibility, if it is already a validated domain. I(ev_days_remaining) is
              less than I(ev_remaining_days), a new validation will be requested using I(validation_method).
        type: int
seealso:
    - module: openssl_certificate
      description: Can be used to request certificates from ECS, with C(provider=ECS).
    - module: ecs_certificate
      description: Can be used to request a Certificate from ECS using a verified domain.
extends_documentation_fragment:
    - ecs_credential
'''

EXAMPLES = r'''
- name: Request domain validation using email validation for client ID of 2.
  ecs_domain:
    domain_name: ansible.com
    client_id: 2
    verification_method: EMAIL
    verification_email: admin@ansible.com

- name: Request domain validation using DNS. If domain is already valid,
        request revalidation if expires within 90 days
  ecs_domain:
    domain_name: ansible.com
    verification_method: DNS
    ov_remaining_days: 90

- name: Request domain validation using web server validation, and revalidate
        if fewer than 60 days remaining of EV eligibility.
  ecs_domain:
    domain_name: ansible.com
    verification_method: WEB_SERVER
    ev_remaining_days: 60

- name: Request domain validation using manual validation.
  ecs_domain:
    domain_name: ansible.com
    verification_method: MANUAL
'''

RETURN = '''
domain_status:
    description: Status of the current domain. Will be one of C(APPROVED), C(DECLINED), C(CANCELLED), C(INITIAL_VERIFICATION), C(DECLINED), C(CANCELLED),
                 C(RE_VERIFICATION), C(EXPIRED), C(EXPIRING)
    returned: changed or success
    type: str
    sample: APPROVED
verification_method:
    description: Verification method used to request the domain validation. If C(changed) will be the same as I(verification_method) input parameter.
    returned: changed or success
    type: str
    sample: DNS
file_location:
    description: The location that ECS will be expecting to be able to find the file for domain verification, containing the contents of I(file_contents).
    returned: I(verification_method) is C(WEB_SERVER)
    type: str
    sample: http://ansible.com/.well-known/pki-validation/abcd.txt
file_contents:
    description: The contents of the file that ECS will be expecting to find at C(file_location).
    returned: I(verification_method) is C(WEB_SERVER)
    type: str
    sample: AB23CD41432522FF2526920393982FAB
emails:
    description:
        - The list of emails used to request validation of this domain.
        - Domains requested using this module will only have a list of size 1.
    returned: I(verification_method) is C(EMAIL)
    type: list
    sample: [ admin@ansible.com, administrator@ansible.com ]
dns_location:
    description: The location that ECS will be expecting to be able to find the DNS entry for domain verification, containing the contents of I(DNS_contents).
    returned: changed and if I(verification_method) is C(DNS)
    type: str
    sample: _pki-validation.ansible.com
dns_contents:
    description: The value that ECS will be expecting to find in the DNS record located at I(DNS_location).
    returned: changed and if I(verification_method) is C(DNS)
    type: str
    sample: AB23CD41432522FF2526920393982FAB
dns_resource_type:
    description: The type of resource record that ECS will be expecting for the DNS record located at I(DNS_location).
    returned: changed and if I(verification_method) is C(DNS)
    type: str
    sample: TXT
client_id:
    description: Client ID that the domain belongs to. If the input value I(client_id) is specified, this will always be the same as I(client_id)
    returned: changed or success
    type: int
    sample: 1
ov_eligible:
    description: Whether the domain is eligible for submission of "OV" certificates. Will never be C(False) if I(ov_eligible) is C(True)
    returned: success and I(domain_status) is C(APPROVED), C(RE_VERIFICATION) or C(EXPIRING).
    type: bool
    sample: True
ov_days_remaining:
    description: The number of days the domain remains eligible for submission of "OV" certificates. Will never be less than the value of I(ev_days_remaining)
    returned: success and I(ov_eligible) is C(True) and I(domain_status) is C(APPROVED), C(RE_VERIFICATION) or C(EXPIRING).
    type: int
    sample: 129
ev_eligible:
    description: Whether the domain is eligible for submission of "EV" certificates. Will never be C(True) if I(ov_eligible) is C(False)
    returned: success and I(domain_status) is C(APPROVED), C(RE_VERIFICATION) or C(EXPIRING).
    type: bool
    sample: True
ev_days_remaining:
    description: The number of days the domain remains eligible for submission of "EV" certificates. Will never be greater than the value of
                 I(ov_days_remaining)
    returned: success and I(ev_eligible) is C(True) and I(domain_status) is C(APPROVED), C(RE_VERIFICATION) or C(EXPIRING).
    type: int
    sample: 94

'''

from ansible.module_utils.ecs.api import (
    ecs_client_argument_spec,
    ECSClient,
    RestOperationException,
    SessionConfigurationException,
)

import datetime
import time
from ansible.module_utils.basic import AnsibleModule


def calculate_days_remaining(expiry_date):
    days_remaining = None
    if expiry_date:
        expiry_datetime = datetime.datetime.strptime(expiry_date, '%Y-%m-%dT%H:%M:%SZ')
        days_remaining = (expiry_datetime - datetime.datetime.now()).days
    return days_remaining


class EcsDomain(object):
    '''
    Entrust Certificate Services domain class.
    '''

    def __init__(self, module):
        self.changed = False
        self.domain_status = None
        self.verification_method = None
        self.file_location = None
        self.file_contents = None
        self.dns_location = None
        self.dns_contents = None
        self.dns_resource_type = None
        self.emails = None
        self.ov_eligible = None
        self.ov_days_remaining = None
        self.ev_eligble = None
        self.ev_days_remaining = None
        # Note that verification_method is the 'current' verification
        # method of the domain, we'll use module.params when requesting a new
        # one, in case the verification method has changed.
        self.verification_method = None

        self.force = module.params['force']

    def set_domain_details(self, domain_details):
        self.verification_method = domain_details['verificationMethod']
        self.domain_status = domain_details['status']
        self.ov_eligible = domain_details.get('ovEligible')
        self.ov_days_remaining = convert_days_remaining(domain_details.get('ovExpiry'))
        self.ev_eligible = domain_details.get('evEligible')
        self.ev_days_remaining = convert_days_remaining(domain_details.get('evExpiry'))
        self.client_id = domain_details['clientId']

        if self.verification_method == 'DNS' and domain_details.get('dnsMethod'):
            self.dns_location = domain_details['dnsMethod']['recordDomain']
            self.dns_resource_type = domain_details['dnsMethod']['recordType']
            self.dns_contents = domain_details['dnsMethod']['recordValue']
        elif self.verification_method == 'WEB_SERVER' and domain_details.get('webServerMethod'):
            self.file_location = domain_details['webServerMethod']['fileLocation']
            self.file_contents = domain_details['webServerMethod']['fileContents']
        elif self.verification_method == 'EMAIL' and domain_details.get('emailMethod'):
            self.emails = domain_details['emailMethod']

    def check(self, module):
        try:
            domain_details = self.ecs_client.GetDomain(clientId=module.params['client_id'], domain=self.domain_name)
            set_domain_details(domain_details)
            if self.domain_status != 'APPROVED' and self.domain_status != 'INITIAL_VERIFICATION' and
            self.domain_status != 'RE_VERIFICATION' and self.domain_status != 'EXPIRING':
                return False

            # If domain verification is in process, we want to return the random values and treat it as a valid.
            if self.domain_status == 'INITIAL_VERIFICATION' or self.domain_status == 'RE_VERIFICATION':
                # Unless the verification method has changed, in which case we need to do a reverify request.
                if self.verification_method != module.params['verification_method']:
                    return False

            # Need to check if value is not none, because 0 is a valid input
            if module.params['ev_remaining_days'] is not None and self.ev_days_remaining < module.params['ev_remaining_days']:
                return False
            if self.ov_days_remaining < module.params['ov_remaining_days']:
                return False

            return True
        except RestOperationException as e:
            module.fail_json('Failed to get domain details for domain. Likely does not exist.')

    def request_domain(self, module):
        if not self.check(module) or self.force:
            body = {}

            body['verificationMethod'] = module.params['verification_method']
            if module.params['verification_method'] == 'EMAIL':
                emailMethod = {}
                emailMethod['emailSource'] = 'SPECIFIED'
                emailMethod['email'] = module.params['verification_email']
            # Only populate domain name in body if it is not an existing domain
            if not self.domain_status:
                body['domainName'] = module.params['domain_name']
            try:
                if not self.domain_status:
                    self.ecs_client.AddDomainRequest(clientId=module.params['client_id'], Body=body)
                else:
                    self.ecs_client.ReverifyDomainRequest(clientId=module.params['client_id'], domain=module.params['domain_name'], Body=body)

                time.sleep(5)
                result = self.ecs_client.GetDomain(clientId=module.params['client_id'], domain=module.params['domain_name'])

                # It takes a bit of time before the random values are available
                if module.params['verification_method'] == 'DNS' or module.params['verification_method'] == 'FILE'
                for i in range(2):
                    # Check both that random values are now available, and that they're different than were populated by previous 'check'
                    if module.params['verification_method'] == 'DNS':
                        if result.get('dnsMethod') and result.get['dnsMethod']['recordValue'] != self.dns_contents:
                            break
                    elif module.params['verification_method'] == 'WEB_SERVER':
                        if result.get('webServerMethod') and result.get['webServerMethod']['fileContents'] != self.file_contents:
                            break
                    time.sleep(10)
                    result = self.ecs_client.GetDomain(clientId=module.params['client_id'], domain=module.params['domain_name'])
                self.changed = True
                set_domain_details(result)
            except RestOperationException as e:
                module.fail_json(msg='Failed to request domain validation from Entrust (ECS) {0}'.format(e.message))

    def dump(self):
        result = {
            'changed': self.changed,
            'client_id': self.client_id,
            'domain_status': self.domain_status,
            'verification_method': self.verification_method,
            'ov_eligible': self.ov_eligible,
            'ov_days_remaining': self.ov_days_remaining,
            'ev_eligible': self.ev_eligible,
            'ev_days_remaining': self.ev_days_remaining,
            'emails': self.emails,
        }

        if self.verification_method == 'DNS':
            result['dns_location'] = self.dns_location
            result['dns_contents'] = self.dns_contents
            result['dns_resource_type'] = self.dns_resource_type
        elif self.verification_method == 'FILE':
            result['file_location'] = self.file_location
            result['file_contents'] = self.file_contents
        elif self.verification_method == 'EMAIL':
            result['emails'] = self.emails

        return result


def ecs_domain_argument_spec():
    return dict(
        client_id=dict(type='int', default=1),
        domain_name=dict(type='str', required=True),
        verification_method=dict(type='str', choices=['DNS', 'EMAIL', 'MANUAL', 'WEB_SERVER']),
        verification_email=dict(type='str'),
        ov_remaining_days=dict(type='int', default=60),
        ev_remaining_days=dict(type='int'),
        force=dict(type='bool', default=False),
    )


def main():
    ecs_argument_spec = ecs_client_argument_spec()
    ecs_argument_spec.update(ecs_domain_argument_spec())
    module = AnsibleModule(
        argument_spec=ecs_argument_spec,
        required_if=(
            ['verification_method', 'EMAIL', ['verification_email']]
        ),
        supports_check_mode=False,
    )

    if module.params['verification_email'] and module.params['verification_method'] != 'EMAIL':
        module.fail_json(msg='The verification_email field is invalid when verification_method="{0}".'.format(module.params['verification_method']))

    domain = EcsDomain(module)
    domain.request_validation(module)
    result = domain.dump()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
