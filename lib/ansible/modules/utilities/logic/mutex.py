#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Aram Alipoor <aram.alipoor@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: mutex

short_description: Generic logical mutex locking to prevent race conditions, globally or per-host.

version_added: "2.8"

description:
    - This module provides a logical mutex utility to prevent other instances of ansible or ansible-playbook
      to run into race condition based on your implementation and requirements.
    - Useful when you need to run a logical operation synchronously. An example would be to adding a master
      node in a cluster when the it does not support adding new masters simultaneously,
      i.e. multiple ansible-playbook's running at the same time.
    - It is possible to have per-host mutex locks, instead of a global one. A common use-case is when a
      local set of operations does not support mutex locking internally.

options:
    name:
        description:
            - System-wide unique name of the logical mutex. Any other task requiring this lock needs to wait until.
        required: true
    state:
        description:
            - Desired state of the mutex lock.
            - If set as `locked` and mutex is not already locked, it will be locked and task will succeed.
            - If set as `locked` and mutex is already locked by another ansible process task will fail.
            - Use this task in conjunction with `retries` and `delay` to wait for lock to release as long as
              you desire.
            - If set as `released` and mutex is already locked and current ansible process is the lock owner
              lock will be released otherwise does nothing.
            - If set as `released` and mutex is already released it does nothing.
        default: "locked"
        choices: [ locked, released ]
    force_release:
        description:
          - Forcefully release the lock without considering current state.
          - Usually this should not be needed unless a deadlock has happened and you are sure releasing the lock
            forcefully will not create a race condition i.e. you are sure there are no other ansible processes
            currently running that need this lock.
        type: bool
        default: 'no'
    per_host:
        description:
          - Determines if the lock must be introduced globally or per-host.
          - If set to `yes` mutex lock is shared between all hosts meaning that it is owner by local machine
            running the ansible process.
          - If set to `no` mutex locks will be created per-host and owner by each host. i.e. This task will succeed
            for hosts where the lock is released and will fail for hosts for which the mutex is still locked.
        type: bool
        default: 'no'
    release_on_exit:
        description:
          - Determines whether if the lock be released when ansible process is exiting.
            This avoid deadlocks if locks are not manually unlocked.
        type: bool
        default: 'yes'

author:
    - Aram Alipoor (@aramalipoor)
'''

EXAMPLES = '''
- name: Masters can be created in cluster one at a time
  mutex:
    name: master_creation

- name: Installation steps of foo app should not run multiple times
  mutex:
    name: foo_installation
    per_host: yes

- name: Wait at most 30 minutes until a master can be added to cluster
  mutex:
    name: master_creation
  retries: 30
  delay: 60
  register: master_creation_lock
  until: master_creation_lock.state != "released"

- name: Release mutex lock for adding a master to cluster
  mutex:
    name: master_creation
    state: released

# Sometimes you need to deliberately leave a mutex locked so that you
# know this node has already been through an installation process but have failed middle-way.
# This can help you decide if you want to destroy the node completely and create everything from scratch.
#
# This is most useful when you have dozens of cattle nodes (Pets vs. Cattle analogy) and it is much easier
# to re-create if something has failed midway.
- name: Start installation of a very complex system on a cattle node
  mutex:
    name: node_provisioning
    release_on_exit: no
'''

RETURN = '''
name:
    description: System-wide unique name of the mutex lock.
    type: str
    returned: always
path:
    description: Real absolute path to the lock file.
    type: str
    returned: always
state:
    description: Current state of the lock.
    type: bool
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', default="locked", choices=['locked', 'released']),
        force_release=dict(type='bool', required=False, default=False),
        per_host=dict(type='bool', required=False, default=False),
        release_on_exit=dict(type='bool', required=False, default=True)
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # TODO Fill result with current state and expected path to lock file

    if module.check_mode:
        return result

    # TODO Write the logic for mutex locks using lib/ansible/module_utils/common/file.py's FileLock

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
