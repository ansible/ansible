#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Jeroen Hoekx <jeroen.hoekx@dsquare.be>
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
author: Jeroen Hoekx
"""

EXAMPLES = """
# Deploy a hello world application
- jboss: src=/tmp/hello-1.0-SNAPSHOT.war deployment=hello.war state=present
# Update the hello world application
- jboss: src=/tmp/hello-1.1-SNAPSHOT.war deployment=hello.war state=present
# Undeploy the hello world application
- jboss: deployment=hello.war state=absent
"""

import os
import shutil
import time

def is_deployed(deploy_path, deployment):
    return os.path.exists(os.path.join(deploy_path, "%s.deployed"%(deployment)))

def is_undeployed(deploy_path, deployment):
    return os.path.exists(os.path.join(deploy_path, "%s.undeployed"%(deployment)))

def is_failed(deploy_path, deployment):
    return os.path.exists(os.path.join(deploy_path, "%s.failed"%(deployment)))

def main():
    module = AnsibleModule(
        argument_spec = dict(
            src=dict(),
            deployment=dict(required=True),
            deploy_path=dict(default='/var/lib/jbossas/standalone/deployments'),
            state=dict(choices=['absent', 'present'], default='present'),
        ),
    )

    changed = False

    src = module.params['src']
    deployment = module.params['deployment']
    deploy_path = module.params['deploy_path']
    state = module.params['state']

    if state == 'present' and not src:
        module.fail_json(msg="Argument 'src' required.")

    if not os.path.exists(deploy_path):
        module.fail_json(msg="deploy_path does not exist.")

    deployed = is_deployed(deploy_path, deployment)

    if state == 'present' and not deployed:
        if not os.path.exists(src):
            module.fail_json(msg='Source file %s does not exist.'%(src))
        if is_failed(deploy_path, deployment):
            ### Clean up old failed deployment
            os.remove(os.path.join(deploy_path, "%s.failed"%(deployment)))

        shutil.copyfile(src, os.path.join(deploy_path, deployment))
        while not deployed:
            deployed = is_deployed(deploy_path, deployment)
            if is_failed(deploy_path, deployment):
                module.fail_json(msg='Deploying %s failed.'%(deployment))
            time.sleep(1)
        changed = True

    if state == 'present' and deployed:
        if module.sha1(src) != module.sha1(os.path.join(deploy_path, deployment)):
            os.remove(os.path.join(deploy_path, "%s.deployed"%(deployment)))
            shutil.copyfile(src, os.path.join(deploy_path, deployment))
            deployed = False
            while not deployed:
                deployed = is_deployed(deploy_path, deployment)
                if is_failed(deploy_path, deployment):
                    module.fail_json(msg='Deploying %s failed.'%(deployment))
                time.sleep(1)
            changed = True

    if state == 'absent' and deployed:
        os.remove(os.path.join(deploy_path, "%s.deployed"%(deployment)))
        while deployed:
            deployed = not is_undeployed(deploy_path, deployment)
            if is_failed(deploy_path, deployment):
                module.fail_json(msg='Undeploying %s failed.'%(deployment))
            time.sleep(1)
        changed = True

    module.exit_json(changed=changed)

# import module snippets
from ansible.module_utils.basic import *
main()
