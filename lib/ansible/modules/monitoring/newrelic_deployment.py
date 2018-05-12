#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2018 Davinder Pal <dpsangwal@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: newrelic_deployment
version_added: "0.1"
author: "Davinder Pal (@116davinder)"
short_description: Notify newrelic about app deployments using newrelic v2 api
description:
   - Notify newrelic about app deployments (see https://docs.newrelic.com/docs/apm/new-relic-apm/maintenance/record-deployments)
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
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    required: false
    default: 'yes'
    type: bool
    version_added: 2.5.3

requirements: []
'''

EXAMPLES = '''
- newrelic_deployment:
    token: XXXXXXXXX
    app_name: ansibleApp
    user: ansible deployment user
    revision: '1.X'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.six.moves.urllib.parse import urlencode
import json

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
            revision=dict(required=True),
            user=dict(required=False),
            validate_certs=dict(default='True', type='bool'),
        ),
        required_one_of=[['app_name', 'application_id']]
    )

    # testing params
    params = {}
    if module.params["app_name"] and module.params["application_id"]:
        module.fail_json(msg="only one of 'app_name' or 'application_id' can be set")
    if module.params["app_name"]:
	params["app_name"] = module.params["app_name"]
    elif module.params["application_id"]:
    	params["application_id"] = module.params["application_id"]
    else:
    	module.fail_json(msg="you must set one of 'app_name' or 'application_id'")

    if module.params["app_name"]:
	data="filter[name]=" + str(module.params["app_name"])
      	resp, info = fetch_url(module,
                             "https://api.newrelic.com/v2/applications.json",
                             headers={'x-api-key': module.params["token"],
                             'Content-type': 'application/x-www-form-urlencoded'},
                             data=data,
                             method="GET")
      	if info['status'] != 200:
            module.fail_json(msg="unable to get application list from newrelic: %s" % info['msg'])
      	else:
            body = json.loads(resp.read())
      	if body == None:
            module.fail_json(msg="No Data for applications")
    	else:
            app_id = body["applications"][0]["id"]
            if app_id == None:
                module.fail_json(msg="App not found in NewRelic Registerd Applications List")
    else:
    	app_id = module.params["application_id"]

    # Send the data to NewRelic
    url = "https://api.newrelic.com/v2/applications/" + str(app_id) + "/deployments.json"
    data={ "deployment": { \
                        "revision": str(module.params["revision"]), \
                        "changelog": str(module.params["changelog"]), \
                        "description": str(module.params["description"]), \
                        "user": str(module.params["user"])
                        } \
          }
    headers = {
        'x-api-key': module.params["token"],
        'Content-Type': 'application/json',
    }
    response, info = fetch_url(module, url, data=module.jsonify(data), headers=headers, method="POST")
    if info['status'] == 201:
    	module.exit_json(changed=True)
    else:
    	module.fail_json(msg="unable to update newrelic: %s" % info['msg'])

if __name__ == '__main__':
    main()
