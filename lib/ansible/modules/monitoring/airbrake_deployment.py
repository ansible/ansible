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
author:
- "Bruce Pennypacker (@bpennypacker)"
- "Patrick Humpal (@phumpal)"
short_description: Notify airbrake about app deployments
description:
   - Notify airbrake about app deployments (see https://airbrake.io/docs/api/#deploys-v4)
options:
  project_id:
    description:
      - Airbrake PROJECT_ID
    required: true
    version_added: '2.10'
  project_key:
    description:
      - Airbrake PROJECT_KEY.
    required: true
    version_added: '2.10'
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
    default: "https://api.airbrake.io/api/v4/projects/"
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
    project_id: '12345'
    project_key: 'AAAAAA'
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
            project_id=dict(required=True, no_log=True),
            project_key=dict(required=True, no_log=True),
            environment=dict(required=True),
            user=dict(required=False),
            repo=dict(required=False),
            revision=dict(required=False),
            url=dict(required=False, default='https://api.airbrake.io/api/v4/projects/'),
            validate_certs=dict(default='yes', type='bool'),
        ),
        supports_check_mode=True
    )

    # Build list of params
    params = {}

    if module.params["environment"]:
        params["environment"] = module.params["environment"]

    if module.params["user"]:
        params["username"] = module.params["user"]

    if module.params["repo"]:
        params["repository"] = module.params["repo"]

    if module.params["revision"]:
        params["revision"] = module.params["revision"]

    # Build deploy url
    url = module.params.get('url') + module.params["project_id"] + '/deploys?key=' + module.params["project_key"]

    # If we're in check mode, just exit pretending like we succeeded
    if module.check_mode:
        module.exit_json(changed=True)

    json_body = module.jsonify(params)

    # Build header
    headers = {'Content-Type': 'application/json'}

    # Notify Airbrake of deploy
    response, info = fetch_url(module, url, data=json_body,
                               headers=headers, method='POST')
    if info['status'] == 201:
        module.exit_json(changed=True)
    else:
        module.fail_json(msg="HTTP result code: %d connecting to %s" % (info['status'], url))


if __name__ == '__main__':
    main()
