#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rax_cbs_attachments
short_description: Manipulate Rackspace Cloud Block Storage Volume Attachments
description:
     - Manipulate Rackspace Cloud Block Storage Volume Attachments
version_added: 1.6
options:
  device:
    description:
      - The device path to attach the volume to, e.g. /dev/xvde.
      - Before 2.4 this was a required field. Now it can be left to null to auto assign the device name.
    default: null
    required: false
  volume:
    description:
      - Name or id of the volume to attach/detach
    default: null
    required: true
  server:
    description:
      - Name or id of the server to attach/detach
    default: null
    required: true
  state:
    description:
      - Indicate desired state of the resource
    choices:
      - present
      - absent
    default: present
    required: true
  wait:
    description:
      - wait for the volume to be in 'in-use'/'available' state before returning
    default: "no"
    choices:
      - "yes"
      - "no"
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 300
author:
    - "Christopher H. Laco (@claco)"
    - "Matt Martz (@sivel)"
extends_documentation_fragment: rackspace.openstack
'''

EXAMPLES = '''
- name: Attach a Block Storage Volume
  gather_facts: False
  hosts: local
  connection: local
  tasks:
    - name: Storage volume attach request
      local_action:
        module: rax_cbs_attachments
        credentials: ~/.raxpub
        volume: my-volume
        server: my-server
        device: /dev/xvdd
        region: DFW
        wait: yes
        state: present
      register: my_volume
'''

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.rax import (NON_CALLABLES,
                                      rax_argument_spec,
                                      rax_find_server,
                                      rax_find_volume,
                                      rax_required_together,
                                      rax_to_dict,
                                      setup_rax_module,
                                      )


def cloud_block_storage_attachments(module, state, volume, server, device,
                                    wait, wait_timeout):
    cbs = pyrax.cloud_blockstorage
    cs = pyrax.cloudservers

    if cbs is None or cs is None:
        module.fail_json(msg='Failed to instantiate client. This '
                             'typically indicates an invalid region or an '
                             'incorrectly capitalized region name.')

    changed = False
    instance = {}

    volume = rax_find_volume(module, pyrax, volume)

    if not volume:
        module.fail_json(msg='No matching storage volumes were found')

    if state == 'present':
        server = rax_find_server(module, pyrax, server)

        if (volume.attachments and
                volume.attachments[0]['server_id'] == server.id):
            changed = False
        elif volume.attachments:
            module.fail_json(msg='Volume is attached to another server')
        else:
            try:
                volume.attach_to_instance(server, mountpoint=device)
                changed = True
            except Exception as e:
                module.fail_json(msg='%s' % e.message)

            volume.get()

        for key, value in vars(volume).items():
            if (isinstance(value, NON_CALLABLES) and
                    not key.startswith('_')):
                instance[key] = value

        result = dict(changed=changed)

        if volume.status == 'error':
            result['msg'] = '%s failed to build' % volume.id
        elif wait:
            attempts = wait_timeout // 5
            pyrax.utils.wait_until(volume, 'status', 'in-use',
                                   interval=5, attempts=attempts)

        volume.get()
        result['volume'] = rax_to_dict(volume)

        if 'msg' in result:
            module.fail_json(**result)
        else:
            module.exit_json(**result)

    elif state == 'absent':
        server = rax_find_server(module, pyrax, server)

        if (volume.attachments and
                volume.attachments[0]['server_id'] == server.id):
            try:
                volume.detach()
                if wait:
                    pyrax.utils.wait_until(volume, 'status', 'available',
                                           interval=3, attempts=0,
                                           verbose=False)
                changed = True
            except Exception as e:
                module.fail_json(msg='%s' % e.message)

            volume.get()
            changed = True
        elif volume.attachments:
            module.fail_json(msg='Volume is attached to another server')

        result = dict(changed=changed, volume=rax_to_dict(volume))

        if volume.status == 'error':
            result['msg'] = '%s failed to build' % volume.id

        if 'msg' in result:
            module.fail_json(**result)
        else:
            module.exit_json(**result)

    module.exit_json(changed=changed, volume=instance)


def main():
    argument_spec = rax_argument_spec()
    argument_spec.update(
        dict(
            device=dict(required=False),
            volume=dict(required=True),
            server=dict(required=True),
            state=dict(default='present', choices=['present', 'absent']),
            wait=dict(type='bool', default=False),
            wait_timeout=dict(type='int', default=300)
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=rax_required_together()
    )

    if not HAS_PYRAX:
        module.fail_json(msg='pyrax is required for this module')

    device = module.params.get('device')
    volume = module.params.get('volume')
    server = module.params.get('server')
    state = module.params.get('state')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')

    setup_rax_module(module, pyrax)

    cloud_block_storage_attachments(module, state, volume, server, device,
                                    wait, wait_timeout)


if __name__ == '__main__':
    main()
