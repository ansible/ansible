#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2014 Benjamin Curtis <benjamin.curtis@gmail.com>
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
    required: false
    default: None
  repo:
    description:
      - URL of the project repository
    required: false
    default: None
  revision:
    description:
      - A hash, number, tag, or other identifier showing what revision was deployed
    required: false
    default: None
  url:
    description:
      - Optional URL to submit the notification to.
    required: false
    default: "https://api.honeybadger.io/v1/deploys"
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
- honeybadger_deployment: token=AAAAAA
                          environment='staging'
                          user='ansible'
                          revision=b6826b8
                          repo=git@github.com:user/repo.git
'''

RETURN = '''# '''

import urllib

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.urls import *

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
        data = urllib.urlencode(params)
        response, info = fetch_url(module, url, data=data)
    except Exception:
        e = get_exception()
        module.fail_json(msg='Unable to notify Honeybadger: %s' % e)
    else:
        if info['status'] == 200:
            module.exit_json(changed=True)
        else:
            module.fail_json(msg="HTTP result code: %d connecting to %s" % (info['status'], url))

if __name__ == '__main__':
    main()

