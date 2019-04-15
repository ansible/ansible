#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Evgeniy Krysanov <evgeniy.krysanov@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community',
}

DOCUMENTATION = r'''
---
module: bitbucket_pipeline_known_host
short_description: Manages Bitbucket pipeline known hosts
description:
  - Manages Bitbucket pipeline known hosts under the "SSH Keys" menu.
  - The host fingerprint will be retrieved automatically, but in case of an error, one can use I(key) field to specify it manually.
version_added: "2.8"
author:
  - Evgeniy Krysanov (@catcombo)
requirements:
    - paramiko
options:
  client_id:
    description:
      - The OAuth consumer key.
      - If not set the environment variable C(BITBUCKET_CLIENT_ID) will be used.
    type: str
  client_secret:
    description:
      - The OAuth consumer secret.
      - If not set the environment variable C(BITBUCKET_CLIENT_SECRET) will be used.
    type: str
  repository:
    description:
      - The repository name.
    type: str
    required: true
  username:
    description:
      - The repository owner.
    type: str
    required: true
  name:
    description:
      - The FQDN of the known host.
    type: str
    required: true
  key:
    description:
      - The public key.
    type: str
  state:
    description:
      - Indicates desired state of the record.
    type: str
    required: true
    choices: [ absent, present ]
notes:
  - Bitbucket OAuth consumer key and secret can be obtained from Bitbucket profile -> Settings -> Access Management -> OAuth.
  - Check mode is supported.
'''

EXAMPLES = r'''
- name: Create known hosts from the list
  bitbucket_pipeline_known_host:
    repository: 'bitbucket-repo'
    username: bitbucket_username
    name: '{{ item }}'
    state: present
  with_items:
    - bitbucket.org
    - example.com

- name: Remove known host
  bitbucket_pipeline_known_host:
    repository: bitbucket-repo
    username: bitbucket_username
    name: bitbucket.org
    state: absent

- name: Specify public key file
  bitbucket_pipeline_known_host:
    repository: bitbucket-repo
    username: bitbucket_username
    name: bitbucket.org
    key: '{{lookup("file", "bitbucket.pub") }}'
    state: absent
'''

RETURN = r''' # '''

import socket

try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.source_control.bitbucket import BitbucketHelper

error_messages = {
    'invalid_params': 'Account or repository was not found',
    'unknown_key_type': 'Public key type is unknown',
}

BITBUCKET_API_ENDPOINTS = {
    'known-host-list': '%s/2.0/repositories/{username}/{repo_slug}/pipelines_config/ssh/known_hosts/' % BitbucketHelper.BITBUCKET_API_URL,
    'known-host-detail': '%s/2.0/repositories/{username}/{repo_slug}/pipelines_config/ssh/known_hosts/{known_host_uuid}' % BitbucketHelper.BITBUCKET_API_URL,
}


def get_existing_known_host(module, bitbucket):
    """
    Search for a host in Bitbucket pipelines known hosts
    with the name specified in module param `name`

    :param module: instance of the :class:`AnsibleModule`
    :param bitbucket: instance of the :class:`BitbucketHelper`
    :return: existing host or None if not found
    :rtype: dict or None

    Return example::

        {
            'type': 'pipeline_known_host',
            'uuid': '{21cc0590-bebe-4fae-8baf-03722704119a7}'
            'hostname': 'bitbucket.org',
            'public_key': {
                'type': 'pipeline_ssh_public_key',
                'md5_fingerprint': 'md5:97:8c:1b:f2:6f:14:6b:4b:3b:ec:aa:46:46:74:7c:40',
                'sha256_fingerprint': 'SHA256:zzXQOXSFBEiUtuE8AikoYKwbHaxvSc0ojez9YXaGp1A',
                'key_type': 'ssh-rsa',
                'key': 'AAAAB3NzaC1yc2EAAAABIwAAAQEAubiN81eDcafrgMeLzaFPsw2kN...seeFVBoGqzHM9yXw=='
            },
        }
    """
    content = {
        'next': BITBUCKET_API_ENDPOINTS['known-host-list'].format(
            username=module.params['username'],
            repo_slug=module.params['repository'],
        )
    }

    # Look through all response pages in search of hostname we need
    while 'next' in content:
        info, content = bitbucket.request(
            api_url=content['next'],
            method='GET',
        )

        if info['status'] == 404:
            module.fail_json(msg='Invalid `repository` or `username`.')

        if info['status'] != 200:
            module.fail_json(msg='Failed to retrieve list of known hosts: {0}'.format(info))

        host = next(filter(lambda v: v['hostname'] == module.params['name'], content['values']), None)

        if host is not None:
            return host

    return None


