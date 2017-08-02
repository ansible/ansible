#!/usr/bin/python

# (c) 2013, Vincent Van der Kussen <vincent at vanderkussen.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovirt
author: "Vincent Van der Kussen (@vincentvdk)"
short_description: oVirt/RHEV platform management
description:
    - This module only supports oVirt/RHEV version 3. A newer module M(ovirt_vms) supports oVirt/RHV version 4.
    - Allows you to create new instances, either from scratch or an image, in addition to deleting or stopping instances on the oVirt/RHEV platform.
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
  instance_dns:
    description:
     - define the instance's Primary DNS server
    required: false
    aliases: [ dns ]
    version_added: "2.1"
  instance_domain:
    description:
     - define the instance's Domain
    required: false
    aliases: [ domain ]
    version_added: "2.1"
  instance_hostname:
    description:
     - define the instance's Hostname
    required: false
    aliases: [ hostname ]
    version_added: "2.1"
  instance_ip:
    description:
     - define the instance's IP
    required: false
    aliases: [ ip ]
    version_added: "2.1"
  instance_netmask:
    description:
     - define the instance's Netmask
    required: false
    aliases: [ netmask ]
    version_added: "2.1"
  instance_rootpw:
    description:
     - define the instance's Root password
    required: false
    aliases: [ rootpw ]
    version_added: "2.1"
  instance_key:
    description:
     - define the instance's Authorized key
    required: false
    aliases: [ key ]
    version_added: "2.1"
  state:
    description:
     - create, terminate or remove instances
    default: 'present'
    required: false
    aliases: []
    choices: ['present', 'absent', 'shutdown', 'started', 'restarted']

requirements:
  - "python >= 2.6"
  - "ovirt-engine-sdk-python"
'''
EXAMPLES = '''
# Basic example provisioning from image.

ovirt:
    user: admin@internal
    url: https://ovirt.example.com
    instance_name: ansiblevm04
    password: secret
    image: centos_64
    zone: cluster01
    resource_type: template"

# Full example to create new instance from scratch
ovirt:
    instance_name: testansible
    resource_type: new
    instance_type: server
    user: admin@internal
    password: secret
    url: https://ovirt.example.com
    instance_disksize: 10
    zone: cluster01
    region: datacenter1
    instance_cpus: 1
    instance_nic: nic1
    instance_network: rhevm
    instance_mem: 1000
    disk_alloc: thin
    sdomain: FIBER01
    instance_cores: 1
    instance_os: rhel_6x64
    disk_int: virtio"

# stopping an instance
ovirt:
    instance_name: testansible
    state: stopped
    user: admin@internal
    password: secret
    url: https://ovirt.example.com

# starting an instance
ovirt:
    instance_name: testansible
    state: started
    user: admin@internal
    password: secret
    url: https://ovirt.example.com

# starting an instance with cloud init information
ovirt:
    instance_name: testansible
    state: started
    user: admin@internal
    password: secret
    url: https://ovirt.example.com
    hostname: testansible
    domain: ansible.local
    ip: 192.0.2.100
    netmask: 255.255.255.0
    gateway: 192.0.2.1
    rootpw: bigsecret

