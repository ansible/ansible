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

DOCUMENTATION = '''
---
module: sl_vm
short_description: create or cancel a virtual instance in SoftLayer
description:
  - Creates or cancels SoftLayer instances. When created, optionally waits for it to be 'running'.
version_added: "2.1"
options:
  instance_id:
    description:
      - Instance Id of the virtual instance to perform action option
    required: false
    default: null
  hostname:
    description:
      - Hostname to be provided to a virtual instance
    required: false
    default: null
  domain:
    description:
      - Domain name to be provided to a virtual instance
    required: false
    default: null
  datacenter:
    description:
      - Datacenter for the virtual instance to be deployed
    required: false
    default: null
  tags:
    description:
      - Tag or list of tags to be provided to a virtual instance
    required: false
    default: null
  hourly:
    description:
      - Flag to determine if the instance should be hourly billed
    required: false
    default: true
  private:
    description:
      - Flag to determine if the instance should be private only
    required: false
    default: false
  dedicated:
    description:
      - Falg to determine if the instance should be deployed in dedicated space
    required: false
    default: false
  local_disk:
    description:
      - Flag to determine if local disk should be used for the new instance
    required: false
    default: true
  cpus:
    description:
      - Count of cpus to be assigned to new virtual instance
    required: true
    default: null
  memory:
    description:
      - Amount of memory to be assigned to new virtual instance
    required: true
    default: null
  disks:
    description:
      - List of disk sizes to be assigned to new virtual instance
    required: true
    default: [25]
  os_code:
    description:
      - OS Code to be used for new virtual instance
    required: false
    default: null
  image_id:
    description:
      - Image Template to be used for new virtual instance
    required: false
    default: null
  nic_speed:
    description:
      - NIC Speed to be assigned to new virtual instance
    required: false
    default: 10
  public_vlan:
    description:
      - VLAN by its Id to be assigned to the public NIC
    required: false
    default: null
  private_vlan:
    description:
      - VLAN by its Id to be assigned to the private NIC
    required: false
    default: null
  ssh_keys:
    description:
      - List of ssh keys by their Id to be assigned to a virtual instance
    required: false
    default: null
  post_uri:
    description:
      - URL of a post provisioning script ot be loaded and exectued on virtual instance
    required: false
    default: null
  state:
    description:
      - Create, or cancel a virtual instance. Specify "present" for create, "absent" to cancel.
    required: false
    default: 'present'
  wait:
    description:
      - Flag used to wait for active status before returning
    required: false
    default: true
  wait_timeout:
    description:
      - time in seconds before wait returns
    required: false
    default: 600

requirements:
    - "python >= 2.6"
    - "softlayer >= 4.1.1"
author: "Matt Colton (@mcltn)"
'''

EXAMPLES = '''
- name: Build instance
  hosts: localhost
  gather_facts: False
  tasks:
  - name: Build instance request
    local_action:
      module: sl_vm
      hostname: instance-1
      domain: anydomain.com
      datacenter: dal09
      tags: ansible-module-test
      hourly: True
      private: False
      dedicated: False
      local_disk: True
      cpus: 1
      memory: 1024
      disks: [25]
      os_code: UBUNTU_LATEST
      wait: False

- name: Build additional instances
  hosts: localhost
  gather_facts: False
  tasks:
  - name: Build instances request
    local_action:
      module: sl_vm
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
      - { hostname: 'instance-2', domain: 'anydomain.com', datacenter: 'dal09', tags: ['ansible-module-test', 'ansible-module-test-slaves'], hourly: True, private: False, dedicated: False, local_disk: True, cpus: 1, memory: 1024, disks: [25,100], os_code: 'UBUNTU_LATEST', ssh_keys: [], wait: True }
      - { hostname: 'instance-3', domain: 'anydomain.com', datacenter: 'dal09', tags: ['ansible-module-test', 'ansible-module-test-slaves'], hourly: True, private: False, dedicated: False, local_disk: True, cpus: 1, memory: 1024, disks: [25,100], os_code: 'UBUNTU_LATEST', ssh_keys: [], wait: True }


- name: Cancel instances
  hosts: localhost
  gather_facts: False
  tasks:
  - name: Cancel by tag
    local_action:
      module: sl_vm
      state: absent
      tags: ansible-module-test
'''

# TODO: Disabled RETURN as it is breaking the build for docs. Needs to be fixed.
RETURN = '''# '''

import time

#TODO: get this info from API
STATES = ['present', 'absent']
DATACENTERS = ['ams01','ams03','che01','dal01','dal05','dal06','dal09','dal10','fra02','hkg02','hou02','lon02','mel01','mex01','mil01','mon01','osl01','par01','sjc01','sjc03','sao01','sea01','sng01','syd01','tok02','tor01','wdc01','wdc04']
CPU_SIZES = [1,2,4,8,16,32,56]
MEMORY_SIZES = [1024,2048,4096,6144,8192,12288,16384,32768,49152,65536,131072,247808]
INITIALDISK_SIZES = [25,100]
LOCALDISK_SIZES = [25,100,150,200,300]
SANDISK_SIZES = [10,20,25,30,40,50,75,100,125,150,175,200,250,300,350,400,500,750,1000,1500,2000]
NIC_SPEEDS = [10,100,1000]

