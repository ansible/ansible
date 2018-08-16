#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2013 Bruce Pennypacker <bruce@pennypacker.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: airbrake_deployment
version_added: "1.2"
author: "Bruce Pennypacker (@bpennypacker)"
short_description: Notify airbrake about app deployments
description:
   - Notify airbrake about app deployments (see http://help.airbrake.io/kb/api-2/deploy-tracking)
options:
  token:
    description:
      - API token.
    required: true
  environment:
    description:
      - The airbrake environment name, typically 'production', 'staging', etc.
    required: true
  user:
    description:
      - The username of the person doing the deployment
    required: false
  repo:
    description:
      - URL of the project repository
    required: false
  revision:
    description:
      - A hash, number, tag, or other identifier showing what revision was deployed
    required: false
  url:
    description:
      - Optional URL to submit the notification to. Use to send notifications to Airbrake-compliant tools like Errbit.
    required: false
    default: "https://airbrake.io/deploys.txt"
    version_added: "1.5"
  validate_certs:
    description:
      - If C(no), SSL certificates for the target url will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    required: false
    default: 'yes'
    type: bool

requirements: []
'''

EXAMPLES = '''
- airbrake_deployment:
    token: AAAAAA
    environment: staging
    user: ansible
    revision: '4.2'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.six.moves.urllib.parse import urlencode


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
            url=dict(required=False, default='https://api.airbrake.io/deploys.txt'),
            validate_certs=dict(default='yes', type='bool'),
        ),
        supports_check_mode=True
    )

    # build list of params
    params = {}

    if module.params["environment"]:
        params["deploy[rails_env]"] = module.params["environment"]

    if module.params["user"]:
        params["deploy[local_username]"] = module.params["user"]

    if module.params["repo"]:
        params["deploy[scm_repository]"] = module.params["repo"]

    if module.params["revision"]:
        params["deploy[scm_revision]"] = module.params["revision"]

    params["api_key"] = module.params["token"]

    url = module.params.get('url')

    # If we're in check mode, just exit pretending like we succeeded
    if module.check_mode:
        module.exit_json(changed=True)

    # Send the data to airbrake
    data = urlencode(params)
    response, info = fetch_url(module, url, data=data)
    if info['status'] == 200:
        module.exit_json(changed=True)
    else:
        module.fail_json(msg="HTTP result code: %d connecting to %s" % (info['status'], url))


if __name__ == '__main__':
    main()
