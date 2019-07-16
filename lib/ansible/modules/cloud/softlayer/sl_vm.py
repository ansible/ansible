#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: sl_vm
short_description: create or cancel a virtual instance in SoftLayer
description:
  - Creates or cancels SoftLayer instances.
  - When created, optionally waits for it to be 'running'.
version_added: "2.1"
options:
  instance_id:
    description:
      - Instance Id of the virtual instance to perform action option.
  hostname:
    description:
      - Hostname to be provided to a virtual instance.
  domain:
    description:
      - Domain name to be provided to a virtual instance.
  datacenter:
    description:
      - Datacenter for the virtual instance to be deployed.
  tags:
    description:
      - Tag or list of tags to be provided to a virtual instance.
  hourly:
    description:
      - Flag to determine if the instance should be hourly billed.
    type: bool
    default: 'yes'
  private:
    description:
      - Flag to determine if the instance should be private only.
    type: bool
    default: 'no'
  dedicated:
    description:
      - Flag to determine if the instance should be deployed in dedicated space.
    type: bool
    default: 'no'
  local_disk:
    description:
      - Flag to determine if local disk should be used for the new instance.
    type: bool
    default: 'yes'
  cpus:
    description:
      - Count of cpus to be assigned to new virtual instance.
    required: true
  memory:
    description:
      - Amount of memory to be assigned to new virtual instance.
    required: true
  disks:
    description:
      - List of disk sizes to be assigned to new virtual instance.
    required: true
    default: [ 25 ]
  os_code:
    description:
      - OS Code to be used for new virtual instance.
  image_id:
    description:
      - Image Template to be used for new virtual instance.
  nic_speed:
    description:
      - NIC Speed to be assigned to new virtual instance.
    default: 10
  public_vlan:
    description:
      - VLAN by its Id to be assigned to the public NIC.
  private_vlan:
    description:
      - VLAN by its Id to be assigned to the private NIC.
  ssh_keys:
    description:
      - List of ssh keys by their Id to be assigned to a virtual instance.
  post_uri:
    description:
      - URL of a post provisioning script to be loaded and executed on virtual instance.
  state:
    description:
      - Create, or cancel a virtual instance.
      - Specify C(present) for create, C(absent) to cancel.
    choices: [ absent, present ]
    default: present
  wait:
    description:
      - Flag used to wait for active status before returning.
    type: bool
    default: 'yes'
  wait_time:
    description:
      - Time in seconds before wait returns.
    default: 600
requirements:
    - python >= 2.6
    - softlayer >= 4.1.1
author:
- Matt Colton (@mcltn)
'''

EXAMPLES = '''
- name: Build instance
  hosts: localhost
  gather_facts: no
  tasks:
  - name: Build instance request
    sl_vm:
      hostname: instance-1
      domain: anydomain.com
      datacenter: dal09
      tags: ansible-module-test
      hourly: yes
      private: no
      dedicated: no
      local_disk: yes
      cpus: 1
      memory: 1024
      disks: [25]
      os_code: UBUNTU_LATEST
      wait: no

- name: Build additional instances
  hosts: localhost
  gather_facts: no
  tasks:
  - name: Build instances request
    sl_vm:
      hostname: "{{ item.hostname }}"
      domain: "{{ item.domain }}"
      datacenter: "{{ item.datacenter }}"
      tags: "{{ item.tags }}"
      hourly: "{{ item.hourly }}"
      private: "{{ item.private }}"
      dedicated: "{{ item.dedicated }}"
      local_disk: "{{ item.local_disk }}"
      cpus: "{{ item.cpus }}"
      memory: "{{ item.memory }}"
      disks: "{{ item.disks }}"
      os_code: "{{ item.os_code }}"
      ssh_keys: "{{ item.ssh_keys }}"
      wait: "{{ item.wait }}"
    with_items:
      - hostname: instance-2
        domain: anydomain.com
        datacenter: dal09
        tags:
          - ansible-module-test
          - ansible-module-test-slaves
        hourly: yes
        private: no
        dedicated: no
        local_disk: yes
        cpus: 1
        memory: 1024
        disks:
          - 25
          - 100
        os_code: UBUNTU_LATEST
        ssh_keys: []
        wait: True
      - hostname: instance-3
        domain: anydomain.com
        datacenter: dal09
        tags:
          - ansible-module-test
          - ansible-module-test-slaves
        hourly: yes
        private: no
        dedicated: no
        local_disk: yes
        cpus: 1
        memory: 1024
        disks:
          - 25
          - 100
        os_code: UBUNTU_LATEST
        ssh_keys: []
        wait: yes

- name: Cancel instances
  hosts: localhost
  gather_facts: no
  tasks:
  - name: Cancel by tag
    sl_vm:
      state: absent
      tags: ansible-module-test
'''

# TODO: Disabled RETURN as it is breaking the build for docs. Needs to be fixed.
RETURN = '''# '''

import json
import time

try:
    import SoftLayer
    from SoftLayer import VSManager

    HAS_SL = True
    vsManager = VSManager(SoftLayer.create_client_from_env())
except ImportError:
    HAS_SL = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import string_types