try:
  import SoftLayer
  from SoftLayer import VSManager

  HAS_SL = True
  vsManager = VSManager(SoftLayer.create_client_from_env())
except ImportError:
  HAS_SL = False


def create_virtual_instance(module):

  instances = vsManager.list_instances(
    hostname = module.params.get('hostname'),
    domain = module.params.get('domain'),
    datacenter = module.params.get('datacenter')
  )

  if instances:
    return False, None


  # Check if OS or Image Template is provided (Can't be both, defaults to OS)
  if (module.params.get('os_code') != None and module.params.get('os_code') != ''):
    module.params['image_id'] = ''
  elif (module.params.get('image_id') != None and module.params.get('image_id') != ''):
    module.params['os_code'] = ''
    module.params['disks'] = [] # Blank out disks since it will use the template
  else:
    return False, None

  tags = module.params.get('tags')
  if isinstance(tags, list):
    tags = ','.join(map(str, module.params.get('tags')))

  instance = vsManager.create_instance(
    hostname = module.params.get('hostname'),
    domain = module.params.get('domain'),
    cpus = module.params.get('cpus'),
    memory = module.params.get('memory'),
    hourly = module.params.get('hourly'),
    datacenter = module.params.get('datacenter'),
    os_code = module.params.get('os_code'),
    image_id = module.params.get('image_id'),
    local_disk = module.params.get('local_disk'),
    disks = module.params.get('disks'),
    ssh_keys = module.params.get('ssh_keys'),
    nic_speed = module.params.get('nic_speed'),
    private = module.params.get('private'),
    public_vlan = module.params.get('public_vlan'),
    private_vlan = module.params.get('private_vlan'),
    dedicated = module.params.get('dedicated'),
    post_uri = module.params.get('post_uri'),
    tags = tags)

  if instance != None and instance['id'] > 0:
    return True, instance
  else:
    return False, None


def wait_for_instance(module,id):
  instance = None
  completed = False
  wait_timeout = time.time() + module.params.get('wait_time')
  while not completed and wait_timeout > time.time():
    try:
      completed = vsManager.wait_for_ready(id, 10, 2)
      if completed:
        instance = vsManager.get_instance(id)
    except:
      completed = False

  return completed, instance


def cancel_instance(module):
  canceled = True
  if module.params.get('instance_id') == None and (module.params.get('tags') or module.params.get('hostname') or module.params.get('domain')):
    tags = module.params.get('tags')
    if isinstance(tags, basestring):
      tags = [module.params.get('tags')]
    instances = vsManager.list_instances(tags = tags, hostname = module.params.get('hostname'), domain = module.params.get('domain'))
    for instance in instances:
      try:
        vsManager.cancel_instance(instance['id'])
      except:
        canceled = False
  elif module.params.get('instance_id') and module.params.get('instance_id') != 0:
    try:
      vsManager.cancel_instance(instance['id'])
    except:
      canceled = False
  else:
    return False, None

  return canceled, None


def main():

  module = AnsibleModule(
    argument_spec=dict(
      instance_id=dict(),
      hostname=dict(),
      domain=dict(),
      datacenter=dict(choices=DATACENTERS),
      tags=dict(),
      hourly=dict(type='bool', default=True),
      private=dict(type='bool', default=False),
      dedicated=dict(type='bool', default=False),
      local_disk=dict(type='bool', default=True),
      cpus=dict(type='int', choices=CPU_SIZES),
      memory=dict(type='int', choices=MEMORY_SIZES),
      disks=dict(type='list', default=[25]),
      os_code=dict(),
      image_id=dict(),
      nic_speed=dict(type='int', choices=NIC_SPEEDS),
      public_vlan=dict(),
      private_vlan=dict(),
      ssh_keys=dict(type='list', default=[]),
      post_uri=dict(),
      state=dict(default='present', choices=STATES),
      wait=dict(type='bool', default=True),
      wait_time=dict(type='int', default=600)
    )
  )

  if not HAS_SL:
    module.fail_json(msg='softlayer python library required for this module')

  if module.params.get('state') == 'absent':
    (changed, instance) = cancel_instance(module)

  elif module.params.get('state') == 'present':
      (changed, instance) = create_virtual_instance(module)
      if module.params.get('wait') == True and instance:
        (changed, instance) = wait_for_instance(module, instance['id'])

  module.exit_json(changed=changed, instance=json.loads(json.dumps(instance, default=lambda o: o.__dict__)))

from ansible.module_utils.basic import *

if __name__ == '__main__':
  main()
