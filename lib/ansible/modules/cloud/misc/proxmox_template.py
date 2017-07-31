#!/usr/bin/python
#
# Copyright: Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: proxmox_template
short_description: management of OS templates in Proxmox VE cluster
description:
  - allows you to upload/delete templates in Proxmox VE cluster
version_added: "2.0"
options:
  api_host:
    description:
      - the host of the Proxmox VE cluster
    required: true
  api_user:
    description:
      - the user to authenticate with
    required: true
  api_password:
    description:
      - the password to authenticate with
      - you can use PROXMOX_PASSWORD environment variable
    default: null
    required: false
  validate_certs:
    description:
      - enable / disable https certificate verification
    default: false
    required: false
    type: bool
  node:
    description:
      - Proxmox VE node, when you will operate with template
    default: null
    required: true
  src:
    description:
      - path to uploaded file
      - required only for C(state=present)
    default: null
    required: false
    aliases: ['path']
  template:
    description:
      - the template name
      - required only for states C(absent), C(info)
    default: null
    required: false
  content_type:
    description:
      - content type
      - required only for C(state=present)
    default: 'vztmpl'
    required: false
    choices: ['vztmpl', 'iso']
  storage:
    description:
      - target storage
    default: 'local'
    required: false
  timeout:
    description:
      - timeout for operations
    default: 30
    required: false
  force:
    description:
      - can be used only with C(state=present), exists template will be overwritten
    default: false
    required: false
    type: bool
  state:
    description:
     - Indicate desired state of the template
    choices: ['present', 'absent']
    default: present
notes:
  - Requires proxmoxer and requests modules on host. This modules can be installed with pip.
requirements: [ "proxmoxer", "requests" ]
author: "Sergei Antipov @UnderGreen"
'''

EXAMPLES = '''
# Upload new openvz template with minimal options
- proxmox_template:
    node: uk-mc02
    api_user: root@pam
    api_password: 1q2w3e
    api_host: node1
    src: ~/ubuntu-14.04-x86_64.tar.gz

# Upload new openvz template with minimal options use environment PROXMOX_PASSWORD variable(you should export it before)
- proxmox_template:
    node: uk-mc02
    api_user: root@pam
    api_host: node1
    src: ~/ubuntu-14.04-x86_64.tar.gz

# Upload new openvz template with all options and force overwrite
- proxmox_template:
    node: uk-mc02
    api_user: root@pam
    api_password: 1q2w3e
    api_host: node1
    storage: local
    content_type: vztmpl
    src: ~/ubuntu-14.04-x86_64.tar.gz
    force: yes

# Delete template with minimal options
- proxmox_template:
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
    taskid = proxmox.nodes(node).storage(storage).upload.post(content=content_type, filename=open(realpath))
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
            api_host=dict(required=True),
            api_user=dict(required=True),
            api_password=dict(no_log=True),
            validate_certs=dict(type='bool', default='no'),
            node=dict(),
            src=dict(),
            template=dict(),
            content_type=dict(default='vztmpl', choices=['vztmpl', 'iso']),
            storage=dict(default='local'),
            timeout=dict(type='int', default=30),
            force=dict(type='bool', default='no'),
            state=dict(default='present', choices=['present', 'absent']),
        )
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

            from ansible import utils
            realpath = utils.path_dwim(None, src)
            template = os.path.basename(realpath)
            if get_template(proxmox, node, storage, content_type, template) and not module.params['force']:
                module.exit_json(changed=False, msg='template with volid=%s:%s/%s is already exists' % (storage, content_type, template))
            elif not src:
                module.fail_json(msg='src param to uploading template file is mandatory')
            elif not (os.path.exists(realpath) and os.path.isfile(realpath)):
                module.fail_json(msg='template file on path %s not exists' % realpath)

            if upload_template(module, proxmox, api_host, node, storage, content_type, realpath, timeout):
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
