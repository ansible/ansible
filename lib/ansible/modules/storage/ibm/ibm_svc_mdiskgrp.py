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
module: ibm_svc_mdiskgrp
short_description: Manage mdiskgrp commands
description:
  - Ansible interface to managing mdiskgrp commands mkmdiskgrp, chmdiskgrp, rmmdiskgrp
version_added: "2.7"
options:
  name:
    description:
      - Mdisk group name C(pool).
    required: true
    type: str
  state:
    description:
      - Whether to create (C(present)), or remove (C(absent)) an mdisk group.
    choices: [ absent, present ]
    required: true
    type: str
  clustername:
    description:
      - description
    required: true
    type: str
  domain:
    description:
    - rest api
    type: str
    required: true
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
  datareduction:
    description:
    - Define whether to use data reduction pools on the mdisk group
    type: str
    default: 'no'
    choices: ['yes', 'no']
  easytier:
    description:
    - Define whether to use easyier with the mdisk group
    type: str
    default: 'off'
    choices: ['on', 'off', 'auto']
  encrypt:
    description:
    - Define whether to use encryption with the mdisk group
    type: str
    default: 'no'
    choices: ['yes', 'no']
  ext:
    description:
    - Group size
    type: int
  log_path:
    description:
    - For extra logging
    type: str
  validate_certs:
    description:
      - validate_certs
    type: bool
  parentmdiskgrp:
    description:
      - parentmdiskgrp for sub pool
    type: str
  unit:
    description:
      - unit for sub pool
    type: str
  size:
    description:
      - size for sub pool
    type: int
author:
    - John Hetherington(@John)
'''
EXAMPLES = '''
- name: Create new mdiskgrp named pool1
  mdiskgrp:
    name: pool1
    state: present
    clustername: mcr-fab3-04
    domain:
    username: superuser
    password: letmein
    datareduction: no
    easytier: auto
    encrypt: no
    ext: 1024

- name: Delete mdiskgrp named pool1
  mdiskgrp:
    name: pool1
    state: absent
    clustername: mcr-fab3-04
    domain:
    username: superuser
    password: letmein
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


