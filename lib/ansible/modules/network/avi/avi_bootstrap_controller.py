#!/usr/bin/python
"""
# Created on 5 April, 2019
#
# @author: Shrikant Chaudhari (shrikant.chaudhari@avinetworks.com) GitHub ID: gitshrikant
#
# module_check: not supported
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
#
"""

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_bootstrap_controller
author: Shrikant Chaudhari (@gitshrikant) <shrikant.chaudhari@avinetworks.com>
short_description: avi bootstrap controller module.
description:
    - This module can be used for initializing the password of a user.
    - This module is useful for setting up admin password for Controller bootstrap.
version_added: 2.9
requirements: [ avisdk, subprocess ]
options:
    password:
        description:
            - New password to initialize controller password.
    ssh_key_pair:
        description:
            - AWS/Azure ssh key pair to login on the controller instance.
    force_mode:
        description:
            - Avoid check for login with given password and re-initialise controller
              with given password even if controller password is initialised before
    con_wait_time:
        description:
            - Wait for controller to come up for given con_wait_time
        default: 3600
    round_wait:
        description:
            - Retry after every rount_wait time to check for controller state.
        default: 10

extends_documentation_fragment:
    - avi
'''

EXAMPLES = '''
  - name: Initialize user password
    avi_bootstrap_controller:
      avi_credentials:
        controller: "controller_ip"
        port: "443"
        api_version: "18.2.3"
      ssh_key_pair: "/path/to/key-pair-file.pem"
      password: new_password
      con_wait_time: 3600
      round_wait: 10

'''

RETURN = '''
obj:
    description: Avi REST resource
    returned: success, changed
    type: dict
'''

import time

try:
    import subprocess
    import json
    HAS_LIB = True
except ImportError:
    HAS_LIB = False

from ansible.module_utils.basic import AnsibleModule


try:
    from ansible.module_utils.network.avi.avi import (
        avi_common_argument_spec, ansible_return, avi_obj_cmp,
        cleanup_absent_fields, HAS_AVI)
    from ansible.module_utils.network.avi.avi_api import (
        ApiSession, AviCredentials)
    from ansible.module_utils.urls import Request
except ImportError:
    HAS_AVI = False


def controller_wait(controller_ip, port=None, round_wait=10, wait_time=3600):
    """
    It waits for controller to come up for a given wait_time (default 1 hour).
    :return: controller_up: Boolean value for controller up state.
    """
    count = 0
    max_count = wait_time / round_wait
    ctrl_port = port if port else 80
    path = "http://{0}:{1}{2}".format(controller_ip, ctrl_port, "/api/cluster/runtime")
    ctrl_status = False
    while True:
        if count >= max_count:
            break
        try:
            req = Request()
            r = req.open('GET', path).read()
            if json.load(r)['cluster_state']['state'] == 'CLUSTER_UP_NO_HA':
                ctrl_status = True
                break
        except Exception as e:
            pass
        time.sleep(round_wait)
        count += 1
    return ctrl_status


def main():
    argument_specs = dict(
        password=dict(type='str', required=True, no_log=True),
        ssh_key_pair=dict(type='str', required=True),
        force_mode=dict(type='bool', default=False),
        # Max time to wait for controller up state
        con_wait_time=dict(type='int', default=3600),
        # Retry after every rount_wait time to check for controller state.
        round_wait=dict(type='int', default=10),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(argument_spec=argument_specs)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    if not HAS_LIB:
        return module.fail_json(
            msg='avi_api_fileservice, subprocess and json modules are required for this module')

    api_creds = AviCredentials()
    api_creds.update_from_ansible_module(module)
    new_password = module.params.get('password')
    key_pair = module.params.get('ssh_key_pair')
    force_mode = module.params.get('force_mode')
    # Wait for controller to come up for given con_wait_time
    controller_up = controller_wait(api_creds.controller, api_creds.port, module.params['round_wait'],
                                    module.params['con_wait_time'])
    if not controller_up:
        return module.fail_json(
            msg='Something wrong with the controller. The Controller is not in the up state.')
    if not force_mode:
        # Check for admin login with new password before initializing controller password.
        try:
            ApiSession.get_session(
                api_creds.controller, "admin",
                password=new_password, timeout=api_creds.timeout,
                tenant=api_creds.tenant, tenant_uuid=api_creds.tenant_uuid,
                token=api_creds.token, port=api_creds.port)
            module.exit_json(msg="Already initialized controller password with a given password.", changed=False)
        except Exception as e:
            pass
    cmd = "ssh -o \"StrictHostKeyChecking no\" -t -i " + key_pair + " admin@" + \
          api_creds.controller + " \"ls /opt/avi/scripts/initialize_admin_user.py && echo -e '" + \
          api_creds.controller + "\\n" + new_password + "' | sudo /opt/avi/scripts/initialize_admin_user.py\""
    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    cmd_status = process.returncode
    if cmd_status == 0:
        return module.exit_json(changed=True, msg="Successfully initialized controller with new password. "
                                "return_code: %s output: %s error: %s" % (cmd_status, stdout, stderr))
    else:
        return module.fail_json(msg='Fail to initialize password for controllers return_code: %s '
                                'output: %s error: %s' % (cmd_status, stdout, stderr))


if __name__ == '__main__':
    main()
