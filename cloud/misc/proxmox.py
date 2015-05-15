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

import os
import logging

try:
  from proxmoxer import ProxmoxAPI
  HAS_PROXMOXER = True
except ImportError:
  HAS_PROXMOXER = False

def get_instance(proxmox, vmid):
  return [ vm for vm in proxmox.cluster.resources.get(type='vm') if vm['vmid'] == int(vmid) ]

def content_check(proxmox, node, ostemplate, storage):
  return [ True for cnt in proxmox.nodes(node).storage(storage).content.get() if cnt['volid'] == ostemplate ]

def node_check(proxmox, node):
  return [ True for nd in proxmox.nodes.get() if nd['node'] == node ]

def create_instance(proxmox, vmid, node, disk, storage, cpus, memory, swap, **kwargs):
  proxmox_node = proxmox.nodes(node)
  logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(name)s: %(message)s')
  proxmox_node.openvz.create(vmid=vmid, storage=storage, memory=memory, swap=swap,
                             cpus=cpus, disk=disk, **kwargs)

def main():
  module = AnsibleModule(
    argument_spec = dict(
      api_host = dict(required=True),
      api_user = dict(required=True),
      api_password = dict(),
      vmid = dict(required=True),
      https_verify_ssl = dict(type='bool', choices=BOOLEANS, default='no'),
      node = dict(),
      password = dict(),
      hostname = dict(),
      ostemplate = dict(),
      disk = dict(dtype='int', default=3),
      cpus = dict(type='int', default=1),
      memory = dict(type='int', default=512),
      swap = dict(type='int', default=0),
      netif = dict(),
      ip_address = dict(),
      onboot = dict(type='bool', choices=BOOLEANS, default='no'),
      storage = dict(default='local'),
      cpuunits = dict(type='int', default=1000),
      nameserver = dict(),
      searchdomain = dict(),
      force = dict(type='bool', choices=BOOLEANS, default='no'),
      state = dict(default='present', choices=['present', 'absent', 'stopped', 'started', 'restart']),
    )
  )

  if not HAS_PROXMOXER:
    module.fail_json(msg='proxmoxer required for this module')

  state = module.params['state']
  api_user = module.params['api_user']
  api_host = module.params['api_host']
  api_password = module.params['api_password']
  vmid = module.params['vmid']
  https_verify_ssl = module.params['https_verify_ssl']
  node = module.params['node']
  disk = module.params['disk']
  cpus = module.params['cpus']
  memory = module.params['memory']
  swap = module.params['swap']
  storage = module.params['storage']

  # If password not set get it from PROXMOX_PASSWORD env
  if not api_password:
    try:
      api_password = os.environ['PROXMOX_PASSWORD']
    except KeyError, e:
      module.fail_json(msg='You should set api_password param or use PROXMOX_PASSWORD environment variable')

  try:
    proxmox = ProxmoxAPI(api_host, user=api_user, password=api_password, verify_ssl=https_verify_ssl)
  except Exception, e:
    module.fail_json(msg='authorization on proxmox cluster failed with exception: %s' % e)

  if state == 'present':
    try:
      if get_instance(proxmox, vmid) and not module.params['force']:
        module.exit_json(changed=False, msg="VM with vmid = %s is already exists" % vmid)
      elif not (node, module.params['hostname'] and module.params['password'] and module.params['ostemplate']):
        module.fail_json(msg='node, hostname, password and ostemplate are mandatory for creating vm')
      elif not node_check(proxmox, node):
        module.fail_json(msg="node '%s' not exists in cluster" % node)
      elif not content_check(proxmox, node, module.params['ostemplate'], storage):
        module.fail_json(msg="ostemplate '%s' not exists on node %s and storage %s"
                         % (module.params['ostemplate'], node, storage))

      create_instance(proxmox, vmid, node, disk, storage, cpus, memory, swap,
                      password = module.params['password'],
                      hostname = module.params['hostname'],
                      ostemplate = module.params['ostemplate'],
                      netif = module.params['netif'],
                      ip_address = module.params['ip_address'],
                      onboot = int(module.params['onboot']),
                      cpuunits = module.params['cpuunits'],
                      nameserver = module.params['nameserver'],
                      searchdomain = module.params['searchdomain'],
                      force = int(module.params['force']))

      module.exit_json(changed=True, vmid=vmid)
    except Exception, e:
      module.fail_json(msg="creation of VM %s failed with exception: %s" % ( vmid, e ))

  elif state == 'started':
    try:
      vm = get_instance(proxmox, vmid)
      if not vm:
        module.fail_json(msg='VM with vmid %s not exists in cluster' % vmid)
      if [ True for vm in proxmox.node(vm[0]['node']).openvz(vmid).status.current.get()['status'] == 'started' ]:
        module.exit_json(changed=False, vmid=vmid)

      proxmox.nodes(vm[0]['node']).openvz(vmid).status.start.post()
      module.exit_json(changed=True, vmid=vmid)
    except Exception, e:
      module.fail_json(msg="starting of VM %s failed with exception: %s" % ( vmid, e ))

  elif state == 'stopped':
    try:
      vm = get_instance(proxmox, vmid)
      if not vm:
        module.fail_json(msg='VM with vmid %s not exists in cluster' % vmid)
      if [ True for vm in proxmox.node(vm[0]['node']).openvz(vmid).status.current.get()['status'] == 'stopped' ]:
        module.exit_json(changed=False, vmid=vmid)

      proxmox.nodes(vm[0]['node']).openvz(vmid).status.shutdown.post()
      module.exit_json(changed=True, vmid=vmid)
    except Exception, e:
      module.fail_json(msg="deletion of VM %s failed with exception: %s" % ( vmid, e ))

  elif state == 'absent':
    try:
      vm = get_instance(proxmox, vmid)
      if not vm:
        module.exit_json(changed=False, vmid=vmid)

      proxmox.nodes(vm[0]['node']).openvz.delete(vmid)
      module.exit_json(changed=True, vmid=vmid)
    except Exception, e:
      module.fail_json(msg="deletion of VM %s failed with exception: %s" % ( vmid, e ))

# import module snippets
from ansible.module_utils.basic import *
main()
