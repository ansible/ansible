#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2014, Max Riveiro, <kavu13@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rollbar_deployment
version_added: 1.6
author: "Max Riveiro (@kavu)"
short_description: Notify Rollbar about app deployments
description:
  - Notify Rollbar about app deployments
    (see https://rollbar.com/docs/deploys_other/)
options:
  token:
    description:
      - Your project access token.
    required: true
  environment:
    description:
      - Name of the environment being deployed, e.g. 'production'.
    required: true
  revision:
    description:
      - Revision number/sha being deployed.
    required: true
  user:
    description:
      - User who deployed.
    required: false
  rollbar_user:
    description:
      - Rollbar username of the user who deployed.
    required: false
  comment:
    description:
      - Deploy comment (e.g. what is being deployed).
    required: false
  url:
    description:
      - Optional URL to submit the notification to.
    required: false
    default: 'https://api.rollbar.com/api/1/deploy/'
  validate_certs:
    description:
      - If C(no), SSL certificates for the target url will not be validated.
        This should only be used on personally controlled sites using
        self-signed certificates.
    required: false
    default: 'yes'
    type: bool
'''

EXAMPLES = '''
- rollbar_deployment:
    token: AAAAAA
    environment: staging
    user: ansible
    revision: '4.2'
    rollbar_user: admin
    comment: Test Deploy
'''
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url


def main():

    module = AnsibleModule(
        argument_spec=dict(
            token=dict(required=True),
            environment=dict(required=True),
            revision=dict(required=True),
            user=dict(required=False),
            rollbar_user=dict(required=False),
            comment=dict(required=False),
            url=dict(
                required=False,
                default='https://api.rollbar.com/api/1/deploy/'
            ),
            validate_certs=dict(default='yes', type='bool'),
        ),
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(changed=True)

    params = dict(
        access_token=module.params['token'],
        environment=module.params['environment'],
        revision=module.params['revision']
    )

    if module.params['user']:
        params['local_username'] = module.params['user']

    if module.params['rollbar_user']:
        params['rollbar_username'] = module.params['rollbar_user']

    if module.params['comment']:
        params['comment'] = module.params['comment']

    url = module.params.get('url')

    try:
        data = urlencode(params)
        response, info = fetch_url(module, url, data=data)
    except Exception as e:
        module.fail_json(msg='Unable to notify Rollbar: %s' % to_native(e), exception=traceback.format_exc())
    else:
        if info['status'] == 200:
            module.exit_json(changed=True)
        else:
            module.fail_json(msg='HTTP result code: %d connecting to %s' % (info['status'], url))


if __name__ == '__main__':
    main()
