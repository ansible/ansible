#!/usr/bin/python

# (c) 2013, Vincent Van der Kussen <vincent at vanderkussen.org>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: ovirt
author: Vincent Van der Kussen
short_description: oVirt/RHEV platform management
description:
    - allows you to create new instances, either from scratch or an image, in addition to deleting or stopping instances on the oVirt/RHEV platform
version_added: "1.4"
options:
  user:
    description:
     - the user to authenticate with
    default: null
    required: true
    aliases: []
  url:
    description:
     - the url of the oVirt instance
    default: null
    required: true
    aliases: []
  instance_name:
    description:
     - the name of the instance to use
    default: null
    required: true
    aliases: [ vmname ]
  password:
    description:
     - password of the user to authenticate with
    default: null
    required: true
    aliases: []
  image:
    description:
     - template to use for the instance
    default: null
    required: false
    aliases: []
  resource_type:
    description:
     - whether you want to deploy an image or create an instance from scratch.
    default: null
    required: false
    aliases: []
    choices: [ 'new', 'template' ]
  zone:
    description:
     - deploy the image to this oVirt cluster
    default: null
    required: false
    aliases: []
  instance_disksize:
    description:
     - size of the instance's disk in GB
    default: null
    required: false
    aliases: [ vm_disksize]
  instance_cpus:
    description:
     - the instance's number of cpu's
    default: 1
    required: false
    aliases: [ vmcpus ]
  instance_nic:
    description:
     - name of the network interface in oVirt/RHEV
    default: null
    required: false
    aliases: [ vmnic  ]
  instance_network:
    description:
     - the logical network the machine should belong to
    default: rhevm
    required: false
    aliases: [ vmnetwork ]
  instance_mem:
    description:
     - the instance's amount of memory in MB
    default: null
    required: false
    aliases: [ vmmem ]
  instance_type:
    description:
     - define if the instance is a server or desktop
    default: server
    required: false
    aliases: [ vmtype ]
    choices: [ 'server', 'desktop' ]
  disk_alloc:
    description:
     - define if disk is thin or preallocated
    default: thin
    required: false
    aliases: []
    choices: [ 'thin', 'preallocated' ]
  disk_int:
    description:
     - interface type of the disk
    default: virtio
    required: false
    aliases: []
    choices: [ 'virtio', 'ide' ]
  instance_os:
    description:
     - type of Operating System
    default: null
    required: false
    aliases: [ vmos ]
  instance_cores:
    description:
     - define the instance's number of cores
    default: 1
    required: false
    aliases: [ vmcores ]
  sdomain:
    description:
     - the Storage Domain where you want to create the instance's disk on.
    default: null
    required: false
    aliases: []
  region:
    description:
     - the oVirt/RHEV datacenter where you want to deploy to
    default: null
    required: false
    aliases: []
  state:
    description:
     - create, terminate or remove instances
    default: 'present'
    required: false
    aliases: []
    choices: ['present', 'absent', 'shutdown', 'started', 'restarted']

requirements: [ "ovirt-engine-sdk" ]
'''
EXAMPLES = '''
# Basic example provisioning from image.

action: ovirt >
    user=admin@internal 
    url=https://ovirt.example.com 
    instance_name=ansiblevm04 
    password=secret 
    image=centos_64 
    zone=cluster01 
    resource_type=template"

# Full example to create new instance from scratch
action: ovirt > 
    instance_name=testansible 
    resource_type=new 
    instance_type=server 
    user=admin@internal 
    password=secret 
    url=https://ovirt.example.com 
    instance_disksize=10 
    zone=cluster01 
    region=datacenter1 
    instance_cpus=1 
    instance_nic=nic1 
    instance_network=rhevm 
    instance_mem=1000 
    disk_alloc=thin 
    sdomain=FIBER01 
    instance_cores=1 
    instance_os=rhel_6x64 
    disk_int=virtio"

# stopping an instance
action: ovirt >
    instance_name=testansible
    state=stopped
    user=admin@internal
    password=secret
    url=https://ovirt.example.com

# starting an instance
action: ovirt >
    instance_name=testansible 
    state=started 
    user=admin@internal 
    password=secret 
    url=https://ovirt.example.com


