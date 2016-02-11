#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Virt management features

Copyright 2007, 2012 Red Hat, Inc
Michael DeHaan <michael.dehaan@gmail.com>
Seth Vidal <skvidal@fedoraproject.org>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

DOCUMENTATION = '''
---
module: virt
short_description: Manages virtual machines supported by libvirt
description:
     - Manages virtual machines supported by I(libvirt).
version_added: "0.2"
options:
  name:
    description:
      - name of the guest VM being managed. Note that VM must be previously
        defined with xml.
    required: true
    default: null
    aliases: []
  state:
    description:
      - Note that there may be some lag for state requests like C(shutdown)
        since these refer only to VM states. After starting a guest, it may not
        be immediately accessible.
    required: false
    choices: [ "running", "shutdown", "destroyed", "paused" ]
    default: "no"
  command:
    description:
      - in addition to state management, various non-idempotent commands are available. See examples
    required: false
    choices: ["create","status", "start", "stop", "pause", "unpause",
              "shutdown", "undefine", "destroy", "get_xml", "autostart",
              "freemem", "list_vms", "info", "nodeinfo", "virttype", "define"]
  uri:
    description:
      - libvirt connection uri
    required: false
    defaults: qemu:///system
  xml:
    description:
      - XML document used with the define command
    required: false
    default: null
requirements:
    - "python >= 2.6"
    - "libvirt-python"
author:
    - "Ansible Core Team"
    - "Michael DeHaan"
    - "Seth Vidal"
'''

EXAMPLES = '''
# a playbook task line:
- virt: name=alpha state=running

# /usr/bin/ansible invocations
ansible host -m virt -a "name=alpha command=status"
ansible host -m virt -a "name=alpha command=get_xml"
ansible host -m virt -a "name=alpha command=create uri=lxc:///"

# a playbook example of defining and launching an LXC guest
tasks:
  - name: define vm
    virt: name=foo
          command=define
          xml="{{ lookup('template', 'container-template.xml.j2') }}"
          uri=lxc:///
  - name: start vm
    virt: name=foo state=running uri=lxc:///
'''

VIRT_FAILED = 1
VIRT_SUCCESS = 0
VIRT_UNAVAILABLE=2

import sys

try:
    import libvirt
except ImportError:
    HAS_VIRT = False
else:
    HAS_VIRT = True

ALL_COMMANDS = []
VM_COMMANDS = ['create','status', 'start', 'stop', 'pause', 'unpause',
                'shutdown', 'undefine', 'destroy', 'get_xml', 'autostart', 'define']
HOST_COMMANDS = ['freemem', 'list_vms', 'info', 'nodeinfo', 'virttype']
ALL_COMMANDS.extend(VM_COMMANDS)
ALL_COMMANDS.extend(HOST_COMMANDS)

VIRT_STATE_NAME_MAP = {
   0 : "running",
   1 : "running",
   2 : "running",
   3 : "paused",
   4 : "shutdown",
   5 : "shutdown",
   6 : "crashed"
}

class VMNotFound(Exception):
    pass

