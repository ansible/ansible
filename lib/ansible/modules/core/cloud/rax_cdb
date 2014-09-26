#!/usr/bin/python -tt
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
module: rax_cdb
short_description: create/delete or resize a Rackspace Cloud Databases instance
description:
  - creates / deletes or resize a Rackspace Cloud Databases instance
    and optionally waits for it to be 'running'. The name option needs to be
    unique since it's used to identify the instance.
version_added: "1.8"
options:
  name:
    description:
      - Name of the databases server instance
    default: null
  flavor:
    description:
      - flavor to use for the instance 1 to 6 (i.e. 512MB to 16GB)
    default: 1
  volume:
    description:
      - Volume size of the database 1-150GB
    default: 2
  state:
    description:
      - Indicate desired state of the resource
    choices: ['present', 'absent']
    default: present
  wait:
    description:
      - wait for the instance to be in state 'running' before returning
    default: "no"
    choices: [ "yes", "no" ]
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 300
author: Simon JAILLET
extends_documentation_fragment: rackspace
'''

EXAMPLES = '''
- name: Build a Cloud Databases
  gather_facts: False
  tasks:
    - name: Server build request
      local_action:
        module: rax_cdb
        credentials: ~/.raxpub
        region: IAD
        name: db-server1
        flavor: 1
        volume: 2
        wait: yes
        state: present
      register: rax_db_server
'''

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False


def find_instance(name):

    cdb = pyrax.cloud_databases
    instances = cdb.list()
    if instances:
        for instance in instances:
            if instance.name == name:
                return instance
    return False


def save_instance(module, name, flavor, volume, wait, wait_timeout):

    for arg, value in dict(name=name, flavor=flavor,
                           volume=volume).iteritems():
        if not value:
            module.fail_json(msg='%s is required for the "rax_cdb"'
                                 ' module' % arg)

    if not (volume >= 1 and volume <= 150):
        module.fail_json(msg='volume is required to be between 1 and 150')

    cdb = pyrax.cloud_databases

    flavors = []
    for item in cdb.list_flavors():
        flavors.append(item.id)

    if not (flavor in flavors):
        module.fail_json(msg='unexisting flavor reference "%s"' % str(flavor))

    changed = False

    instance = find_instance(name)

    if not instance:
        action = 'create'
        try:
            instance = cdb.create(name=name, flavor=flavor, volume=volume)
        except Exception, e:
            module.fail_json(msg='%s' % e.message)
        else:
            changed = True

    else:
        action = None

        if instance.volume.size != volume:
            action = 'resize'
            if instance.volume.size > volume:
                module.fail_json(changed=False, action=action,
                                 msg='The new volume size must be larger than '
                                     'the current volume size',
                                cdb=rax_to_dict(instance))
            instance.resize_volume(volume)
            changed = True

        if int(instance.flavor.id) != flavor:
            action = 'resize'
            pyrax.utils.wait_until(instance, 'status', 'ACTIVE',
                                   attempts=wait_timeout)
            instance.resize(flavor)
            changed = True

    if wait:
        pyrax.utils.wait_until(instance, 'status', 'ACTIVE',
                               attempts=wait_timeout)

    if wait and instance.status != 'ACTIVE':
        module.fail_json(changed=changed, action=action,
                         cdb=rax_to_dict(instance),
                         msg='Timeout waiting for "%s" databases instance to '
                             'be created' % name)

    module.exit_json(changed=changed, action=action, cdb=rax_to_dict(instance))


def delete_instance(module, name, wait, wait_timeout):

    if not name:
        module.fail_json(msg='name is required for the "rax_cdb" module')

    changed = False

    instance = find_instance(name)
    if not instance:
        module.exit_json(changed=False, action='delete')

    try:
        instance.delete()
    except Exception, e:
        module.fail_json(msg='%s' % e.message)
    else:
        changed = True

    if wait:
        pyrax.utils.wait_until(instance, 'status', 'SHUTDOWN',
                               attempts=wait_timeout)

    if wait and instance.status != 'SHUTDOWN':
        module.fail_json(changed=changed, action='delete',
                         cdb=rax_to_dict(instance),
                         msg='Timeout waiting for "%s" databases instance to '
                             'be deleted' % name)

    module.exit_json(changed=changed, action='delete',
                     cdb=rax_to_dict(instance))


def rax_cdb(module, state, name, flavor, volume, wait, wait_timeout):

    # act on the state
    if state == 'present':
        save_instance(module, name, flavor, volume, wait, wait_timeout)
    elif state == 'absent':
        delete_instance(module, name, wait, wait_timeout)


def main():
    argument_spec = rax_argument_spec()
    argument_spec.update(
        dict(
            name=dict(type='str', required=True),
            flavor=dict(type='int', default=1),
            volume=dict(type='int', default=2),
            state=dict(default='present', choices=['present', 'absent']),
            wait=dict(type='bool', default=False),
            wait_timeout=dict(type='int', default=300),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=rax_required_together(),
    )

    if not HAS_PYRAX:
        module.fail_json(msg='pyrax is required for this module')

    name = module.params.get('name')
    flavor = module.params.get('flavor')
    volume = module.params.get('volume')
    state = module.params.get('state')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')

    setup_rax_module(module, pyrax)
    rax_cdb(module, state, name, flavor, volume, wait, wait_timeout)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.rax import *

# invoke the module
main()
