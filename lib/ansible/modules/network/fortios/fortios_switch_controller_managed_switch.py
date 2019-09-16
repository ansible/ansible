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

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_switch_controller_managed_switch
short_description: Configure FortiSwitch devices that are managed by this FortiGate in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify switch_controller feature and managed_switch category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.5
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
            - FortiOS or FortiGate IP address.
        type: str
        required: false
    username:
        description:
            - FortiOS or FortiGate username.
        type: str
        required: false
    password:
        description:
            - FortiOS or FortiGate password.
        type: str
        default: ""
    vdom:
        description:
            - Virtual domain, among those defined previously. A vdom is a
              virtual instance of the FortiGate that can be configured and
              used as a different unit.
        type: str
        default: root
    https:
        description:
            - Indicates if the requests towards FortiGate must use HTTPS protocol.
        type: bool
        default: true
    ssl_verify:
        description:
            - Ensures FortiGate certificate must be verified by a proper CA.
        type: bool
        default: true
        version_added: 2.9
    state:
        description:
            - Indicates whether to create or remove the object.
              This attribute was present already in previous version in a deeper level.
              It has been moved out to this outer level.
        type: str
        required: false
        choices:
            - present
            - absent
        version_added: 2.9
    switch_controller_managed_switch:
        description:
            - Configure FortiSwitch devices that are managed by this FortiGate.
        default: null
        type: dict
        suboptions:
            state:
                description:
                    - B(Deprecated)
                    - Starting with Ansible 2.9 we recommend using the top-level 'state' parameter.
                    - HORIZONTALLINE
                    - Indicates whether to create or remove the object.
                type: str
                required: false
                choices:
                    - present
                    - absent
            802_1X_settings:
                description:
                    - Configuration method to edit FortiSwitch 802.1X global settings.
                type: dict
                suboptions:
                    link_down_auth:
                        description:
                            - Authentication state to set if a link is down.
                        type: str
                        choices:
                            - set-unauth
                            - no-action
                    local_override:
                        description:
                            - Enable to override global 802.1X settings on individual FortiSwitches.
                        type: str
                        choices:
                            - enable
                            - disable
                    max_reauth_attempt:
                        description:
                            - Maximum number of authentication attempts (0 - 15).
                        type: int
                    reauth_period:
                        description:
                            - Reauthentication time interval (1 - 1440 min).
                        type: int
            custom_command:
                description:
                    - Configuration method to edit FortiSwitch commands to be pushed to this FortiSwitch device upon rebooting the FortiGate switch controller
                       or the FortiSwitch.
                type: list
                suboptions:
                    command_entry:
                        description:
                            - List of FortiSwitch commands.
                        type: str
                    command_name:
                        description:
                            - Names of commands to be pushed to this FortiSwitch device, as configured under config switch-controller custom-command. Source
                               switch-controller.custom-command.command-name.
                        type: str
            delayed_restart_trigger:
                description:
                    - Delayed restart triggered for this FortiSwitch.
                type: int
            description:
                description:
                    - Description.
                type: str
            directly_connected:
                description:
                    - Directly connected FortiSwitch.
                type: int
            dynamic_capability:
                description:
                    - List of features this FortiSwitch supports (not configurable) that is sent to the FortiGate device for subsequent configuration
                       initiated by the FortiGate device.
                type: int
            dynamically_discovered:
                description:
                    - Dynamically discovered FortiSwitch.
                type: int
            fsw_wan1_admin:
                description:
                    - FortiSwitch WAN1 admin status; enable to authorize the FortiSwitch as a managed switch.
                type: str
                choices:
                    - discovered
                    - disable
                    - enable
            fsw_wan1_peer:
                description:
                    - Fortiswitch WAN1 peer port.
                type: str
            fsw_wan2_admin:
                description:
                    - FortiSwitch WAN2 admin status; enable to authorize the FortiSwitch as a managed switch.
                type: str
                choices:
                    - discovered
                    - disable
                    - enable
            fsw_wan2_peer:
                description:
                    - FortiSwitch WAN2 peer port.
                type: str
            igmp_snooping:
                description:
                    - Configure FortiSwitch IGMP snooping global settings.
                type: dict
                suboptions:
                    aging_time:
                        description:
                            - Maximum time to retain a multicast snooping entry for which no packets have been seen (15 - 3600 sec).
                        type: int
                    flood_unknown_multicast:
                        description:
                            - Enable/disable unknown multicast flooding.
                        type: str
                        choices:
                            - enable
                            - disable
                    local_override:
                        description:
                            - Enable/disable overriding the global IGMP snooping configuration.
                        type: str
                        choices:
                            - enable
                            - disable
            max_allowed_trunk_members:
                description:
                    - FortiSwitch maximum allowed trunk members.
                type: int
            mirror:
                description:
                    - Configuration method to edit FortiSwitch packet mirror.
                type: list
                suboptions:
                    dst:
                        description:
                            - Destination port.
                        type: str
                    name:
                        description:
                            - Mirror name.
                        required: true
                        type: str
                    src_egress:
                        description:
                            - Source egress interfaces.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Interface name.
                                required: true
                                type: str
                    src_ingress:
                        description:
                            - Source ingress interfaces.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Interface name.
                                required: true
                                type: str
                    status:
                        description:
                            - Active/inactive mirror configuration.
                        type: str
                        choices:
                            - active
                            - inactive
                    switching_packet:
                        description:
                            - Enable/disable switching functionality when mirroring.
                        type: str
                        choices:
                            - enable
                            - disable
            name:
                description:
                    - Managed-switch name.
                type: str
            owner_vdom:
                description:
                    - VDOM which owner of port belongs to.
                type: str
            poe_detection_type:
                description:
                    - PoE detection type for FortiSwitch.
                type: int
            poe_pre_standard_detection:
                description:
                    - Enable/disable PoE pre-standard detection.
                type: str
                choices:
                    - enable
                    - disable
            ports:
                description:
                    - Managed-switch port list.
                type: list
                suboptions:
                    allowed_vlans:
                        description:
                            - Configure switch port tagged vlans
                        type: list
                        suboptions:
                            vlan_name:
                                description:
                                    - VLAN name. Source system.interface.name.
                                type: str
                    allowed_vlans_all:
                        description:
                            - Enable/disable all defined vlans on this port.
                        type: str
                        choices:
                            - enable
                            - disable
                    arp_inspection_trust:
                        description:
                            - Trusted or untrusted dynamic ARP inspection.
                        type: str
                        choices:
                            - untrusted
                            - trusted
                    bundle:
                        description:
                            - Enable/disable Link Aggregation Group (LAG) bundling for non-FortiLink interfaces.
                        type: str
                        choices:
                            - enable
                            - disable
                    description:
                        description:
                            - Description for port.
                        type: str
                    dhcp_snoop_option82_trust:
                        description:
                            - Enable/disable allowance of DHCP with option-82 on untrusted interface.
                        type: str
                        choices:
                            - enable
                            - disable
                    dhcp_snooping:
                        description:
                            - Trusted or untrusted DHCP-snooping interface.
                        type: str
                        choices:
                            - untrusted
                            - trusted
                    discard_mode:
                        description:
                            - Configure discard mode for port.
                        type: str
                        choices:
                            - none
                            - all-untagged
                            - all-tagged
                    edge_port:
                        description:
                            - Enable/disable this interface as an edge port, bridging connections between workstations and/or computers.
                        type: str
                        choices:
                            - enable
                            - disable
                    export_tags:
                        description:
                            - Switch controller export tag name.
                        type: list
                        suboptions:
                            tag_name:
                                description:
                                    - Switch tag name. Source switch-controller.switch-interface-tag.name.
                                type: str
                    export_to:
                        description:
                            - Export managed-switch port to a tenant VDOM. Source system.vdom.name.
                        type: str
                    export_to_pool:
                        description:
                            - Switch controller export port to pool-list. Source switch-controller.virtual-port-pool.name.
                        type: str
                    export_to_pool_flag:
                        description:
                            - Switch controller export port to pool-list.
                        type: int
                    fgt_peer_device_name:
                        description:
                            - FGT peer device name.
                        type: str
                    fgt_peer_port_name:
                        description:
                            - FGT peer port name.
                        type: str
                    fiber_port:
                        description:
                            - Fiber-port.
                        type: int
                    flags:
                        description:
                            - Port properties flags.
                        type: int
                    fortilink_port:
                        description:
                            - FortiLink uplink port.
                        type: int
                    igmp_snooping:
                        description:
                            - Set IGMP snooping mode for the physical port interface.
                        type: str
                        choices:
                            - enable
                            - disable
                    igmps_flood_reports:
                        description:
                            - Enable/disable flooding of IGMP reports to this interface when igmp-snooping enabled.
                        type: str
                        choices:
                            - enable
                            - disable
                    igmps_flood_traffic:
                        description:
                            - Enable/disable flooding of IGMP snooping traffic to this interface.
                        type: str
                        choices:
                            - enable
                            - disable
                    isl_local_trunk_name:
                        description:
                            - ISL local trunk name.
                        type: str
                    isl_peer_device_name:
                        description:
                            - ISL peer device name.
                        type: str
                    isl_peer_port_name:
                        description:
                            - ISL peer port name.
                        type: str
                    lacp_speed:
                        description:
                            - end Link Aggregation Control Protocol (LACP) messages every 30 seconds (slow) or every second (fast).
                        type: str
                        choices:
                            - slow
                            - fast
                    learning_limit:
                        description:
                            - Limit the number of dynamic MAC addresses on this Port (1 - 128, 0 = no limit, default).
                        type: int
                    lldp_profile:
                        description:
                            - LLDP port TLV profile. Source switch-controller.lldp-profile.name.
                        type: str
                    lldp_status:
                        description:
                            - LLDP transmit and receive status.
                        type: str
                        choices:
                            - disable
                            - rx-only
                            - tx-only
                            - tx-rx
                    loop_guard:
                        description:
                            - Enable/disable loop-guard on this interface, an STP optimization used to prevent network loops.
                        type: str
                        choices:
                            - enabled
                            - disabled
                    loop_guard_timeout:
                        description:
                            - Loop-guard timeout (0 - 120 min).
                        type: int
                    max_bundle:
                        description:
                            - Maximum size of LAG bundle (1 - 24)
                        type: int
                    mclag:
                        description:
                            - Enable/disable multi-chassis link aggregation (MCLAG).
                        type: str
                        choices:
                            - enable
                            - disable
                    member_withdrawal_behavior:
                        description:
                            - Port behavior after it withdraws because of loss of control packets.
                        type: str
                        choices:
                            - forward
                            - block
                    members:
                        description:
                            - Aggregated LAG bundle interfaces.
                        type: list
                        suboptions:
                            member_name:
                                description:
                                    - Interface name from available options.
                                type: str
                    min_bundle:
                        description:
                            - Minimum size of LAG bundle (1 - 24)
                        type: int
                    mode:
                        description:
                            - "LACP mode: ignore and do not send control messages, or negotiate 802.3ad aggregation passively or actively."
                        type: str
                        choices:
                            - static
                            - lacp-passive
                            - lacp-active
                    poe_capable:
                        description:
                            - PoE capable.
                        type: int
                    poe_pre_standard_detection:
                        description:
                            - Enable/disable PoE pre-standard detection.
                        type: str
                        choices:
                            - enable
                            - disable
                    poe_status:
                        description:
                            - Enable/disable PoE status.
                        type: str
                        choices:
                            - enable
                            - disable
                    port_name:
                        description:
                            - Switch port name.
                        type: str
                    port_number:
                        description:
                            - Port number.
                        type: int
                    port_owner:
                        description:
                            - Switch port name.
                        type: str
                    port_prefix_type:
                        description:
                            - Port prefix type.
                        type: int
                    port_security_policy:
                        description:
                            - Switch controller authentication policy to apply to this managed switch from available options. Source switch-controller
                              .security-policy.802-1X.name switch-controller.security-policy.captive-portal.name.
                        type: str
                    port_selection_criteria:
                        description:
                            - Algorithm for aggregate port selection.
                        type: str
                        choices:
                            - src-mac
                            - dst-mac
                            - src-dst-mac
                            - src-ip
                            - dst-ip
                            - src-dst-ip
                    qos_policy:
                        description:
                            - Switch controller QoS policy from available options. Source switch-controller.qos.qos-policy.name.
                        type: str
                    sample_direction:
                        description:
                            - sFlow sample direction.
                        type: str
                        choices:
                            - tx
                            - rx
                            - both
                    sflow_counter_interval:
                        description:
                            - sFlow sampler counter polling interval (1 - 255 sec).
                        type: int
                    sflow_sample_rate:
                        description:
                            - sFlow sampler sample rate (0 - 99999 p/sec).
                        type: int
                    sflow_sampler:
                        description:
                            - Enable/disable sFlow protocol on this interface.
                        type: str
                        choices:
                            - enabled
                            - disabled
                    speed:
                        description:
                            - Switch port speed; default and available settings depend on hardware.
                        type: str
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
                    speed_mask:
                        description:
                            - Switch port speed mask.
                        type: int
                    stacking_port:
                        description:
                            - Stacking port.
                        type: int
                    status:
                        description:
                            - "Switch port admin status: up or down."
                        type: str
                        choices:
                            - up
                            - down
                    stp_bpdu_guard:
                        description:
                            - Enable/disable STP BPDU guard on this interface.
                        type: str
                        choices:
                            - enabled
                            - disabled
                    stp_bpdu_guard_timeout:
                        description:
                            - BPDU Guard disabling protection (0 - 120 min).
                        type: int
                    stp_root_guard:
                        description:
                            - Enable/disable STP root guard on this interface.
                        type: str
                        choices:
                            - enabled
                            - disabled
                    stp_state:
                        description:
                            - Enable/disable Spanning Tree Protocol (STP) on this interface.
                        type: str
                        choices:
                            - enabled
                            - disabled
                    switch_id:
                        description:
                            - Switch id.
                        type: str
                    type:
                        description:
                            - "Interface type: physical or trunk port."
                        type: str
                        choices:
                            - physical
                            - trunk
                    untagged_vlans:
                        description:
                            - Configure switch port untagged vlans
                        type: list
                        suboptions:
                            vlan_name:
                                description:
                                    - VLAN name. Source system.interface.name.
                                type: str
                    virtual_port:
                        description:
                            - Virtualized switch port.
                        type: int
                    vlan:
                        description:
                            - Assign switch ports to a VLAN. Source system.interface.name.
                        type: str
            pre_provisioned:
                description:
                    - Pre-provisioned managed switch.
                type: int
            staged_image_version:
                description:
                    - Staged image version for FortiSwitch.
                type: str
            storm_control:
                description:
                    - Configuration method to edit FortiSwitch storm control for measuring traffic activity using data rates to prevent traffic disruption.
                type: dict
                suboptions:
                    broadcast:
                        description:
                            - Enable/disable storm control to drop broadcast traffic.
                        type: str
                        choices:
                            - enable
                            - disable
                    local_override:
                        description:
                            - Enable to override global FortiSwitch storm control settings for this FortiSwitch.
                        type: str
                        choices:
                            - enable
                            - disable
                    rate:
                        description:
                            - Rate in packets per second at which storm traffic is controlled (1 - 10000000). Storm control drops excess traffic data rates
                               beyond this threshold.
                        type: int
                    unknown_multicast:
                        description:
                            - Enable/disable storm control to drop unknown multicast traffic.
                        type: str
                        choices:
                            - enable
                            - disable
                    unknown_unicast:
                        description:
                            - Enable/disable storm control to drop unknown unicast traffic.
                        type: str
                        choices:
                            - enable
                            - disable
            stp_settings:
                description:
                    - Configuration method to edit Spanning Tree Protocol (STP) settings used to prevent bridge loops.
                type: dict
                suboptions:
                    forward_time:
                        description:
                            - Period of time a port is in listening and learning state (4 - 30 sec).
                        type: int
                    hello_time:
                        description:
                            - Period of time between successive STP frame Bridge Protocol Data Units (BPDUs) sent on a port (1 - 10 sec).
                        type: int
                    local_override:
                        description:
                            - Enable to configure local STP settings that override global STP settings.
                        type: str
                        choices:
                            - enable
                            - disable
                    max_age:
                        description:
                            - Maximum time before a bridge port saves its configuration BPDU information (6 - 40 sec).
                        type: int
                    max_hops:
                        description:
                            - Maximum number of hops between the root bridge and the furthest bridge (1- 40).
                        type: int
                    name:
                        description:
                            - Name of local STP settings configuration.
                        type: str
                    pending_timer:
                        description:
                            - Pending time (1 - 15 sec).
                        type: int
                    revision:
                        description:
                            - STP revision number (0 - 65535).
                        type: int
                    status:
                        description:
                            - Enable/disable STP.
                        type: str
                        choices:
                            - enable
                            - disable
            switch_device_tag:
                description:
                    - User definable label/tag.
                type: str
            switch_id:
                description:
                    - Managed-switch id.
                type: str
            switch_log:
                description:
                    - Configuration method to edit FortiSwitch logging settings (logs are transferred to and inserted into the FortiGate event log).
                type: dict
                suboptions:
                    local_override:
                        description:
                            - Enable to configure local logging settings that override global logging settings.
                        type: str
                        choices:
                            - enable
                            - disable
                    severity:
                        description:
                            - Severity of FortiSwitch logs that are added to the FortiGate event log.
                        type: str
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
                        type: str
                        choices:
                            - enable
                            - disable
            switch_profile:
                description:
                    - FortiSwitch profile. Source switch-controller.switch-profile.name.
                type: str
            switch_stp_settings:
                description:
                    - Configure spanning tree protocol (STP).
                type: dict
                suboptions:
                    status:
                        description:
                            - Enable/disable STP.
                        type: str
                        choices:
                            - enable
                            - disable
            type:
                description:
                    - Indication of switch type, physical or virtual.
                type: str
                choices:
                    - virtual
                    - physical
            version:
                description:
                    - FortiSwitch version.
                type: int
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
   ssl_verify: "False"
  tasks:
  - name: Configure FortiSwitch devices that are managed by this FortiGate.
    fortios_switch_controller_managed_switch:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      switch_controller_managed_switch:
        802_1X_settings:
            link_down_auth: "set-unauth"
            local_override: "enable"
            max_reauth_attempt: "6"
            reauth_period: "7"
        custom_command:
         -
            command_entry: "<your_own_value>"
            command_name: "<your_own_value> (source switch-controller.custom-command.command-name)"
        delayed_restart_trigger: "11"
        description: "<your_own_value>"
        directly_connected: "13"
        dynamic_capability: "14"
        dynamically_discovered: "15"
        fsw_wan1_admin: "discovered"
        fsw_wan1_peer: "<your_own_value>"
        fsw_wan2_admin: "discovered"
        fsw_wan2_peer: "<your_own_value>"
        igmp_snooping:
            aging_time: "21"
            flood_unknown_multicast: "enable"
            local_override: "enable"
        max_allowed_trunk_members: "24"
        mirror:
         -
            dst: "<your_own_value>"
            name: "default_name_27"
            src_egress:
             -
                name: "default_name_29"
            src_ingress:
             -
                name: "default_name_31"
            status: "active"
            switching_packet: "enable"
        name: "default_name_34"
        owner_vdom: "<your_own_value>"
        poe_detection_type: "36"
        poe_pre_standard_detection: "enable"
        ports:
         -
            allowed_vlans:
             -
                vlan_name: "<your_own_value> (source system.interface.name)"
            allowed_vlans_all: "enable"
            arp_inspection_trust: "untrusted"
            bundle: "enable"
            description: "<your_own_value>"
            dhcp_snoop_option82_trust: "enable"
            dhcp_snooping: "untrusted"
            discard_mode: "none"
            edge_port: "enable"
            export_tags:
             -
                tag_name: "<your_own_value> (source switch-controller.switch-interface-tag.name)"
            export_to: "<your_own_value> (source system.vdom.name)"
            export_to_pool: "<your_own_value> (source switch-controller.virtual-port-pool.name)"
            export_to_pool_flag: "53"
            fgt_peer_device_name: "<your_own_value>"
            fgt_peer_port_name: "<your_own_value>"
            fiber_port: "56"
            flags: "57"
            fortilink_port: "58"
            igmp_snooping: "enable"
            igmps_flood_reports: "enable"
            igmps_flood_traffic: "enable"
            isl_local_trunk_name: "<your_own_value>"
            isl_peer_device_name: "<your_own_value>"
            isl_peer_port_name: "<your_own_value>"
            lacp_speed: "slow"
            learning_limit: "66"
            lldp_profile: "<your_own_value> (source switch-controller.lldp-profile.name)"
            lldp_status: "disable"
            loop_guard: "enabled"
            loop_guard_timeout: "70"
            max_bundle: "71"
            mclag: "enable"
            member_withdrawal_behavior: "forward"
            members:
             -
                member_name: "<your_own_value>"
            min_bundle: "76"
            mode: "static"
            poe_capable: "78"
            poe_pre_standard_detection: "enable"
            poe_status: "enable"
            port_name: "<your_own_value>"
            port_number: "82"
            port_owner: "<your_own_value>"
            port_prefix_type: "84"
            port_security_policy: "<your_own_value> (source switch-controller.security-policy.802-1X.name switch-controller.security-policy.captive-portal
              .name)"
            port_selection_criteria: "src-mac"
            qos_policy: "<your_own_value> (source switch-controller.qos.qos-policy.name)"
            sample_direction: "tx"
            sflow_counter_interval: "89"
            sflow_sample_rate: "90"
            sflow_sampler: "enabled"
            speed: "10half"
            speed_mask: "93"
            stacking_port: "94"
            status: "up"
            stp_bpdu_guard: "enabled"
            stp_bpdu_guard_timeout: "97"
            stp_root_guard: "enabled"
            stp_state: "enabled"
            switch_id: "<your_own_value>"
            type: "physical"
            untagged_vlans:
             -
                vlan_name: "<your_own_value> (source system.interface.name)"
            virtual_port: "104"
            vlan: "<your_own_value> (source system.interface.name)"
        pre_provisioned: "106"
        staged_image_version: "<your_own_value>"
        storm_control:
            broadcast: "enable"
            local_override: "enable"
            rate: "111"
            unknown_multicast: "enable"
            unknown_unicast: "enable"
        stp_settings:
            forward_time: "115"
            hello_time: "116"
            local_override: "enable"
            max_age: "118"
            max_hops: "119"
            name: "default_name_120"
            pending_timer: "121"
            revision: "122"
            status: "enable"
        switch_device_tag: "<your_own_value>"
        switch_id: "<your_own_value>"
        switch_log:
            local_override: "enable"
            severity: "emergency"
            status: "enable"
        switch_profile: "<your_own_value> (source switch-controller.switch-profile.name)"
        switch_stp_settings:
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
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortios.fortios import FortiOSHandler
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG


