#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2014 Benjamin Curtis <benjamin.curtis@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: honeybadger_deployment
author: "Benjamin Curtis (@stympy)"
version_added: "2.2"
short_description: Notify Honeybadger.io about app deployments
description:
   - Notify Honeybadger.io about app deployments (see http://docs.honeybadger.io/article/188-deployment-tracking)
options:
  token:
    description:
      - API token.
    required: true
  environment:
    description:
      - The environment name, typically 'production', 'staging', etc.
    required: true
  user:
    description:
      - The username of the person doing the deployment
  repo:
    description:
      - URL of the project repository
  revision:
    description:
      - A hash, number, tag, or other identifier showing what revision was deployed
  url:
    description:
      - Optional URL to submit the notification to.
    default: "https://api.honeybadger.io/v1/deploys"
  validate_certs:
    description:
      - If C(no), SSL certificates for the target url will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    type: bool
    default: 'yes'

'''

EXAMPLES = '''
- honeybadger_deployment:
    token: AAAAAA
    environment: staging
    user: ansible
    revision: b6826b8
    repo: 'git@github.com:user/repo.git'
'''

RETURN = '''# '''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url


# ===========================================
# Module execution.
#

def main():

    module = AnsibleModule(
        argument_spec=dict(
            token=dict(required=True, no_log=True),
            environment=dict(required=True),
            user=dict(required=False),
            repo=dict(required=False),
            revision=dict(required=False),
            url=dict(required=False, default='https://api.honeybadger.io/v1/deploys'),
            validate_certs=dict(default='yes', type='bool'),
        ),
        supports_check_mode=True
    )

    params = {}

    if module.params["environment"]:
        params["deploy[environment]"] = module.params["environment"]

    if module.params["user"]:
        params["deploy[local_username]"] = module.params["user"]

    if module.params["repo"]:
        params["deploy[repository]"] = module.params["repo"]

    if module.params["revision"]:
        params["deploy[revision]"] = module.params["revision"]

    params["api_key"] = module.params["token"]

    url = module.params.get('url')

    # If we're in check mode, just exit pretending like we succeeded
    if module.check_mode:
        module.exit_json(changed=True)

    try:
        data = urlencode(params)
        response, info = fetch_url(module, url, data=data)
    except Exception as e:
        module.fail_json(msg='Unable to notify Honeybadger: %s' % to_native(e), exception=traceback.format_exc())
    else:
        if info['status'] == 201:
            module.exit_json(changed=True)
        else:
            module.fail_json(msg="HTTP result code: %d connecting to %s" % (info['status'], url))


if __name__ == '__main__':
    main()