def get_host_key(module, hostname):
    """
    Fetches public key for specified host

    :param module: instance of the :class:`AnsibleModule`
    :param hostname: host name
    :return: key type and key content
    :rtype: tuple

    Return example::

        (
            'ssh-rsa',
            'AAAAB3NzaC1yc2EAAAABIwAAA...SBne8+seeFVBoGqzHM9yXw==',
        )
    """
    try:
        sock = socket.socket()
        sock.connect((hostname, 22))
    except socket.error:
        module.fail_json(msg='Error opening socket to {0}'.format(hostname))

    try:
        trans = paramiko.transport.Transport(sock)
        trans.start_client()
        host_key = trans.get_remote_server_key()
    except paramiko.SSHException:
        module.fail_json(msg='SSH error on retrieving {0} server key'.format(hostname))

    trans.close()
    sock.close()

    key_type = host_key.get_name()
    key = host_key.get_base64()

    return key_type, key


def create_known_host(module, bitbucket):
    hostname = module.params['name']
    key_param = module.params['key']

    if key_param is None:
        key_type, key = get_host_key(module, hostname)
    elif ' ' in key_param:
        key_type, key = key_param.split(' ', 1)
    else:
        module.fail_json(msg=error_messages['unknown_key_type'])

    info, content = bitbucket.request(
        api_url=BITBUCKET_API_ENDPOINTS['known-host-list'].format(
            username=module.params['username'],
            repo_slug=module.params['repository'],
        ),
        method='POST',
        data={
            'hostname': hostname,
            'public_key': {
                'key_type': key_type,
                'key': key,
            }
        },
    )

    if info['status'] == 404:
        module.fail_json(msg=error_messages['invalid_params'])

    if info['status'] != 201:
        module.fail_json(msg='Failed to create known host `{hostname}`: {info}'.format(
            hostname=module.params['hostname'],
            info=info,
        ))


def delete_known_host(module, bitbucket, known_host_uuid):
    info, content = bitbucket.request(
        api_url=BITBUCKET_API_ENDPOINTS['known-host-detail'].format(
            username=module.params['username'],
            repo_slug=module.params['repository'],
            known_host_uuid=known_host_uuid,
        ),
        method='DELETE',
    )

    if info['status'] == 404:
        module.fail_json(msg=error_messages['invalid_params'])

    if info['status'] != 204:
        module.fail_json(msg='Failed to delete known host `{hostname}`: {info}'.format(
            hostname=module.params['name'],
            info=info,
        ))


def main():
    argument_spec = BitbucketHelper.bitbucket_argument_spec()
    argument_spec.update(
        repository=dict(type='str', required=True),
        username=dict(type='str', required=True),
        name=dict(type='str', required=True),
        key=dict(type='str'),
        state=dict(type='str', choices=['present', 'absent'], required=True),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if (module.params['key'] is None) and (not HAS_PARAMIKO):
        module.fail_json(msg='`paramiko` package not found, please install it.')

    bitbucket = BitbucketHelper(module)

    # Retrieve access token for authorized API requests
    bitbucket.fetch_access_token()

    # Retrieve existing known host
    existing_host = get_existing_known_host(module, bitbucket)
    state = module.params['state']
    changed = False

    # Create new host in case it doesn't exists
    if not existing_host and (state == 'present'):
        if not module.check_mode:
            create_known_host(module, bitbucket)
        changed = True

    # Delete host
    elif existing_host and (state == 'absent'):
        if not module.check_mode:
            delete_known_host(module, bitbucket, existing_host['uuid'])
        changed = True

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
