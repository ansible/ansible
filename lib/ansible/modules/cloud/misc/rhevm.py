#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Timothy Vandenbrande <timothy.vandenbrande@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: rhevm
short_description: RHEV/oVirt automation
description:
    - This module only supports oVirt/RHEV version 3.
    - A newer module M(ovirt_vm) supports oVirt/RHV version 4.
    - Allows you to create/remove/update or powermanage virtual machines on a RHEV/oVirt platform.
version_added: "2.2"
requirements:
    - ovirtsdk
author:
- Timothy Vandenbrande (@TimothyVandenbrande)
options:
    user:
        description:
            - The user to authenticate with.
        type: str
        default: admin@internal
    password:
        description:
            - The password for user authentication.
        type: str
    server:
        description:
            - The name/IP of your RHEV-m/oVirt instance.
        type: str
        default: 127.0.0.1
    port:
        description:
            - The port on which the API is reachable.
        type: int
        default: 443
    insecure_api:
        description:
            - A boolean switch to make a secure or insecure connection to the server.
        type: bool
        default: no
    name:
        description:
            - The name of the VM.
        type: str
    cluster:
        description:
            - The RHEV/oVirt cluster in which you want you VM to start.
        type: str
    datacenter:
        description:
            - The RHEV/oVirt datacenter in which you want you VM to start.
        type: str
        default: Default
    state:
        description:
            - This serves to create/remove/update or powermanage your VM.
        type: str
        choices: [ absent, cd, down, info, ping, present, restarted, up ]
        default: present
    image:
        description:
            - The template to use for the VM.
        type: str
    type:
        description:
            - To define if the VM is a server or desktop.
        type: str
        choices: [ desktop, host, server ]
        default: server
    vmhost:
        description:
            - The host you wish your VM to run on.
        type: str
    vmcpu:
        description:
            - The number of CPUs you want in your VM.
        type: int
        default: 2
    cpu_share:
        description:
            - This parameter is used to configure the CPU share.
        type: int
        default: 0
    vmmem:
        description:
            - The amount of memory you want your VM to use (in GB).
        type: int
        default: 1
    osver:
        description:
            - The operating system option in RHEV/oVirt.
        type: str
        default: rhel_6x64
    mempol:
        description:
            - The minimum amount of memory you wish to reserve for this system.
        type: int
        default: 1
    vm_ha:
        description:
            - To make your VM High Available.
        type: bool
        default: yes
    disks:
        description:
            - This option uses complex arguments and is a list of disks with the options name, size and domain.
        type: list
    ifaces:
        description:
            - This option uses complex arguments and is a list of interfaces with the options name and vlan.
        type: list
        aliases: [ interfaces, nics ]
    boot_order:
        description:
            - This option uses complex arguments and is a list of items that specify the bootorder.
        type: list
        default: [ hd, network ]
    del_prot:
        description:
            - This option sets the delete protection checkbox.
        type: bool
        default: yes
    cd_drive:
        description:
            - The CD you wish to have mounted on the VM when I(state = 'CD').
        type: str
    timeout:
        description:
            - The timeout you wish to define for power actions.
            - When I(state = 'up').
            - When I(state = 'down').
            - When I(state = 'restarted').
        type: int
'''

RETURN = r'''
vm:
    description: Returns all of the VMs variables and execution.
    returned: always
    type: dict
    sample: '{
        "boot_order": [
            "hd",
            "network"
        ],
        "changed": true,
        "changes": [
            "Delete Protection"
        ],
        "cluster": "C1",
        "cpu_share": "0",
        "created": false,
        "datacenter": "Default",
        "del_prot": true,
        "disks": [
            {
                "domain": "ssd-san",
                "name": "OS",
                "size": 40
            }
        ],
        "eth0": "00:00:5E:00:53:00",
        "eth1": "00:00:5E:00:53:01",
        "eth2": "00:00:5E:00:53:02",
        "exists": true,
        "failed": false,
        "ifaces": [
            {
                "name": "eth0",
                "vlan": "Management"
            },
            {
                "name": "eth1",
                "vlan": "Internal"
            },
            {
                "name": "eth2",
                "vlan": "External"
            }
        ],
        "image": false,
        "mempol": "0",
        "msg": [
            "VM exists",
            "cpu_share was already set to 0",
            "VM high availability was already set to True",
            "The boot order has already been set",
            "VM delete protection has been set to True",
            "Disk web2_Disk0_OS already exists",
            "The VM starting host was already set to host416"
        ],
        "name": "web2",
        "type": "server",
        "uuid": "4ba5a1be-e60b-4368-9533-920f156c817b",
        "vm_ha": true,
        "vmcpu": "4",
        "vmhost": "host416",
        "vmmem": "16"
    }'
'''

EXAMPLES = r'''
- name: Basic get info from VM
  rhevm:
    server: rhevm01
    user: '{{ rhev.admin.name }}'
    password: '{{ rhev.admin.pass }}'
    name: demo
    state: info

- name: Basic create example from image
  rhevm:
    server: rhevm01
    user: '{{ rhev.admin.name }}'
    password: '{{ rhev.admin.pass }}'
    name: demo
    cluster: centos
    image: centos7_x64
    state: present

- name: Power management
  rhevm:
    server: rhevm01
    user: '{{ rhev.admin.name }}'
    password: '{{ rhev.admin.pass }}'
    cluster: RH
    name: uptime_server
    image: centos7_x64
    state: down

