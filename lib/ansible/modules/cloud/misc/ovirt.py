#!/usr/bin/python

# (c) 2013, Vincent Van der Kussen <vincent at vanderkussen.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
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
from ansible.module_utils._text import to_native


class OvirtVM(object):
    def __init__(self, module):
        self.conn = None
        self.module = module
        self.url = module.params['url']
        self.user = module.params['user']
        self.password = module.params['password']
        self.vmname = module.params['instance_name']
        self.image = module.params['image']  # name of the image to deploy
        self.resource_type = module.params['resource_type']  # template or from scratch
        self.zone = module.params['zone']  # oVirt cluster
        self.vmdisk_size = module.params['instance_disksize']  # disksize
        self.vmcpus = module.params['instance_cpus']  # number of cpu
        self.vmnic = module.params['instance_nic']  # network interface
        self.vmnetwork = module.params['instance_network']  # logical network
        self.vmmem = module.params['instance_mem']  # mem size
        self.vmdisk_alloc = module.params['disk_alloc']  # thin, preallocated
        self.vmdisk_int = module.params['disk_int']  # disk interface virtio or ide
        self.vmos = module.params['instance_os']  # Operating System
        self.vmtype = module.params['instance_type']  # server or desktop
        self.vmcores = module.params['instance_cores']  # number of cores
        self.sdomain = module.params['sdomain']  # storage domain to store disk on
        self.region = module.params['region']  # oVirt Datacenter
        self.hostname = module.params['instance_hostname']
        self.ip = module.params['instance_ip']
        self.netmask = module.params['instance_netmask']
        self.gateway = module.params['instance_gateway']
        self.domain = module.params['instance_domain']
        self.dns = module.params['instance_dns']
        self.rootpw = module.params['instance_rootpw']
        self.key = module.params['instance_key']

    def connect(self):
        api = API(url=self.url + '/api', username=self.user, password=self.password, insecure=True)
        try:
            api.test()
        except Exception as exc:
            self.module.fail_json("error connecting to the oVirt API: %s" % to_native(exc))
        self.conn = api

    def get_vm(self, vm_name):
        """ Get VM Object and return it's name if object exists"""
        vm = self.conn.vms.get(name=vm_name)
        if vm is None:
            name = "empty"
        else:
            name = vm.get_name()
        return name

    def create_vm_template(self, vm_name):
        """ Create an instance from a template"""
        vm_params = params.VM(name=vm_name,
                              cluster=self.conn.clusters.get(name=self.zone),
                              template=self.conn.templates.get(name=self.image),
                              disks=params.Disks(clone=True))
        try:
            self.conn.vms.add(vm_params)
        except:
            raise Exception('Error adding template {0}'.format(self.image))

    def create_vm(self, vm_name):
        """Create a VM from scratch"""
        if self.vmdisk_alloc == 'thin':
            disk_type = "cow"
        elif self.vmdisk_alloc == 'preallocated':
            disk_type = "raw"

        vmparams = params.VM(name=vm_name,
                             cluster=self.conn.clusters.get(name=self.zone),
                             os=params.OperatingSystem(type_=self.vmos),
                             template=self.conn.templates.get(name="Blank"),
                             memory=1024 * 1024 * int(self.vmmem),
                             cpu=params.CPU(topology=params.CpuTopology(cores=int(self.vmcores))),
                             type_=self.vmtype)

        vmdisk = params.Disk(size=1024 * 1024 * 1024 * int(self.vmdisk_size),
                             wipe_after_delete=True,
                             sparse=False,
                             interface=self.vmdisk_int,
                             type_="System",
                             format=disk_type,
                             storage_domains=params.StorageDomains(storage_domain=[self.conn.storagedomains.get(name=self.sdomain)]))
        # define network parameters
        network_net = params.Network(name=self.vmnetwork)
        nic_net1 = params.NIC(name=self.vmnic, network=network_net, interface='virtio')

        try:
            self.conn.vms.add(vmparams)
        except:
            raise Exception("Error creating VM with specified parameters")
        vm = self.conn.vms.get(name=vm_name)
        try:
            vm.disks.add(vmdisk)
        except:
            raise Exception("Error attaching disk")
        try:
            vm.nics.add(nic_net1)
        except:
            raise Exception("Error adding nic")

    def vm_stop(self, vm_name):
        """ Stop an instance"""
        vm = self.conn.vms.get(name=vm_name)
        vm.stop()

    def vm_restart(self, vm_name):
        """Restart an instance"""
        state = self.vm_status(vm_name)
        vm = self.conn.vms.get(name=vm_name)
        vm.stop()
        while vm.get_status().get_state() != 'down':
            time.sleep(5)
        vm.start()

    def vm_remove(self, vm_name):
        """Remove an instance"""
        vm = self.conn.vms.get(name=vm_name)
        vm.delete()

    def vm_status(self, vm_name):
        """ Get the VMs status"""
        status = self.conn.vms.get(name=vm_name).status.state
        return status

    def vm_start(self, vm_name):
        """ Start given instance"""
        vm = self.conn.vms.get(name=vm_name)
        use_cloud_init = False
        nics = None
        nic = None
        if self.hostname or self.ip or self.netmask or self.gateway or self.domain or self.dns or self.rootpw or self.key:
            use_cloud_init = True
        if self.ip and self.netmask and self.gateway:
            ipinfo = params.IP(address=self.ip, netmask=self.netmask, gateway=self.gateway)
            nic = params.GuestNicConfiguration(name='eth0', boot_protocol='STATIC', ip=ipinfo, on_boot=True)
            nics = params.Nics()
        nics = params.GuestNicsConfiguration(nic_configuration=[nic])
        initialization = params.Initialization(regenerate_ssh_keys=True,
                                               host_name=self.hostname,
                                               domain=self.domain, user_name='root',
                                               root_password=self.rootpw,
                                               nic_configurations=nics,
                                               dns_servers=self.dns,
                                               authorized_ssh_keys=self.key)
        action = params.Action(use_cloud_init=use_cloud_init, vm=params.VM(initialization=initialization))
        vm.start(action=action)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent', 'shutdown', 'started', 'restart']),
            # name=dict(required=True),
            user=dict(required=True),
            url=dict(required=True),
            instance_name=dict(required=True, aliases=['vmname']),
            password=dict(required=True, no_log=True),
            image=dict(),
            resource_type=dict(choices=['new', 'template']),
            zone=dict(),
            instance_disksize=dict(aliases=['vm_disksize']),
            instance_cpus=dict(default=1, aliases=['vmcpus']),
            instance_nic=dict(aliases=['vmnic']),
            instance_network=dict(default='rhevm', aliases=['vmnetwork']),
            instance_mem=dict(aliases=['vmmem']),
            instance_type=dict(default='server', aliases=['vmtype'], choices=['server', 'desktop']),
            disk_alloc=dict(default='thin', choices=['thin', 'preallocated']),
            disk_int=dict(default='virtio', choices=['virtio', 'ide']),
            instance_os=dict(aliases=['vmos']),
            instance_cores=dict(default=1, aliases=['vmcores']),
            instance_hostname=dict(aliases=['hostname']),
            instance_ip=dict(aliases=['ip']),
            instance_netmask=dict(aliases=['netmask']),
            instance_gateway=dict(aliases=['gateway']),
            instance_domain=dict(aliases=['domain']),
            instance_dns=dict(aliases=['dns']),
            instance_rootpw=dict(aliases=['rootpw'], no_log=True),
            instance_key=dict(aliases=['key']),
            sdomain=dict(),
            region=dict(),
        )
    )

    if not HAS_OVIRTSDK:
        module.fail_json(msg='ovirtsdk required for this module')

    state = module.params['state']
    vm_name = module.params['instance_name']
    resource_type = module.params['resource_type']
    ovirt = OvirtVM(module)

    # Initialize connection
    ovirt.connect()

    if state == 'present':
        if ovirt.get_vm(vm_name) == "empty":
            if resource_type == 'template':
                try:
                    ovirt.create_vm_template(vm_name)
                except Exception as exc:
                    module.fail_json(msg=exc)
                module.exit_json(changed=True, msg="deployed VM %s from template %s" % (vm_name, ovirt.image))
            elif resource_type == 'new':
                try:
                    ovirt.create_vm(vm_name)
                except Exception as e:
                    module.fail_json(msg='%s' % e)
                module.exit_json(changed=True, msg="deployed VM %s from scratch" % vm_name)
            else:
                module.exit_json(changed=False, msg="You did not specify a resource type")
        else:
            module.exit_json(changed=False, msg="VM %s already exists" % vm_name)

    if state == 'started':
        if ovirt.vm_status(vm_name) == 'up':
            module.exit_json(changed=False, msg="VM %s is already running" % vm_name)
        else:
            ovirt.vm_start(vm_name)
            module.exit_json(changed=True, msg="VM %s started" % vm_name)

    if state == 'shutdown':
        if ovirt.vm_status(vm_name) == 'down':
            module.exit_json(changed=False, msg="VM %s is already shutdown" % vm_name)
        else:
            ovirt.vm_stop(vm_name)
            module.exit_json(changed=True, msg="VM %s is shutting down" % vm_name)

    if state == 'restart':
        if ovirt.vm_status(vm_name) == 'up':
            ovirt.vm_restart(vm_name)
            module.exit_json(changed=True, msg="VM %s is restarted" % vm_name)
        else:
            module.exit_json(changed=False, msg="VM %s is not running" % vm_name)

    if state == 'absent':
        if ovirt.get_vm(vm_name) == "empty":
            module.exit_json(changed=False, msg="VM %s does not exist" % vm_name)
        else:
            ovirt.vm_remove(vm_name)
            module.exit_json(changed=True, msg="VM %s removed" % vm_name)

if __name__ == '__main__':
    main()
