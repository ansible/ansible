#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Jeroen Hoekx <jeroen.hoekx@dsquare.be>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r"""
module: jboss
version_added: "1.4"
short_description: Deploy applications to JBoss
description:
  - Deploy applications to JBoss standalone using the filesystem.
options:
  deployment:
    required: true
    description:
      - The name of the deployment.
    type: str
  src:
    description:
      - The remote path of the application ear or war to deploy.
      - Required when I(state=present).
      - Ignored when I(state=absent).
    type: path
  deploy_path:
    default: /var/lib/jbossas/standalone/deployments
    description:
      - The location in the filesystem where the deployment scanner listens.
    type: path
  state:
    choices: [ present, absent ]
    default: "present"
    description:
      - Whether the application should be deployed or undeployed.
    type: str
notes:
  - The JBoss standalone deployment-scanner has to be enabled in standalone.xml
  - The module can wait until I(deployment) file is deployed/undeployed by deployment-scanner.
    Duration of waiting time depends on scan-interval parameter from standalone.xml.
  - Ensure no identically named application is deployed through the JBoss CLI
seealso:
- name: WildFly reference
  description: Complete reference of the WildFly documentation.
  link: https://docs.wildfly.org
author:
  - Jeroen Hoekx (@jhoekx)
"""

EXAMPLES = r"""
- name: Deploy a hello world application to the default deploy_path
  jboss:
    src: /tmp/hello-1.0-SNAPSHOT.war
    deployment: hello.war
    state: present

- name: Update the hello world application to the non-default deploy_path
  jboss:
    src: /tmp/hello-1.1-SNAPSHOT.war
    deploy_path: /opt/wildfly/deployment
    deployment: hello.war
    state: present

- name: Undeploy the hello world application from the default deploy_path
  jboss:
    deployment: hello.war
    state: absent
"""

RETURN = r""" # """

import os
import shutil
import time
from ansible.module_utils.basic import AnsibleModule


DEFAULT_DEPLOY_PATH = '/var/lib/jbossas/standalone/deployments'


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
            deployment=dict(type='str', required=True),
            deploy_path=dict(type='path', default=DEFAULT_DEPLOY_PATH),
            state=dict(type='str', choices=['absent', 'present'], default='present'),
        ),
        required_if=[('state', 'present', ('src',))],
        supports_check_mode=True
    )

    result = dict(changed=False)

    src = module.params['src']
    deployment = module.params['deployment']
    deploy_path = module.params['deploy_path']
    state = module.params['state']

    if not os.path.exists(deploy_path):
        module.fail_json(msg="deploy_path does not exist.")

    if state == 'absent' and src:
        module.warn('Parameter src is ignored when state=absent')
    elif state == 'present' and not os.path.exists(src):
        module.fail_json(msg='Source file %s does not exist.' % src)

    deployed = is_deployed(deploy_path, deployment)

    # === when check_mode ===
    if module.check_mode:
        if state == 'present':
            if not deployed:
                result['changed'] = True

            elif deployed:
                if module.sha1(src) != module.sha1(os.path.join(deploy_path, deployment)):
                    result['changed'] = True

        elif state == 'absent' and deployed:
            result['changed'] = True

        module.exit_json(**result)
    # =======================

    if state == 'present' and not deployed:
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
