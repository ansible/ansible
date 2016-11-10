#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Maciej Delmanowski <drybjed@gmail.com>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: virt_net
author: "Maciej Delmanowski (@drybjed)"
version_added: "2.0"
short_description: Manage libvirt network configuration
description:
     - Manage I(libvirt) networks.
options:
    name:
        required: true
        aliases: ['network']
        description:
            - name of the network being managed. Note that network must be previously
              defined with xml.
    state:
        required: false
        choices: [ "active", "inactive", "present", "absent" ]
        description:
            - specify which state you want a network to be in.
              If 'active', network will be started.
              If 'present', ensure that network is present but do not change its
              state; if it's missing, you need to specify xml argument.
              If 'inactive', network will be stopped.
              If 'undefined' or 'absent', network will be removed from I(libvirt) configuration.
    command:
        required: false
        choices: [ "define", "create", "start", "stop", "destroy",
                   "undefine", "get_xml", "list_nets", "facts",
                   "info", "status", "modify"]
        description:
            - in addition to state management, various non-idempotent commands are available.
              See examples.
              Modify was added in version 2.1
    autostart:
        required: false
        choices: ["yes", "no"]
        description:
            - Specify if a given storage pool should be started automatically on system boot.
    uri:
        required: false
        default: "qemu:///system"
        description:
            - libvirt connection uri.
    xml:
        required: false
        description:
            - XML document used with the define command.
requirements:
    - "python >= 2.6"
    - "python-libvirt"
    - "python-lxml"
'''

EXAMPLES = '''
# Define a new network
- virt_net: command=define name=br_nat xml='{{ lookup("template", "network/bridge.xml.j2") }}'

# Start a network
- virt_net: command=create name=br_nat

# List available networks
- virt_net: command=list_nets

# Get XML data of a specified network
- virt_net: command=get_xml name=br_nat

# Stop a network
- virt_net: command=destroy name=br_nat

# Undefine a network
- virt_net: command=undefine name=br_nat

# Gather facts about networks
# Facts will be available as 'ansible_libvirt_networks'
- virt_net: command=facts

# Gather information about network managed by 'libvirt' remotely using uri
- virt_net: command=info uri='{{ item }}'
  with_items: "{{ libvirt_uris }}"
  register: networks

# Ensure that a network is active (needs to be defined and built first)
- virt_net: state=active name=br_nat

# Ensure that a network is inactive
- virt_net: state=inactive name=br_nat

# Ensure that a given network will be started at boot
- virt_net: autostart=yes name=br_nat