'''
import sys

try:
    from ovirtsdk.api import API
    from ovirtsdk.xml import params
except ImportError:
    print "failed=True msg='ovirtsdk required for this module'"
    sys.exit(1)

# ------------------------------------------------------------------- #
# create connection with API
#
def conn(url, user, password):
    api = API(url=url, username=user, password=password, insecure=True)
    try:
        value = api.test()
    except:
        print "error connecting to the oVirt API"
        sys.exit(1)
    return api

# ------------------------------------------------------------------- #
# Create VM from scratch
def create_vm(conn, vmtype, vmname, zone, vmdisk_size, vmcpus, vmnic, vmnetwork, vmmem, vmdisk_alloc, sdomain, vmcores, vmos, vmdisk_int):
    if vmdisk_alloc == 'thin':
        # define VM params
        vmparams = params.VM(name=vmname,cluster=conn.clusters.get(name=zone),os=params.OperatingSystem(type_=vmos),template=conn.templates.get(name="Blank"),memory=1024 * 1024 * int(vmmem),cpu=params.CPU(topology=params.CpuTopology(cores=int(vmcores))), type_=vmtype)
        # define disk params
        vmdisk= params.Disk(size=1024 * 1024 * 1024 * int(vmdisk_size), wipe_after_delete=True, sparse=True, interface=vmdisk_int, type_="System", format='cow',
        storage_domains=params.StorageDomains(storage_domain=[conn.storagedomains.get(name=sdomain)]))
        # define network parameters
        network_net = params.Network(name=vmnetwork)
        nic_net1 = params.NIC(name='nic1', network=network_net, interface='virtio')
    elif vmdisk_alloc == 'preallocated':
        # define VM params
        vmparams = params.VM(name=vmname,cluster=conn.clusters.get(name=zone),os=params.OperatingSystem(type_=vmos),template=conn.templates.get(name="Blank"),memory=1024 * 1024 * int(vmmem),cpu=params.CPU(topology=params.CpuTopology(cores=int(vmcores))) ,type_=vmtype)
        # define disk params
        vmdisk= params.Disk(size=1024 * 1024 * 1024 * int(vmdisk_size), wipe_after_delete=True, sparse=False, interface=vmdisk_int, type_="System", format='raw',
        storage_domains=params.StorageDomains(storage_domain=[conn.storagedomains.get(name=sdomain)]))
        # define network parameters
        network_net = params.Network(name=vmnetwork)
        nic_net1 = params.NIC(name=vmnic, network=network_net, interface='virtio')
        
    try:
        conn.vms.add(vmparams)
    except:
        print "Error creating VM with specified parameters"
        sys.exit(1)
    vm = conn.vms.get(name=vmname)
    try:
        vm.disks.add(vmdisk)
    except:
        print "Error attaching disk"
    try:
        vm.nics.add(nic_net1)
    except:
        print "Error adding nic"


# create an instance from a template
def create_vm_template(conn, vmname, image, zone):
    vmparams = params.VM(name=vmname, cluster=conn.clusters.get(name=zone), template=conn.templates.get(name=image),disks=params.Disks(clone=True))
    try:
        conn.vms.add(vmparams)
    except:
        print 'error adding template %s' % image
        sys.exit(1)


# start instance
def vm_start(conn, vmname):
    vm = conn.vms.get(name=vmname)
    vm.start()

# Stop instance
def vm_stop(conn, vmname):
    vm = conn.vms.get(name=vmname)
    vm.stop()

# restart instance
def vm_restart(conn, vmname):
    state = vm_status(conn, vmname)
    vm = conn.vms.get(name=vmname)
    vm.stop()
    while conn.vms.get(vmname).get_status().get_state() != 'down':
        time.sleep(5)
    vm.start()

# remove an instance
def vm_remove(conn, vmname):
    vm = conn.vms.get(name=vmname)
    vm.delete()

# ------------------------------------------------------------------- #
# VM statuses
#
# Get the VMs status
def vm_status(conn, vmname):
    status = conn.vms.get(name=vmname).status.state
    print "vm status is : %s" % status
    return status


# Get VM object and return it's name if object exists
def get_vm(conn, vmname):
    vm = conn.vms.get(name=vmname)
    if vm == None:
        name = "empty"
        print "vmname: %s" % name
    else:
        name = vm.get_name()
        print "vmname: %s" % name
    return name

# ------------------------------------------------------------------- #
# Hypervisor operations
#
# not available yet
# ------------------------------------------------------------------- #
# Main

def main():

    module = AnsibleModule(
        argument_spec = dict(
            state = dict(default='present', choices=['present', 'absent', 'shutdown', 'started', 'restart']),
            #name      = dict(required=True),
            user = dict(required=True),
            url = dict(required=True),
            instance_name = dict(required=True, aliases=['vmname']),
            password = dict(required=True),
            image = dict(),
            resource_type = dict(choices=['new', 'template']),
            zone = dict(),
            instance_disksize = dict(aliases=['vm_disksize']),
            instance_cpus = dict(default=1, aliases=['vmcpus']),
            instance_nic = dict(aliases=['vmnic']),
            instance_network = dict(default='rhevm', aliases=['vmnetwork']),
            instance_mem = dict(aliases=['vmmem']),
            instance_type = dict(default='server', aliases=['vmtype'], choices=['server', 'desktop']),
            disk_alloc = dict(default='thin', choices=['thin', 'preallocated']),
            disk_int = dict(default='virtio', choices=['virtio', 'ide']),
            instance_os = dict(aliases=['vmos']),
            instance_cores = dict(default=1, aliases=['vmcores']),
            sdomain = dict(),
            region = dict(),
        )
    )

    state         = module.params['state']
    user          = module.params['user']
    url           = module.params['url']
    vmname        = module.params['instance_name']
    password      = module.params['password']
    image         = module.params['image']              # name of the image to deploy
    resource_type = module.params['resource_type']      # template or from scratch
    zone          = module.params['zone']               # oVirt cluster
    vmdisk_size   = module.params['instance_disksize']  # disksize
    vmcpus        = module.params['instance_cpus']      # number of cpu
    vmnic         = module.params['instance_nic']       # network interface
    vmnetwork     = module.params['instance_network']   # logical network
    vmmem         = module.params['instance_mem']       # mem size 
    vmdisk_alloc  = module.params['disk_alloc']         # thin, preallocated
    vmdisk_int    = module.params['disk_int']           # disk interface virtio or ide
    vmos          = module.params['instance_os']        # Operating System
    vmtype        = module.params['instance_type']      # server or desktop
    vmcores       = module.params['instance_cores']     # number of cores
    sdomain       = module.params['sdomain']            # storage domain to store disk on
    region        = module.params['region']             # oVirt Datacenter
    #initialize connection
    c = conn(url+"/api", user, password)

    if state == 'present':
        if get_vm(c, vmname) == "empty":
            if resource_type == 'template':
                create_vm_template(c, vmname, image, zone)
                module.exit_json(changed=True, msg="deployed VM %s from template %s"  % (vmname,image))
            elif resource_type == 'new':
                # FIXME: refactor, use keyword args.
                create_vm(c, vmtype, vmname, zone, vmdisk_size, vmcpus, vmnic, vmnetwork, vmmem, vmdisk_alloc, sdomain, vmcores, vmos, vmdisk_int)
                module.exit_json(changed=True, msg="deployed VM %s from scratch"  % vmname)
            else:
                module.exit_json(changed=False, msg="You did not specify a resource type")
        else:
            module.exit_json(changed=False, msg="VM %s already exists" % vmname)

    if state == 'started':
        if vm_status(c, vmname) == 'up':
            module.exit_json(changed=False, msg="VM %s is already running" % vmname)
        else:
            vm_start(c, vmname)
            module.exit_json(changed=True, msg="VM %s started" % vmname)

    if state == 'shutdown':
        if vm_status(c, vmname) == 'down':
            module.exit_json(changed=False, msg="VM %s is already shutdown" % vmname)
        else:
            vm_stop(c, vmname)
            module.exit_json(changed=True, msg="VM %s is shutting down" % vmname)
    
    if state == 'restart':
        if vm_status(c, vmname) == 'up':
            vm_restart(c, vmname)
            module.exit_json(changed=True, msg="VM %s is restarted" % vmname)
        else:
            module.exit_json(changed=False, msg="VM %s is not running" % vmname)

    if state == 'absent':
        if get_vm(c, vmname) == "empty":
            module.exit_json(changed=False, msg="VM %s does not exist" % vmname)
        else:
            vm_remove(c, vmname)
            module.exit_json(changed=True, msg="VM %s removed" % vmname)




# import module snippets
from ansible.module_utils.basic import *
main()
