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
author: Matt Coddington
short_description: Notify newrelic about app deployments
description:
   - Notify newrelic about app deployments (see http://newrelic.github.io/newrelic_api/NewRelicApi/Deployment.html)
options:
  token:
    description:
      - API token.
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

# informational: requirements for nodes
requirements: [ urllib, urllib2 ]
'''

EXAMPLES = '''
- newrelic_deployment: token=AAAAAA
                       app_name=myapp
                       user='ansible deployment'
                       revision=1.0
'''

HAS_URLLIB = True
try:
    import urllib
except ImportError:
    HAS_URLLIB = False

HAS_URLLIB2 = True
try:
    import urllib2
except ImportError:
    HAS_URLLIB2 = False

# ===========================================
# Module execution.
#

def main():

    if not HAS_URLLIB:
        module.fail_json(msg="urllib is not installed")
    if not HAS_URLLIB2:
        module.fail_json(msg="urllib2 is not installed")

    module = AnsibleModule(
        argument_spec=dict(
            token=dict(required=True),
            app_name=dict(required=False),
            application_id=dict(required=False),
            changelog=dict(required=False),
            description=dict(required=False),
            revision=dict(required=False),
            user=dict(required=False),
            appname=dict(required=False),
            environment=dict(required=False),
        ),
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
    try:
        req = urllib2.Request("https://rpm.newrelic.com/deployments.xml", urllib.urlencode(params))
        req.add_header('x-api-key',module.params["token"])
        result=urllib2.urlopen(req)
        # urlopen behaves differently in python 2.4 and 2.6 so we handle
        # both cases here.  In python 2.4 it throws an exception if the
        # return code is anything other than a 200.  In python 2.6 it
        # doesn't throw an exception for any 2xx return codes.  In both
        # cases we expect newrelic should return a 201 on success. So 
        # to handle both cases, both the except & else cases below are
        # effectively identical.
    except Exception, e:
        if e.code == 201:
            module.exit_json(changed=True)
        else:
            module.fail_json(msg="unable to update newrelic: %s" % e)
    else:
        if result.code == 201:
            module.exit_json(changed=True)
        else:
            module.fail_json(msg="result code: %d" % result.code)

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>
main()

