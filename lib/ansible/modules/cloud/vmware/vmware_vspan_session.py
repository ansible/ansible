#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, CrySyS Lab <www.crysys.hu>
# Copyright: (c) 2018, Peter Gyorgy <gyorgy.peter@edu.bme.hu>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
import time

__metaclass__=type

ANSIBLE_METADATA={
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION='''
---
module: vmware_vspan_session
short_description: Create or remove a Port Mirroring session.
description:
   - This module can be used to create, delete or edit different kind of port mirroring sessions.
author:
- Peter Gyorgy <gyorgy.peter1996@gmail.com>
notes:
    - Tested on vSphere 6.7
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    switch:
        description:
            - The name of the switch to create or remove
        required: True
    name:
        description:
            - Name of the session.
        required: True
    state:
        description:
            - Create or remove the session.
        default: 'present'
        choices:
            - 'present'
            - 'absent'
        required: False
    type:
        description:
            - Select the mirroring type.
            - '- C(encapsulatedRemoteMirrorSource) (str): In encapsulatedRemoteMirrorSource session, Distributed Ports
            can be used as source entities, and Ip address can be used as destination entities.'
            - '- C(remoteMirrorDest) (str): In remoteMirrorDest session, vlan Ids can be used as source entities, and
            Distributed Ports can be used as destination entities.'
            - '- C(remoteMirrorSource) (str): In remoteMirrorSource session, Distributed Ports can be used as source
            entities, and uplink ports name can be used as destination entities.'
            - '- C(dvPortMirror) (str): In dvPortMirror session, Distributed Ports can be used as both source and
            destination entities.'
        default: 'dvPortMirror'
        choices:
            - 'encapsulatedRemoteMirrorSource'
            - 'remoteMirrorDest'
            - 'remoteMirrorSource'
            - 'dvPortMirror'
        required: False
    enabled:
        description:
            - Whether the session is enabled.
        type: bool
        default: True
    description:
        description:
            - The description for the session.
        required: False
    source_port_transmitted:
        description:
            - Source port for which transmitted packets are mirrored.
        required: False
    source_port_received:
        description:
            - Source port for which received packets are mirrored.
        required: False
    destination_port:
        description:
            - Destination port that received the mirrored packets. Also any port designated in the value of this
             property can not match the source port in any of the Distributed Port Mirroring session.
        required: False
    encapsulation_vlan_id:
        description:
            - VLAN ID used to encapsulate the mirrored traffic.
        required: False
    strip_original_vlan:
        description:
            - Whether to strip the original VLAN tag. if false, the original VLAN tag will be preserved on the mirrored
            traffic. If encapsulationVlanId has been set and this property is false, the frames will be double tagged
            with the original VLAN ID as the inner tag.
        type: bool
        required: False
    mirrored_packet_length:
        description:
            - An integer that describes how much of each frame to mirror. If unset, all of the frame would be mirrored.
             Setting this property to a smaller value is useful when the consumer will look only at the headers.
             The value cannot be less than 60.
        required: False
    normal_traffic_allowed:
        description:
            - Whether or not destination ports can send and receive "normal" traffic. Setting this to false will make
            mirror ports be used solely for mirroring and not double as normal access ports.
        type: bool
        required: False
    sampling_rate:
        description:
            - Sampling rate of the session. If its value is n, one of every n packets is mirrored.
            Valid values are between 1 to 65535, and default value is 1.
        type: int
        required: False
    source_vm_transmitted:
        description:
            - With this parameter it is possible, to add a NIC of a VM to a port mirroring session.
            - 'Valid attributes are:'
            - '- C(name) (str): Name of the VM'
            - '- C(nic_label) (bool): Label of the Network Interface Card to use.'
    source_vm_received:
        description:
            - With this parameter it is possible, to add a NIC of a VM to a port mirroring session.
            - 'Valid attributes are:'
            - '- C(name) (str): Name of the VM'
            - '- C(nic_label) (bool): Label of the Network Interface Card to use.'
    destination_vm:
        description:
            - With this parameter it is possible, to add a NIC of a VM to a port mirroring session.
            - 'Valid attributes are:'
            - '- C(name) (str): Name of the VM'
            - '- C(nic_label) (bool): Label of the Network Interface Card to use.'
        required: False
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES='''
- name: Create distributed mirroring session.
  vmware_vspan_session:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    switch_name: dvSwitch
    state: present
    name: Basic Session
    enabled: True
    description: "Example description"
    source_port_transmitted: 817
    source_port_received: 817
    destination_port: 815

  delegate_to: localhost

- name: Create remote destination mirroring session.
  vmware_vspan_session:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    switch_name: dvSwitch
    state: present
    name: Remote Session
    enabled: True
    description: "Example description"
    source_port_received: 105
    destination_port: 815
    type: "remoteMirrorDest"

  delegate_to: localhost

- name: Create remote destination mirroring session.
  vmware_vspan_session:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    switch_name: dvSwitch
    state: absent
    name: Remote Session

  delegate_to: localhost
'''

try:
    from pyVmomi import vim, vmodl
except ImportError as e:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (vmware_argument_spec, PyVmomi, find_dvs_by_name,
                                         find_vm_by_name, wait_for_task)



class VMwareVspanSession(PyVmomi):
    def __init__(self, module):
        super(VMwareVspanSession, self).__init__(module)
        self.switch=module.params['switch']
        self.name=module.params['name']
        self.type=module.params['type']
        self.enabled=module.params['enabled']
        self.state=module.params['state']
        self.description=module.params['description']
        self.source_port_transmitted=module.params['source_port_transmitted']
        self.source_port_received=module.params['source_port_received']
        self.destination_port=module.params['destination_port']
        self.encapsulation_vlan_id=module.params['encapsulation_vlan_id']
        self.strip_original_vlan=module.params['strip_original_vlan']
        self.mirrored_packet_length=module.params['mirrored_packet_length']
        self.normal_traffic_allowed=module.params['normal_traffic_allowed']
        self.sampling_rate=module.params['sampling_rate']
        self.dv_switch=find_dvs_by_name(self.content, self.switch)
        self.operation=None
        self.modified_ports=dict()
        self.deleted_session=None
        if module.params['source_vm_transmitted'] is not None:
            self.source_vm_transmitted_name=module.params['source_vm_transmitted']['name']
            self.source_vm_transmitted_nic_label=module.params['source_vm_transmitted']['nic_label']
        if module.params['source_vm_received'] is not None:
            self.source_vm_received_name=module.params['source_vm_received']['name']
            self.source_vm_received_nic_label=module.params['source_vm_received']['nic_label']
        if module.params['destination_vm'] is not None:
            self.destination_vm_name=module.params['destination_vm']['name']
            self.destination_vm_nic_label=module.params['destination_vm']['nic_label']

    def set_operation(self):
        """Sets the operation according to state"""
        if self.state=='absent':
            self.operation='remove'
        elif self.state=='present' and self.find_session_by_name() is None:
            self.operation='add'
        else:
            self.operation='edit'

    def find_session_by_name(self):
        """Finds a session by name

        Returns
        -------
        vim.dvs.VmwareDistributedVirtualSwitch.VspanSession
            The session if there was a session by the given name, else returns None
        """
        for vspan_session in self.dv_switch.config.vspanSession:
            if vspan_session.name==self.name:
                return vspan_session
        return None

    def get_vm_port(self, vm_name, nic_label):
        """Finds the port of the VM

        Returns
        -------
        str
            the port number as a string, or None if the NIC couldnt be found
        """
        vm=find_vm_by_name(self.content, vm_name)
        if vm is None:
            self.module.fail_json(msg='There is no VM with this name.')
        for hardware in vm.config.hardware.device:
            if isinstance(hardware, vim.vm.device.VirtualVmxnet3):
                if hardware.deviceInfo.label==nic_label:
                    return hardware.backing.port.portKey
        return None

    def set_port_for_vm(self):
        """Sets the ports, to the VM's specified port."""
        if hasattr(self, 'source_vm_transmitted_name') and hasattr(self, 'source_vm_transmitted_nic_label'):
            port=self.get_vm_port(self.source_vm_transmitted_name, self.source_vm_transmitted_nic_label)
            if port is not None:
                self.source_port_transmitted=port
        if hasattr(self, 'source_vm_received_name') and hasattr(self, 'source_vm_received_nic_label'):
            port=self.get_vm_port(self.source_vm_received_name, self.source_vm_received_nic_label)
            if port is not None:
                self.source_port_received=port
        if hasattr(self, 'destination_vm_name') and hasattr(self, 'destination_vm_nic_label'):
            port=self.get_vm_port(self.destination_vm_name, self.destination_vm_nic_label)
            if port is not None:
                self.destination_port=port

    def process_operation(self):
        """Calls the create or delete function based on the operation"""
        self.set_operation()
        if self.operation=='remove':
            results=self.remove_vspan_session()
            self.module.exit_json(**results)
        if self.operation=='add':
            self.set_port_for_vm()
            results=self.add_vspan_session()
            self.module.exit_json(**results)
        if self.operation=='edit':
            self.remove_vspan_session()
            self.set_port_for_vm()
            results=self.add_vspan_session()
            self.module.exit_json(**results)

    def set_port_security_promiscuous(self, port, state):
        """Set the given port to the given promiscuous state.

        Parameters
        ----------
        port : str
            PortKey
        state: bool
            State of the promiscuous mode, if true its allowed, else not.
        """
        # Creating the new port policy
        vim_bool=vim.BoolPolicy(value=state)
        port_policy=vim.dvs.VmwareDistributedVirtualSwitch.SecurityPolicy(allowPromiscuous=vim_bool)
        port_settings=vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy(securityPolicy=port_policy)
        port_spec=vim.dvs.DistributedVirtualPort.ConfigSpec(
            operation="edit",
            key=port,
            setting=port_settings
        )
        task=self.dv_switch.ReconfigureDVPort_Task([port_spec])
        try:
            wait_for_task(task)
        except Exception:
            self.restore_original_state()
            self.module.fail_json(msg=task.info.error.msg)

    def turn_off_promiscuous(self):
        """Disable all promiscuous mode ports, and give them back in a list.

        Returns
        -------
        list
            Contains every port, where promiscuous mode has been turned off
        """
        # Ports that are in mirror sessions
        ports=[]
        ports_of_selected_session=[]
        for vspan_session in self.dv_switch.config.vspanSession:
            if vspan_session.sourcePortReceived is not None:
                session_ports=vspan_session.sourcePortReceived.portKey
                for port in session_ports:
                    if vspan_session.name==self.name:
                        ports_of_selected_session.append(port)
                    elif not(port in ports):
                        ports.append(port)
            if vspan_session.sourcePortTransmitted is not None:
                session_ports=vspan_session.sourcePortTransmitted.portKey
                for port in session_ports:
                    if vspan_session.name==self.name:
                        ports_of_selected_session.append(port)
                    elif not(port in ports):
                        ports.append(port)
            if vspan_session.destinationPort is not None:
                session_ports=vspan_session.destinationPort.portKey
                for port in session_ports:
                    if vspan_session.name==self.name:
                        ports_of_selected_session.append(port)
                    elif not(port in ports):
                        ports.append(port)
        promiscuous_ports=[]
        if ports:
            dv_ports=self.dv_switch.FetchDVPorts(vim.dvs.PortCriteria(portKey=ports))
            # If a port is promiscuous set disable it, and add it to the array to enable it after the changes are made.
            for dv_port in dv_ports:
                if dv_port.config.setting.securityPolicy.allowPromiscuous.value:
                    self.set_port_security_promiscuous(dv_port.key, False)
                    self.modified_ports.update({dv_port.key: True})
                    promiscuous_ports.append(dv_port.key)
        if ports_of_selected_session:
            current_dv_ports=self.dv_switch.FetchDVPorts(vim.dvs.PortCriteria(portKey=ports_of_selected_session))
            for dv_port in current_dv_ports:
                if dv_port.config.setting.securityPolicy.allowPromiscuous.value:
                    self.set_port_security_promiscuous(dv_port.key, False)
                    self.modified_ports.update({dv_port.key: True})
        # Return the promiscuous ports array, to set them back after the config is finished.
        return promiscuous_ports

    def delete_mirroring_session(self, key):
        """Deletes the mirroring session.

        Parameters
        ----------
        key : str
            Key of the Session
        """
        session=vim.dvs.VmwareDistributedVirtualSwitch.VspanSession(
            key=key
        )
        config_version=self.dv_switch.config.configVersion
        s_spec=vim.dvs.VmwareDistributedVirtualSwitch.VspanConfigSpec(vspanSession=session, operation="remove")
        c_spec=vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec(vspanConfigSpec=[s_spec], configVersion=config_version)
        task=self.dv_switch.ReconfigureDvs_Task(c_spec)
        try:
            wait_for_task(task)
        except Exception:
            self.restore_original_state()
            self.module.fail_json(msg=task.info.error.msg)

    def restore_original_state(self):
        """In case of failure restore, the changes we made."""
        for port, state in self.modified_ports.items():
            self.set_port_security_promiscuous(port, state)
        if self.deleted_session is not None:
            session=self.deleted_session
            config_version=self.dv_switch.config.configVersion
            s_spec=vim.dvs.VmwareDistributedVirtualSwitch.VspanConfigSpec(vspanSession=session, operation="add")
            c_spec=vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec(vspanConfigSpec=[s_spec], configVersion=config_version)
            # Revert the delete
            task=self.dv_switch.ReconfigureDvs_Task(c_spec)
            try:
                wait_for_task(task)
            except Exception:
                self.restore_original_state()
                self.module.fail_json(msg=task.info.error.msg)

    def remove_vspan_session(self):
        """Calls the necessary functions to delete a VSpanSession."""
        results=dict(changed=False, result="")
        mirror_session=self.find_session_by_name()
        if mirror_session is None:
            self.module.fail_json(msg='There is no VSpanSession with this name.')
        promiscuous_ports=self.turn_off_promiscuous()
        session_key=mirror_session.key
        # Delete Mirroring Session
        self.delete_mirroring_session(session_key)
        # Session
        self.deleted_session=mirror_session
        # Set back the promiscuous ports
        if promiscuous_ports:
            for port in promiscuous_ports:
                self.set_port_security_promiscuous(port, True)
        results['changed']=True
        results['result']='VSpan Session has been deleted'
        return results

    def check_if_session_name_is_free(self):
        """Checks whether the name is used or not

        Returns
        -------
        bool
            True if the name is free and False if it is used.
        """
        for vspan_session in self.dv_switch.config.vspanSession:
            if vspan_session.name==self.name:
                return False
        return True

    def create_vspan_session(self):
        """Builds up the session, adds the parameters that we specified, then creates it on the vSwitch"""

        session=vim.dvs.VmwareDistributedVirtualSwitch.VspanSession(
            name=self.name,
            enabled=True
        )
        if self.type is not None:
            session.sessionType=self.type
            if self.type=='encapsulatedRemoteMirrorSource':
                if self.source_port_received is not None:
                    port=vim.dvs.VmwareDistributedVirtualSwitch.VspanPorts(portKey=str(self.source_port_received))
                    session.sourcePortReceived=port
                if self.source_port_transmitted is not None:
                    port=vim.dvs.VmwareDistributedVirtualSwitch.VspanPorts(portKey=str(self.source_port_transmitted))
                    session.sourcePortTransmitted=port
                if self.destination_port is not None:
                    port=vim.dvs.VmwareDistributedVirtualSwitch.VspanPorts(ipAddress=str(self.destination_port))
                    session.destinationPort=port
            if self.type=='remoteMirrorSource':
                if self.source_port_received is not None:
                    port=vim.dvs.VmwareDistributedVirtualSwitch.VspanPorts(portKey=str(self.source_port_received))
                    session.sourcePortReceived=port
                if self.source_port_transmitted is not None:
                    port=vim.dvs.VmwareDistributedVirtualSwitch.VspanPorts(portKey=str(self.source_port_transmitted))
                    session.sourcePortTransmitted=port
                if self.destination_port is not None:
                    port=vim.dvs.VmwareDistributedVirtualSwitch.VspanPorts(uplinkPortName=str(self.destination_port))
                    session.destinationPort=port
            if self.type=='remoteMirrorDest':
                if self.source_port_received is not None:
                    port=vim.dvs.VmwareDistributedVirtualSwitch.VspanPorts(vlans=[int(self.source_port_received)])
                    session.sourcePortReceived=port
                if self.destination_port is not None:
                    port=vim.dvs.VmwareDistributedVirtualSwitch.VspanPorts(portKey=str(self.destination_port))
                    session.destinationPort=port
            if self.type=='dvPortMirror':
                if self.source_port_received is not None:
                    port=vim.dvs.VmwareDistributedVirtualSwitch.VspanPorts(portKey=str(self.source_port_received))
                    session.sourcePortReceived=port
                if self.source_port_transmitted is not None:
                    port=vim.dvs.VmwareDistributedVirtualSwitch.VspanPorts(portKey=str(self.source_port_transmitted))
                    session.sourcePortTransmitted=port
                if self.destination_port is not None:
                    port=vim.dvs.VmwareDistributedVirtualSwitch.VspanPorts(portKey=str(self.destination_port))
                    session.destinationPort=port
        if self.description is not None:
            session.description=self.description
        if self.encapsulation_vlan_id is not None:
            session.encapsulationVlanId=self.encapsulation_vlan_id
        if self.strip_original_vlan is not None:
            session.stripOriginalVlan=self.strip_original_vlan
        if self.mirrored_packet_length is not None:
            session.mirroredPacketLength=self.mirrored_packet_length
        if self.normal_traffic_allowed is not None:
            session.normalTrafficAllowed=self.normal_traffic_allowed
        if self.sampling_rate is not None:
            session.samplingRate=self.sampling_rate
        config_version=self.dv_switch.config.configVersion
        s_spec=vim.dvs.VmwareDistributedVirtualSwitch.VspanConfigSpec(vspanSession=session, operation="add")
        c_spec=vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec(vspanConfigSpec=[s_spec], configVersion=config_version)
        task=self.dv_switch.ReconfigureDvs_Task(c_spec)
        try:
            wait_for_task(task)
        except Exception:
            self.restore_original_state()
            self.module.fail_json(msg=task.info.error.msg)

    def add_vspan_session(self):
        """Calls the necessary functions to create a VSpanSession"""
        results=dict(changed=False, result="")
        promiscous_ports=self.turn_off_promiscuous()
        if not self.check_if_session_name_is_free():
            self.module.fail_json(msg='There is another VSpan Session with this name.')
        # Locate the ports, we want to use
        dv_ports=self.dv_switch.FetchDVPorts(vim.dvs.PortCriteria(portKey=[str(self.source_port_received),
                                                                          str(self.source_port_transmitted),
                                                                          str(self.destination_port)]))
        for dv_port in dv_ports:
            if dv_port.config.setting.securityPolicy.allowPromiscuous.value:
                self.set_port_security_promiscuous(dv_port.key, False)
                self.modified_ports.update({dv_port.key: True})
        # Now we can create the VspanSession
        self.create_vspan_session()
        # Finally we can set the destination port to promiscuous mode
        if self.type=='dvPortMirror' or self.type=='remoteMirrorDest':
            self.set_port_security_promiscuous(str(self.destination_port), True)
        # Set Back the Promiscuous ports
        if promiscous_ports:
            for port in promiscous_ports:
                self.set_port_security_promiscuous(port, True)
        results['changed']=True
        results['result']='Mirroring session has been created.'
        return results


def main():
    argument_spec=vmware_argument_spec()
    argument_spec.update(dict(
        switch=dict(type='str', required=True, aliases=['switch_name']),
        name=dict(type='str', required=True),
        state=dict(type='str', required=True, choices=['present', 'absent']),
        type=dict(type='str', default='dvPortMirror', choices=['dvPortMirror',
                                                               'encapsulatedRemoteMirrorSource',
                                                               'remoteMirrorDest',
                                                               'remoteMirrorSource']),
        enabled=dict(type='bool', default=True),
        description=dict(type='str'),
        source_port_transmitted=dict(type='str'),
        source_port_received=dict(type='str'),
        destination_port=dict(type='str'),
        encapsulation_vlan_id=dict(type='int'),
        strip_original_vlan=dict(type='bool'),
        mirrored_packet_length=dict(type='int'),
        normal_traffic_allowed=dict(type='bool'),
        sampling_rate=dict(type='int'),
        source_vm_transmitted=dict(type='dict',
                                   options=dict(
                                       name=dict(type='str'),
                                       nic_label=dict(type='str'))),
        source_vm_received=dict(type='dict',
                                options=dict(
                                    name=dict(type='str'),
                                    nic_label=dict(type='str'))),
        destination_vm=dict(type='dict',
                            options=dict(
                                name=dict(type='str'),
                                nic_label=dict(type='str'))),
    ))
    module=AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)
    session=VMwareVspanSession(module)
    session.process_operation()


if __name__=='__main__':
    main()