def login(data, fos):
    host = data['host']
    username = data['username']
    password = data['password']
    ssl_verify = data['ssl_verify']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password, verify=ssl_verify)


def filter_switch_controller_managed_switch_data(json):
    option_list = ['802_1X_settings', 'custom_command', 'delayed_restart_trigger',
                   'description', 'directly_connected', 'dynamic_capability',
                   'dynamically_discovered', 'fsw_wan1_admin', 'fsw_wan1_peer',
                   'fsw_wan2_admin', 'fsw_wan2_peer', 'igmp_snooping',
                   'max_allowed_trunk_members', 'mirror', 'name',
                   'owner_vdom', 'poe_detection_type', 'poe_pre_standard_detection',
                   'ports', 'pre_provisioned', 'staged_image_version',
                   'storm_control', 'stp_settings', 'switch_device_tag',
                   'switch_id', 'switch_log', 'switch_profile',
                   'switch_stp_settings', 'type', 'version']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def underscore_to_hyphen(data):
    if isinstance(data, list):
        for elem in data:
            elem = underscore_to_hyphen(elem)
    elif isinstance(data, dict):
        new_data = {}
        for k, v in data.items():
            new_data[k.replace('_', '-')] = underscore_to_hyphen(v)
        data = new_data

    return data


def switch_controller_managed_switch(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['switch_controller_managed_switch'] and data['switch_controller_managed_switch']:
        state = data['switch_controller_managed_switch']['state']
    else:
        state = True
    switch_controller_managed_switch_data = data['switch_controller_managed_switch']
    filtered_data = underscore_to_hyphen(filter_switch_controller_managed_switch_data(switch_controller_managed_switch_data))

    if state == "present":
        return fos.set('switch-controller',
                       'managed-switch',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('switch-controller',
                          'managed-switch',
                          mkey=filtered_data['switch-id'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_switch_controller(data, fos):

    if data['switch_controller_managed_switch']:
        resp = switch_controller_managed_switch(data, fos)

    return not is_successful_status(resp), \
        resp['status'] == "success", \
        resp


def main():
    fields = {
        "host": {"required": False, "type": "str"},
        "username": {"required": False, "type": "str"},
        "password": {"required": False, "type": "str", "default": "", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "ssl_verify": {"required": False, "type": "bool", "default": True},
        "state": {"required": False, "type": "str",
                  "choices": ["present", "absent"]},
        "switch_controller_managed_switch": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "802_1X_settings": {"required": False, "type": "dict",
                                    "options": {
                                        "link_down_auth": {"required": False, "type": "str",
                                                           "choices": ["set-unauth", "no-action"]},
                                        "local_override": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]},
                                        "max_reauth_attempt": {"required": False, "type": "int"},
                                        "reauth_period": {"required": False, "type": "int"}
                                    }},
                "custom_command": {"required": False, "type": "list",
                                   "options": {
                                       "command_entry": {"required": False, "type": "str"},
                                       "command_name": {"required": False, "type": "str"}
                                   }},
                "delayed_restart_trigger": {"required": False, "type": "int"},
                "description": {"required": False, "type": "str"},
                "directly_connected": {"required": False, "type": "int"},
                "dynamic_capability": {"required": False, "type": "int"},
                "dynamically_discovered": {"required": False, "type": "int"},
                "fsw_wan1_admin": {"required": False, "type": "str",
                                   "choices": ["discovered", "disable", "enable"]},
                "fsw_wan1_peer": {"required": False, "type": "str"},
                "fsw_wan2_admin": {"required": False, "type": "str",
                                   "choices": ["discovered", "disable", "enable"]},
                "fsw_wan2_peer": {"required": False, "type": "str"},
                "igmp_snooping": {"required": False, "type": "dict",
                                  "options": {
                                      "aging_time": {"required": False, "type": "int"},
                                      "flood_unknown_multicast": {"required": False, "type": "str",
                                                                  "choices": ["enable", "disable"]},
                                      "local_override": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]}
                                  }},
                "max_allowed_trunk_members": {"required": False, "type": "int"},
                "mirror": {"required": False, "type": "list",
                           "options": {
                               "dst": {"required": False, "type": "str"},
                               "name": {"required": True, "type": "str"},
                               "src_egress": {"required": False, "type": "list",
                                              "options": {
                                                  "name": {"required": True, "type": "str"}
                                              }},
                               "src_ingress": {"required": False, "type": "list",
                                               "options": {
                                                   "name": {"required": True, "type": "str"}
                                               }},
                               "status": {"required": False, "type": "str",
                                          "choices": ["active", "inactive"]},
                               "switching_packet": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]}
                           }},
                "name": {"required": False, "type": "str"},
                "owner_vdom": {"required": False, "type": "str"},
                "poe_detection_type": {"required": False, "type": "int"},
                "poe_pre_standard_detection": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                "ports": {"required": False, "type": "list",
                          "options": {
                              "allowed_vlans": {"required": False, "type": "list",
                                                "options": {
                                                    "vlan_name": {"required": False, "type": "str"}
                                                }},
                              "allowed_vlans_all": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]},
                              "arp_inspection_trust": {"required": False, "type": "str",
                                                       "choices": ["untrusted", "trusted"]},
                              "bundle": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                              "description": {"required": False, "type": "str"},
                              "dhcp_snoop_option82_trust": {"required": False, "type": "str",
                                                            "choices": ["enable", "disable"]},
                              "dhcp_snooping": {"required": False, "type": "str",
                                                "choices": ["untrusted", "trusted"]},
                              "discard_mode": {"required": False, "type": "str",
                                               "choices": ["none", "all-untagged", "all-tagged"]},
                              "edge_port": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                              "export_tags": {"required": False, "type": "list",
                                              "options": {
                                                  "tag_name": {"required": False, "type": "str"}
                                              }},
                              "export_to": {"required": False, "type": "str"},
                              "export_to_pool": {"required": False, "type": "str"},
                              "export_to_pool_flag": {"required": False, "type": "int"},
                              "fgt_peer_device_name": {"required": False, "type": "str"},
                              "fgt_peer_port_name": {"required": False, "type": "str"},
                              "fiber_port": {"required": False, "type": "int"},
                              "flags": {"required": False, "type": "int"},
                              "fortilink_port": {"required": False, "type": "int"},
                              "igmp_snooping": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                              "igmps_flood_reports": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                              "igmps_flood_traffic": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                              "isl_local_trunk_name": {"required": False, "type": "str"},
                              "isl_peer_device_name": {"required": False, "type": "str"},
                              "isl_peer_port_name": {"required": False, "type": "str"},
                              "lacp_speed": {"required": False, "type": "str",
                                             "choices": ["slow", "fast"]},
                              "learning_limit": {"required": False, "type": "int"},
                              "lldp_profile": {"required": False, "type": "str"},
                              "lldp_status": {"required": False, "type": "str",
                                              "choices": ["disable", "rx-only", "tx-only",
                                                          "tx-rx"]},
                              "loop_guard": {"required": False, "type": "str",
                                             "choices": ["enabled", "disabled"]},
                              "loop_guard_timeout": {"required": False, "type": "int"},
                              "max_bundle": {"required": False, "type": "int"},
                              "mclag": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                              "member_withdrawal_behavior": {"required": False, "type": "str",
                                                             "choices": ["forward", "block"]},
                              "members": {"required": False, "type": "list",
                                          "options": {
                                              "member_name": {"required": False, "type": "str"}
                                          }},
                              "min_bundle": {"required": False, "type": "int"},
                              "mode": {"required": False, "type": "str",
                                       "choices": ["static", "lacp-passive", "lacp-active"]},
                              "poe_capable": {"required": False, "type": "int"},
                              "poe_pre_standard_detection": {"required": False, "type": "str",
                                                             "choices": ["enable", "disable"]},
                              "poe_status": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                              "port_name": {"required": False, "type": "str"},
                              "port_number": {"required": False, "type": "int"},
                              "port_owner": {"required": False, "type": "str"},
                              "port_prefix_type": {"required": False, "type": "int"},
                              "port_security_policy": {"required": False, "type": "str"},
                              "port_selection_criteria": {"required": False, "type": "str",
                                                          "choices": ["src-mac", "dst-mac", "src-dst-mac",
                                                                      "src-ip", "dst-ip", "src-dst-ip"]},
                              "qos_policy": {"required": False, "type": "str"},
                              "sample_direction": {"required": False, "type": "str",
                                                   "choices": ["tx", "rx", "both"]},
                              "sflow_counter_interval": {"required": False, "type": "int"},
                              "sflow_sample_rate": {"required": False, "type": "int"},
                              "sflow_sampler": {"required": False, "type": "str",
                                                "choices": ["enabled", "disabled"]},
                              "speed": {"required": False, "type": "str",
                                        "choices": ["10half", "10full", "100half",
                                                    "100full", "1000auto", "1000fiber",
                                                    "1000full", "10000", "40000",
                                                    "auto", "auto-module", "100FX-half",
                                                    "100FX-full", "100000full", "2500full",
                                                    "25000full", "50000full"]},
                              "speed_mask": {"required": False, "type": "int"},
                              "stacking_port": {"required": False, "type": "int"},
                              "status": {"required": False, "type": "str",
                                         "choices": ["up", "down"]},
                              "stp_bpdu_guard": {"required": False, "type": "str",
                                                 "choices": ["enabled", "disabled"]},
                              "stp_bpdu_guard_timeout": {"required": False, "type": "int"},
                              "stp_root_guard": {"required": False, "type": "str",
                                                 "choices": ["enabled", "disabled"]},
                              "stp_state": {"required": False, "type": "str",
                                            "choices": ["enabled", "disabled"]},
                              "switch_id": {"required": False, "type": "str"},
                              "type": {"required": False, "type": "str",
                                       "choices": ["physical", "trunk"]},
                              "untagged_vlans": {"required": False, "type": "list",
                                                 "options": {
                                                     "vlan_name": {"required": False, "type": "str"}
                                                 }},
                              "virtual_port": {"required": False, "type": "int"},
                              "vlan": {"required": False, "type": "str"}
                          }},
                "pre_provisioned": {"required": False, "type": "int"},
                "staged_image_version": {"required": False, "type": "str"},
                "storm_control": {"required": False, "type": "dict",
                                  "options": {
                                      "broadcast": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]},
                                      "local_override": {"required": False, "type": "str",
                                                         "choices": ["enable", "disable"]},
                                      "rate": {"required": False, "type": "int"},
                                      "unknown_multicast": {"required": False, "type": "str",
                                                            "choices": ["enable", "disable"]},
                                      "unknown_unicast": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]}
                                  }},
                "stp_settings": {"required": False, "type": "dict",
                                 "options": {
                                     "forward_time": {"required": False, "type": "int"},
                                     "hello_time": {"required": False, "type": "int"},
                                     "local_override": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                     "max_age": {"required": False, "type": "int"},
                                     "max_hops": {"required": False, "type": "int"},
                                     "name": {"required": False, "type": "str"},
                                     "pending_timer": {"required": False, "type": "int"},
                                     "revision": {"required": False, "type": "int"},
                                     "status": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]}
                                 }},
                "switch_device_tag": {"required": False, "type": "str"},
                "switch_id": {"required": False, "type": "str"},
                "switch_log": {"required": False, "type": "dict",
                               "options": {
                                   "local_override": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                   "severity": {"required": False, "type": "str",
                                                "choices": ["emergency", "alert", "critical",
                                                            "error", "warning", "notification",
                                                            "information", "debug"]},
                                   "status": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]}
                               }},
                "switch_profile": {"required": False, "type": "str"},
                "switch_stp_settings": {"required": False, "type": "dict",
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

    # legacy_mode refers to using fortiosapi instead of HTTPAPI
    legacy_mode = 'host' in module.params and module.params['host'] is not None and \
                  'username' in module.params and module.params['username'] is not None and \
                  'password' in module.params and module.params['password'] is not None

    if not legacy_mode:
        if module._socket_path:
            connection = Connection(module._socket_path)
            fos = FortiOSHandler(connection)

            is_error, has_changed, result = fortios_switch_controller(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_switch_controller(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
