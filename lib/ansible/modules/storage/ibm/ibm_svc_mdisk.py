#!/usr/bin/python
# Copyright (C) 2018 IBM CORPORATION
# Author(s): John Hetherington <john.hetherington@uk.ibm.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ibm_svc_mdisk
short_description: Manage mdisk commands
description:
  - Ansible interface to manage mdisk related commands
version_added: "2.7"
options:
  name:
    description:
      - Create mdisk name C(mdisk1).
    required: true
    type: str
  state:
    description:
      - Whether to create (C(present)), or remove (C(absent)) the mdisk.
    choices: [ absent, present ]
    required: true
    type: str
  clustername:
    description:
      - name of host cluster
    type: str
  domain:
    description:
      - domain for IBM SVC storage
    type: str
  username:
    description:
      - rest api username
    type: str
    required: true
  password:
    description:
      - rest api password
    type: str
    required: true
  drive:
    description:
      - Drive or drives to use as members of the raid array
    type: str
  mdiskgrp:
    description:
      - The storage pool to which you want to add the mdisk
    type: str
  log_path:
    description:
      - Debug logging to this file
    type: str
  validate_certs:
    description:
      - validate_certs
    type: bool
  level:
    description:
      - level
    type: str
    choices: ['raid0', 'raid1', 'raid5', 'raid6', 'raid10']
  encrypt:
    description:
      - encrypt
    type: str
    default: 'no'
    choices: ['yes', 'no']
author:
    - John Hetherington(@John)
'''
EXAMPLES = '''
- name: Create new array mdisk named mdisk20
  mdisk:
    name: mdisk20
    state: present
    clustername: mcr-tb5-29-cl
    username: superuser
    password: letmein
    level: raid0
    drive: '5:6'
    encrypt: no
    mdiskgrp: pool20

- name: Delete mdisk named mdisk20
  mdisk:
    name: mdisk20
    state: absent
    clustername: mcr-tb5-29-cl
    username: superuser
    password: letmein
    mdiskgrp: pool20
