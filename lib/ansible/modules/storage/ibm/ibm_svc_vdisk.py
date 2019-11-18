#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2019 IBM CORPORATION
# Author(s): Jamie Jordan <jamie.jordan@ibm.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: ibm_svc_vdisk
short_description: Manage vdisk commands
description:
  - Ansible interface to managing vdisk commands mkvdisk, chvdisk, rmvdisk
version_added: "2.7"
options:
  name:
    description:
      - vdisk name C(volume).
    required: true
    type: str
  state:
    description:
      - Whether to create (C(present)), or remove (C(absent)) a vdisk group.
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
  mdiskgrp:
    description:
    - Specify pool for adding the vdisk to by name or ID
    type: str
  easytier:
    description:
    - Define whether to use easyier with the vdisk
    type: str
    default: 'off'
    choices: [ 'on', 'off', 'auto' ]
  size:
    description:
    - Define size of vdisk
    type: str
  unit:
    description:
    - Define unit of storage for the size option.
    type: str
    choices: [ b, kb, mb, gb, tb, pb ]
    default: mb
  validate_certs:
    description:
    - validate_certs
    type: bool
  log_path:
    description:
    - For extra logging
    type: str
author:
    - Jamie Jordan(@Jamie)
'''

EXAMPLES = '''
- name: execute mkvdisk
  ibm_svc_vdisk:
        clustername: mcr-tb5-cluster-03
        domain: stglab.manchester.uk.ibm.com
        username: superuser
        password: passw0rd
        log_path: /tmp/playbook.debug
        name: volume0
        state: present
        mdiskgrp: 0
        easytier: 'off'
        size: "4294967296"
        unit: b

- name: execute rmvdisk
  ibm_svc_vdisk:
        clustername: mcr-tb5-cluster-03
        domain: stglab.manchester.uk.ibm.com
        username: superuser
        password: passw0rd
        log_path: /tmp/playbook.debug
        name: volume0
        state: absent
