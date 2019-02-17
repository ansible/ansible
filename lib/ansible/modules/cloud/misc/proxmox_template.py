#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: proxmox_template
short_description: Manage OS templates in Proxmox VE cluster
description:
  - Allows you to upload/delete templates in Proxmox VE cluster.
version_added: "2.0"
options:
  api_host:
    description:
      - The host of the Proxmox VE cluster.
    type: str
    required: true
  api_user:
    description:
      - The user to authenticate with.
    type: str
    required: true
  api_password:
    description:
      - The password to authenticate with.
      - You can use PROXMOX_PASSWORD environment variable.
    type: str
  validate_certs:
    description:
      - Whether HTTPS certificate verification is enabled.
    type: bool
    default: no
  node:
    description:
      - Proxmox VE node, when you will operate with template.
    type: str
    required: true
  src:
    description:
      - Path to uploaded file.
      - Required only for C(state=present).
    type: path
    aliases: [ path ]
  template:
    description:
      - The template name.
      - Required only for states C(absent), C(info).
    type: str
  content_type:
    description:
      - Content type.
      - Required only for C(state=present).
    choices: [ iso, vztmpl ]
    default: vztmpl
  storage:
    description:
      - Target storage.
    type: str
    default: local
  timeout:
    description:
      - Timeout for operations.
    type: int
    default: 30
  force:
    description:
      - Can be used only with C(state=present), exists template will be overwritten.
    type: bool
    default: no
  state:
    description:
     - Indicate desired state of the template.
    type: str
    choices: [ absent, present ]
    default: present
notes:
  - Requires proxmoxer and requests modules on host. This modules can be installed with pip.
requirements:
- proxmoxer
- requests
author:
- Sergei Antipov (@UnderGreen)
'''

EXAMPLES = r'''
- name: Upload new openvz template with minimal options
  proxmox_template:
    node: uk-mc02
    api_user: root@pam
    api_password: 1q2w3e
    api_host: node1
    src: ~/ubuntu-14.04-x86_64.tar.gz

# Use environment PROXMOX_PASSWORD variable, you should export it before
- name: Upload new openvz template with minimal options
  proxmox_template:
    node: uk-mc02
    api_user: root@pam
    api_host: node1
    src: ~/ubuntu-14.04-x86_64.tar.gz

- name: Upload new openvz template with all options and force overwrite
  proxmox_template:
    node: uk-mc02
    api_user: root@pam
    api_password: 1q2w3e
    api_host: node1
    storage: local
    content_type: vztmpl
    src: ~/ubuntu-14.04-x86_64.tar.gz
    force: yes

- name: Delete template with minimal options
  proxmox_template:
    node: uk-mc02
    api_user: root@pam
    api_password: 1q2w3e
    api_host: node1
    template: ubuntu-14.04-x86_64.tar.gz
    state: absent
'''

import os
import time

try:
    from proxmoxer import ProxmoxAPI
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False

from ansible.module_utils.basic import AnsibleModule


def get_template(proxmox, node, storage, content_type, template):
    return [True for tmpl in proxmox.nodes(node).storage(storage).content.get()
            if tmpl['volid'] == '%s:%s/%s' % (storage, content_type, template)]


def upload_template(module, proxmox, api_host, node, storage, content_type, realpath, timeout):
    taskid = proxmox.nodes(node).storage(storage).upload.post(content=content_type, filename=open(realpath, 'rb'))
    while timeout:
        task_status = proxmox.nodes(api_host.split('.')[0]).tasks(taskid).status.get()
        if task_status['status'] == 'stopped' and task_status['exitstatus'] == 'OK':
            return True
        timeout = timeout - 1
        if timeout == 0:
            module.fail_json(msg='Reached timeout while waiting for uploading template. Last line in task before timeout: %s'
                             % proxmox.node(node).tasks(taskid).log.get()[:1])

        time.sleep(1)
    return False


def delete_template(module, proxmox, node, storage, content_type, template, timeout):
    volid = '%s:%s/%s' % (storage, content_type, template)
    proxmox.nodes(node).storage(storage).content.delete(volid)
    while timeout:
        if not get_template(proxmox, node, storage, content_type, template):
            return True
        timeout = timeout - 1
        if timeout == 0:
            module.fail_json(msg='Reached timeout while waiting for deleting template.')

        time.sleep(1)
    return False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_host=dict(type='str', required=True),
            api_user=dict(type='str', required=True),
            api_password=dict(type='str', no_log=True),
            validate_certs=dict(type='bool', default=False),
            node=dict(type='str'),
            src=dict(type='path', aliases=['path']),
            template=dict(type='str'),
            content_type=dict(type='str', default='vztmpl', choices=['iso', 'vztmpl']),
            storage=dict(type='str', default='local'),
            timeout=dict(type='int', default=30),
            force=dict(type='bool', default=False),
            state=dict(type='str', default='present', choices=['absent', 'present']),
        ),
    )

    if not HAS_PROXMOXER:
        module.fail_json(msg='proxmoxer required for this module')

    state = module.params['state']
    api_user = module.params['api_user']
    api_host = module.params['api_host']
    api_password = module.params['api_password']
    validate_certs = module.params['validate_certs']
    node = module.params['node']
    storage = module.params['storage']
    timeout = module.params['timeout']

    # If password not set get it from PROXMOX_PASSWORD env
    if not api_password:
        try:
            api_password = os.environ['PROXMOX_PASSWORD']
        except KeyError as e:
            module.fail_json(msg='You should set api_password param or use PROXMOX_PASSWORD environment variable')

    try:
        proxmox = ProxmoxAPI(api_host, user=api_user, password=api_password, verify_ssl=validate_certs)
    except Exception as e:
        module.fail_json(msg='authorization on proxmox cluster failed with exception: %s' % e)

    if state == 'present':
        try:
            content_type = module.params['content_type']
            src = module.params['src']

            template = os.path.basename(src)
            if get_template(proxmox, node, storage, content_type, template) and not module.params['force']:
                module.exit_json(changed=False, msg='template with volid=%s:%s/%s is already exists' % (storage, content_type, template))
            elif not src:
                module.fail_json(msg='src param to uploading template file is mandatory')
            elif not (os.path.exists(src) and os.path.isfile(src)):
                module.fail_json(msg='template file on path %s not exists' % src)

            if upload_template(module, proxmox, api_host, node, storage, content_type, src, timeout):
                module.exit_json(changed=True, msg='template with volid=%s:%s/%s uploaded' % (storage, content_type, template))
        except Exception as e:
            module.fail_json(msg="uploading of template %s failed with exception: %s" % (template, e))

    elif state == 'absent':
        try:
            content_type = module.params['content_type']
            template = module.params['template']

            if not template:
                module.fail_json(msg='template param is mandatory')
            elif not get_template(proxmox, node, storage, content_type, template):
                module.exit_json(changed=False, msg='template with volid=%s:%s/%s is already deleted' % (storage, content_type, template))

            if delete_template(module, proxmox, node, storage, content_type, template, timeout):
                module.exit_json(changed=True, msg='template with volid=%s:%s/%s deleted' % (storage, content_type, template))
        except Exception as e:
            module.fail_json(msg="deleting of template %s failed with exception: %s" % (template, e))


if __name__ == '__main__':
    main()
