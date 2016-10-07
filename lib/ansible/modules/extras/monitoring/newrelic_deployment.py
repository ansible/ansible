#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2013 Matt Coddington <coddington@gmail.com>
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
module: newrelic_deployment
version_added: "1.2"
author: "Matt Coddington (@mcodd)"
short_description: Notify newrelic about app deployments
description:
   - Notify newrelic about app deployments (see https://docs.newrelic.com/docs/apm/new-relic-apm/maintenance/deployment-notifications#api)
options:
  token:
    description:
      - API token, to place in the x-api-key header.
    required: true
  app_name:
    description:
      - (one of app_name or application_id are required) The value of app_name in the newrelic.yml file used by the application
    required: false
  application_id:
    description:
      - (one of app_name or application_id are required) The application id, found in the URL when viewing the application in RPM
    required: false
  changelog:
    description:
      - A list of changes for this deployment
    required: false
  description:
    description:
      - Text annotation for the deployment - notes for you
    required: false
  revision:
    description:
      - A revision number (e.g., git commit SHA)
    required: false
  user:
    description:
      - The name of the user/process that triggered this deployment
    required: false
  appname:
    description:
      - Name of the application
    required: false
  environment:
    description:
      - The environment for this deployment
    required: false
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    required: false
    default: 'yes'
    choices: ['yes', 'no']
    version_added: 1.5.1

requirements: []
'''

EXAMPLES = '''
- newrelic_deployment: token=AAAAAA
                       app_name=myapp
                       user='ansible deployment'
                       revision=1.0
'''

import urllib

# ===========================================
# Module execution.
#

def main():

    module = AnsibleModule(
        argument_spec=dict(
            token=dict(required=True, no_log=True),
            app_name=dict(required=False),
            application_id=dict(required=False),
            changelog=dict(required=False),
            description=dict(required=False),
            revision=dict(required=False),
            user=dict(required=False),
            appname=dict(required=False),
            environment=dict(required=False),
            validate_certs = dict(default='yes', type='bool'),
        ),
        required_one_of=[['app_name', 'application_id']],
        supports_check_mode=True
    )

    # build list of params
    params = {}
    if module.params["app_name"] and module.params["application_id"]:
        module.fail_json(msg="only one of 'app_name' or 'application_id' can be set")

    if module.params["app_name"]:
        params["app_name"] = module.params["app_name"]
    elif module.params["application_id"]:
        params["application_id"] = module.params["application_id"]
    else:
        module.fail_json(msg="you must set one of 'app_name' or 'application_id'")
    
    for item in [ "changelog", "description", "revision", "user", "appname", "environment" ]:
        if module.params[item]:
            params[item] = module.params[item]

    # If we're in check mode, just exit pretending like we succeeded
    if module.check_mode:
        module.exit_json(changed=True)

    # Send the data to NewRelic
    url = "https://rpm.newrelic.com/deployments.xml"
    data = urllib.urlencode(params)
    headers = {
        'x-api-key': module.params["token"],
    }
    response, info = fetch_url(module, url, data=data, headers=headers)
    if info['status'] in (200, 201):
        module.exit_json(changed=True)
    else:
        module.fail_json(msg="unable to update newrelic: %s" % info['msg'])

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

main()

