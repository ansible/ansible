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
from ansible.module_utils.basic import AnsibleModule


def is_deployed(deploy_path, deployment):
    return os.path.exists(os.path.join(deploy_path, "%s.deployed" % deployment))


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
        ),
        required_if=[('state', 'present', ('src',))]
    )

    result = dict(changed=False)

    src = module.params['src']
    deployment = module.params['deployment']
    deploy_path = module.params['deploy_path']
    state = module.params['state']

    if not os.path.exists(deploy_path):
        module.fail_json(msg="deploy_path does not exist.")

    deployed = is_deployed(deploy_path, deployment)

    if state == 'present' and not deployed:
        if not os.path.exists(src):
            module.fail_json(msg='Source file %s does not exist.' % src)
        if is_failed(deploy_path, deployment):
            # Clean up old failed deployment
            os.remove(os.path.join(deploy_path, "%s.failed" % deployment))

        shutil.copyfile(src, os.path.join(deploy_path, deployment))
        while not deployed:
            deployed = is_deployed(deploy_path, deployment)
            if is_failed(deploy_path, deployment):
                module.fail_json(msg='Deploying %s failed.' % deployment)
            time.sleep(1)
        result['changed'] = True

    if state == 'present' and deployed:
        if module.sha1(src) != module.sha1(os.path.join(deploy_path, deployment)):
            os.remove(os.path.join(deploy_path, "%s.deployed" % deployment))
            shutil.copyfile(src, os.path.join(deploy_path, deployment))
            deployed = False
            while not deployed:
                deployed = is_deployed(deploy_path, deployment)
                if is_failed(deploy_path, deployment):
                    module.fail_json(msg='Deploying %s failed.' % deployment)
                time.sleep(1)
            result['changed'] = True

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