- name: Multi disk, multi nic create example
  rhevm:
    server: rhevm01
    user: '{{ rhev.admin.name }}'
    password: '{{ rhev.admin.pass }}'
    cluster: RH
    name: server007
    type: server
    vmcpu: 4
    vmmem: 2
    ifaces:
    - name: eth0
      vlan: vlan2202
    - name: eth1
      vlan: vlan36
    - name: eth2
      vlan: vlan38
    - name: eth3
      vlan: vlan2202
    disks:
    - name: root
      size: 10
      domain: ssd-san
    - name: swap
      size: 10
      domain: 15kiscsi-san
    - name: opt
      size: 10
      domain: 15kiscsi-san
    - name: var
      size: 10
      domain: 10kiscsi-san
    - name: home
      size: 10
      domain: sata-san
    boot_order:
    - network
    - hd
    state: present

- name: Add a CD to the disk cd_drive
  rhevm:
    user: '{{ rhev.admin.name }}'
    password: '{{ rhev.admin.pass }}'
    name: server007
    cd_drive: rhev-tools-setup.iso
    state: cd

- name: New host deployment + host network configuration
  rhevm:
    password: '{{ rhevm.admin.pass }}'
    name: ovirt_node007
    type: host
    cluster: rhevm01
    ifaces:
    - name: em1
    - name: em2
    - name: p3p1
      ip: 172.31.224.200
      netmask: 255.255.254.0
    - name: p3p2
      ip: 172.31.225.200
      netmask: 255.255.254.0
    - name: bond0
      bond:
      - em1
      - em2
      network: rhevm
      ip: 172.31.222.200
      netmask: 255.255.255.0
      management: yes
    - name: bond0.36
      network: vlan36
      ip: 10.2.36.200
      netmask: 255.255.254.0
      gateway: 10.2.36.254
    - name: bond0.2202
      network: vlan2202
    - name: bond0.38
      network: vlan38
    state: present