# Disable autostart for a given network
- virt_net: autostart=no name=br_nat
'''

VIRT_FAILED = 1
VIRT_SUCCESS = 0
VIRT_UNAVAILABLE=2


try:
    import libvirt
except ImportError:
    HAS_VIRT = False
else:
    HAS_VIRT = True

try:
    from lxml import etree
except ImportError:
    HAS_XML = False
else:
    HAS_XML = True

from ansible.module_utils.basic import AnsibleModule


ALL_COMMANDS = []
ENTRY_COMMANDS = ['create', 'status', 'start', 'stop',
                  'undefine', 'destroy', 'get_xml', 'define',
                  'modify' ]
HOST_COMMANDS = [ 'list_nets', 'facts', 'info' ]
ALL_COMMANDS.extend(ENTRY_COMMANDS)
ALL_COMMANDS.extend(HOST_COMMANDS)

ENTRY_STATE_ACTIVE_MAP = {
    0 : "inactive",
    1 : "active"
}

ENTRY_STATE_AUTOSTART_MAP = {
    0 : "no",
    1 : "yes"
}

ENTRY_STATE_PERSISTENT_MAP = {
    0 : "no",
    1 : "yes"
}

class EntryNotFound(Exception):
    pass


class LibvirtConnection(object):

    def __init__(self, uri, module):

        self.module = module

        conn = libvirt.open(uri)

        if not conn:
            raise Exception("hypervisor connection failure")

        self.conn = conn

    def find_entry(self, entryid):
        # entryid = -1 returns a list of everything

        results = []

        # Get active entries
        for name in self.conn.listNetworks():
            entry = self.conn.networkLookupByName(name)
            results.append(entry)

        # Get inactive entries
        for name in self.conn.listDefinedNetworks():
            entry = self.conn.networkLookupByName(name)
            results.append(entry)

        if entryid == -1:
            return results

        for entry in results:
            if entry.name() == entryid:
                return entry

        raise EntryNotFound("network %s not found" % entryid)

    def create(self, entryid):
        if not self.module.check_mode:
            return self.find_entry(entryid).create()
        else:
            try:
                state = self.find_entry(entryid).isActive()
            except:
                return self.module.exit_json(changed=True)
            if not state:
                return self.module.exit_json(changed=True)

    def modify(self, entryid, xml):
        network = self.find_entry(entryid)
        # identify what type of entry is given in the xml
        new_data = etree.fromstring(xml)
        old_data = etree.fromstring(network.XMLDesc(0))
        if new_data.tag == 'host':
            mac_addr = new_data.get('mac')
            hosts = old_data.xpath('/network/ip/dhcp/host')
            # find the one mac we're looking for
            host = None
            for h in hosts:
                if h.get('mac') == mac_addr:
                    host = h
                    break
            if host is None:
                # add the host
                if not self.module.check_mode:
                    res = network.update (libvirt.VIR_NETWORK_UPDATE_COMMAND_ADD_LAST,
                        libvirt.VIR_NETWORK_SECTION_IP_DHCP_HOST,
                        -1, xml, libvirt.VIR_NETWORK_UPDATE_AFFECT_CURRENT)
                else:
                    # pretend there was a change
                    res = 0
                if res == 0: 
                    return True
            else:
                # change the host
                if host.get('name') == new_data.get('name') and host.get('ip') == new_data.get('ip'):
                    return False
                else:
                    if not self.module.check_mode:
                        res = network.update (libvirt.VIR_NETWORK_UPDATE_COMMAND_MODIFY,
                            libvirt.VIR_NETWORK_SECTION_IP_DHCP_HOST,
                            -1, xml, libvirt.VIR_NETWORK_UPDATE_AFFECT_CURRENT)
                    else:
                        # pretend there was a change
                        res = 0
                    if res == 0:
                        return True
            #  command, section, parentIndex, xml, flags=0
            self.module.fail_json(msg='updating this is not supported yet '+unicode(xml))

    def destroy(self, entryid):
        if not self.module.check_mode:
            return self.find_entry(entryid).destroy()
        else:
            if self.find_entry(entryid).isActive():
                return self.module.exit_json(changed=True)

    def undefine(self, entryid):
        if not self.module.check_mode:
            return self.find_entry(entryid).undefine()
        else:
            if not self.find_entry(entryid):
                return self.module.exit_json(changed=True)

    def get_status2(self, entry):
        state = entry.isActive()
        return ENTRY_STATE_ACTIVE_MAP.get(state,"unknown")

    def get_status(self, entryid):
        if not self.module.check_mode:
            state = self.find_entry(entryid).isActive()
            return ENTRY_STATE_ACTIVE_MAP.get(state,"unknown")
        else:
            try:
                state = self.find_entry(entryid).isActive()
                return ENTRY_STATE_ACTIVE_MAP.get(state,"unknown")
            except:
                return ENTRY_STATE_ACTIVE_MAP.get("inactive","unknown")

    def get_uuid(self, entryid):
        return self.find_entry(entryid).UUIDString()

    def get_xml(self, entryid):
        return self.find_entry(entryid).XMLDesc(0)

    def get_forward(self, entryid):
        xml = etree.fromstring(self.find_entry(entryid).XMLDesc(0))
        try:
            result = xml.xpath('/network/forward')[0].get('mode')
        except:
            raise ValueError('Forward mode not specified')
        return result

    def get_domain(self, entryid):
        xml = etree.fromstring(self.find_entry(entryid).XMLDesc(0))
        try:
            result = xml.xpath('/network/domain')[0].get('name')
        except:
            raise ValueError('Domain not specified')
        return result

    def get_macaddress(self, entryid):
        xml = etree.fromstring(self.find_entry(entryid).XMLDesc(0))
        try:
            result = xml.xpath('/network/mac')[0].get('address')
        except:
            raise ValueError('MAC address not specified')
        return result

    def get_autostart(self, entryid):
        state = self.find_entry(entryid).autostart()
        return ENTRY_STATE_AUTOSTART_MAP.get(state,"unknown")

    def get_autostart2(self, entryid):
        if not self.module.check_mode:
            return self.find_entry(entryid).autostart()
        else:
            try:
                return self.find_entry(entryid).autostart()
            except:
                return self.module.exit_json(changed=True)

    def set_autostart(self, entryid, val):
        if not self.module.check_mode:
            return self.find_entry(entryid).setAutostart(val)
        else:
            try:
                state = self.find_entry(entryid).autostart()
            except:
                return self.module.exit_json(changed=True)
            if bool(state) != val:
                return self.module.exit_json(changed=True)

    def get_bridge(self, entryid):
        return self.find_entry(entryid).bridgeName()

    def get_persistent(self, entryid):
        state = self.find_entry(entryid).isPersistent()
        return ENTRY_STATE_PERSISTENT_MAP.get(state,"unknown")

    def define_from_xml(self, entryid, xml):
        if not self.module.check_mode:
            return self.conn.networkDefineXML(xml)
        else:
            try:
                self.find_entry(entryid)
            except:
                return self.module.exit_json(changed=True)


class VirtNetwork(object):

    def __init__(self, uri, module):
        self.module = module
        self.uri = uri
        self.conn = LibvirtConnection(self.uri, self.module)

    def get_net(self, entryid):
        return self.conn.find_entry(entryid)

    def list_nets(self, state=None):
        results = []
        for entry in self.conn.find_entry(-1):
            if state:
                if state == self.conn.get_status2(entry):
                    results.append(entry.name())
            else:
                results.append(entry.name())
        return results

    def state(self):
        results = []
        for entry in self.list_nets():
            state_blurb = self.conn.get_status(entry)
            results.append("%s %s" % (entry,state_blurb))
        return results

    def autostart(self, entryid):
        return self.conn.set_autostart(entryid, True)

    def get_autostart(self, entryid):
        return self.conn.get_autostart2(entryid)

    def set_autostart(self, entryid, state):
        return self.conn.set_autostart(entryid, state)

    def create(self, entryid):
        return self.conn.create(entryid)
    
    def modify(self, entryid, xml):
        return self.conn.modify(entryid, xml)

    def start(self, entryid):
        return self.conn.create(entryid)

    def stop(self, entryid):
        return self.conn.destroy(entryid)

    def destroy(self, entryid):
        return self.conn.destroy(entryid)

    def undefine(self, entryid):
        return self.conn.undefine(entryid)

    def status(self, entryid):
        return self.conn.get_status(entryid)

    def get_xml(self, entryid):
        return self.conn.get_xml(entryid)

    def define(self, entryid, xml):
        return self.conn.define_from_xml(entryid, xml)

    def info(self):
        return self.facts(facts_mode='info')

    def facts(self, facts_mode='facts'):
        results = dict()
        for entry in self.list_nets():
            results[entry] = dict()
            results[entry]["autostart"] = self.conn.get_autostart(entry)
            results[entry]["persistent"] = self.conn.get_persistent(entry)
            results[entry]["state"] = self.conn.get_status(entry)
            results[entry]["bridge"] = self.conn.get_bridge(entry)
            results[entry]["uuid"] = self.conn.get_uuid(entry)

            try:
                results[entry]["forward_mode"] = self.conn.get_forward(entry)
            except ValueError:
                pass

            try:
                results[entry]["domain"] = self.conn.get_domain(entry)
            except ValueError:
                pass

            try:
                results[entry]["macaddress"] = self.conn.get_macaddress(entry)
            except ValueError:
                pass

        facts = dict()
        if facts_mode == 'facts':
            facts["ansible_facts"] = dict()
            facts["ansible_facts"]["ansible_libvirt_networks"] = results
        elif facts_mode == 'info':
            facts['networks'] = results
        return facts


def core(module):

    state     = module.params.get('state', None)
    name      = module.params.get('name', None)
    command   = module.params.get('command', None)
    uri       = module.params.get('uri', None)
    xml       = module.params.get('xml', None)
    autostart = module.params.get('autostart', None)

    v = VirtNetwork(uri, module)
    res = {}

    if state and command == 'list_nets':
        res = v.list_nets(state=state)
        if not isinstance(res, dict):
            res = { command: res }
        return VIRT_SUCCESS, res

    if state:
        if not name:
            module.fail_json(msg = "state change requires a specified name")

        res['changed'] = False
        if state in [ 'active' ]:
            if v.status(name) is not 'active':
                res['changed'] = True
                res['msg'] = v.start(name)
        elif state in [ 'present' ]:
            try:
                v.get_net(name)
            except EntryNotFound:
                if not xml:
                    module.fail_json(msg = "network '" + name + "' not present, but xml not specified")
                v.define(name, xml)
                res = {'changed': True, 'created': name}
        elif state in [ 'inactive' ]:
            entries = v.list_nets()
            if name in entries:
                if v.status(name) is not 'inactive':
                    res['changed'] = True
                    res['msg'] = v.destroy(name)
        elif state in [ 'undefined', 'absent' ]:
            entries = v.list_nets()
            if name in entries:
                if v.status(name) is not 'inactive':
                    v.destroy(name)
                res['changed'] = True
                res['msg'] = v.undefine(name)
        else:
            module.fail_json(msg="unexpected state")

        return VIRT_SUCCESS, res

    if command:
        if command in ENTRY_COMMANDS:
            if not name:
                module.fail_json(msg = "%s requires 1 argument: name" % command)
            if command in ('define', 'modify'):
                if not xml:
                    module.fail_json(msg = command+" requires xml argument")
                try:
                    v.get_net(name)
                except EntryNotFound:
                    v.define(name, xml)
                    res = {'changed': True, 'created': name}
                else:
                    if command == 'modify':
                        mod = v.modify(name, xml)
                        res = {'changed': mod, 'modified': name}
                return VIRT_SUCCESS, res
            res = getattr(v, command)(name)
            if not isinstance(res, dict):
                res = { command: res }
            return VIRT_SUCCESS, res

        elif hasattr(v, command):
            res = getattr(v, command)()
            if not isinstance(res, dict):
                res = { command: res }
            return VIRT_SUCCESS, res

        else:
            module.fail_json(msg="Command %s not recognized" % command)

    if autostart is not None:
        if not name:
            module.fail_json(msg = "state change requires a specified name")

        res['changed'] = False
        if autostart:
            if not v.get_autostart(name):
                res['changed'] = True
                res['msg'] = v.set_autostart(name, True)
        else:
            if v.get_autostart(name):
                res['changed'] = True
                res['msg'] = v.set_autostart(name, False)

        return VIRT_SUCCESS, res

    module.fail_json(msg="expected state or command parameter to be specified")


def main():

    module = AnsibleModule (
        argument_spec = dict(
            name = dict(aliases=['network']),
            state = dict(choices=['active', 'inactive', 'present', 'absent']),
            command = dict(choices=ALL_COMMANDS),
            uri = dict(default='qemu:///system'),
            xml = dict(),
            autostart = dict(type='bool')
        ),
        supports_check_mode = True
    )

    if not HAS_VIRT:
        module.fail_json(
            msg='The `libvirt` module is not importable. Check the requirements.'
        )

    if not HAS_XML:
        module.fail_json(
            msg='The `lxml` module is not importable. Check the requirements.'
        )

    rc = VIRT_SUCCESS
    try:
        rc, result = core(module)
    except Exception as e:
        module.fail_json(msg=str(e))

    if rc != 0: # something went wrong emit the msg
        module.fail_json(rc=rc, msg=result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