class LibvirtConnection(object):

    def __init__(self, uri, module):

        self.module = module

        cmd = "uname -r"
        rc, stdout, stderr = self.module.run_command(cmd)

        if "xen" in stdout:
            conn = libvirt.open(None)
        elif "esx" in uri:
            auth = [[libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_NOECHOPROMPT], [], None]
            conn = libvirt.openAuth(uri, auth)
        else:
            conn = libvirt.open(uri)

        if not conn:
            raise Exception("hypervisor connection failure")

        self.conn = conn

    def find_vm(self, vmid):
        """
        Extra bonus feature: vmid = -1 returns a list of everything
        """
        conn = self.conn

        vms = []

        # this block of code borrowed from virt-manager:
        # get working domain's name
        ids = conn.listDomainsID()
        for id in ids:
            vm = conn.lookupByID(id)
            vms.append(vm)
        # get defined domain
        names = conn.listDefinedDomains()
        for name in names:
            vm = conn.lookupByName(name)
            vms.append(vm)

        if vmid == -1:
            return vms

        for vm in vms:
            if vm.name() == vmid:
                return vm

        raise VMNotFound("virtual machine %s not found" % vmid)

    def shutdown(self, vmid):
        return self.find_vm(vmid).shutdown()

    def pause(self, vmid):
        return self.suspend(self.conn,vmid)

    def unpause(self, vmid):
        return self.resume(self.conn,vmid)

    def suspend(self, vmid):
        return self.find_vm(vmid).suspend()

    def resume(self, vmid):
        return self.find_vm(vmid).resume()

    def create(self, vmid):
        return self.find_vm(vmid).create()

    def destroy(self, vmid):
        return self.find_vm(vmid).destroy()

    def undefine(self, vmid):
        return self.find_vm(vmid).undefine()

    def get_status2(self, vm):
        state = vm.info()[0]
        return VIRT_STATE_NAME_MAP.get(state,"unknown")

    def get_status(self, vmid):
        state = self.find_vm(vmid).info()[0]
        return VIRT_STATE_NAME_MAP.get(state,"unknown")

    def nodeinfo(self):
        return self.conn.getInfo()

    def get_type(self):
        return self.conn.getType()

    def get_xml(self, vmid):
        vm = self.conn.lookupByName(vmid)
        return vm.XMLDesc(0)

    def get_maxVcpus(self, vmid):
        vm = self.conn.lookupByName(vmid)
        return vm.maxVcpus()

    def get_maxMemory(self, vmid):
        vm = self.conn.lookupByName(vmid)
        return vm.maxMemory()

    def getFreeMemory(self):
        return self.conn.getFreeMemory()

    def get_autostart(self, vmid):
        vm = self.conn.lookupByName(vmid)
        return vm.autostart()

    def set_autostart(self, vmid, val):
        vm = self.conn.lookupByName(vmid)
        return vm.setAutostart(val)

    def define_from_xml(self, xml):
        return self.conn.defineXML(xml)


class Virt(object):

    def __init__(self, uri, module):
        self.module = module
        self.uri = uri

    def __get_conn(self):
        self.conn = LibvirtConnection(self.uri, self.module)
        return self.conn

    def get_vm(self, vmid):
        self.__get_conn()
        return self.conn.find_vm(vmid)

    def state(self):
        vms = self.list_vms()
        state = []
        for vm in vms:
            state_blurb = self.conn.get_status(vm)
            state.append("%s %s" % (vm,state_blurb))
        return state

    def info(self):
        vms = self.list_vms()
        info = dict()
        for vm in vms:
            data = self.conn.find_vm(vm).info()
            # libvirt returns maxMem, memory, and cpuTime as long()'s, which
            # xmlrpclib tries to convert to regular int's during serialization.
            # This throws exceptions, so convert them to strings here and
            # assume the other end of the xmlrpc connection can figure things
            # out or doesn't care.
            info[vm] = {
                "state"     : VIRT_STATE_NAME_MAP.get(data[0],"unknown"),
                "maxMem"    : str(data[1]),
                "memory"    : str(data[2]),
                "nrVirtCpu" : data[3],
                "cpuTime"   : str(data[4]),
            }
            info[vm]["autostart"] = self.conn.get_autostart(vm)

        return info

    def nodeinfo(self):
        self.__get_conn()
        info = dict()
        data = self.conn.nodeinfo()
        info = {
            "cpumodel"     : str(data[0]),
            "phymemory"    : str(data[1]),
            "cpus"         : str(data[2]),
            "cpumhz"       : str(data[3]),
            "numanodes"    : str(data[4]),
            "sockets"      : str(data[5]),
            "cpucores"     : str(data[6]),
            "cputhreads"   : str(data[7])
        }
        return info

    def list_vms(self, state=None):
        self.conn = self.__get_conn()
        vms = self.conn.find_vm(-1)
        results = []
        for x in vms:
            try:
                if state:
                    vmstate = self.conn.get_status2(x)
                    if vmstate == state:
                        results.append(x.name())
                else:
                    results.append(x.name())
            except:
                pass
        return results

    def virttype(self):
        return self.__get_conn().get_type()

    def autostart(self, vmid):
        self.conn = self.__get_conn()
        return self.conn.set_autostart(vmid, True)

    def freemem(self):
        self.conn = self.__get_conn()
        return self.conn.getFreeMemory()

    def shutdown(self, vmid):
        """ Make the machine with the given vmid stop running.  Whatever that takes.  """
        self.__get_conn()
        self.conn.shutdown(vmid)
        return 0


    def pause(self, vmid):
        """ Pause the machine with the given vmid.  """

        self.__get_conn()
        return self.conn.suspend(vmid)

    def unpause(self, vmid):
        """ Unpause the machine with the given vmid.  """

        self.__get_conn()
        return self.conn.resume(vmid)

    def create(self, vmid):
        """ Start the machine via the given vmid """

        self.__get_conn()
        return self.conn.create(vmid)

    def start(self, vmid):
        """ Start the machine via the given id/name """

        self.__get_conn()
        return self.conn.create(vmid)

    def destroy(self, vmid):
        """ Pull the virtual power from the virtual domain, giving it virtually no time to virtually shut down.  """
        self.__get_conn()
        return self.conn.destroy(vmid)

    def undefine(self, vmid):
        """ Stop a domain, and then wipe it from the face of the earth.  (delete disk/config file) """

        self.__get_conn()
        return self.conn.undefine(vmid)

    def status(self, vmid):
        """
        Return a state suitable for server consumption.  Aka, codes.py values, not XM output.
        """
        self.__get_conn()
        return self.conn.get_status(vmid)

    def get_xml(self, vmid):
        """
        Receive a Vm id as input
        Return an xml describing vm config returned by a libvirt call
        """

        self.__get_conn()
        return self.conn.get_xml(vmid)

    def get_maxVcpus(self, vmid):
        """
        Gets the max number of VCPUs on a guest
        """

        self.__get_conn()
        return self.conn.get_maxVcpus(vmid)

    def get_max_memory(self, vmid):
        """
        Gets the max memory on a guest
        """

        self.__get_conn()
        return self.conn.get_MaxMemory(vmid)

    def define(self, xml):
        """
        Define a guest with the given xml
        """
        self.__get_conn()
        return self.conn.define_from_xml(xml)

