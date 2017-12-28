#!/usr/bin/python -tt
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


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
  cdb_type:
    description:
      - type of instance (i.e. MySQL, MariaDB, Percona)
    default: MySQL
    version_added: "2.0"
    aliases: ['type']
  cdb_version:
    description:
      - version of database (MySQL supports 5.1 and 5.6, MariaDB supports 10, Percona supports 5.6)
    choices: ['5.1', '5.6', '10']
    version_added: "2.0"
    aliases: ['version']
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
author: "Simon JAILLET (@jails)"
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
        cdb_type: MySQL
        cdb_version: 5.6
        wait: yes
        state: present
      register: rax_db_server
'''

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.rax import rax_argument_spec, rax_required_together, rax_to_dict, setup_rax_module


def find_instance(name):

    cdb = pyrax.cloud_databases
    instances = cdb.list()
    if instances:
        for instance in instances:
            if instance.name == name:
                return instance
    return False


def save_instance(module, name, flavor, volume, cdb_type, cdb_version, wait,
                  wait_timeout):

    for arg, value in dict(name=name, flavor=flavor,
                           volume=volume, type=cdb_type, version=cdb_version
                           ).items():
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
            instance = cdb.create(name=name, flavor=flavor, volume=volume,
                                  type=cdb_type, version=cdb_version)
        except Exception as e:
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
    except Exception as e:
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


def rax_cdb(module, state, name, flavor, volume, cdb_type, cdb_version, wait,
            wait_timeout):

    # act on the state
    if state == 'present':
        save_instance(module, name, flavor, volume, cdb_type, cdb_version, wait,
                      wait_timeout)
    elif state == 'absent':
        delete_instance(module, name, wait, wait_timeout)


def main():
    argument_spec = rax_argument_spec()
    argument_spec.update(
        dict(
            name=dict(type='str', required=True),
            flavor=dict(type='int', default=1),
            volume=dict(type='int', default=2),
            cdb_type=dict(type='str', default='MySQL', aliases=['type']),
            cdb_version=dict(type='str', default='5.6', aliases=['version']),
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
    cdb_type = module.params.get('cdb_type')
    cdb_version = module.params.get('cdb_version')
    state = module.params.get('state')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')

    setup_rax_module(module, pyrax)
    rax_cdb(module, state, name, flavor, volume, cdb_type, cdb_version, wait, wait_timeout)


if __name__ == '__main__':
    main()
