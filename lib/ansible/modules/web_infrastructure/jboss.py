#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Jeroen Hoekx <jeroen.hoekx@dsquare.be>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
module: jboss
version_added: "1.4"
short_description: deploy applications to JBoss
description:
  - Deploy applications to JBoss standalone using the filesystem
options:
  deployment:
    required: true
    description:
      - The name of the deployment
  src:
    required: false
    description:
      - The remote path of the application ear or war to deploy
  deploy_path:
    required: false
    default: /var/lib/jbossas/standalone/deployments
    description:
      - The location in the filesystem where the deployment scanner listens
  state:
    required: false
    choices: [ present, absent ]
    default: "present"
    description:
      - Whether the application should be deployed or undeployed
notes:
  - "The JBoss standalone deployment-scanner has to be enabled in standalone.xml"
  - "Ensure no identically named application is deployed through the JBoss CLI"
author: "Jeroen Hoekx (@jhoekx)"
"""

EXAMPLES = """
# Deploy a hello world application
- jboss:
    src: /tmp/hello-1.0-SNAPSHOT.war
    deployment: hello.war
    state: present

# Update the hello world application
- jboss:
    src: /tmp/hello-1.1-SNAPSHOT.war
    deployment: hello.war
    state: present

# Undeploy the hello world application
- jboss:
    deployment: hello.war
    state: absent
"""

import os
import shutil
import time
import json
import requests
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


def is_deployed(module, deploy_path, deployment):

    data_dict = {
        "operation": "read-resource",
        "address": {
            "deployment": deployment
        },
        "include-runtime": True
    }

    headers = {
        'Content-Type': 'application/json'
    }

    data = json.dumps(data_dict)

    resp, info = fetch_url(module, 'http://%s:9990/management' % module.params['hostname'], data=data, headers=headers)

    try:
        assert info['status'] == 200
    except AssertionError:
        return os.path.exists(os.path.join(deploy_path, "%s.deployed" % deployment))

    resp_data = resp.read()
    resp_json = json.loads(resp_data)

    return resp_json['result']['status'] == "OK"


def is_undeployed(deploy_path, deployment):
    return os.path.exists(os.path.join(deploy_path, "%s.undeployed" % deployment))


def is_failed(deploy_path, deployment):
    return os.path.exists(os.path.join(deploy_path, "%s.failed" % deployment))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            src=dict(type='path'),
            deployment=dict(required=True),
            deploy_path=dict(type='path', default='/var/lib/jbossas/standalone/deployments'),
            state=dict(choices=['absent', 'present'], default='present'),
            url_password=dict(required=True),
            url_username=dict(required=True),
            hostname=dict(default='localhost')
        ),
        required_if=[('state', 'present', ('src',))]
    )

    result = dict(changed=False)

    src = module.params['src']
    deployment = module.params['deployment']
    deploy_path = module.params['deploy_path']
    state = module.params['state']
    hostname = module.params['hostname']
    username = module.params['url_username']
    password = module.params['url_password']

    if not os.path.exists(deploy_path):
        module.fail_json(msg="deploy_path does not exist.")

    deployed = is_deployed(module, deploy_path, deployment)

    if state == 'present' and not deployed:
        if not os.path.exists(src):
            module.fail_json(msg='Source file %s does not exist.' % src)
        if is_failed(deploy_path, deployment):
            # Clean up old failed deployment
            os.remove(os.path.join(deploy_path, "%s.failed" % deployment))

        shutil.copyfile(src, os.path.join(deploy_path, deployment))
        while not deployed:
            deployed = is_deployed(module, deploy_path, deployment)
            if is_failed(deploy_path, deployment):
                module.fail_json(msg='Deploying %s failed.' % deployment)
            time.sleep(1)
        result['changed'] = True

    if state == 'present' and deployed:
        data_dict = {
            'operation': 'read-resource',
            'address': {
                'deployment': deployment
            },
            'include-runtime': True
        }

        headers = {
            'Content-Type': 'application/json'
        }
        data = json.dumps(data_dict)

        resp, info = fetch_url(module, 'http://%s:9990/management' % hostname, data=data, headers=headers)

        try:
            assert info['status'] == 200
        except AssertionError:
            if info['status'] != -1:
                module.fail_json(msg=info['msg'])
            else:
                if module.sha1(src) != module.sha1(os.path.join(deploy_path, deployment)):
                    module.exit_json(**result)

                    os.remove(os.path.join(deploy_path, "%s.deployed" % deployment))
                    shutil.copyfile(src, os.path.join(deploy_path, deployment))
                    deployed = False
                    while not deployed:
                        deployed = is_deployed(module, deploy_path, deployment)
                        if is_failed(deploy_path, deployment):
                            module.fail_json(msg='Deploying %s failed.' % deployment)
                        time.sleep(1)
                    result['changed'] = True
                    module.exit_json(**result)

        resp_json = json.loads(resp.read())

        # Process existing deployment hash
        deployment_hash_dict = (key for key in resp_json['result']['content'] if 'hash' in key).next()
        deployment_hash_base64 = deployment_hash_dict['hash']['BYTES_VALUE']
        deployment_hash_hex = deployment_hash_base64.decode('base64').encode('hex')

        if module.sha1(src) != deployment_hash_hex:

            resp = requests.post(
                'http://%s/management/add-content',
                files={'file': open(src, 'rb')},
                auth=requests.auth.HTTPDigestAuth(username, password)
            )

            if resp.status_code < 400:
                result['changed'] = True
            else:
                module.fail_json(msg={'status': 'HTTP %s %s' % (resp.status_code, resp.reason)})

    if state == 'absent' and deployed:
        os.remove(os.path.join(deploy_path, "%s.deployed" % deployment))
        while deployed:
            deployed = not is_undeployed(deploy_path, deployment)
            if is_failed(deploy_path, deployment):
                module.fail_json(msg='Undeploying %s failed.' % deployment)
            time.sleep(1)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