def core(module):

    state      = module.params.get('state', None)
    guest      = module.params.get('name', None)
    command    = module.params.get('command', None)
    uri        = module.params.get('uri', None)
    xml        = module.params.get('xml', None)

    v = Virt(uri, module)
    res = {}

    if state and command=='list_vms':
        res = v.list_vms(state=state)
        if type(res) != dict:
            res = { command: res }
        return VIRT_SUCCESS, res

    if state:
        if not guest:
            module.fail_json(msg = "state change requires a guest specified")

        res['changed'] = False
        if state == 'running':
            if v.status(guest) is 'paused':
                res['changed'] = True
                res['msg'] = v.unpause(guest)
            elif v.status(guest) is not 'running':
                res['changed'] = True
                res['msg'] = v.start(guest)
        elif state == 'shutdown':
            if v.status(guest) is not 'shutdown':
                res['changed'] = True
                res['msg'] = v.shutdown(guest)
        elif state == 'destroyed':
            if v.status(guest) is not 'shutdown':
                res['changed'] = True
                res['msg'] = v.destroy(guest)
        elif state == 'paused':
            if v.status(guest) is 'running':
                res['changed'] = True
                res['msg'] = v.pause(guest)
        else:
            module.fail_json(msg="unexpected state")

        return VIRT_SUCCESS, res

    if command:
        if command in VM_COMMANDS:
            if not guest:
                module.fail_json(msg = "%s requires 1 argument: guest" % command)
            if command == 'define':
                if not xml:
                    module.fail_json(msg = "define requires xml argument")
                try:
                    v.get_vm(guest)
                except VMNotFound:
                    v.define(xml)
                    res = {'changed': True, 'created': guest}
                return VIRT_SUCCESS, res
            res = getattr(v, command)(guest)
            if type(res) != dict:
                res = { command: res }
            return VIRT_SUCCESS, res

        elif hasattr(v, command):
            res = getattr(v, command)()
            if type(res) != dict:
                res = { command: res }
            return VIRT_SUCCESS, res

        else:
            module.fail_json(msg="Command %s not recognized" % basecmd)

    module.fail_json(msg="expected state or command parameter to be specified")

def main():

    module = AnsibleModule(argument_spec=dict(
        name = dict(aliases=['guest']),
        state = dict(choices=['running', 'shutdown', 'destroyed', 'paused']),
        command = dict(choices=ALL_COMMANDS),
        uri = dict(default='qemu:///system'),
        xml = dict(),
    ))

    if not HAS_VIRT:
        module.fail_json(
            msg='The `libvirt` module is not importable. Check the requirements.'
        )

    rc = VIRT_SUCCESS
    try:
        rc, result = core(module)
    except Exception, e:
        module.fail_json(msg=str(e))

    if rc != 0: # something went wrong emit the msg
        module.fail_json(rc=rc, msg=result)
    else:
        module.exit_json(**result)


# import module snippets
from ansible.module_utils.basic import *
main()
