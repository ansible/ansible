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
version_added: "2.8"
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

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # caught by imported HAS_BOTO3


def get_identity_dkim_settings(module, client, identity):
    try:
        response = client.get_identity_dkim_attributes(Identities=[identity])
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to retrieve identity DKIM settings for {identity}'.format(identity=identity))
    dkim_attributes = response['DkimAttributes']

    return dkim_attributes[identity]


def ses_verify_dkim_domain(module, client, identity):
    domain = identity.split('@')[-1]
    try:
        response = client.verify_domain_dkim(Domain=domain)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to start DKIM verification for {domain}.'.format(domain=domain))
    dkim_tokens = response['DkimTokens']
    return dkim_tokens


def enable_identity_dkim_settings(module, client, identity):
    try:
        response = client.set_identity_dkim_enabled(DkimEnabled=True, Identity=identity)
        return response
    except (BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to enable DKIM for {identity}.'.format(identity=identity))
    except (ClientError) as e:
        pass # The enable call will always return a ClientError, complaining about missing DNS record, but still changes setting to 'enabled'.
        # So once DNS validation goes through it should work already, hence we ignore errors here.

def disable_identity_dkim_settings(module, client, identity):
    try:
        response = client.set_identity_dkim_enabled(DkimEnabled=False, Identity=identity)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to disable DKIM settings for {identity}'.format(identity=identity))
    return response


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

    if state == 'enabled':
        ses_verify_dkim_domain(module, client, identity)
        enable_identity_dkim_settings(module, client, identity)
        # TODO: find a way to easily detect changes (updates to identity)
        changed = True
    else:
        disable_identity_dkim_settings(module, client, identity)

    attributes = get_identity_dkim_settings(module, client, identity)

    module.exit_json(changed=changed, dkim_attributes=camel_dict_to_snake_dict(attributes))


if __name__ == '__main__':
    main()