'''
import time

try:
    from ovirtsdk.api import API
    from ovirtsdk.xml import params
    HAS_OVIRTSDK = True
except ImportError:
    HAS_OVIRTSDK = False

from ansible.module_utils.basic import AnsibleModule


# ------------------------------------------------------------------- #
# create connection with API
#
def conn(url, user, password):
    api = API(url=url, username=user, password=password, insecure=True)
    try:
        value = api.test()
    except:
        raise Exception("error connecting to the oVirt API")
    return api

# ------------------------------------------------------------------- #
# Create VM from scratch
def create_vm(conn, vmtype, vmname, zone, vmdisk_size, vmcpus, vmnic, vmnetwork, vmmem, vmdisk_alloc, sdomain, vmcores, vmos, vmdisk_int):
    if vmdisk_alloc == 'thin':
        # define VM params
        vmparams = params.VM(name=vmname, cluster=conn.clusters.get(name=zone), os=params.OperatingSystem(type_=vmos),
                             template=conn.templates.get(name="Blank"), memory=1024 * 1024 * int(vmmem),
                             cpu=params.CPU(topology=params.CpuTopology(cores=int(vmcores))), type_=vmtype)
        # define disk params
        vmdisk= params.Disk(size=1024 * 1024 * 1024 * int(vmdisk_size), wipe_after_delete=True, sparse=True, interface=vmdisk_int, type_="System", format='cow',
        storage_domains=params.StorageDomains(storage_domain=[conn.storagedomains.get(name=sdomain)]))
        # define network parameters
        network_net = params.Network(name=vmnetwork)
        nic_net1 = params.NIC(name='nic1', network=network_net, interface='virtio')
    elif vmdisk_alloc == 'preallocated':
        # define VM params
        vmparams = params.VM(name=vmname, cluster=conn.clusters.get(name=zone), os=params.OperatingSystem(type_=vmos),
                             template=conn.templates.get(name="Blank"), memory=1024 * 1024 * int(vmmem),
                             cpu=params.CPU(topology=params.CpuTopology(cores=int(vmcores))) ,type_=vmtype)
        # define disk params
        vmdisk= params.Disk(size=1024 * 1024 * 1024 * int(vmdisk_size), wipe_after_delete=True, sparse=False, interface=vmdisk_int, type_="System",
                            format='raw', storage_domains=params.StorageDomains(storage_domain=[conn.storagedomains.get(name=sdomain)]))
        # define network parameters
        network_net = params.Network(name=vmnetwork)
        nic_net1 = params.NIC(name=vmnic, network=network_net, interface='virtio')

    try:
        conn.vms.add(vmparams)
    except:
        raise Exception("Error creating VM with specified parameters")
    vm = conn.vms.get(name=vmname)
    try:
        vm.disks.add(vmdisk)
    except:
        raise Exception("Error attaching disk")
    try:
        vm.nics.add(nic_net1)
    except:
        raise Exception("Error adding nic")


# create an instance from a template
def create_vm_template(conn, vmname, image, zone):
    vmparams = params.VM(name=vmname, cluster=conn.clusters.get(name=zone), template=conn.templates.get(name=image),disks=params.Disks(clone=True))
    try:
        conn.vms.add(vmparams)
    except:
        raise Exception('error adding template %s' % image)


# start instance
def vm_start(conn, vmname, hostname=None, ip=None, netmask=None, gateway=None,
             domain=None, dns=None, rootpw=None, key=None):
    vm = conn.vms.get(name=vmname)
    use_cloud_init = False
    nics = None
    nic = None
    if hostname or ip or netmask or gateway or domain or dns or rootpw or key:
        use_cloud_init = True
    if ip and netmask and gateway:
        ipinfo = params.IP(address=ip, netmask=netmask, gateway=gateway)
        nic = params.GuestNicConfiguration(name='eth0', boot_protocol='STATIC', ip=ipinfo, on_boot=True)
        nics = params.Nics()
    nics = params.GuestNicsConfiguration(nic_configuration=[nic])
    initialization=params.Initialization(regenerate_ssh_keys=True, host_name=hostname, domain=domain, user_name='root',
                                         root_password=rootpw, nic_configurations=nics, dns_servers=dns,
                                         authorized_ssh_keys=key)
    action = params.Action(use_cloud_init=use_cloud_init, vm=params.VM(initialization=initialization))
    vm.start(action=action)

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
    return status


# Get VM object and return it's name if object exists
def get_vm(conn, vmname):
    vm = conn.vms.get(name=vmname)
    if vm is None:
        name = "empty"
    else:
        name = vm.get_name()
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
            password = dict(required=True, no_log=True),
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
            instance_hostname = dict(aliases=['hostname']),
            instance_ip = dict(aliases=['ip']),
            instance_netmask = dict(aliases=['netmask']),
            instance_gateway = dict(aliases=['gateway']),
            instance_domain = dict(aliases=['domain']),
            instance_dns = dict(aliases=['dns']),
            instance_rootpw = dict(aliases=['rootpw']),
            instance_key = dict(aliases=['key']),
            sdomain = dict(),
            region = dict(),
        )
    )

    if not HAS_OVIRTSDK:
        module.fail_json(msg='ovirtsdk required for this module')

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
    hostname      = module.params['instance_hostname']
    ip            = module.params['instance_ip']
    netmask       = module.params['instance_netmask']
    gateway       = module.params['instance_gateway']
    domain        = module.params['instance_domain']
    dns           = module.params['instance_dns']
    rootpw        = module.params['instance_rootpw']
    key            = module.params['instance_key']
    #initialize connection
    try:
        c = conn(url+"/api", user, password)
    except Exception as e:
        module.fail_json(msg='%s' % e)

    if state == 'present':
        if get_vm(c, vmname) == "empty":
            if resource_type == 'template':
                try:
                    create_vm_template(c, vmname, image, zone)
                except Exception as e:
                    module.fail_json(msg='%s' % e)
                module.exit_json(changed=True, msg="deployed VM %s from template %s"  % (vmname,image))
            elif resource_type == 'new':
                # FIXME: refactor, use keyword args.
                try:
                    create_vm(c, vmtype, vmname, zone, vmdisk_size, vmcpus, vmnic, vmnetwork, vmmem, vmdisk_alloc, sdomain, vmcores, vmos, vmdisk_int)
                except Exception as e:
                    module.fail_json(msg='%s' % e)
                module.exit_json(changed=True, msg="deployed VM %s from scratch"  % vmname)
            else:
                module.exit_json(changed=False, msg="You did not specify a resource type")
        else:
            module.exit_json(changed=False, msg="VM %s already exists" % vmname)

    if state == 'started':
        if vm_status(c, vmname) == 'up':
            module.exit_json(changed=False, msg="VM %s is already running" % vmname)
        else:
            #vm_start(c, vmname)
            vm_start(c, vmname, hostname, ip, netmask, gateway, domain, dns, rootpw, key)
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


if __name__ == '__main__':
    main()