class IBMSVCmdiskgrp(object):
    def __init__(self):
        argument_spec = svc_argument_spec()

        argument_spec.update(
            dict(
                name=dict(type='str', required=True),
                state=dict(type='str', required=True, choices=['absent', 'present']),
                datareduction=dict(type='str', default='no', choices=['yes', 'no']),
                easytier=dict(type='str', default='off', choices=['on', 'off', 'auto']),
                encrypt=dict(type='str', default='no', choices=['yes', 'no']),
                ext=dict(type='int'),
                parentmdiskgrp=dict(type='str'),
                size=dict(type='int'),
                unit=dict(type='str')
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
        self.datareduction = self.module.params.get('datareduction', None)
        self.easytier = self.module.params.get('easytier', None)
        self.encrypt = self.module.params.get('encrypt', None)
        self.ext = self.module.params.get('ext', None)

        self.parentmdiskgrp = self.module.params.get('parentmdiskgrp', None)
        self.size = self.module.params.get('size', None)
        self.unit = self.module.params.get('unit', None)

        self.restapi = IBMSVCRestApi(
            module=self.module,
            clustername=self.module.params['clustername'],
            domain=self.module.params['domain'],
            username=self.module.params['username'],
            password=self.module.params['password'],
            validate_certs=self.module.params['validate_certs'],
            log_path=log_path
        )

    def mdiskgrp_exists(self):
        return self.restapi.svc_obj_info(cmd='lsmdiskgrp', cmdopts=None, cmdargs=[self.name])

    def mdiskgrp_create(self):
        if self.module.check_mode:
            self.changed = True
            return

        # So ext is optional to mkmdiskgrp but make required in ansible
        # until all options for create are implemented.
        # if not self.ext:
        #    self.module.fail_json(msg="You must pass in ext to the module.")

        self.debug("creating mdisk group '%s'", self.name)

        # Make command
        cmd = 'mkmdiskgrp'
        cmdopts = {}

        if self.parentmdiskgrp:
            cmdopts['parentmdiskgrp'] = self.parentmdiskgrp
            if self.size:
                cmdopts['size'] = self.size
            if self.unit:
                cmdopts['unit'] = self.unit
        else:
            if self.datareduction:
                cmdopts['datareduction'] = self.datareduction
            if self.easytier:
                cmdopts['easytier'] = self.easytier
            if self.encrypt:
                cmdopts['encrypt'] = self.encrypt
            if self.ext:
                cmdopts['ext'] = str(self.ext)
        cmdopts['name'] = self.name
        self.debug("creating mdisk group command %s opts %s", cmd, cmdopts)

        # Run command
        result = self.restapi.svc_run_command(cmd, cmdopts, cmdargs=None)
        self.debug("creating mdisk group result %s", result)

        if 'message' in result:
            self.changed = True
            self.debug("creating mdisk group command result message %s", result['message'])
        else:
            self.module.fail_json(
                msg="Failed to create mdisk group [%s]" % (self.name))

    def mdiskgrp_delete(self):
        self.debug("deleting mdiskgrp '%s'", self.name)

        cmd = 'rmmdiskgrp'
        cmdopts = None
        cmdargs = [self.name]

        result = self.restapi.svc_run_command(cmd, cmdopts, cmdargs)

        # Any error will have been raised in svc_run_command
        # chmkdiskgrp does not output anything when successful.
        self.changed = True

    def mdiskgrp_update(self, modify):
        # updte the mdisk group
        self.debug("updating mdiskgrp '%s'", self.name)

        cmd = 'chmdiskgrp'
        cmdopts = {}
        # TBD: Be smarter handling many properties.
        # if 'easytier' in modify:
        #    cmdopts['easytier'] = self.easytier
        # cmdargs = [self.name]

        # result = self.restapi.svc_run_command(cmd, cmdopts, cmdargs)

        # Any error will have been raised in svc_run_command
        # chmkdiskgrp does not output anything when successful.
        self.changed = True

    # TBD: Implement a more generic way to check for properties to modify.
    def mdiskgrp_probe(self, data):
        props = []

        # TBD: The parameter is easytier but the view has easy_tier label.
        # if self.easytier:
        #    if self.easytier != data['easy_tier']:
        #        props += ['easytier']

        if props is []:
            props = None

        self.debug("mdiskgrp_probe props='%s'", data)
        return props

    def apply(self):
        changed = False
        msg = None

        mdiskgrp_data = self.mdiskgrp_exists()

        if mdiskgrp_data:
            if self.state == 'absent':
                self.debug("CHANGED: mdisk group exists, but requested state is 'absent'")
                changed = True
            elif self.state == 'present':
                # This is where we detect if chmdiskgrp should be called.
                modify = self.mdiskgrp_probe(mdiskgrp_data)
                if modify:
                    changed = True
        else:
            if self.state == 'present':
                self.debug("CHANGED: mdisk group does not exist, but requested state is 'present'")
                changed = True

        if changed:
            if self.module.check_mode:
                self.debug('skipping changes due to check mode')
            else:
                if self.state == 'present':
                    if not mdiskgrp_data:
                        self.mdiskgrp_create()
                        msg = "Mdisk group [%s] has been created." % (self.name)
                    else:
                        # This is where we would modify
                        self.mdiskgrp_update(modify)
                        msg = "Mdisk group [%s] has been modified." % (self.name)

                elif self.state == 'absent':
                    self.mdiskgrp_delete()
                    msg = "Volume [%s] has been deleted." % (self.name)
        else:
            self.debug("exiting with no changes")
            if self.state == 'absent':
                msg = "Mdisk group [%s] did not exist." % (self.name)
            else:
                msg = "Mdisk group [%s] already exists." % (self.name)

        self.module.exit_json(msg=msg, changed=changed)


def main():
    v = IBMSVCmdiskgrp()
    try:
        v.apply()
    except Exception as e:
        v.debug("Exception in apply(): \n%s", format_exc())
        v.module.fail_json(msg="Module failed. Error [%s]." % to_native(e))


if __name__ == '__main__':
    main()
