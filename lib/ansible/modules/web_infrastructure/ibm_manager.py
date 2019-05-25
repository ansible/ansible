#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, Tommy Davison <tntdavison@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ibm_manager

short_description: Module that controls the state of an IBM Deployment Manager

version_added: "2.9"

description:
    - Module that controls the state of IBM Node Deployment Manager.
    - Module is idempotent.
    - Module depends on having the pre-req IBM products installed.
    - Module is aimed at running in a WebSphere ND installation run time.

options:
    state:
        description:
            - Describes the state in which to send IBM Node Agent.
        required: true
        choices:
          - start
          - stop
    path:
        description:
            - Path of IBM Install root. E.g /opt/WebSphere/AppServer.
        required: true
    profile:
        description:
            - Name of IBM Profile that the node agent belongs to.
        required: true


author:
    - Tom Davison (@tntdavison784)
'''


EXAMPLES = '''
- name: Start Deployment Manager
  ibm_manager:
    state: start
    path: /opt/WebSphere/AppServer
    profile: Dmgr01
- name: Stop DMGR
  ibm_manager:
    state: stop
    path: /opt/WebSphere/AppServer
    profile: DmgrProfile
'''


RETURN = '''
result:
    description: Descibes changed state or failed state
    type: str
message:
    description: Succesfully sent Deployment Manager into state

'''
import os
from ansible.module_utils.basic import AnsibleModule


def deployment_manager(module):
    """Function that controls deployment manager state.
    Available states are: stop, and start. Function only controls
    the send state of the module. Meaning, that the checks for running
    service are not done in this module, but rather done in main function.
    """

    manager = "{0}/profiles/{1}/bin/{2}Manager.sh".format(module.params['path'],
    module.params['profile'], module.params['state'])

    run_manager = module.run_command(manager)
    if run_manager[0] != 0:
        module.fail_json(
            msg="Failed to send Deployment Manager into state {0}. \
            See stdout/stderr for details.".format(module.params['state']),
            changed=False,
            stdout=run_manager[1],
            stderr=run_manager[2]
        )
    module.exit_json(
        msg="Successfully sent Deployment Manager into state {0}".format(module.params['state']),
        changed=True
    )


def check_service(module):
    """Function that checks the state of deployment manager.
    If dmgr.pid exists then dmgr is  considered running.
    if not dmgr.pid then dmgr is considered stopped.
    Function calls in deployment_manager function after all checks have been made to
    either start or stop depending on the provided state."""

    dmgr_pid = "{0}/profiles/{1}/logs/dmgr/dmgr.pid".format(module.params['path'],
                                                            module.params['profile'])

    if module.params['state'] == 'start':
        if os.path.exists(dmgr_pid):
            if module.check_mode:
                module.exit_json(
                    msg="Deployment Manager already running.",
                    changed=False
                )
            module.exit_json(
                msg="Deployment Manager already running.",
                changed=False
            )
        else:
            if module.check_mode:
                module.exit_json(
                    msg="Deployment Manager will be started.",
                    changed=True
                )
            deployment_manager(module)

    if module.params['state'] == 'stop':
        if not os.path.exists(dmgr_pid):
            if module.check_mode:
                module.exit_json(
                    msg="Deployment Manager already stopped",
                    changed=False
                )
            module.exit_json(
                msg="Deployment Manager already stopped",
                changed=False
            )
        else:
            if module.check_mode:
                module.exit_json(
                    msg="Deployment Manager will be stopped",
                    changed=True
                )
            deployment_manager(module)


def main():
    """
    Main Module logic.
    Imports sub functions to determine state status.
    """

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', required=True, choices=['start', 'stop']),
            profile=dict(type='str', required=True),
            path=dict(type='str', required=True)
        ),
        supports_check_mode=True
    )

    state = module.params['state']
    profile = module.params['profile']
    path = module.params['path']

# check_service function calls in deployment_manager function
# Function also takes care of the dry run checks
    check_service(module)


if __name__ == "__main__":
    main()
