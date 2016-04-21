#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2013 Bruce Pennypacker <bruce@pennypacker.org>
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
    choices: ['yes', 'no']

requirements: []
'''

EXAMPLES = '''
- airbrake_deployment: token=AAAAAA
                       environment='staging'
                       user='ansible'
                       revision=4.2
'''

import urllib

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
    data = urllib.urlencode(params)
    response, info = fetch_url(module, url, data=data)
    if info['status'] == 200:
        module.exit_json(changed=True)
    else:
        module.fail_json(msg="HTTP result code: %d connecting to %s" % (info['status'], url))

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

main()

