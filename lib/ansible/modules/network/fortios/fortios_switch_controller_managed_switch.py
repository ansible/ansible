#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
# Copyright 2019 Fortinet, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# the lib use python logging can get it if the following is set in your
# Ansible config.

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_switch_controller_managed_switch
short_description: Configure FortiSwitch devices that are managed by this FortiGate in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify switch_controller feature and managed_switch category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.2
version_added: "2.8"
author:
    - Miguel Angel Munoz (@mamunozgonzalez)
    - Nicolas Thomas (@thomnico)
notes:
    - Requires fortiosapi library developed by Fortinet
    - Run as a local_action in your playbook
requirements:
    - fortiosapi>=0.9.8
options:
    host:
       description:
            - FortiOS or FortiGate ip address.
       required: true
    username:
        description:
            - FortiOS or FortiGate username.
        required: true
    password:
        description:
            - FortiOS or FortiGate password.
        default: ""
    vdom:
        description:
            - Virtual domain, among those defined previously. A vdom is a
              virtual instance of the FortiGate that can be configured and
              used as a different unit.
        default: root
    https:
        description:
            - Indicates if the requests towards FortiGate must use HTTPS
              protocol
        type: bool
        default: true
    switch_controller_managed_switch:
        description:
            - Configure FortiSwitch devices that are managed by this FortiGate.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            802-1X-settings:
                description:
                    - Configuration method to edit FortiSwitch 802.1X global settings.
                suboptions:
                    link-down-auth:
                        description:
                            - Authentication state to set if a link is down.
                        choices:
                            - set-unauth
                            - no-action
                    local-override:
                        description:
                            - Enable to override global 802.1X settings on individual FortiSwitches.
                        choices:
                            - enable
                            - disable
                    max-reauth-attempt:
                        description:
                            - Maximum number of authentication attempts (0 - 15, default = 3).
                    reauth-period:
                        description:
                            - Reauthentication time interval (1 - 1440 min, default = 60, 0 = disable).
            connected:
                description:
                    - CAPWAP connection.
            custom-command:
                description:
                    - Configuration method to edit FortiSwitch commands to be pushed to this FortiSwitch device upon rebooting the FortiGate switch controller
                       or the FortiSwitch.
                suboptions:
                    command-entry:
                        description:
                            - List of FortiSwitch commands.
                        required: true
                    command-name:
                        description:
                            - Names of commands to be pushed to this FortiSwitch device, as configured under config switch-controller custom-command. Source
                               switch-controller.custom-command.command-name.
            delayed-restart-trigger:
                description:
                    - Delayed restart triggered for this FortiSwitch.
            description:
                description:
                    - Description.
            directly-connected:
                description:
                    - Directly connected FortiSwitch.
            dynamic-capability:
                description:
                    - List of features this FortiSwitch supports (not configurable) that is sent to the FortiGate device for subsequent configuration
                       initiated by the FortiGate device.
            dynamically-discovered:
                description:
                    - Dynamically discovered FortiSwitch.
            fsw-wan1-admin:
                description:
                    - FortiSwitch WAN1 admin status; enable to authorize the FortiSwitch as a managed switch.
                choices:
                    - discovered
                    - disable
                    - enable
            fsw-wan1-peer:
                description:
                    - Fortiswitch WAN1 peer port.
            fsw-wan2-admin:
                description:
                    - FortiSwitch WAN2 admin status; enable to authorize the FortiSwitch as a managed switch.
                choices:
                    - discovered
                    - disable
                    - enable
            fsw-wan2-peer:
                description:
                    - FortiSwitch WAN2 peer port.
            igmp-snooping:
                description:
                    - Configure FortiSwitch IGMP snooping global settings.
                suboptions:
                    aging-time:
                        description:
                            - Maximum time to retain a multicast snooping entry for which no packets have been seen (15 - 3600 sec, default = 300).
                    flood-unknown-multicast:
                        description:
                            - Enable/disable unknown multicast flooding.
                        choices:
                            - enable
                            - disable
                    local-override:
                        description:
                            - Enable/disable overriding the global IGMP snooping configuration.
                        choices:
                            - enable
                            - disable
            max-allowed-trunk-members:
                description:
                    - FortiSwitch maximum allowed trunk members.
            mirror:
                description:
                    - Configuration method to edit FortiSwitch packet mirror.
                suboptions:
                    dst:
                        description:
                            - Destination port.
                    name:
                        description:
                            - Mirror name.
                        required: true
                    src-egress:
                        description:
                            - Source egress interfaces.
                        suboptions:
                            name:
                                description:
                                    - Interface name.
                                required: true
                    src-ingress:
                        description:
                            - Source ingress interfaces.
                        suboptions:
                            name:
                                description:
                                    - Interface name.
                                required: true
                    status:
                        description:
                            - Active/inactive mirror configuration.
                        choices:
                            - active
                            - inactive
                    switching-packet:
                        description:
                            - Enable/disable switching functionality when mirroring.
                        choices:
                            - enable
                            - disable
            name:
                description:
                    - Managed-switch name.
            owner-vdom:
                description:
                    - VDOM which owner of port belongs to.
            poe-pre-standard-detection:
                description:
                    - Enable/disable PoE pre-standard detection.
                choices:
                    - enable
                    - disable
            ports:
                description:
                    - Managed-switch port list.
                suboptions:
                    allowed-vlans:
                        description:
                            - Configure switch port tagged vlans
                        suboptions:
                            vlan-name:
                                description:
                                    - VLAN name. Source system.interface.name.
                                required: true
                    allowed-vlans-all:
                        description:
                            - Enable/disable all defined vlans on this port.
                        choices:
                            - enable
                            - disable
                    arp-inspection-trust:
                        description:
                            - Trusted or untrusted dynamic ARP inspection.
                        choices:
                            - untrusted
                            - trusted
                    bundle:
                        description:
                            - Enable/disable Link Aggregation Group (LAG) bundling for non-FortiLink interfaces.
                        choices:
                            - enable
                            - disable
                    description:
                        description:
                            - Description for port.
                    dhcp-snoop-option82-trust:
                        description:
                            - Enable/disable allowance of DHCP with option-82 on untrusted interface.
                        choices:
                            - enable
                            - disable
                    dhcp-snooping:
                        description:
                            - Trusted or untrusted DHCP-snooping interface.
                        choices:
                            - untrusted
                            - trusted
                    discard-mode:
                        description:
                            - Configure discard mode for port.
                        choices:
                            - none
                            - all-untagged
                            - all-tagged
                    edge-port:
                        description:
                            - Enable/disable this interface as an edge port, bridging connections between workstations and/or computers.
                        choices:
                            - enable
                            - disable
                    export-tags:
                        description:
                            - Switch controller export tag name.
                        suboptions:
                            tag-name:
                                description:
                                    - Switch tag name. Source switch-controller.switch-interface-tag.name.
                                required: true
                    export-to:
                        description:
                            - Export managed-switch port to a tenant VDOM. Source system.vdom.name.
                    export-to-pool:
                        description:
                            - Switch controller export port to pool-list. Source switch-controller.virtual-port-pool.name.
                    export-to-pool_flag:
                        description:
                            - Switch controller export port to pool-list.
                    fgt-peer-device-name:
                        description:
                            - FGT peer device name.
                    fgt-peer-port-name:
                        description:
                            - FGT peer port name.
                    fiber-port:
                        description:
                            - Fiber-port.
                    flags:
                        description:
                            - Port properties flags.
                    fortilink-port:
                        description:
                            - FortiLink uplink port.
                    igmp-snooping:
                        description:
                            - Set IGMP snooping mode for the physical port interface.
                        choices:
                            - enable
                            - disable
                    igmps-flood-reports:
                        description:
                            - Enable/disable flooding of IGMP reports to this interface when igmp-snooping enabled.
                        choices:
                            - enable
                            - disable
                    igmps-flood-traffic:
                        description:
                            - Enable/disable flooding of IGMP snooping traffic to this interface.
                        choices:
                            - enable
                            - disable
                    isl-local-trunk-name:
                        description:
                            - ISL local trunk name.
                    isl-peer-device-name:
                        description:
                            - ISL peer device name.
                    isl-peer-port-name:
                        description:
                            - ISL peer port name.
                    lacp-speed:
                        description:
                            - end Link Aggregation Control Protocol (LACP) messages every 30 seconds (slow) or every second (fast).
                        choices:
                            - slow
                            - fast
                    learning-limit:
                        description:
                            - Limit the number of dynamic MAC addresses on this Port (1 - 128, 0 = no limit, default).
                    lldp-profile:
                        description:
                            - LLDP port TLV profile. Source switch-controller.lldp-profile.name.
                    lldp-status:
                        description:
                            - LLDP transmit and receive status.
                        choices:
                            - disable
                            - rx-only
                            - tx-only
                            - tx-rx
                    loop-guard:
                        description:
                            - Enable/disable loop-guard on this interface, an STP optimization used to prevent network loops.
                        choices:
                            - enabled
                            - disabled
                    loop-guard-timeout:
                        description:
                            - Loop-guard timeout (0 - 120 min, default = 45).
                    max-bundle:
                        description:
                            - Maximum size of LAG bundle (1 - 24, default = 24)
                    mclag:
                        description:
                            - Enable/disable multi-chassis link aggregation (MCLAG).
                        choices:
                            - enable
                            - disable
                    member-withdrawal-behavior:
                        description:
                            - Port behavior after it withdraws because of loss of control packets.
                        choices:
                            - forward
                            - block
                    members:
                        description:
                            - Aggregated LAG bundle interfaces.
                        suboptions:
                            member-name:
                                description:
                                    - Interface name from available options.
                                required: true
                    min-bundle:
                        description:
                            - Minimum size of LAG bundle (1 - 24, default = 1)
                    mode:
                        description:
                            - "LACP mode: ignore and do not send control messages, or negotiate 802.3ad aggregation passively or actively."
                        choices:
                            - static
                            - lacp-passive
                            - lacp-active
                    poe-capable:
                        description:
                            - PoE capable.
                    poe-pre-standard-detection:
                        description:
                            - Enable/disable PoE pre-standard detection.
                        choices:
                            - enable
                            - disable
                    poe-status:
                        description:
                            - Enable/disable PoE status.
                        choices:
                            - enable
                            - disable
                    port-name:
                        description:
                            - Switch port name.
                        required: true
                    port-number:
                        description:
                            - Port number.
                    port-owner:
                        description:
                            - Switch port name.
                    port-prefix-type:
                        description:
                            - Port prefix type.
                    port-security-policy:
                        description:
                            - Switch controller authentication policy to apply to this managed switch from available options. Source switch-controller
                              .security-policy.802-1X.name switch-controller.security-policy.captive-portal.name.
                    port-selection-criteria:
                        description:
                            - Algorithm for aggregate port selection.
                        choices:
                            - src-mac
                            - dst-mac
                            - src-dst-mac
                            - src-ip
                            - dst-ip
                            - src-dst-ip
                    qos-policy:
                        description:
                            - Switch controller QoS policy from available options. Source switch-controller.qos.qos-policy.name.
                    sample-direction:
                        description:
                            - sFlow sample direction.
                        choices:
                            - tx
                            - rx
                            - both
                    sflow-counter-interval:
                        description:
                            - sFlow sampler counter polling interval (1 - 255 sec).
                    sflow-sample-rate:
                        description:
                            - sFlow sampler sample rate (0 - 99999 p/sec).
                    sflow-sampler:
                        description:
                            - Enable/disable sFlow protocol on this interface.
                        choices:
                            - enabled
                            - disabled
                    speed:
                        description:
                            - Switch port speed; default and available settings depend on hardware.
                        choices:
                            - 10half
                            - 10full
                            - 100half
                            - 100full
                            - 1000auto
                            - 1000fiber
                            - 1000full
                            - 10000
                            - 40000
                            - auto
                            - auto-module
                            - 100FX-half
                            - 100FX-full
                            - 100000full
                            - 2500full
                            - 25000full
                            - 50000full
                    speed-mask:
                        description:
                            - Switch port speed mask.
                    stacking-port:
                        description:
                            - Stacking port.
                    status:
                        description:
                            - "Switch port admin status: up or down."
                        choices:
                            - up
                            - down
                    stp-bpdu-guard:
                        description:
                            - Enable/disable STP BPDU guard on this interface.
                        choices:
                            - enabled
                            - disabled
                    stp-bpdu-guard-timeout:
                        description:
                            - BPDU Guard disabling protection (0 - 120 min).
                    stp-root-guard:
                        description:
                            - Enable/disable STP root guard on this interface.
                        choices:
                            - enabled
                            - disabled
                    stp-state:
                        description:
                            - Enable/disable Spanning Tree Protocol (STP) on this interface.
                        choices:
                            - enabled
                            - disabled
                    switch-id:
                        description:
                            - Switch id.
                    type:
                        description:
                            - "Interface type: physical or trunk port."
                        choices:
                            - physical
                            - trunk
                    untagged-vlans:
                        description:
                            - Configure switch port untagged vlans
                        suboptions:
                            vlan-name:
                                description:
                                    - VLAN name. Source system.interface.name.
                                required: true
                    virtual-port:
                        description:
                            - Virtualized switch port.
                    vlan:
                        description:
                            - Assign switch ports to a VLAN. Source system.interface.name.
            pre-provisioned:
                description:
                    - Pre-provisioned managed switch.
            staged-image-version:
                description:
                    - Staged image version for FortiSwitch.
            storm-control:
                description:
                    - Configuration method to edit FortiSwitch storm control for measuring traffic activity using data rates to prevent traffic disruption.
                suboptions:
                    broadcast:
                        description:
                            - Enable/disable storm control to drop broadcast traffic.
                        choices:
                            - enable
                            - disable
                    local-override:
                        description:
                            - Enable to override global FortiSwitch storm control settings for this FortiSwitch.
                        choices:
                            - enable
                            - disable
                    rate:
                        description:
                            - Rate in packets per second at which storm traffic is controlled (1 - 10000000, default = 500). Storm control drops excess
                               traffic data rates beyond this threshold.
                    unknown-multicast:
                        description:
                            - Enable/disable storm control to drop unknown multicast traffic.
                        choices:
                            - enable
                            - disable
                    unknown-unicast:
                        description:
                            - Enable/disable storm control to drop unknown unicast traffic.
                        choices:
                            - enable
                            - disable
            stp-settings:
                description:
                    - Configuration method to edit Spanning Tree Protocol (STP) settings used to prevent bridge loops.
                suboptions:
                    forward-time:
                        description:
                            - Period of time a port is in listening and learning state (4 - 30 sec, default = 15).
                    hello-time:
                        description:
                            - Period of time between successive STP frame Bridge Protocol Data Units (BPDUs) sent on a port (1 - 10 sec, default = 2).
                    local-override:
                        description:
                            - Enable to configure local STP settings that override global STP settings.
                        choices:
                            - enable
                            - disable
                    max-age:
                        description:
                            - Maximum time before a bridge port saves its configuration BPDU information (6 - 40 sec, default = 20).
                    max-hops:
                        description:
                            - Maximum number of hops between the root bridge and the furthest bridge (1- 40, default = 20).
                    name:
                        description:
                            - Name of local STP settings configuration.
                    pending-timer:
                        description:
                            - Pending time (1 - 15 sec, default = 4).
                    revision:
                        description:
                            - STP revision number (0 - 65535).
                    status:
                        description:
                            - Enable/disable STP.
                        choices:
                            - enable
                            - disable
            switch-device-tag:
                description:
                    - User definable label/tag.
            switch-id:
                description:
                    - Managed-switch id.
                required: true
            switch-log:
                description:
                    - Configuration method to edit FortiSwitch logging settings (logs are transferred to and inserted into the FortiGate event log).
                suboptions:
                    local-override:
                        description:
                            - Enable to configure local logging settings that override global logging settings.
                        choices:
                            - enable
                            - disable
                    severity:
                        description:
                            - Severity of FortiSwitch logs that are added to the FortiGate event log.
                        choices:
                            - emergency
                            - alert
                            - critical
                            - error
                            - warning
                            - notification
                            - information
                            - debug
                    status:
                        description:
                            - Enable/disable adding FortiSwitch logs to the FortiGate event log.
                        choices:
                            - enable
                            - disable
            switch-profile:
                description:
                    - FortiSwitch profile. Source switch-controller.switch-profile.name.
            switch-stp-settings:
                description:
                    - Configure spanning tree protocol (STP).
                suboptions:
                    status:
                        description:
                            - Enable/disable STP.
                        choices:
                            - enable
                            - disable
            type:
                description:
                    - Indication of switch type, physical or virtual.
                choices:
                    - virtual
                    - physical
            version:
                description:
                    - FortiSwitch version.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure FortiSwitch devices that are managed by this FortiGate.
    fortios_switch_controller_managed_switch:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      switch_controller_managed_switch:
        state: "present"
        802-1X-settings:
            link-down-auth: "set-unauth"
            local-override: "enable"
            max-reauth-attempt: "6"
            reauth-period: "7"
        connected: "8"
        custom-command:
         -
            command-entry: "<your_own_value>"
            command-name: "<your_own_value> (source switch-controller.custom-command.command-name)"
        delayed-restart-trigger: "12"
        description: "<your_own_value>"
        directly-connected: "14"
        dynamic-capability: "15"
        dynamically-discovered: "16"
        fsw-wan1-admin: "discovered"
        fsw-wan1-peer: "<your_own_value>"
        fsw-wan2-admin: "discovered"
        fsw-wan2-peer: "<your_own_value>"
        igmp-snooping:
            aging-time: "22"
            flood-unknown-multicast: "enable"
            local-override: "enable"
        max-allowed-trunk-members: "25"
        mirror:
         -
            dst: "<your_own_value>"
            name: "default_name_28"
            src-egress:
             -
                name: "default_name_30"
            src-ingress:
             -
                name: "default_name_32"
            status: "active"
            switching-packet: "enable"
        name: "default_name_35"
        owner-vdom: "<your_own_value>"
        poe-pre-standard-detection: "enable"
        ports:
         -
            allowed-vlans:
             -
                vlan-name: "<your_own_value> (source system.interface.name)"
            allowed-vlans-all: "enable"
            arp-inspection-trust: "untrusted"
            bundle: "enable"
            description: "<your_own_value>"
            dhcp-snoop-option82-trust: "enable"
            dhcp-snooping: "untrusted"
            discard-mode: "none"
            edge-port: "enable"
            export-tags:
             -
                tag-name: "<your_own_value> (source switch-controller.switch-interface-tag.name)"
            export-to: "<your_own_value> (source system.vdom.name)"
            export-to-pool: "<your_own_value> (source switch-controller.virtual-port-pool.name)"
            export-to-pool_flag: "53"
            fgt-peer-device-name: "<your_own_value>"
            fgt-peer-port-name: "<your_own_value>"
            fiber-port: "56"
            flags: "57"
            fortilink-port: "58"
            igmp-snooping: "enable"
            igmps-flood-reports: "enable"
            igmps-flood-traffic: "enable"
            isl-local-trunk-name: "<your_own_value>"
            isl-peer-device-name: "<your_own_value>"
            isl-peer-port-name: "<your_own_value>"
            lacp-speed: "slow"
            learning-limit: "66"
            lldp-profile: "<your_own_value> (source switch-controller.lldp-profile.name)"
            lldp-status: "disable"
            loop-guard: "enabled"
            loop-guard-timeout: "70"
            max-bundle: "71"
            mclag: "enable"
            member-withdrawal-behavior: "forward"
            members:
             -
                member-name: "<your_own_value>"
            min-bundle: "76"
            mode: "static"
            poe-capable: "78"
            poe-pre-standard-detection: "enable"
            poe-status: "enable"
            port-name: "<your_own_value>"
            port-number: "82"
            port-owner: "<your_own_value>"
            port-prefix-type: "84"
            port-security-policy: "<your_own_value> (source switch-controller.security-policy.802-1X.name switch-controller.security-policy.captive-portal
              .name)"
            port-selection-criteria: "src-mac"
            qos-policy: "<your_own_value> (source switch-controller.qos.qos-policy.name)"
            sample-direction: "tx"
            sflow-counter-interval: "89"
            sflow-sample-rate: "90"
            sflow-sampler: "enabled"
            speed: "10half"
            speed-mask: "93"
            stacking-port: "94"
            status: "up"
            stp-bpdu-guard: "enabled"
            stp-bpdu-guard-timeout: "97"
            stp-root-guard: "enabled"
            stp-state: "enabled"
            switch-id: "<your_own_value>"
            type: "physical"
            untagged-vlans:
             -
                vlan-name: "<your_own_value> (source system.interface.name)"
            virtual-port: "104"
            vlan: "<your_own_value> (source system.interface.name)"
        pre-provisioned: "106"
        staged-image-version: "<your_own_value>"
        storm-control:
            broadcast: "enable"
            local-override: "enable"
            rate: "111"
            unknown-multicast: "enable"
            unknown-unicast: "enable"
        stp-settings:
            forward-time: "115"
            hello-time: "116"
            local-override: "enable"
            max-age: "118"
            max-hops: "119"
            name: "default_name_120"
            pending-timer: "121"
            revision: "122"
            status: "enable"
        switch-device-tag: "<your_own_value>"
        switch-id: "<your_own_value>"
        switch-log:
            local-override: "enable"
            severity: "emergency"
            status: "enable"
        switch-profile: "<your_own_value> (source switch-controller.switch-profile.name)"
        switch-stp-settings:
            status: "enable"
        type: "virtual"
        version: "134"
