#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: aws_ses_identity_dkim
short_description: Manages SES email and domain identity
description:
    - This module allows a user to enable DKIM settings on an existing SES identity. It will also return
      the identity tokens for you to add to DNS.
version_added: "2.9"
author: Stefan Horning (@stefanhorning)

options:
    identity:
        description:
            - The SES identity you would like to enable DKIM for.
            - This should be the email address or domain identifying an existing SES identity
        required: true
    state:
        description:
            - Enable or disable DKIM on the identity
        default: enabled
        choices: [ 'enabled', 'disabled']
requirements: [ 'botocore', 'boto3' ]
extends_documentation_fragment:
    - aws
    - ec2

'''

EXAMPLES = '''
# Note: to setup SES identities use the aws_ses_identity module.

- name: Enable DKIM setting for identity example@example.com
  aws_ses_identity_dkim:
      identity: example@example.com

- name: Enable DKIM setting for identity example.com
  aws_ses_identity_dkim:
    identity: example.com
  register: dkim_results

- name: Example how to aws_ses_identity_dkim results to set DNS records for validation (if you use Route53 service for DNS)
  route53:
    record: "{{ item }}._domainkey.example.com"
    value: "{{ item }}.dkim.amazonses.com"
    type: CNAME
    zone: example.com
  with_items: "{{ dkim_results.dkim_attributes.dkim_tokens }}"

- name: Disable DKIM setting for identity example.com
  aws_ses_identity_dkim:
    identity: example.com
    state: disabled
'''

RETURN = '''
dkim_attributes:
    description: Dictionary with DKIM information
    type: complex
    returned: always
    sample: {
        "dkim_tokens": [],
        "dkim_enabled": "True",
        "dkim_verification_status": "Pending"
    }
    contains:
        dkim_tokens:
            descritpion: Array of the 3 DKIM verification tokens needed for DNS records
            type: list
            sample: ['u5d5fa5twxzdni4aaoffdqvgnvku5kvu', '6xzw7n3abimypkyan5s6kuse4nymrfo2', 'nkwigx63eervm4hyja2lwzhjcfqyhka7']
        dkim_enabled:
            description: Boolean indicating if DKIM email sending is enabled or disabled for identity
            type: bool
            sample: True
        dkim_verification_status:
            description: Status of the DKIM verification process (DNS verification)
            type: str
            sample: 'Pending'
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, AWSRetry

import os
import time

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # caught by imported HAS_BOTO3


def _get_state_check(state):
    if state == 'enabled':
        return lambda attributes: attributes['DkimEnabled'] and attributes['DkimTokens']
    elif state == 'disabled':
        return lambda attributes: not attributes['DkimEnabled']
    elif state == 'any':
        return lambda attributes: True
    else:
        raise RuntimeError('Unknown state ' + state)


def get_identity_dkim_settings(module, client, identity, wait_for, retries=10, retry_delay=10):
    for retry in range(1, retries + 1):
        try:
            response = client.get_identity_dkim_attributes(Identities=[identity])
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg='Failed to retrieve identity DKIM settings for {identity}'.format(identity=identity))
        dkim_attributes = response['DkimAttributes'][identity]

        # get_identity_dkim_attributes seems to take some time to consistently return the updated status
        # so when we've changed the state we loop until we get the state we're expecting.
        if wait_for(dkim_attributes):
            break
        time.sleep(retry_delay)

    return dkim_attributes


def ses_verify_dkim_domain(module, client, identity):
    domain = identity.split('@')[-1]
    try:
        if not module.check_mode:
            response = client.verify_domain_dkim(Domain=domain)
            return response['DkimTokens']
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to start DKIM verification for {domain}.'.format(domain=domain))


def set_identity_dkim_enabled(module, client, identity, enabled, retries=10, retry_delay=10):
    if enabled:
        operation = 'enable'
    else:
        operation = 'disable'
    for retry in range(1, retries + 1):
        try:
            if not module.check_mode:
                return client.set_identity_dkim_enabled(DkimEnabled=enabled, Identity=identity)
        except (BotoCoreError) as e:
            module.fail_json_aws(e, msg='Failed to {operation} DKIM for {identity}.'.format(
                operation=operation,
                identity=identity,
            ))
        except (ClientError) as e:
            error = e.response.get('Error', {})
            error_code = error.get('Code',  'Unknown')
            error_message = error.get('Message',  'Unknown')
            # verify_dkim_domain seems to take some time to replicate the status consistently to
            # other parts of the SES API. So if we get this specific client error we retry after
            # a delay  so that we correctly enable or disable DKIM.
            # Note we need this even when disabling since this seems to fail tests sometimes even
            # after having succeeded once. It seems that we get inconsistent failures for some time
            # until the domain verification attempt is fully propagated.
            if (retry >= retries or
                    not (error_code == 'InvalidParameterValue' and 'not verified for DKIM signing' in error_message)):
                module.fail_json_aws(e, msg='Failed to {operation} DKIM for {identity}.'.format(
                    operation=operation,
                    identity=identity,
                ))
            time.sleep(retry_delay)


def main():
    module = AnsibleAWSModule(
        argument_spec={
            "identity": dict(required=True, type='str'),
            "state": dict(default='enabled', choices=['enabled', 'disabled']),
        },
        supports_check_mode=True,
    )

    # SES APIs seem to have a much lower throttling threshold than most of the rest of the AWS APIs.
    # Docs say 1 call per second. This shouldn't actually be a big problem for normal usage, but
    # the ansible build runs multiple instances of the test in parallel that's caused throttling
    # failures so apply a jittered backoff to call SES calls.
    client = module.client('ses', retry_decorator=AWSRetry.jittered_backoff())

    identity = module.params.get('identity')
    state = module.params.get('state')
    changed = False

    state_check = _get_state_check(state)

    # Get current DKIM attributes to see if they need changing
    # Note that the get_identity_dkim_settings seems to take a long time to consistently return the
    # updated result. So to make the tests reliable we force a wait here till we get to the expected
    # state. Simply waiting for the correct return on change isn't sufficient since the old state seems
    # to still be randomly returned for some time.
    #
    # This should only present a problem when rapidly switching back and forth as we do in tests, so
    # this should not cause failures in real usage.
    attributes = get_identity_dkim_settings(module, client, identity,
                                            _get_state_check(os.environ.get('TEST_ONLY_FORCE_INITIAL_STATE', 'any')))
    current_state = attributes['DkimEnabled']

    if not state_check(attributes):
        # Update DKIM settings
        if state == 'enabled':
            ses_verify_dkim_domain(module, client, identity)
        set_identity_dkim_enabled(module, client, identity, state == 'enabled')
        changed = True
        wait_for = state_check
        if module.check_mode:
            wait_for = _get_state_check('any')
        attributes = get_identity_dkim_settings(module, client, identity, wait_for)

    module.exit_json(changed=changed, dkim_attributes=camel_dict_to_snake_dict(attributes))


if __name__ == '__main__':
    main()