# TODO: get this info from API
STATES = ['present', 'absent']
DATACENTERS = ['ams01', 'ams03', 'che01', 'dal01', 'dal05', 'dal06', 'dal09', 'dal10', 'dal12', 'dal13', 'fra02',
               'fra04', 'fra05', 'hkg02', 'hou02', 'lon02', 'lon04', 'lon06', 'mel01', 'mex01', 'mil01', 'mon01',
               'osl01', 'par01', 'sao01', 'sea01', 'seo01', 'sjc01', 'sjc03', 'sjc04', 'sng01', 'syd01', 'syd04',
               'tok02', 'tor01', 'wdc01', 'wdc04', 'wdc06', 'wdc07']
CPU_SIZES = [1, 2, 4, 8, 16, 32, 56]
MEMORY_SIZES = [1024, 2048, 4096, 6144, 8192, 12288, 16384, 32768, 49152, 65536, 131072, 247808]
INITIALDISK_SIZES = [25, 100]
LOCALDISK_SIZES = [25, 100, 150, 200, 300]
SANDISK_SIZES = [10, 20, 25, 30, 40, 50, 75, 100, 125, 150, 175, 200, 250, 300, 350, 400, 500, 750, 1000, 1500, 2000]
NIC_SPEEDS = [10, 100, 1000]


def create_virtual_instance(module):

    instances = vsManager.list_instances(
        hostname=module.params.get('hostname'),
        domain=module.params.get('domain'),
        datacenter=module.params.get('datacenter')
    )

    if instances:
        return False, None

    # Check if OS or Image Template is provided (Can't be both, defaults to OS)
    if (module.params.get('os_code') is not None and module.params.get('os_code') != ''):
        module.params['image_id'] = ''
    elif (module.params.get('image_id') is not None and module.params.get('image_id') != ''):
        module.params['os_code'] = ''
        module.params['disks'] = []  # Blank out disks since it will use the template
    else:
        return False, None

    tags = module.params.get('tags')
    if isinstance(tags, list):
        tags = ','.join(map(str, module.params.get('tags')))

    instance = vsManager.create_instance(
        hostname=module.params.get('hostname'),
        domain=module.params.get('domain'),
        cpus=module.params.get('cpus'),
        memory=module.params.get('memory'),
        hourly=module.params.get('hourly'),
        datacenter=module.params.get('datacenter'),
        os_code=module.params.get('os_code'),
        image_id=module.params.get('image_id'),
        local_disk=module.params.get('local_disk'),
        disks=module.params.get('disks'),
        ssh_keys=module.params.get('ssh_keys'),
        nic_speed=module.params.get('nic_speed'),
        private=module.params.get('private'),
        public_vlan=module.params.get('public_vlan'),
        private_vlan=module.params.get('private_vlan'),
        dedicated=module.params.get('dedicated'),
        post_uri=module.params.get('post_uri'),
        tags=tags,
    )

    if instance is not None and instance['id'] > 0:
        return True, instance
    else:
        return False, None


def wait_for_instance(module, id):
    instance = None
    completed = False
    wait_timeout = time.time() + module.params.get('wait_time')
    while not completed and wait_timeout > time.time():
        try:
            completed = vsManager.wait_for_ready(id, 10, 2)
            if completed:
                instance = vsManager.get_instance(id)
        except Exception:
            completed = False

    return completed, instance


def cancel_instance(module):
    canceled = True
    if module.params.get('instance_id') is None and (module.params.get('tags') or module.params.get('hostname') or module.params.get('domain')):
        tags = module.params.get('tags')
        if isinstance(tags, string_types):
            tags = [module.params.get('tags')]
        instances = vsManager.list_instances(tags=tags, hostname=module.params.get('hostname'), domain=module.params.get('domain'))
        for instance in instances:
            try:
                vsManager.cancel_instance(instance['id'])
            except Exception:
                canceled = False
    elif module.params.get('instance_id') and module.params.get('instance_id') != 0:
        try:
            vsManager.cancel_instance(instance['id'])
        except Exception:
            canceled = False
    else:
        return False, None

    return canceled, None


def main():

    module = AnsibleModule(
        argument_spec=dict(
            instance_id=dict(type='str'),
            hostname=dict(type='str'),
            domain=dict(type='str'),
            datacenter=dict(type='str', choices=DATACENTERS),
            tags=dict(type='str'),
            hourly=dict(type='bool', default=True),
            private=dict(type='bool', default=False),
            dedicated=dict(type='bool', default=False),
            local_disk=dict(type='bool', default=True),
            cpus=dict(type='int', choices=CPU_SIZES),
            memory=dict(type='int', choices=MEMORY_SIZES),
            disks=dict(type='list', default=[25]),
            os_code=dict(type='str'),
            image_id=dict(type='str'),
            nic_speed=dict(type='int', choices=NIC_SPEEDS),
            public_vlan=dict(type='str'),
            private_vlan=dict(type='str'),
            ssh_keys=dict(type='list', default=[]),
            post_uri=dict(type='str'),
            state=dict(type='str', default='present', choices=STATES),
            wait=dict(type='bool', default=True),
            wait_time=dict(type='int', default=600),
        )
    )

    if not HAS_SL:
        module.fail_json(msg='softlayer python library required for this module')

    if module.params.get('state') == 'absent':
        (changed, instance) = cancel_instance(module)

    elif module.params.get('state') == 'present':
        (changed, instance) = create_virtual_instance(module)
        if module.params.get('wait') is True and instance:
            (changed, instance) = wait_for_instance(module, instance['id'])

    module.exit_json(changed=changed, instance=json.loads(json.dumps(instance, default=lambda o: o.__dict__)))


if __name__ == '__main__':
    main()