'''

import time

try:
    from ovirtsdk.api import API
    from ovirtsdk.xml import params
    HAS_SDK = True
except ImportError:
    HAS_SDK = False

from ansible.module_utils.basic import AnsibleModule


RHEV_FAILED = 1
RHEV_SUCCESS = 0
RHEV_UNAVAILABLE = 2

RHEV_TYPE_OPTS = ['desktop', 'host', 'server']
STATE_OPTS = ['absent', 'cd', 'down', 'info', 'ping', 'present', 'restart', 'up']

msg = []
changed = False
failed = False


class RHEVConn(object):
    'Connection to RHEV-M'

    def __init__(self, module):
        self.module = module

        user = module.params.get('user')
        password = module.params.get('password')
        server = module.params.get('server')
        port = module.params.get('port')
        insecure_api = module.params.get('insecure_api')

        url = "https://%s:%s" % (server, port)

        try:
            api = API(url=url, username=user, password=password, insecure=str(insecure_api))
            api.test()
            self.conn = api
        except Exception:
            raise Exception("Failed to connect to RHEV-M.")

    def __del__(self):
        self.conn.disconnect()

    def createVMimage(self, name, cluster, template):
        try:
            vmparams = params.VM(
                name=name,
                cluster=self.conn.clusters.get(name=cluster),
                template=self.conn.templates.get(name=template),
                disks=params.Disks(clone=True)
            )
            self.conn.vms.add(vmparams)
            setMsg("VM is created")
            setChanged()
            return True
        except Exception as e:
            setMsg("Failed to create VM")
            setMsg(str(e))
            setFailed()
            return False

    def createVM(self, name, cluster, os, actiontype):
        try:
            vmparams = params.VM(
                name=name,
                cluster=self.conn.clusters.get(name=cluster),
                os=params.OperatingSystem(type_=os),
                template=self.conn.templates.get(name="Blank"),
                type_=actiontype
            )
            self.conn.vms.add(vmparams)
            setMsg("VM is created")
            setChanged()
            return True
        except Exception as e:
            setMsg("Failed to create VM")
            setMsg(str(e))
            setFailed()
            return False

    def createDisk(self, vmname, diskname, disksize, diskdomain, diskinterface, diskformat, diskallocationtype, diskboot):
        VM = self.get_VM(vmname)

        newdisk = params.Disk(
            name=diskname,
            size=1024 * 1024 * 1024 * int(disksize),
            wipe_after_delete=True,
            sparse=diskallocationtype,
            interface=diskinterface,
            format=diskformat,
            bootable=diskboot,
            storage_domains=params.StorageDomains(
                storage_domain=[self.get_domain(diskdomain)]
            )
        )

        try:
            VM.disks.add(newdisk)
            VM.update()
            setMsg("Successfully added disk " + diskname)
            setChanged()
        except Exception as e:
            setFailed()
            setMsg("Error attaching " + diskname + "disk, please recheck and remove any leftover configuration.")
            setMsg(str(e))
            return False

        try:
            currentdisk = VM.disks.get(name=diskname)
            attempt = 1
            while currentdisk.status.state != 'ok':
                currentdisk = VM.disks.get(name=diskname)
                if attempt == 100:
                    setMsg("Error, disk %s, state %s" % (diskname, str(currentdisk.status.state)))
                    raise Exception()
                else:
                    attempt += 1
                    time.sleep(2)
            setMsg("The disk  " + diskname + " is ready.")
        except Exception as e:
            setFailed()
            setMsg("Error getting the state of " + diskname + ".")
            setMsg(str(e))
            return False
        return True

    def createNIC(self, vmname, nicname, vlan, interface):
        VM = self.get_VM(vmname)
        CLUSTER = self.get_cluster_byid(VM.cluster.id)
        DC = self.get_DC_byid(CLUSTER.data_center.id)
        newnic = params.NIC(
            name=nicname,
            network=DC.networks.get(name=vlan),
            interface=interface
        )

        try:
            VM.nics.add(newnic)
            VM.update()
            setMsg("Successfully added iface " + nicname)
            setChanged()
        except Exception as e:
            setFailed()
            setMsg("Error attaching " + nicname + " iface, please recheck and remove any leftover configuration.")
            setMsg(str(e))
            return False

        try:
            currentnic = VM.nics.get(name=nicname)
            attempt = 1
            while currentnic.active is not True:
                currentnic = VM.nics.get(name=nicname)
                if attempt == 100:
                    setMsg("Error, iface %s, state %s" % (nicname, str(currentnic.active)))
                    raise Exception()
                else:
                    attempt += 1
                    time.sleep(2)
            setMsg("The iface  " + nicname + " is ready.")
        except Exception as e:
            setFailed()
            setMsg("Error getting the state of " + nicname + ".")
            setMsg(str(e))
            return False
        return True

    def get_DC(self, dc_name):
        return self.conn.datacenters.get(name=dc_name)

    def get_DC_byid(self, dc_id):
        return self.conn.datacenters.get(id=dc_id)

    def get_VM(self, vm_name):
        return self.conn.vms.get(name=vm_name)

    def get_cluster_byid(self, cluster_id):
        return self.conn.clusters.get(id=cluster_id)

    def get_cluster(self, cluster_name):
        return self.conn.clusters.get(name=cluster_name)

    def get_domain_byid(self, dom_id):
        return self.conn.storagedomains.get(id=dom_id)

    def get_domain(self, domain_name):
        return self.conn.storagedomains.get(name=domain_name)

    def get_disk(self, disk):
        return self.conn.disks.get(disk)

    def get_network(self, dc_name, network_name):
        return self.get_DC(dc_name).networks.get(network_name)

    def get_network_byid(self, network_id):
        return self.conn.networks.get(id=network_id)

    def get_NIC(self, vm_name, nic_name):
        return self.get_VM(vm_name).nics.get(nic_name)

    def get_Host(self, host_name):
        return self.conn.hosts.get(name=host_name)

    def get_Host_byid(self, host_id):
        return self.conn.hosts.get(id=host_id)

    def set_Memory(self, name, memory):
        VM = self.get_VM(name)
        VM.memory = int(int(memory) * 1024 * 1024 * 1024)
        try:
            VM.update()
            setMsg("The Memory has been updated.")
            setChanged()
            return True
        except Exception as e:
            setMsg("Failed to update memory.")
            setMsg(str(e))
            setFailed()
            return False

    def set_Memory_Policy(self, name, memory_policy):
        VM = self.get_VM(name)
        VM.memory_policy.guaranteed = int(int(memory_policy) * 1024 * 1024 * 1024)
        try:
            VM.update()
            setMsg("The memory policy has been updated.")
            setChanged()
            return True
        except Exception as e:
            setMsg("Failed to update memory policy.")
            setMsg(str(e))
            setFailed()
            return False

    def set_CPU(self, name, cpu):
        VM = self.get_VM(name)
        VM.cpu.topology.cores = int(cpu)
        try:
            VM.update()
            setMsg("The number of CPUs has been updated.")
            setChanged()
            return True
        except Exception as e:
            setMsg("Failed to update the number of CPUs.")
            setMsg(str(e))
            setFailed()
            return False

    def set_CPU_share(self, name, cpu_share):
        VM = self.get_VM(name)
        VM.cpu_shares = int(cpu_share)
        try:
            VM.update()
            setMsg("The CPU share has been updated.")
            setChanged()
            return True
        except Exception as e:
            setMsg("Failed to update the CPU share.")
            setMsg(str(e))
            setFailed()
            return False

    def set_Disk(self, diskname, disksize, diskinterface, diskboot):
        DISK = self.get_disk(diskname)
        setMsg("Checking disk " + diskname)
        if DISK.get_bootable() != diskboot:
            try:
                DISK.set_bootable(diskboot)
                setMsg("Updated the boot option on the disk.")
                setChanged()
            except Exception as e:
                setMsg("Failed to set the boot option on the disk.")
                setMsg(str(e))
                setFailed()
                return False
        else:
            setMsg("The boot option of the disk is correct")
        if int(DISK.size) < (1024 * 1024 * 1024 * int(disksize)):
            try:
                DISK.size = (1024 * 1024 * 1024 * int(disksize))
                setMsg("Updated the size of the disk.")
                setChanged()
            except Exception as e:
                setMsg("Failed to update the size of the disk.")
                setMsg(str(e))
                setFailed()
                return False
        elif int(DISK.size) > (1024 * 1024 * 1024 * int(disksize)):
            setMsg("Shrinking disks is not supported")
            setFailed()
            return False
        else:
            setMsg("The size of the disk is correct")
        if str(DISK.interface) != str(diskinterface):
            try:
                DISK.interface = diskinterface
                setMsg("Updated the interface of the disk.")
                setChanged()
            except Exception as e:
                setMsg("Failed to update the interface of the disk.")
                setMsg(str(e))
                setFailed()
                return False
        else:
            setMsg("The interface of the disk is correct")
        return True

    def set_NIC(self, vmname, nicname, newname, vlan, interface):
        NIC = self.get_NIC(vmname, nicname)
        VM = self.get_VM(vmname)
        CLUSTER = self.get_cluster_byid(VM.cluster.id)
        DC = self.get_DC_byid(CLUSTER.data_center.id)
        NETWORK = self.get_network(str(DC.name), vlan)
        checkFail()
        if NIC.name != newname:
            NIC.name = newname
            setMsg('Updating iface name to ' + newname)
            setChanged()
        if str(NIC.network.id) != str(NETWORK.id):
            NIC.set_network(NETWORK)
            setMsg('Updating iface network to ' + vlan)
            setChanged()
        if NIC.interface != interface:
            NIC.interface = interface
            setMsg('Updating iface interface to ' + interface)
            setChanged()
        try:
            NIC.update()
            setMsg('iface has successfully been updated.')
        except Exception as e:
            setMsg("Failed to update the iface.")
            setMsg(str(e))
            setFailed()
            return False
        return True

    def set_DeleteProtection(self, vmname, del_prot):
        VM = self.get_VM(vmname)
        VM.delete_protected = del_prot
        try:
            VM.update()
            setChanged()
        except Exception as e:
            setMsg("Failed to update delete protection.")
            setMsg(str(e))
            setFailed()
            return False
        return True

    def set_BootOrder(self, vmname, boot_order):
        VM = self.get_VM(vmname)
        bootorder = []
        for device in boot_order:
            bootorder.append(params.Boot(dev=device))
        VM.os.boot = bootorder

        try:
            VM.update()
            setChanged()
        except Exception as e:
            setMsg("Failed to update the boot order.")
            setMsg(str(e))
            setFailed()
            return False
        return True

    def set_Host(self, host_name, cluster, ifaces):
        HOST = self.get_Host(host_name)
        CLUSTER = self.get_cluster(cluster)

        if HOST is None:
            setMsg("Host does not exist.")
            ifacelist = dict()
            networklist = []
            manageip = ''

            try:
                for iface in ifaces:
                    try:
                        setMsg('creating host interface ' + iface['name'])
                        if 'management' in iface:
                            manageip = iface['ip']
                        if 'boot_protocol' not in iface:
                            if 'ip' in iface:
                                iface['boot_protocol'] = 'static'
                            else:
                                iface['boot_protocol'] = 'none'
                        if 'ip' not in iface:
                            iface['ip'] = ''
                        if 'netmask' not in iface:
                            iface['netmask'] = ''
                        if 'gateway' not in iface:
                            iface['gateway'] = ''

                        if 'network' in iface:
                            if 'bond' in iface:
                                bond = []
                                for slave in iface['bond']:
                                    bond.append(ifacelist[slave])
                                try:
                                    tmpiface = params.Bonding(
                                        slaves=params.Slaves(host_nic=bond),
                                        options=params.Options(
                                            option=[
                                                params.Option(name='miimon', value='100'),
                                                params.Option(name='mode', value='4')
                                            ]
                                        )
                                    )
                                except Exception as e:
                                    setMsg('Failed to create the bond for  ' + iface['name'])
                                    setFailed()
                                    setMsg(str(e))
                                    return False
                                try:
                                    tmpnetwork = params.HostNIC(
                                        network=params.Network(name=iface['network']),
                                        name=iface['name'],
                                        boot_protocol=iface['boot_protocol'],
                                        ip=params.IP(
                                            address=iface['ip'],
                                            netmask=iface['netmask'],
                                            gateway=iface['gateway']
                                        ),
                                        override_configuration=True,
                                        bonding=tmpiface)
                                    networklist.append(tmpnetwork)
                                    setMsg('Applying network ' + iface['name'])
                                except Exception as e:
                                    setMsg('Failed to set' + iface['name'] + ' as network interface')
                                    setFailed()
                                    setMsg(str(e))
                                    return False
                            else:
                                tmpnetwork = params.HostNIC(
                                    network=params.Network(name=iface['network']),
                                    name=iface['name'],
                                    boot_protocol=iface['boot_protocol'],
                                    ip=params.IP(
                                        address=iface['ip'],
                                        netmask=iface['netmask'],
                                        gateway=iface['gateway']
                                    ))
                                networklist.append(tmpnetwork)
                                setMsg('Applying network ' + iface['name'])
                        else:
                            tmpiface = params.HostNIC(
                                name=iface['name'],
                                network=params.Network(),
                                boot_protocol=iface['boot_protocol'],
                                ip=params.IP(
                                    address=iface['ip'],
                                    netmask=iface['netmask'],
                                    gateway=iface['gateway']
                                ))
                        ifacelist[iface['name']] = tmpiface
                    except Exception as e:
                        setMsg('Failed to set ' + iface['name'])
                        setFailed()
                        setMsg(str(e))
                        return False
            except Exception as e:
                setMsg('Failed to set networks')
                setMsg(str(e))
                setFailed()
                return False

            if manageip == '':
                setMsg('No management network is defined')
                setFailed()
                return False

            try:
                HOST = params.Host(name=host_name, address=manageip, cluster=CLUSTER, ssh=params.SSH(authentication_method='publickey'))
                if self.conn.hosts.add(HOST):
                    setChanged()
                    HOST = self.get_Host(host_name)
                    state = HOST.status.state
                    while (state != 'non_operational' and state != 'up'):
                        HOST = self.get_Host(host_name)
                        state = HOST.status.state
                        time.sleep(1)
                        if state == 'non_responsive':
                            setMsg('Failed to add host to RHEVM')
                            setFailed()
                            return False

                    setMsg('status host: up')
                    time.sleep(5)

                    HOST = self.get_Host(host_name)
                    state = HOST.status.state
                    setMsg('State before setting to maintenance: ' + str(state))
                    HOST.deactivate()
                    while state != 'maintenance':
                        HOST = self.get_Host(host_name)
                        state = HOST.status.state
                        time.sleep(1)
                    setMsg('status host: maintenance')

                    try:
                        HOST.nics.setupnetworks(params.Action(
                            force=True,
                            check_connectivity=False,
                            host_nics=params.HostNics(host_nic=networklist)
                        ))
                        setMsg('nics are set')
                    except Exception as e:
                        setMsg('Failed to apply networkconfig')
                        setFailed()
                        setMsg(str(e))
                        return False

                    try:
                        HOST.commitnetconfig()
                        setMsg('Network config is saved')
                    except Exception as e:
                        setMsg('Failed to save networkconfig')
                        setFailed()
                        setMsg(str(e))
                        return False
            except Exception as e:
                if 'The Host name is already in use' in str(e):
                    setMsg("Host already exists")
                else:
                    setMsg("Failed to add host")
                    setFailed()
                    setMsg(str(e))
                return False

            HOST.activate()
            while state != 'up':
                HOST = self.get_Host(host_name)
                state = HOST.status.state
                time.sleep(1)
                if state == 'non_responsive':
                    setMsg('Failed to apply networkconfig.')
                    setFailed()
                    return False
            setMsg('status host: up')
        else:
            setMsg("Host exists.")

        return True

    def del_NIC(self, vmname, nicname):
        return self.get_NIC(vmname, nicname).delete()

    def remove_VM(self, vmname):
        VM = self.get_VM(vmname)
        try:
            VM.delete()
        except Exception as e:
            setMsg("Failed to remove VM.")
            setMsg(str(e))
            setFailed()
            return False
        return True

    def start_VM(self, vmname, timeout):
        VM = self.get_VM(vmname)
        try:
            VM.start()
        except Exception as e:
            setMsg("Failed to start VM.")
            setMsg(str(e))
            setFailed()
            return False
        return self.wait_VM(vmname, "up", timeout)

    def wait_VM(self, vmname, state, timeout):
        VM = self.get_VM(vmname)
        while VM.status.state != state:
            VM = self.get_VM(vmname)
            time.sleep(10)
            if timeout is not False:
                timeout -= 10
                if timeout <= 0:
                    setMsg("Timeout expired")
                    setFailed()
                    return False
        return True

    def stop_VM(self, vmname, timeout):
        VM = self.get_VM(vmname)
        try:
            VM.stop()
        except Exception as e:
            setMsg("Failed to stop VM.")
            setMsg(str(e))
            setFailed()
            return False
        return self.wait_VM(vmname, "down", timeout)

    def set_CD(self, vmname, cd_drive):
        VM = self.get_VM(vmname)
        try:
            if str(VM.status.state) == 'down':
                cdrom = params.CdRom(file=cd_drive)
                VM.cdroms.add(cdrom)
                setMsg("Attached the image.")
                setChanged()
            else:
                cdrom = VM.cdroms.get(id="00000000-0000-0000-0000-000000000000")
                cdrom.set_file(cd_drive)
                cdrom.update(current=True)
                setMsg("Attached the image.")
                setChanged()
        except Exception as e:
            setMsg("Failed to attach image.")
            setMsg(str(e))
            setFailed()
            return False
        return True

    def set_VM_Host(self, vmname, vmhost):
        VM = self.get_VM(vmname)
        HOST = self.get_Host(vmhost)
        try:
            VM.placement_policy.host = HOST
            VM.update()
            setMsg("Set startup host to " + vmhost)
            setChanged()
        except Exception as e:
            setMsg("Failed to set startup host.")
            setMsg(str(e))
            setFailed()
            return False
        return True

    def migrate_VM(self, vmname, vmhost):
        VM = self.get_VM(vmname)

        HOST = self.get_Host_byid(VM.host.id)
        if str(HOST.name) != vmhost:
            try:
                VM.migrate(
                    action=params.Action(
                        host=params.Host(
                            name=vmhost,
                        )
                    ),
                )
                setChanged()
                setMsg("VM migrated to " + vmhost)
            except Exception as e:
                setMsg("Failed to set startup host.")
                setMsg(str(e))
                setFailed()
                return False
        return True

    def remove_CD(self, vmname):
        VM = self.get_VM(vmname)
        try:
            VM.cdroms.get(id="00000000-0000-0000-0000-000000000000").delete()
            setMsg("Removed the image.")
            setChanged()
        except Exception as e:
            setMsg("Failed to remove the image.")
            setMsg(str(e))
            setFailed()
            return False
        return True


class RHEV(object):
    def __init__(self, module):
        self.module = module

    def __get_conn(self):
        self.conn = RHEVConn(self.module)
        return self.conn

    def test(self):
        self.__get_conn()
        return "OK"

    def getVM(self, name):
        self.__get_conn()
        VM = self.conn.get_VM(name)
        if VM:
            vminfo = dict()
            vminfo['uuid'] = VM.id
            vminfo['name'] = VM.name
            vminfo['status'] = VM.status.state
            vminfo['cpu_cores'] = VM.cpu.topology.cores
            vminfo['cpu_sockets'] = VM.cpu.topology.sockets
            vminfo['cpu_shares'] = VM.cpu_shares
            vminfo['memory'] = (int(VM.memory) // 1024 // 1024 // 1024)
            vminfo['mem_pol'] = (int(VM.memory_policy.guaranteed) // 1024 // 1024 // 1024)
            vminfo['os'] = VM.get_os().type_
            vminfo['del_prot'] = VM.delete_protected
            try:
                vminfo['host'] = str(self.conn.get_Host_byid(str(VM.host.id)).name)
            except Exception:
                vminfo['host'] = None
            vminfo['boot_order'] = []
            for boot_dev in VM.os.get_boot():
                vminfo['boot_order'].append(str(boot_dev.dev))
            vminfo['disks'] = []
            for DISK in VM.disks.list():
                disk = dict()
                disk['name'] = DISK.name
                disk['size'] = (int(DISK.size) // 1024 // 1024 // 1024)
                disk['domain'] = str((self.conn.get_domain_byid(DISK.get_storage_domains().get_storage_domain()[0].id)).name)
                disk['interface'] = DISK.interface
                vminfo['disks'].append(disk)
            vminfo['ifaces'] = []
            for NIC in VM.nics.list():
                iface = dict()
                iface['name'] = str(NIC.name)
                iface['vlan'] = str(self.conn.get_network_byid(NIC.get_network().id).name)
                iface['interface'] = NIC.interface
                iface['mac'] = NIC.mac.address
                vminfo['ifaces'].append(iface)
                vminfo[str(NIC.name)] = NIC.mac.address
            CLUSTER = self.conn.get_cluster_byid(VM.cluster.id)
            if CLUSTER:
                vminfo['cluster'] = CLUSTER.name
        else:
            vminfo = False
        return vminfo

    def createVMimage(self, name, cluster, template, disks):
        self.__get_conn()
        return self.conn.createVMimage(name, cluster, template, disks)

    def createVM(self, name, cluster, os, actiontype):
        self.__get_conn()
        return self.conn.createVM(name, cluster, os, actiontype)

    def setMemory(self, name, memory):
        self.__get_conn()
        return self.conn.set_Memory(name, memory)

    def setMemoryPolicy(self, name, memory_policy):
        self.__get_conn()
        return self.conn.set_Memory_Policy(name, memory_policy)

    def setCPU(self, name, cpu):
        self.__get_conn()
        return self.conn.set_CPU(name, cpu)

    def setCPUShare(self, name, cpu_share):
        self.__get_conn()
        return self.conn.set_CPU_share(name, cpu_share)

    def setDisks(self, name, disks):
        self.__get_conn()
        counter = 0
        bootselect = False
        for disk in disks:
            if 'bootable' in disk:
                if disk['bootable'] is True:
                    bootselect = True

        for disk in disks:
            diskname = name + "_Disk" + str(counter) + "_" + disk.get('name', '').replace('/', '_')
            disksize = disk.get('size', 1)
            diskdomain = disk.get('domain', None)
            if diskdomain is None:
                setMsg("`domain` is a required disk key.")
                setFailed()
                return False
            diskinterface = disk.get('interface', 'virtio')
            diskformat = disk.get('format', 'raw')
            diskallocationtype = disk.get('thin', False)
            diskboot = disk.get('bootable', False)

            if bootselect is False and counter == 0:
                diskboot = True

            DISK = self.conn.get_disk(diskname)

            if DISK is None:
                self.conn.createDisk(name, diskname, disksize, diskdomain, diskinterface, diskformat, diskallocationtype, diskboot)
            else:
                self.conn.set_Disk(diskname, disksize, diskinterface, diskboot)
            checkFail()
            counter += 1

        return True

    def setNetworks(self, vmname, ifaces):
        self.__get_conn()
        VM = self.conn.get_VM(vmname)

        counter = 0
        length = len(ifaces)

        for NIC in VM.nics.list():
            if counter < length:
                iface = ifaces[counter]
                name = iface.get('name', None)
                if name is None:
                    setMsg("`name` is a required iface key.")
                    setFailed()
                elif str(name) != str(NIC.name):
                    setMsg("ifaces are in the wrong order, rebuilding everything.")
                    for NIC in VM.nics.list():
                        self.conn.del_NIC(vmname, NIC.name)
                    self.setNetworks(vmname, ifaces)
                    checkFail()
                    return True
                vlan = iface.get('vlan', None)
                if vlan is None:
                    setMsg("`vlan` is a required iface key.")
                    setFailed()
                checkFail()
                interface = iface.get('interface', 'virtio')
                self.conn.set_NIC(vmname, str(NIC.name), name, vlan, interface)
            else:
                self.conn.del_NIC(vmname, NIC.name)
            counter += 1
            checkFail()

        while counter < length:
            iface = ifaces[counter]
            name = iface.get('name', None)
            if name is None:
                setMsg("`name` is a required iface key.")
                setFailed()
            vlan = iface.get('vlan', None)
            if vlan is None:
                setMsg("`vlan` is a required iface key.")
                setFailed()
            if failed is True:
                return False
            interface = iface.get('interface', 'virtio')
            self.conn.createNIC(vmname, name, vlan, interface)

            counter += 1
            checkFail()
        return True

    def setDeleteProtection(self, vmname, del_prot):
        self.__get_conn()
        VM = self.conn.get_VM(vmname)
        if bool(VM.delete_protected) != bool(del_prot):
            self.conn.set_DeleteProtection(vmname, del_prot)
            checkFail()
            setMsg("`delete protection` has been updated.")
        else:
            setMsg("`delete protection` already has the right value.")
        return True

    def setBootOrder(self, vmname, boot_order):
        self.__get_conn()
        VM = self.conn.get_VM(vmname)
        bootorder = []
        for boot_dev in VM.os.get_boot():
            bootorder.append(str(boot_dev.dev))

        if boot_order != bootorder:
            self.conn.set_BootOrder(vmname, boot_order)
            setMsg('The boot order has been set')
        else:
            setMsg('The boot order has already been set')
        return True

    def removeVM(self, vmname):
        self.__get_conn()
        self.setPower(vmname, "down", 300)
        return self.conn.remove_VM(vmname)

    def setPower(self, vmname, state, timeout):
        self.__get_conn()
        VM = self.conn.get_VM(vmname)
        if VM is None:
            setMsg("VM does not exist.")
            setFailed()
            return False

        if state == VM.status.state:
            setMsg("VM state was already " + state)
        else:
            if state == "up":
                setMsg("VM is going to start")
                self.conn.start_VM(vmname, timeout)
                setChanged()
            elif state == "down":
                setMsg("VM is going to stop")
                self.conn.stop_VM(vmname, timeout)
                setChanged()
            elif state == "restarted":
                self.setPower(vmname, "down", timeout)
                checkFail()
                self.setPower(vmname, "up", timeout)
            checkFail()
            setMsg("the vm state is set to " + state)
        return True

    def setCD(self, vmname, cd_drive):
        self.__get_conn()
        if cd_drive:
            return self.conn.set_CD(vmname, cd_drive)
        else:
            return self.conn.remove_CD(vmname)

    def setVMHost(self, vmname, vmhost):
        self.__get_conn()
        return self.conn.set_VM_Host(vmname, vmhost)

        # pylint: disable=unreachable
        VM = self.conn.get_VM(vmname)
        HOST = self.conn.get_Host(vmhost)

        if VM.placement_policy.host is None:
            self.conn.set_VM_Host(vmname, vmhost)
        elif str(VM.placement_policy.host.id) != str(HOST.id):
            self.conn.set_VM_Host(vmname, vmhost)
        else:
            setMsg("VM's startup host was already set to " + vmhost)
        checkFail()

        if str(VM.status.state) == "up":
            self.conn.migrate_VM(vmname, vmhost)
        checkFail()

        return True

    def setHost(self, hostname, cluster, ifaces):
        self.__get_conn()
        return self.conn.set_Host(hostname, cluster, ifaces)


def checkFail():
    if failed:
        module.fail_json(msg=msg)
    else:
        return True


def setFailed():
    global failed
    failed = True


def setChanged():
    global changed
    changed = True


def setMsg(message):
    global failed
    msg.append(message)


def core(module):

    r = RHEV(module)

    state = module.params.get('state', 'present')

    if state == 'ping':
        r.test()
        return RHEV_SUCCESS, {"ping": "pong"}
    elif state == 'info':
        name = module.params.get('name')
        if not name:
            setMsg("`name` is a required argument.")
            return RHEV_FAILED, msg
        vminfo = r.getVM(name)
        return RHEV_SUCCESS, {'changed': changed, 'msg': msg, 'vm': vminfo}
    elif state == 'present':
        created = False
        name = module.params.get('name')
        if not name:
            setMsg("`name` is a required argument.")
            return RHEV_FAILED, msg
        actiontype = module.params.get('type')
        if actiontype == 'server' or actiontype == 'desktop':
            vminfo = r.getVM(name)
            if vminfo:
                setMsg('VM exists')
            else:
                # Create VM
                cluster = module.params.get('cluster')
                if cluster is None:
                    setMsg("cluster is a required argument.")
                    setFailed()
                template = module.params.get('image')
                if template:
                    disks = module.params.get('disks')
                    if disks is None:
                        setMsg("disks is a required argument.")
                        setFailed()
                    checkFail()
                    if r.createVMimage(name, cluster, template, disks) is False:
                        return RHEV_FAILED, vminfo
                else:
                    os = module.params.get('osver')
                    if os is None:
                        setMsg("osver is a required argument.")
                        setFailed()
                    checkFail()
                    if r.createVM(name, cluster, os, actiontype) is False:
                        return RHEV_FAILED, vminfo
                created = True

            # Set MEMORY and MEMORY POLICY
            vminfo = r.getVM(name)
            memory = module.params.get('vmmem')
            if memory is not None:
                memory_policy = module.params.get('mempol')
                if memory_policy == 0:
                    memory_policy = memory
                mem_pol_nok = True
                if int(vminfo['mem_pol']) == memory_policy:
                    setMsg("Memory is correct")
                    mem_pol_nok = False

                mem_nok = True
                if int(vminfo['memory']) == memory:
                    setMsg("Memory is correct")
                    mem_nok = False

                if memory_policy > memory:
                    setMsg('memory_policy cannot have a higher value than memory.')
                    return RHEV_FAILED, msg

                if mem_nok and mem_pol_nok:
                    if memory_policy > int(vminfo['memory']):
                        r.setMemory(vminfo['name'], memory)
                        r.setMemoryPolicy(vminfo['name'], memory_policy)
                    else:
                        r.setMemoryPolicy(vminfo['name'], memory_policy)
                        r.setMemory(vminfo['name'], memory)
                elif mem_nok:
                    r.setMemory(vminfo['name'], memory)
                elif mem_pol_nok:
                    r.setMemoryPolicy(vminfo['name'], memory_policy)
                checkFail()

            # Set CPU
            cpu = module.params.get('vmcpu')
            if int(vminfo['cpu_cores']) == cpu:
                setMsg("Number of CPUs is correct")
            else:
                if r.setCPU(vminfo['name'], cpu) is False:
                    return RHEV_FAILED, msg

            # Set CPU SHARE
            cpu_share = module.params.get('cpu_share')
            if cpu_share is not None:
                if int(vminfo['cpu_shares']) == cpu_share:
                    setMsg("CPU share is correct.")
                else:
                    if r.setCPUShare(vminfo['name'], cpu_share) is False:
                        return RHEV_FAILED, msg

            # Set DISKS
            disks = module.params.get('disks')
            if disks is not None:
                if r.setDisks(vminfo['name'], disks) is False:
                    return RHEV_FAILED, msg

            # Set NETWORKS
            ifaces = module.params.get('ifaces', None)
            if ifaces is not None:
                if r.setNetworks(vminfo['name'], ifaces) is False:
                    return RHEV_FAILED, msg

            # Set Delete Protection
            del_prot = module.params.get('del_prot')
            if r.setDeleteProtection(vminfo['name'], del_prot) is False:
                return RHEV_FAILED, msg

            # Set Boot Order
            boot_order = module.params.get('boot_order')
            if r.setBootOrder(vminfo['name'], boot_order) is False:
                return RHEV_FAILED, msg

            # Set VM Host
            vmhost = module.params.get('vmhost')
            if vmhost:
                if r.setVMHost(vminfo['name'], vmhost) is False:
                    return RHEV_FAILED, msg

            vminfo = r.getVM(name)
            vminfo['created'] = created
            return RHEV_SUCCESS, {'changed': changed, 'msg': msg, 'vm': vminfo}

        if actiontype == 'host':
            cluster = module.params.get('cluster')
            if cluster is None:
                setMsg("cluster is a required argument.")
                setFailed()
            ifaces = module.params.get('ifaces')
            if ifaces is None:
                setMsg("ifaces is a required argument.")
                setFailed()
            if r.setHost(name, cluster, ifaces) is False:
                return RHEV_FAILED, msg
            return RHEV_SUCCESS, {'changed': changed, 'msg': msg}

    elif state == 'absent':
        name = module.params.get('name')
        if not name:
            setMsg("`name` is a required argument.")
            return RHEV_FAILED, msg
        actiontype = module.params.get('type')
        if actiontype == 'server' or actiontype == 'desktop':
            vminfo = r.getVM(name)
            if vminfo:
                setMsg('VM exists')

                # Set Delete Protection
                del_prot = module.params.get('del_prot')
                if r.setDeleteProtection(vminfo['name'], del_prot) is False:
                    return RHEV_FAILED, msg

                # Remove VM
                if r.removeVM(vminfo['name']) is False:
                    return RHEV_FAILED, msg
                setMsg('VM has been removed.')
                vminfo['state'] = 'DELETED'
            else:
                setMsg('VM was already removed.')
            return RHEV_SUCCESS, {'changed': changed, 'msg': msg, 'vm': vminfo}

    elif state == 'up' or state == 'down' or state == 'restarted':
        name = module.params.get('name')
        if not name:
            setMsg("`name` is a required argument.")
            return RHEV_FAILED, msg
        timeout = module.params.get('timeout')
        if r.setPower(name, state, timeout) is False:
            return RHEV_FAILED, msg
        vminfo = r.getVM(name)
        return RHEV_SUCCESS, {'changed': changed, 'msg': msg, 'vm': vminfo}

    elif state == 'cd':
        name = module.params.get('name')
        cd_drive = module.params.get('cd_drive')
        if r.setCD(name, cd_drive) is False:
            return RHEV_FAILED, msg
        return RHEV_SUCCESS, {'changed': changed, 'msg': msg}


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=['absent', 'cd', 'down', 'info', 'ping', 'present', 'restarted', 'up']),
            user=dict(type='str', default='admin@internal'),
            password=dict(type='str', required=True, no_log=True),
            server=dict(type='str', default='127.0.0.1'),
            port=dict(type='int', default=443),
            insecure_api=dict(type='bool', default=False),
            name=dict(type='str'),
            image=dict(type='str'),
            datacenter=dict(type='str', default="Default"),
            type=dict(type='str', default='server', choices=['desktop', 'host', 'server']),
            cluster=dict(type='str', default=''),
            vmhost=dict(type='str'),
            vmcpu=dict(type='int', default=2),
            vmmem=dict(type='int', default=1),
            disks=dict(type='list'),
            osver=dict(type='str', default="rhel_6x64"),
            ifaces=dict(type='list', aliases=['interfaces', 'nics']),
            timeout=dict(type='int'),
            mempol=dict(type='int', default=1),
            vm_ha=dict(type='bool', default=True),
            cpu_share=dict(type='int', default=0),
            boot_order=dict(type='list', default=['hd', 'network']),
            del_prot=dict(type='bool', default=True),
            cd_drive=dict(type='str'),
        ),
    )

    if not HAS_SDK:
        module.fail_json(msg="The 'ovirtsdk' module is not importable. Check the requirements.")

    rc = RHEV_SUCCESS
    try:
        rc, result = core(module)
    except Exception as e:
        module.fail_json(msg=str(e))

    if rc != 0:  # something went wrong emit the msg
        module.fail_json(rc=rc, msg=result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
