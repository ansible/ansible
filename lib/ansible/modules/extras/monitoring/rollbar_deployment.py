#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2014, Max Riveiro, <kavu13@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

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
    choices: ['yes', 'no']
'''

EXAMPLES = '''
- rollbar_deployment: token=AAAAAA
                      environment='staging'
                      user='ansible'
                      revision=4.2,
                      rollbar_user='admin',
                      comment='Test Deploy'
'''

import urllib

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
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
        data = urllib.urlencode(params)
        response, info = fetch_url(module, url, data=data)
    except Exception:
        e = get_exception()
        module.fail_json(msg='Unable to notify Rollbar: %s' % e)
    else:
        if info['status'] == 200:
            module.exit_json(changed=True)
        else:
            module.fail_json(msg='HTTP result code: %d connecting to %s' % (info['status'], url))


if __name__ == '__main__':
    main()
