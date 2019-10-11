#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2019 IBM CORPORATION
# Author(s): Chun Yao <chunyao@cn.ibm.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: ibm_svc_vol_map
short_description: Manage vdisk commands
description:
  - Ansible interface to managing vdisk commands mkvdisk, chvdisk, rmvdisk
version_added: "2.7"
options:
  volname:
    description:
      - vdisk name C(volname).
    required: true
    type: str
  host:
    description:
      - host name H(host).
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
  log_path:
    description:
    - For extra logging
    type: str
  validate_certs:
    description:
    - validate_certs
    type: bool
author:
    - Chun Yao(@Chunyao)
'''

EXAMPLES = '''
- name: map volume to host
  ibm_svc_vol_map:
        clustername: mcr-tb5-cluster-03
        domain: stglab.manchester.uk.ibm.com
        username: superuser
        password: passw0rd
        log_path: /tmp/playbook.debug
        volname: volume0
        host: host4test
        state: present

- name: unmap volume from host
  ibm_svc_vol_map:
        clustername: mcr-tb5-cluster-03
        domain: stglab.manchester.uk.ibm.com
        username: superuser
        password: passw0rd
        log_path: /tmp/playbook.debug
        volname: volume0
        host: host4test
        state: absent
'''
RETURN = '''
'''

import logging
from traceback import format_exc
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ibm_svc_utils import IBMSVCRestApi, svc_argument_spec
from ansible.module_utils._text import to_native


class IBMSVCvdiskhostmap(object):
    def __init__(self):
        argument_spec = svc_argument_spec()

        argument_spec.update(
            dict(
                volname=dict(type='str', required=True),
                host=dict(type='str', required=True),
                state=dict(type='str', required=True, choices=['absent', 'present']),
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
        self.volname = self.module.params['volname']
        self.host = self.module.params['host']
        self.state = self.module.params['state']

        # Optional

        self.restapi = IBMSVCRestApi(
            module=self.module,
            clustername=self.module.params['clustername'],
            domain=self.module.params['domain'],
            username=self.module.params['username'],
            password=self.module.params['password'],
            validate_certs=self.module.params['validate_certs'],
            log_path=log_path
        )

    def get_existing_vdiskhostmap(self):
        merged_result = {}

        data = self.restapi.svc_obj_info(cmd='lsvdiskhostmap', cmdopts=None, cmdargs=[self.volname])

        if isinstance(data, list):
            for d in data:
                merged_result.update(d)
        else:
            merged_result = data

        return merged_result

    # TBD: Implement a more generic way to check for properties to modify.
    def vdiskhostmap_probe(self, data):
        props = []
        self.debug("vdiskhostmap_probe props='%s'", data)
        # TBD: The parameter is easytier but the view has easy_tier label.

        if (self.host != data['host_name']):
            props += ['host']

        if (self.volname != data['name']):
            props += ['volname']

        if props is []:
            props = None

        self.debug("vdiskhostmap_probe props='%s'", data)
        return props

    def vdiskhostmap_create(self):
        if self.module.check_mode:
            self.changed = True
            return

        if not self.volname:
            self.module.fail_json(msg="You must pass in volname to the module.")
        if not self.host:
            self.module.fail_json(msg="You must pass in host name to the module.")

        self.debug("creating vdiskhostmap '%s' '%s'", self.volname, self.host)

        # Make command
        cmd = 'mkvdiskhostmap'
        cmdopts = {}
        cmdopts['host'] = self.host
        cmdargs = [self.volname]

        self.debug("creating vdiskhostmap command %s opts %s args %s", cmd, cmdopts, cmdargs)

        # Run command
        result = self.restapi.svc_run_command(cmd, cmdopts, cmdargs)
        self.debug("create vdiskhostmap result %s", result)

        if 'message' in result:
            self.changed = True
            self.debug("create vdiskhostmap result message %s", result['message'])
        else:
            self.module.fail_json(
                msg="Failed to create vdiskhostmap [%s]" % self.name)

    def vdiskhostmap_update(self, modify):
        # update the vdiskhostmap
        self.debug("updating vdiskhostmap")

        if 'host_name' in modify:
            self.debug("host name is changed. ")

        if 'volname' in modify:
            self.debug("vol name is changed. ")

        self.changed = True

    def vdiskhostmap_delete(self):
        self.debug("deleting vdiskhostmap '%s'", self.volname)

        cmd = 'rmvdiskhostmap'
        cmdopts = {}
        cmdopts['host'] = self.host
        cmdargs = [self.volname]

        self.restapi.svc_run_command(cmd, cmdopts, cmdargs)

        # Any error will have been raised in svc_run_command
        # chmvdisk does not output anything when successful.
        self.changed = True

    def apply(self):
        changed = False
        msg = None

        vdiskhostmap_data = self.get_existing_vdiskhostmap()
        self.debug("Chun 1 : '%s'", vdiskhostmap_data)

        if vdiskhostmap_data:
            if self.state == 'absent':
                self.debug("CHANGED: vdiskhostmap exists, but requested state is 'absent'")
                changed = True
            elif self.state == 'present':
                # This is where we detect if chvdisk should be called
                modify = self.vdiskhostmap_probe(vdiskhostmap_data)
                if modify:
                    changed = True
        else:
            if self.state == 'present':
                self.debug("CHANGED: vdiskhostmap does not exist, but requested state is 'present'")
                changed = True

        if changed:
            if self.module.check_mode:
                self.debug('skipping changes due to check mode')
            else:
                if self.state == 'present':
                    if not vdiskhostmap_data:
                        self.vdiskhostmap_create()
                        msg = "vdiskhostmap %s %s has been created." % (self.volname, self.host)
                    else:
                        # This is where we would modify
                        self.vdiskhostmap_update(modify)
                        msg = "vdiskhostmap [%s] has been modified." % (self.volname)
                elif self.state == 'absent':
                    self.vdiskhostmap_delete()
                    msg = "vdiskhostmap [%s] has been deleted." % (self.volname)
        else:
            self.debug("exiting with no changes")
            if self.state == 'absent':
                msg = "vdiskhostmap [%s] did not exist." % (self.volname)
            else:
                msg = "vdiskhostmap [%s] already exists." % (self.volname)

        self.module.exit_json(msg=msg, changed=changed)


def main():
    v = IBMSVCvdiskhostmap()
    try:
        v.apply()
    except Exception as e:
        v.debug("Exception in apply(): \n%s", format_exc())
        v.module.fail_json(msg="Module failed. Error [%s]." % to_native(e))


if __name__ == '__main__':
    main()
