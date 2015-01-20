#!/usr/bin/python
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

# This is a DOCUMENTATION stub specific to this module, it extends
# a documentation fragment located in ansible.utils.module_docs_fragments
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
      - The device path to attach the volume to, e.g. /dev/xvde
    default: null
    required: true
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
author: Christopher H. Laco, Matt Martz
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
            except Exception, e:
                module.fail_json(msg='%s' % e.message)

            volume.get()

        for key, value in vars(volume).iteritems():
            if (isinstance(value, NON_CALLABLES) and
                    not key.startswith('_')):
                instance[key] = value

        result = dict(changed=changed)

        if volume.status == 'error':
            result['msg'] = '%s failed to build' % volume.id
        elif wait:
            attempts = wait_timeout / 5
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
            except Exception, e:
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
            device=dict(required=True),
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

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.rax import *

### invoke the module
main()