'''

RETURN = '''
build:
  description: Build number of the fortigate image
  returned: always
  type: str
  sample: '1547'
http_method:
  description: Last method used to provision the content into FortiGate
  returned: always
  type: str
  sample: 'PUT'
http_status:
  description: Last result given by FortiGate on last operation applied
  returned: always
  type: str
  sample: "200"
mkey:
  description: Master key (id) used in the last call to FortiGate
  returned: success
  type: str
  sample: "id"
name:
  description: Name of the table used to fulfill the request
  returned: always
  type: str
  sample: "urlfilter"
path:
  description: Path of the table used to fulfill the request
  returned: always
  type: str
  sample: "webfilter"
revision:
  description: Internal revision number
  returned: always
  type: str
  sample: "17.0.2.10658"
serial:
  description: Serial number of the unit
  returned: always
  type: str
  sample: "FGVMEVYYQT3AB5352"
status:
  description: Indication of the operation's result
  returned: always
  type: str
  sample: "success"
vdom:
  description: Virtual domain used
  returned: always
  type: str
  sample: "root"
version:
  description: Version of the FortiGate
  returned: always
  type: str
  sample: "v5.6.3"

'''

from ansible.module_utils.basic import AnsibleModule

fos = None


def login(data):
    host = data['host']
    username = data['username']
    password = data['password']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password)


def filter_switch_controller_managed_switch_data(json):
    option_list = ['802-1X-settings', 'connected', 'custom-command',
                   'delayed-restart-trigger', 'description', 'directly-connected',
                   'dynamic-capability', 'dynamically-discovered', 'fsw-wan1-admin',
                   'fsw-wan1-peer', 'fsw-wan2-admin', 'fsw-wan2-peer',
                   'igmp-snooping', 'max-allowed-trunk-members', 'mirror',
                   'name', 'owner-vdom', 'poe-pre-standard-detection',
                   'ports', 'pre-provisioned', 'staged-image-version',
                   'storm-control', 'stp-settings', 'switch-device-tag',
                   'switch-id', 'switch-log', 'switch-profile',
                   'switch-stp-settings', 'type', 'version']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def flatten_multilists_attributes(data):
    multilist_attrs = []

    for attr in multilist_attrs:
        try:
            path = "data['" + "']['".join(elem for elem in attr) + "']"
            current_val = eval(path)
            flattened_val = ' '.join(elem for elem in current_val)
            exec(path + '= flattened_val')
        except BaseException:
            pass

    return data


def switch_controller_managed_switch(data, fos):
    vdom = data['vdom']
    switch_controller_managed_switch_data = data['switch_controller_managed_switch']
    flattened_data = flatten_multilists_attributes(switch_controller_managed_switch_data)
    filtered_data = filter_switch_controller_managed_switch_data(flattened_data)
    if switch_controller_managed_switch_data['state'] == "present":
        return fos.set('switch-controller',
                       'managed-switch',
                       data=filtered_data,
                       vdom=vdom)

    elif switch_controller_managed_switch_data['state'] == "absent":
        return fos.delete('switch-controller',
                          'managed-switch',
                          mkey=filtered_data['switch-id'],
                          vdom=vdom)


def fortios_switch_controller(data, fos):
    login(data)

    if data['switch_controller_managed_switch']:
        resp = switch_controller_managed_switch(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "switch_controller_managed_switch": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "802-1X-settings": {"required": False, "type": "dict",
                                    "options": {
                                        "link-down-auth": {"required": False, "type": "str",
                                                           "choices": ["set-unauth", "no-action"]},
                                        "local-override": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]},
                                        "max-reauth-attempt": {"required": False, "type": "int"},
                                        "reauth-period": {"required": False, "type": "int"}
                                    }},
                "connected": {"required": False, "type": "int"},
                "custom-command": {"required": False, "type": "list",
                                   "options": {
                                       "command-entry": {"required": True, "type": "str"},
                                       "command-name": {"required": False, "type": "str"}
                                   }},
                "delayed-restart-trigger": {"required": False, "type": "int"},
                "description": {"required": False, "type": "str"},
                "directly-connected": {"required": False, "type": "int"},
                "dynamic-capability": {"required": False, "type": "int"},
                "dynamically-discovered": {"required": False, "type": "int"},
                "fsw-wan1-admin": {"required": False, "type": "str",
                                   "choices": ["discovered", "disable", "enable"]},
                "fsw-wan1-peer": {"required": False, "type": "str"},
                "fsw-wan2-admin": {"required": False, "type": "str",
                                   "choices": ["discovered", "disable", "enable"]},
                "fsw-wan2-peer": {"required": False, "type": "str"},
                "igmp-snooping": {"required": False, "type": "dict",
                                  "options": {
                                      "aging-time": {"required": False, "type": "int"},
                                      "flood-unknown-multicast": {"required": False, "type": "str",
                                                                  "choices": ["enable", "disable"]},
                                      "local-override": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]}
                                  }},
                "max-allowed-trunk-members": {"required": False, "type": "int"},
                "mirror": {"required": False, "type": "list",
                           "options": {
                               "dst": {"required": False, "type": "str"},
                               "name": {"required": True, "type": "str"},
                               "src-egress": {"required": False, "type": "list",
                                              "options": {
                                                  "name": {"required": True, "type": "str"}
                                              }},
                               "src-ingress": {"required": False, "type": "list",
                                               "options": {
                                                   "name": {"required": True, "type": "str"}
                                               }},
                               "status": {"required": False, "type": "str",
                                          "choices": ["active", "inactive"]},
                               "switching-packet": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]}
                           }},
                "name": {"required": False, "type": "str"},
                "owner-vdom": {"required": False, "type": "str"},
                "poe-pre-standard-detection": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                "ports": {"required": False, "type": "list",
                          "options": {
                              "allowed-vlans": {"required": False, "type": "list",
                                                "options": {
                                                    "vlan-name": {"required": True, "type": "str"}
                                                }},
                              "allowed-vlans-all": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]},
                              "arp-inspection-trust": {"required": False, "type": "str",
                                                       "choices": ["untrusted", "trusted"]},
                              "bundle": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                              "description": {"required": False, "type": "str"},
                              "dhcp-snoop-option82-trust": {"required": False, "type": "str",
                                                            "choices": ["enable", "disable"]},
                              "dhcp-snooping": {"required": False, "type": "str",
                                                "choices": ["untrusted", "trusted"]},
                              "discard-mode": {"required": False, "type": "str",
                                               "choices": ["none", "all-untagged", "all-tagged"]},
                              "edge-port": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                              "export-tags": {"required": False, "type": "list",
                                              "options": {
                                                  "tag-name": {"required": True, "type": "str"}
                                              }},
                              "export-to": {"required": False, "type": "str"},
                              "export-to-pool": {"required": False, "type": "str"},
                              "export-to-pool_flag": {"required": False, "type": "int"},
                              "fgt-peer-device-name": {"required": False, "type": "str"},
                              "fgt-peer-port-name": {"required": False, "type": "str"},
                              "fiber-port": {"required": False, "type": "int"},
                              "flags": {"required": False, "type": "int"},
                              "fortilink-port": {"required": False, "type": "int"},
                              "igmp-snooping": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                              "igmps-flood-reports": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                              "igmps-flood-traffic": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                              "isl-local-trunk-name": {"required": False, "type": "str"},
                              "isl-peer-device-name": {"required": False, "type": "str"},
                              "isl-peer-port-name": {"required": False, "type": "str"},
                              "lacp-speed": {"required": False, "type": "str",
                                             "choices": ["slow", "fast"]},
                              "learning-limit": {"required": False, "type": "int"},
                              "lldp-profile": {"required": False, "type": "str"},
                              "lldp-status": {"required": False, "type": "str",
                                              "choices": ["disable", "rx-only", "tx-only",
                                                          "tx-rx"]},
                              "loop-guard": {"required": False, "type": "str",
                                             "choices": ["enabled", "disabled"]},
                              "loop-guard-timeout": {"required": False, "type": "int"},
                              "max-bundle": {"required": False, "type": "int"},
                              "mclag": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                              "member-withdrawal-behavior": {"required": False, "type": "str",
                                                             "choices": ["forward", "block"]},
                              "members": {"required": False, "type": "list",
                                          "options": {
                                              "member-name": {"required": True, "type": "str"}
                                          }},
                              "min-bundle": {"required": False, "type": "int"},
                              "mode": {"required": False, "type": "str",
                                       "choices": ["static", "lacp-passive", "lacp-active"]},
                              "poe-capable": {"required": False, "type": "int"},
                              "poe-pre-standard-detection": {"required": False, "type": "str",
                                                             "choices": ["enable", "disable"]},
                              "poe-status": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                              "port-name": {"required": True, "type": "str"},
                              "port-number": {"required": False, "type": "int"},
                              "port-owner": {"required": False, "type": "str"},
                              "port-prefix-type": {"required": False, "type": "int"},
                              "port-security-policy": {"required": False, "type": "str"},
                              "port-selection-criteria": {"required": False, "type": "str",
                                                          "choices": ["src-mac", "dst-mac", "src-dst-mac",
                                                                      "src-ip", "dst-ip", "src-dst-ip"]},
                              "qos-policy": {"required": False, "type": "str"},
                              "sample-direction": {"required": False, "type": "str",
                                                   "choices": ["tx", "rx", "both"]},
                              "sflow-counter-interval": {"required": False, "type": "int"},
                              "sflow-sample-rate": {"required": False, "type": "int"},
                              "sflow-sampler": {"required": False, "type": "str",
                                                "choices": ["enabled", "disabled"]},
                              "speed": {"required": False, "type": "str",
                                        "choices": ["10half", "10full", "100half",
                                                    "100full", "1000auto", "1000fiber",
                                                    "1000full", "10000", "40000",
                                                    "auto", "auto-module", "100FX-half",
                                                    "100FX-full", "100000full", "2500full",
                                                    "25000full", "50000full"]},
                              "speed-mask": {"required": False, "type": "int"},
                              "stacking-port": {"required": False, "type": "int"},
                              "status": {"required": False, "type": "str",
                                         "choices": ["up", "down"]},
                              "stp-bpdu-guard": {"required": False, "type": "str",
                                                 "choices": ["enabled", "disabled"]},
                              "stp-bpdu-guard-timeout": {"required": False, "type": "int"},
                              "stp-root-guard": {"required": False, "type": "str",
                                                 "choices": ["enabled", "disabled"]},
                              "stp-state": {"required": False, "type": "str",
                                            "choices": ["enabled", "disabled"]},
                              "switch-id": {"required": False, "type": "str"},
                              "type": {"required": False, "type": "str",
                                       "choices": ["physical", "trunk"]},
                              "untagged-vlans": {"required": False, "type": "list",
                                                 "options": {
                                                     "vlan-name": {"required": True, "type": "str"}
                                                 }},
                              "virtual-port": {"required": False, "type": "int"},
                              "vlan": {"required": False, "type": "str"}
                          }},
                "pre-provisioned": {"required": False, "type": "int"},
                "staged-image-version": {"required": False, "type": "str"},
                "storm-control": {"required": False, "type": "dict",
                                  "options": {
                                      "broadcast": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]},
                                      "local-override": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]},
                                      "rate": {"required": False, "type": "int"},
                                      "unknown-multicast": {"required": False, "type": "str",
                                                            "choices": ["enable", "disable"]},
                                      "unknown-unicast": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]}
                                  }},
                "stp-settings": {"required": False, "type": "dict",
                                 "options": {
                                     "forward-time": {"required": False, "type": "int"},
                                     "hello-time": {"required": False, "type": "int"},
                                     "local-override": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                     "max-age": {"required": False, "type": "int"},
                                     "max-hops": {"required": False, "type": "int"},
                                     "name": {"required": False, "type": "str"},
                                     "pending-timer": {"required": False, "type": "int"},
                                     "revision": {"required": False, "type": "int"},
                                     "status": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]}
                                 }},
                "switch-device-tag": {"required": False, "type": "str"},
                "switch-id": {"required": True, "type": "str"},
                "switch-log": {"required": False, "type": "dict",
                               "options": {
                                   "local-override": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                   "severity": {"required": False, "type": "str",
                                                "choices": ["emergency", "alert", "critical",
                                                            "error", "warning", "notification",
                                                            "information", "debug"]},
                                   "status": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]}
                               }},
                "switch-profile": {"required": False, "type": "str"},
                "switch-stp-settings": {"required": False, "type": "dict",
                                        "options": {
                                            "status": {"required": False, "type": "str",
                                                       "choices": ["enable", "disable"]}
                                        }},
                "type": {"required": False, "type": "str",
                         "choices": ["virtual", "physical"]},
                "version": {"required": False, "type": "int"}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    global fos
    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_switch_controller(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