'''
RETURN = '''
'''
import logging
from traceback import format_exc

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ibm_svc_utils import IBMSVCRestApi, svc_argument_spec
from ansible.module_utils._text import to_native


class IBMSVCvdisk(object):
    def __init__(self):
        argument_spec = svc_argument_spec()

        argument_spec.update(
            dict(
                name=dict(type='str', required=True),
                state=dict(type='str', required=True, choices=['absent', 'present']),
                mdiskgrp=dict(type='str', required=False),
                size=dict(type='str', required=False),
                unit=dict(type='str', default='mb', choices=['b', 'kb', 'mb', 'gb', 'tb', 'pb']),
                easytier=dict(type='str', default='off', choices=['on', 'off', 'auto'])
            )
        )

        self.module = AnsibleModule(argument_spec=argument_spec,
                                    supports_check_mode=True)

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
        self.mdiskgrp = self.module.params['mdiskgrp']
        self.size = self.module.params['size']
        self.unit = self.module.params['unit']
        self.easytier = self.module.params.get('easytier', None)

        self.restapi = IBMSVCRestApi(
            module=self.module,
            clustername=self.module.params['clustername'],
            domain=self.module.params['domain'],
            username=self.module.params['username'],
            password=self.module.params['password'],
            validate_certs=self.module.params['validate_certs'],
            log_path=log_path
        )

    def get_existing_vdisk(self):
        merged_result = {}

        data = self.restapi.svc_obj_info(cmd='lsvdisk', cmdopts=None, cmdargs=[self.name])

        if isinstance(data, list):
            for d in data:
                merged_result.update(d)
        else:
            merged_result = data

        return merged_result

    # TBD: Implement a more generic way to check for properties to modify.
    def vdisk_probe(self, data):
        props = []

        # TBD: The parameter is easytier but the view has easy_tier label.
        if self.easytier:
            if self.easytier != data['easy_tier']:
                props += ['easytier']

        if props is []:
            props = None

        self.debug("vdisk_probe props='%s'", data)
        return props

    def vdisk_create(self):
        if self.module.check_mode:
            self.changed = True
            return

        if not self.mdiskgrp:
            self.module.fail_json(msg="You must pass in mdiskgrp to the module.")
        if not self.size:
            self.module.fail_json(msg="You must pass in size to the module.")
        if not self.unit:
            self.module.fail_json(msg="You must pass in unit to the module.")

        self.debug("creating vdisk '%s'", self.name)

        # Make command
        cmd = 'mkvdisk'
        cmdopts = {}
        if self.mdiskgrp:
            cmdopts['mdiskgrp'] = self.mdiskgrp
        if self.size:
            cmdopts['size'] = self.size
        if self.unit:
            cmdopts['unit'] = self.unit
        if self.easytier:
            cmdopts['easytier'] = self.easytier
        cmdopts['name'] = self.name
        self.debug("creating vdisk command %s opts %s", cmd, cmdopts)

        # Run command
        result = self.restapi.svc_run_command(cmd, cmdopts, cmdargs=None)
        self.debug("create vdisk result %s", result)

        if 'message' in result:
            self.changed = True
            self.debug("create vdisk result message %s", result['message'])
        else:
            self.module.fail_json(
                msg="Failed to create vdisk [%s]" % self.name)

    def vdisk_update(self, modify):
        # update the vdisk
        self.debug("updating vdisk '%s'", self.name)

        cmd = 'chvdisk'
        cmdopts = {}

        # TBD: Be smarter handling many properties.
        if 'easytier' in modify:
            cmdopts['easytier'] = self.easytier
        cmdargs = [self.name]

        self.restapi.svc_run_command(cmd, cmdopts, cmdargs)

        # Any error will have been raised in svc_run_command
        # chvdisk does not output anything when successful.
        self.changed = True

    def vdisk_delete(self):
        self.debug("deleting vdisk '%s'", self.name)

        cmd = 'rmvdisk'
        cmdopts = None
        cmdargs = [self.name]

        self.restapi.svc_run_command(cmd, cmdopts, cmdargs)

        # Any error will have been raised in svc_run_command
        # chmvdisk does not output anything when successful.
        self.changed = True

    def apply(self):
        changed = False
        msg = None

        vdisk_data = self.get_existing_vdisk()

        if vdisk_data:
            if self.state == 'absent':
                self.debug("CHANGED: vdisk exists, but requested state is 'absent'")
                changed = True
            elif self.state == 'present':
                # This is where we detect if chvdisk should be called
                modify = self.vdisk_probe(vdisk_data)
                if modify:
                    changed = True
        else:
            if self.state == 'present':
                self.debug("CHANGED: vdisk does not exist, but requested state is 'present'")
                changed = True

        if changed:
            if self.module.check_mode:
                self.debug('skipping changes due to check mode')
            else:
                if self.state == 'present':
                    if not vdisk_data:
                        self.vdisk_create()
                        msg = "vdisk %s has been created." % (self.name)
                    else:
                        # This is where we would modify
                        self.vdisk_update(modify)
                        msg = "vdisk [%s] has been modified." % (self.name)
                elif self.state == 'absent':
                    self.vdisk_delete()
                    msg = "vdisk [%s] has been deleted." % (self.name)
        else:
            self.debug("exiting with no changes")
            if self.state == 'absent':
                msg = "vdisk [%s] did not exist." % (self.name)
            else:
                msg = "vdisk [%s] already exists." % (self.name)

        self.module.exit_json(msg=msg, changed=changed)


def main():
    v = IBMSVCvdisk()
    try:
        v.apply()
    except Exception as e:
        v.debug("Exception in apply(): \n%s", format_exc())
        v.module.fail_json(msg="Module failed. Error [%s]." % to_native(e))


if __name__ == '__main__':
    main()