'''
RETURN = '''
'''

import json
import logging
import time
from traceback import format_exc
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.ibm_svc_utils import IBMSVCRestApi, svc_argument_spec


class IBMSVCmdisk(object):
    def __init__(self):
        argument_spec = svc_argument_spec()

        argument_spec.update(
            dict(
                name=dict(type='str', required=True),
                state=dict(type='str', required=True, choices=['absent', 'present']),
                level=dict(type='str', choices=['raid0', 'raid1', 'raid5', 'raid6', 'raid10']),
                drive=dict(type='str', default=None),
                encrypt=dict(type='str', default='no', choices=['yes', 'no']),
                mdiskgrp=dict(type='str', required=True)
            )
        )

        mutually_exclusive = []
        self.module = AnsibleModule(argument_spec=argument_spec,
                                    mutually_exclusive=mutually_exclusive,
                                    supports_check_mode=True)
        p = self.module.params

        # logging setup
        log_path = self.module.params['log_path']
        self._logger = logging.getLogger(self.__class__.__name__)
        self.debug = self._logger.debug
        if log_path:
            logging.basicConfig(level=logging.DEBUG, filename=log_path)

        # Required
        self.name = self.module.params['name']
        self.state = self.module.params['state']

        # Optional
        self.level = self.module.params.get('level', None)
        self.drive = self.module.params.get('drive', None)
        self.encrypt = self.module.params.get('encrypt', None)
        self.mdiskgrp = self.module.params.get('mdiskgrp', None)

        self.restapi = IBMSVCRestApi(
            module=self.module,
            clustername=self.module.params['clustername'],
            domain=self.module.params['domain'],
            username=self.module.params['username'],
            password=self.module.params['password'],
            validate_certs=self.module.params['validate_certs'],
            log_path=log_path
        )

    def mdisk_exists(self):
        return self.restapi.svc_obj_info(cmd='lsmdisk', cmdopts=None, cmdargs=[self.name])

    def mdisk_create(self):
        if self.module.check_mode:
            self.changed = True
            return

        # For now we create mdisk via mkarray which needs these options
        # level, drive, mdiskgrp
        if not self.level:
            self.module.fail_json(msg="You must pass in level to the module.")
        if not self.drive:
            self.module.fail_json(msg="You must pass in drive to the module.")
        if not self.mdiskgrp:
            self.module.fail_json(msg="You must pass in mdiskgrp to the module.")

        self.debug("creating mdisk '%s'", self.name)

        # Make command
        cmd = 'mkarray'
        cmdopts = {}
        if self.level:
            cmdopts['level'] = self.level
        if self.drive:
            cmdopts['drive'] = self.drive
        if self.encrypt:
            cmdopts['encrypt'] = self.encrypt
        cmdopts['name'] = self.name
        cmdargs = [self.mdiskgrp]
        self.debug("creating mdisk command=%s opts=%s args=%s", cmd, cmdopts, cmdargs)

        # Run command
        result = self.restapi.svc_run_command(cmd, cmdopts, cmdargs)
        self.debug("create mdisk result %s", result)

        if 'message' in result:
            self.changed = True
            self.debug("create mdisk result message %s", result['message'])
        else:
            self.module.fail_json(
                msg="Failed to create mdisk [%s]" % (self.name))

    def mdisk_delete(self):
        self.debug("deleting mdisk '%s'", self.name)
        cmd = 'rmmdisk'
        cmdopts = {}
        cmdopts['mdisk'] = self.name
        cmdargs = [self.mdiskgrp]

        result = self.restapi.svc_run_command(cmd, cmdopts, cmdargs)

        # Any error will have been raised in svc_run_command
        # chmkdiskgrp does not output anything when successful.
        self.changed = True

    def mdisk_update(self, modify):
        # update the mdisk
        self.debug("updating mdisk '%s'", self.name)

        cmd = 'chmdisk'
        cmdopts = {}
        # chmdisk does not like mdisk arrays.
        cmdargs = [self.name]

        # TBD: Implement changed logic.
        # result = self.restapi.svc_run_command(cmd, cmdopts, cmdargs)

        # Any error will have been raised in svc_run_command
        # chmkdiskgrp does not output anything when successful.
        self.changed = True

    # TBD: Implement a more generic way to check for properties to modify.
    def mdisk_probe(self, data):
        props = []

        if self.encrypt:
            if self.encrypt != data['encrypt']:
                props += ['encrypt']

        if props is []:
            props = None

        self.debug("mdisk_probe props='%s'", data)
        return props

    def apply(self):
        changed = False
        msg = None

        mdisk_data = self.mdisk_exists()

        if mdisk_data:
            if self.state == 'absent':
                self.debug("CHANGED: mdisk exists, but requested state is 'absent'")
                changed = True
            elif self.state == 'present':
                # This is where we detect if chmdisk should be called.
                modify = self.mdisk_probe(mdisk_data)
                if modify:
                    changed = True
        else:
            if self.state == 'present':
                self.debug("CHANGED: mdisk does not exist, but requested state is 'present'")
                changed = True

        if changed:
            if self.module.check_mode:
                self.debug('skipping changes due to check mode')
            else:
                if self.state == 'present':
                    if not mdisk_data:
                        self.mdisk_create()
                        msg = "Mdisk group [%s] has been created." % (self.name)
                    else:
                        # This is where we would modify
                        self.mdisk_update(modify)
                        msg = "Mdisk group [%s] has been modified." % (self.name)

                elif self.state == 'absent':
                    self.mdisk_delete()
                    msg = "Volume [%s] has been deleted." % (self.name)
        else:
            self.debug("exiting with no changes")
            if self.state == 'absent':
                msg = "Mdisk group [%s] did not exist." % (self.name)
            else:
                msg = "Mdisk group [%s] already exists." % (self.name)

        self.module.exit_json(msg=msg, changed=changed)


def main():
    v = IBMSVCmdisk()
    try:
        v.apply()
    except Exception as e:
        v.debug("Exception in apply(): \n%s", format_exc())
        v.module.fail_json(msg="Module failed. Error [%s]." % to_native(e))


if __name__ == '__main__':
    main()
