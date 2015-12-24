#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Matt Hite <mhite@hotmail.com>
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
module: bigip_facts
short_description: "Collect facts from F5 BIG-IP devices"
description:
    - "Collect facts from F5 BIG-IP devices via iControl SOAP API"
version_added: "1.6"
author: "Matt Hite (@mhite)" 
notes:
    - "Requires BIG-IP software version >= 11.4"
    - "F5 developed module 'bigsuds' required (see http://devcentral.f5.com)"
    - "Best run as a local_action in your playbook"
    - "Tested with manager and above account privilege level"

requirements:
    - bigsuds
options:
    server:
        description:
            - BIG-IP host
        required: true
        default: null
        choices: []
        aliases: []
    user:
        description:
            - BIG-IP username
        required: true
        default: null
        choices: []
        aliases: []
    password:
        description:
            - BIG-IP password
        required: true
        default: null
        choices: []
        aliases: []
    validate_certs:
        description:
            - If C(no), SSL certificates will not be validated. This should only be used
              on personally controlled sites.  Prior to 2.0, this module would always
              validate on python >= 2.7.9 and never validate on python <= 2.7.8
        required: false
        default: 'yes'
        choices: ['yes', 'no']
        version_added: 2.0
    session:
        description:
            - BIG-IP session support; may be useful to avoid concurrency
              issues in certain circumstances.
        required: false
        default: true
        choices: []
        aliases: []
    include:
        description:
            - Fact category or list of categories to collect
        required: true
        default: null
        choices: ['address_class', 'certificate', 'client_ssl_profile',
                  'device', 'device_group', 'interface', 'key', 'node', 'pool',
                  'rule', 'self_ip', 'software', 'system_info', 'traffic_group',
                  'trunk', 'virtual_address', 'virtual_server', 'vlan']
        aliases: []
    filter:
        description:
            - Shell-style glob matching string used to filter fact keys. Not
              applicable for software and system_info fact categories.
        required: false
        default: null
        choices: []
        aliases: []
'''

EXAMPLES = '''

## playbook task examples:

---
# file bigip-test.yml
# ...
- hosts: bigip-test
  tasks:
  - name: Collect BIG-IP facts
    local_action: >
      bigip_facts
      server=lb.mydomain.com
      user=admin
      password=mysecret
      include=interface,vlan

'''

try:
    import bigsuds
    from suds import MethodNotFound, WebFault
except ImportError:
    bigsuds_found = False
else:
    bigsuds_found = True

import fnmatch
import traceback
import re

# ===========================================
# bigip_facts module specific support methods.
#

class F5(object):
    """F5 iControl class.

    F5 BIG-IP iControl API class.

    Attributes:
        api: iControl API instance.
    """

    def __init__(self, host, user, password, session=False, validate_certs=True):
        self.api = bigip_api(host, user, password, validate_certs)
        if session:
            self.start_session()

    def start_session(self):
        self.api = self.api.with_session_id()

    def get_api(self):
        return self.api

    def set_recursive_query_state(self, state):
        self.api.System.Session.set_recursive_query_state(state)

    def get_recursive_query_state(self):
        return self.api.System.Session.get_recursive_query_state()

    def enable_recursive_query_state(self):
        self.set_recursive_query_state('STATE_ENABLED')

    def disable_recursive_query_state(self):
        self.set_recursive_query_state('STATE_DISABLED')

    def set_active_folder(self, folder):
        self.api.System.Session.set_active_folder(folder=folder)

    def get_active_folder(self):
        return self.api.System.Session.get_active_folder()


class Interfaces(object):
    """Interfaces class.

    F5 BIG-IP interfaces class.

    Attributes:
        api: iControl API instance.
        interfaces: A list of BIG-IP interface names.
    """

    def __init__(self, api, regex=None):
        self.api = api
        self.interfaces = api.Networking.Interfaces.get_list()
        if regex:
            re_filter = re.compile(regex)
            self.interfaces = filter(re_filter.search, self.interfaces)

    def get_list(self):
        return self.interfaces

    def get_active_media(self):
        return self.api.Networking.Interfaces.get_active_media(self.interfaces)

    def get_actual_flow_control(self):
        return self.api.Networking.Interfaces.get_actual_flow_control(self.interfaces)

    def get_bundle_state(self):
        return self.api.Networking.Interfaces.get_bundle_state(self.interfaces)

    def get_description(self):
        return self.api.Networking.Interfaces.get_description(self.interfaces)

    def get_dual_media_state(self):
        return self.api.Networking.Interfaces.get_dual_media_state(self.interfaces)

    def get_enabled_state(self):
        return self.api.Networking.Interfaces.get_enabled_state(self.interfaces)

    def get_if_index(self):
        return self.api.Networking.Interfaces.get_if_index(self.interfaces)

    def get_learning_mode(self):
        return self.api.Networking.Interfaces.get_learning_mode(self.interfaces)

    def get_lldp_admin_status(self):
        return self.api.Networking.Interfaces.get_lldp_admin_status(self.interfaces)

    def get_lldp_tlvmap(self):
        return self.api.Networking.Interfaces.get_lldp_tlvmap(self.interfaces)

    def get_mac_address(self):
        return self.api.Networking.Interfaces.get_mac_address(self.interfaces)

    def get_media(self):
        return self.api.Networking.Interfaces.get_media(self.interfaces)

    def get_media_option(self):
        return self.api.Networking.Interfaces.get_media_option(self.interfaces)

    def get_media_option_sfp(self):
        return self.api.Networking.Interfaces.get_media_option_sfp(self.interfaces)

    def get_media_sfp(self):
        return self.api.Networking.Interfaces.get_media_sfp(self.interfaces)

    def get_media_speed(self):
        return self.api.Networking.Interfaces.get_media_speed(self.interfaces)

    def get_media_status(self):
        return self.api.Networking.Interfaces.get_media_status(self.interfaces)

    def get_mtu(self):
        return self.api.Networking.Interfaces.get_mtu(self.interfaces)

    def get_phy_master_slave_mode(self):
        return self.api.Networking.Interfaces.get_phy_master_slave_mode(self.interfaces)

    def get_prefer_sfp_state(self):
        return self.api.Networking.Interfaces.get_prefer_sfp_state(self.interfaces)

    def get_flow_control(self):
        return self.api.Networking.Interfaces.get_requested_flow_control(self.interfaces)

    def get_sflow_poll_interval(self):
        return self.api.Networking.Interfaces.get_sflow_poll_interval(self.interfaces)

    def get_sflow_poll_interval_global(self):
        return self.api.Networking.Interfaces.get_sflow_poll_interval_global(self.interfaces)

    def get_sfp_media_state(self):
        return self.api.Networking.Interfaces.get_sfp_media_state(self.interfaces)

    def get_stp_active_edge_port_state(self):
        return self.api.Networking.Interfaces.get_stp_active_edge_port_state(self.interfaces)

    def get_stp_enabled_state(self):
        return self.api.Networking.Interfaces.get_stp_enabled_state(self.interfaces)

    def get_stp_link_type(self):
        return self.api.Networking.Interfaces.get_stp_link_type(self.interfaces)

    def get_stp_protocol_detection_reset_state(self):
        return self.api.Networking.Interfaces.get_stp_protocol_detection_reset_state(self.interfaces)


class SelfIPs(object):
    """Self IPs class.

    F5 BIG-IP Self IPs class.

    Attributes:
        api: iControl API instance.
        self_ips: List of self IPs.
    """

    def __init__(self, api, regex=None):
        self.api = api
        self.self_ips = api.Networking.SelfIPV2.get_list()
        if regex:
            re_filter = re.compile(regex)
            self.self_ips = filter(re_filter.search, self.self_ips)

    def get_list(self):
        return self.self_ips

    def get_address(self):
        return self.api.Networking.SelfIPV2.get_address(self.self_ips)

    def get_allow_access_list(self):
        return self.api.Networking.SelfIPV2.get_allow_access_list(self.self_ips)

    def get_description(self):
        return self.api.Networking.SelfIPV2.get_description(self.self_ips)

    def get_enforced_firewall_policy(self):
        return self.api.Networking.SelfIPV2.get_enforced_firewall_policy(self.self_ips)

    def get_floating_state(self):
        return self.api.Networking.SelfIPV2.get_floating_state(self.self_ips)

    def get_fw_rule(self):
        return self.api.Networking.SelfIPV2.get_fw_rule(self.self_ips)

    def get_netmask(self):
        return self.api.Networking.SelfIPV2.get_netmask(self.self_ips)

    def get_staged_firewall_policy(self):
        return self.api.Networking.SelfIPV2.get_staged_firewall_policy(self.self_ips)

    def get_traffic_group(self):
        return self.api.Networking.SelfIPV2.get_traffic_group(self.self_ips)

    def get_vlan(self):
        return self.api.Networking.SelfIPV2.get_vlan(self.self_ips)

    def get_is_traffic_group_inherited(self):
        return self.api.Networking.SelfIPV2.is_traffic_group_inherited(self.self_ips)


class Trunks(object):
    """Trunks class.

    F5 BIG-IP trunks class.

    Attributes:
        api: iControl API instance.
        trunks: List of trunks.
    """

    def __init__(self, api, regex=None):
        self.api = api
        self.trunks = api.Networking.Trunk.get_list()
        if regex:
            re_filter = re.compile(regex)
            self.trunks = filter(re_filter.search, self.trunks)

    def get_list(self):
        return self.trunks

    def get_active_lacp_state(self):
        return self.api.Networking.Trunk.get_active_lacp_state(self.trunks)

    def get_configured_member_count(self):
        return self.api.Networking.Trunk.get_configured_member_count(self.trunks)

    def get_description(self):
        return self.api.Networking.Trunk.get_description(self.trunks)

    def get_distribution_hash_option(self):
        return self.api.Networking.Trunk.get_distribution_hash_option(self.trunks)

    def get_interface(self):
        return self.api.Networking.Trunk.get_interface(self.trunks)

    def get_lacp_enabled_state(self):
        return self.api.Networking.Trunk.get_lacp_enabled_state(self.trunks)

    def get_lacp_timeout_option(self):
        return self.api.Networking.Trunk.get_lacp_timeout_option(self.trunks)

    def get_link_selection_policy(self):
        return self.api.Networking.Trunk.get_link_selection_policy(self.trunks)

    def get_media_speed(self):
        return self.api.Networking.Trunk.get_media_speed(self.trunks)

    def get_media_status(self):
        return self.api.Networking.Trunk.get_media_status(self.trunks)

    def get_operational_member_count(self):
        return self.api.Networking.Trunk.get_operational_member_count(self.trunks)

    def get_stp_enabled_state(self):
        return self.api.Networking.Trunk.get_stp_enabled_state(self.trunks)

    def get_stp_protocol_detection_reset_state(self):
        return self.api.Networking.Trunk.get_stp_protocol_detection_reset_state(self.trunks)


class Vlans(object):
    """Vlans class.

    F5 BIG-IP Vlans class.

    Attributes:
        api: iControl API instance.
        vlans: List of VLANs.
    """

    def __init__(self, api, regex=None):
        self.api = api
        self.vlans = api.Networking.VLAN.get_list()
        if regex:
            re_filter = re.compile(regex)
            self.vlans = filter(re_filter.search, self.vlans)

    def get_list(self):
        return self.vlans

    def get_auto_lasthop(self):
        return self.api.Networking.VLAN.get_auto_lasthop(self.vlans)

    def get_cmp_hash_algorithm(self):
        return self.api.Networking.VLAN.get_cmp_hash_algorithm(self.vlans)

    def get_description(self):
        return self.api.Networking.VLAN.get_description(self.vlans)

    def get_dynamic_forwarding(self):
        return self.api.Networking.VLAN.get_dynamic_forwarding(self.vlans)

    def get_failsafe_action(self):
        return self.api.Networking.VLAN.get_failsafe_action(self.vlans)

    def get_failsafe_state(self):
        return self.api.Networking.VLAN.get_failsafe_state(self.vlans)

    def get_failsafe_timeout(self):
        return self.api.Networking.VLAN.get_failsafe_timeout(self.vlans)

    def get_if_index(self):
        return self.api.Networking.VLAN.get_if_index(self.vlans)

    def get_learning_mode(self):
        return self.api.Networking.VLAN.get_learning_mode(self.vlans)

    def get_mac_masquerade_address(self):
        return self.api.Networking.VLAN.get_mac_masquerade_address(self.vlans)

    def get_member(self):
        return self.api.Networking.VLAN.get_member(self.vlans)

    def get_mtu(self):
        return self.api.Networking.VLAN.get_mtu(self.vlans)

    def get_sflow_poll_interval(self):
        return self.api.Networking.VLAN.get_sflow_poll_interval(self.vlans)

    def get_sflow_poll_interval_global(self):
        return self.api.Networking.VLAN.get_sflow_poll_interval_global(self.vlans)

    def get_sflow_sampling_rate(self):
        return self.api.Networking.VLAN.get_sflow_sampling_rate(self.vlans)

    def get_sflow_sampling_rate_global(self):
        return self.api.Networking.VLAN.get_sflow_sampling_rate_global(self.vlans)

    def get_source_check_state(self):
        return self.api.Networking.VLAN.get_source_check_state(self.vlans)

    def get_true_mac_address(self):
        return self.api.Networking.VLAN.get_true_mac_address(self.vlans)

    def get_vlan_id(self):
        return self.api.Networking.VLAN.get_vlan_id(self.vlans)


class Software(object):
    """Software class.

    F5 BIG-IP software class.

    Attributes:
        api: iControl API instance.
    """

    def __init__(self, api):
        self.api = api

    def get_all_software_status(self):
        return self.api.System.SoftwareManagement.get_all_software_status()


class VirtualServers(object):
    """Virtual servers class.

    F5 BIG-IP virtual servers class.

    Attributes:
        api: iControl API instance.
        virtual_servers: List of virtual servers.
    """

    def __init__(self, api, regex=None):
        self.api = api
        self.virtual_servers = api.LocalLB.VirtualServer.get_list()
        if regex:
            re_filter = re.compile(regex)
            self.virtual_servers = filter(re_filter.search, self.virtual_servers)

    def get_list(self):
        return self.virtual_servers

    def get_actual_hardware_acceleration(self):
        return self.api.LocalLB.VirtualServer.get_actual_hardware_acceleration(self.virtual_servers)

    def get_authentication_profile(self):
        return self.api.LocalLB.VirtualServer.get_authentication_profile(self.virtual_servers)

    def get_auto_lasthop(self):
        return self.api.LocalLB.VirtualServer.get_auto_lasthop(self.virtual_servers)

    def get_bw_controller_policy(self):
        return self.api.LocalLB.VirtualServer.get_bw_controller_policy(self.virtual_servers)

    def get_clone_pool(self):
        return self.api.LocalLB.VirtualServer.get_clone_pool(self.virtual_servers)

    def get_cmp_enable_mode(self):
        return self.api.LocalLB.VirtualServer.get_cmp_enable_mode(self.virtual_servers)

    def get_connection_limit(self):
        return self.api.LocalLB.VirtualServer.get_connection_limit(self.virtual_servers)

    def get_connection_mirror_state(self):
        return self.api.LocalLB.VirtualServer.get_connection_mirror_state(self.virtual_servers)

    def get_default_pool_name(self):
        return self.api.LocalLB.VirtualServer.get_default_pool_name(self.virtual_servers)

    def get_description(self):
        return self.api.LocalLB.VirtualServer.get_description(self.virtual_servers)

    def get_destination(self):
        return self.api.LocalLB.VirtualServer.get_destination_v2(self.virtual_servers)

    def get_enabled_state(self):
        return self.api.LocalLB.VirtualServer.get_enabled_state(self.virtual_servers)

    def get_enforced_firewall_policy(self):
        return self.api.LocalLB.VirtualServer.get_enforced_firewall_policy(self.virtual_servers)

    def get_fallback_persistence_profile(self):
        return self.api.LocalLB.VirtualServer.get_fallback_persistence_profile(self.virtual_servers)

    def get_fw_rule(self):
        return self.api.LocalLB.VirtualServer.get_fw_rule(self.virtual_servers)

    def get_gtm_score(self):
        return self.api.LocalLB.VirtualServer.get_gtm_score(self.virtual_servers)

    def get_last_hop_pool(self):
        return self.api.LocalLB.VirtualServer.get_last_hop_pool(self.virtual_servers)

    def get_nat64_state(self):
        return self.api.LocalLB.VirtualServer.get_nat64_state(self.virtual_servers)

    def get_object_status(self):
        return self.api.LocalLB.VirtualServer.get_object_status(self.virtual_servers)

    def get_persistence_profile(self):
        return self.api.LocalLB.VirtualServer.get_persistence_profile(self.virtual_servers)

    def get_profile(self):
        return self.api.LocalLB.VirtualServer.get_profile(self.virtual_servers)

    def get_protocol(self):
        return self.api.LocalLB.VirtualServer.get_protocol(self.virtual_servers)

    def get_rate_class(self):
        return self.api.LocalLB.VirtualServer.get_rate_class(self.virtual_servers)

    def get_rate_limit(self):
        return self.api.LocalLB.VirtualServer.get_rate_limit(self.virtual_servers)

    def get_rate_limit_destination_mask(self):
        return self.api.LocalLB.VirtualServer.get_rate_limit_destination_mask(self.virtual_servers)

    def get_rate_limit_mode(self):
        return self.api.LocalLB.VirtualServer.get_rate_limit_mode(self.virtual_servers)

    def get_rate_limit_source_mask(self):
        return self.api.LocalLB.VirtualServer.get_rate_limit_source_mask(self.virtual_servers)

    def get_related_rule(self):
        return self.api.LocalLB.VirtualServer.get_related_rule(self.virtual_servers)

    def get_rule(self):
        return self.api.LocalLB.VirtualServer.get_rule(self.virtual_servers)

    def get_security_log_profile(self):
        return self.api.LocalLB.VirtualServer.get_security_log_profile(self.virtual_servers)

    def get_snat_pool(self):
        return self.api.LocalLB.VirtualServer.get_snat_pool(self.virtual_servers)

    def get_snat_type(self):
        return self.api.LocalLB.VirtualServer.get_snat_type(self.virtual_servers)

    def get_source_address(self):
        return self.api.LocalLB.VirtualServer.get_source_address(self.virtual_servers)

    def get_source_address_translation_lsn_pool(self):
        return self.api.LocalLB.VirtualServer.get_source_address_translation_lsn_pool(self.virtual_servers)

    def get_source_address_translation_snat_pool(self):
        return self.api.LocalLB.VirtualServer.get_source_address_translation_snat_pool(self.virtual_servers)

    def get_source_address_translation_type(self):
        return self.api.LocalLB.VirtualServer.get_source_address_translation_type(self.virtual_servers)

    def get_source_port_behavior(self):
        return self.api.LocalLB.VirtualServer.get_source_port_behavior(self.virtual_servers)

    def get_staged_firewall_policy(self):
        return self.api.LocalLB.VirtualServer.get_staged_firewall_policy(self.virtual_servers)

    def get_translate_address_state(self):
        return self.api.LocalLB.VirtualServer.get_translate_address_state(self.virtual_servers)

    def get_translate_port_state(self):
        return self.api.LocalLB.VirtualServer.get_translate_port_state(self.virtual_servers)

    def get_type(self):
        return self.api.LocalLB.VirtualServer.get_type(self.virtual_servers)

    def get_vlan(self):
        return self.api.LocalLB.VirtualServer.get_vlan(self.virtual_servers)

    def get_wildmask(self):
        return self.api.LocalLB.VirtualServer.get_wildmask(self.virtual_servers)


class Pools(object):
    """Pools class.

    F5 BIG-IP pools class.

    Attributes:
        api: iControl API instance.
        pool_names: List of pool names.
    """

    def __init__(self, api, regex=None):
        self.api = api
        self.pool_names = api.LocalLB.Pool.get_list()
        if regex:
            re_filter = re.compile(regex)
            self.pool_names = filter(re_filter.search, self.pool_names)

    def get_list(self):
        return self.pool_names

    def get_action_on_service_down(self):
        return self.api.LocalLB.Pool.get_action_on_service_down(self.pool_names)

    def get_active_member_count(self):
        return self.api.LocalLB.Pool.get_active_member_count(self.pool_names)

    def get_aggregate_dynamic_ratio(self):
        return self.api.LocalLB.Pool.get_aggregate_dynamic_ratio(self.pool_names)

    def get_allow_nat_state(self):
        return self.api.LocalLB.Pool.get_allow_nat_state(self.pool_names)

    def get_allow_snat_state(self):
        return self.api.LocalLB.Pool.get_allow_snat_state(self.pool_names)

    def get_client_ip_tos(self):
        return self.api.LocalLB.Pool.get_client_ip_tos(self.pool_names)

    def get_client_link_qos(self):
        return self.api.LocalLB.Pool.get_client_link_qos(self.pool_names)

    def get_description(self):
        return self.api.LocalLB.Pool.get_description(self.pool_names)

    def get_gateway_failsafe_device(self):
        return self.api.LocalLB.Pool.get_gateway_failsafe_device(self.pool_names)

    def get_ignore_persisted_weight_state(self):
        return self.api.LocalLB.Pool.get_ignore_persisted_weight_state(self.pool_names)

    def get_lb_method(self):
        return self.api.LocalLB.Pool.get_lb_method(self.pool_names)

    def get_member(self):
        return self.api.LocalLB.Pool.get_member_v2(self.pool_names)

    def get_minimum_active_member(self):
        return self.api.LocalLB.Pool.get_minimum_active_member(self.pool_names)

    def get_minimum_up_member(self):
        return self.api.LocalLB.Pool.get_minimum_up_member(self.pool_names)

    def get_minimum_up_member_action(self):
        return self.api.LocalLB.Pool.get_minimum_up_member_action(self.pool_names)

    def get_minimum_up_member_enabled_state(self):
        return self.api.LocalLB.Pool.get_minimum_up_member_enabled_state(self.pool_names)

    def get_monitor_association(self):
        return self.api.LocalLB.Pool.get_monitor_association(self.pool_names)

    def get_monitor_instance(self):
        return self.api.LocalLB.Pool.get_monitor_instance(self.pool_names)

    def get_object_status(self):
        return self.api.LocalLB.Pool.get_object_status(self.pool_names)

    def get_profile(self):
        return self.api.LocalLB.Pool.get_profile(self.pool_names)

    def get_queue_depth_limit(self):
        return self.api.LocalLB.Pool.get_queue_depth_limit(self.pool_names)

    def get_queue_on_connection_limit_state(self):
        return self.api.LocalLB.Pool.get_queue_on_connection_limit_state(self.pool_names)

    def get_queue_time_limit(self):
        return self.api.LocalLB.Pool.get_queue_time_limit(self.pool_names)

    def get_reselect_tries(self):
        return self.api.LocalLB.Pool.get_reselect_tries(self.pool_names)

    def get_server_ip_tos(self):
        return self.api.LocalLB.Pool.get_server_ip_tos(self.pool_names)

    def get_server_link_qos(self):
        return self.api.LocalLB.Pool.get_server_link_qos(self.pool_names)

    def get_simple_timeout(self):
        return self.api.LocalLB.Pool.get_simple_timeout(self.pool_names)

    def get_slow_ramp_time(self):
        return self.api.LocalLB.Pool.get_slow_ramp_time(self.pool_names)


class Devices(object):
    """Devices class.

    F5 BIG-IP devices class.

    Attributes:
        api: iControl API instance.
        devices: List of devices.
    """

    def __init__(self, api, regex=None):
        self.api = api
        self.devices = api.Management.Device.get_list()
        if regex:
            re_filter = re.compile(regex)
            self.devices = filter(re_filter.search, self.devices)

    def get_list(self):
        return self.devices

    def get_active_modules(self):
        return self.api.Management.Device.get_active_modules(self.devices)

    def get_base_mac_address(self):
        return self.api.Management.Device.get_base_mac_address(self.devices)

    def get_blade_addresses(self):
        return self.api.Management.Device.get_blade_addresses(self.devices)

    def get_build(self):
        return self.api.Management.Device.get_build(self.devices)

    def get_chassis_id(self):
        return self.api.Management.Device.get_chassis_id(self.devices)

    def get_chassis_type(self):
        return self.api.Management.Device.get_chassis_type(self.devices)

    def get_comment(self):
        return self.api.Management.Device.get_comment(self.devices)

    def get_configsync_address(self):
        return self.api.Management.Device.get_configsync_address(self.devices)

    def get_contact(self):
        return self.api.Management.Device.get_contact(self.devices)

    def get_description(self):
        return self.api.Management.Device.get_description(self.devices)

    def get_edition(self):
        return self.api.Management.Device.get_edition(self.devices)

    def get_failover_state(self):
        return self.api.Management.Device.get_failover_state(self.devices)

    def get_local_device(self):
        return self.api.Management.Device.get_local_device()

    def get_hostname(self):
        return self.api.Management.Device.get_hostname(self.devices)

    def get_inactive_modules(self):
        return self.api.Management.Device.get_inactive_modules(self.devices)

    def get_location(self):
        return self.api.Management.Device.get_location(self.devices)

    def get_management_address(self):
        return self.api.Management.Device.get_management_address(self.devices)

    def get_marketing_name(self):
        return self.api.Management.Device.get_marketing_name(self.devices)

    def get_multicast_address(self):
        return self.api.Management.Device.get_multicast_address(self.devices)

    def get_optional_modules(self):
        return self.api.Management.Device.get_optional_modules(self.devices)

    def get_platform_id(self):
        return self.api.Management.Device.get_platform_id(self.devices)

    def get_primary_mirror_address(self):
        return self.api.Management.Device.get_primary_mirror_address(self.devices)

    def get_product(self):
        return self.api.Management.Device.get_product(self.devices)

    def get_secondary_mirror_address(self):
        return self.api.Management.Device.get_secondary_mirror_address(self.devices)

    def get_software_version(self):
        return self.api.Management.Device.get_software_version(self.devices)

    def get_timelimited_modules(self):
        return self.api.Management.Device.get_timelimited_modules(self.devices)

    def get_timezone(self):
        return self.api.Management.Device.get_timezone(self.devices)

    def get_unicast_addresses(self):
        return self.api.Management.Device.get_unicast_addresses(self.devices)


class DeviceGroups(object):
    """Device groups class.

    F5 BIG-IP device groups class.

    Attributes:
        api: iControl API instance.
        device_groups: List of device groups.
    """

    def __init__(self, api, regex=None):
        self.api = api
        self.device_groups = api.Management.DeviceGroup.get_list()
        if regex:
            re_filter = re.compile(regex)
            self.device_groups = filter(re_filter.search, self.device_groups)

    def get_list(self):
        return self.device_groups

    def get_all_preferred_active(self):
        return self.api.Management.DeviceGroup.get_all_preferred_active(self.device_groups)

    def get_autosync_enabled_state(self):
        return self.api.Management.DeviceGroup.get_autosync_enabled_state(self.device_groups)

    def get_description(self):
        return self.api.Management.DeviceGroup.get_description(self.device_groups)

    def get_device(self):
        return self.api.Management.DeviceGroup.get_device(self.device_groups)

    def get_full_load_on_sync_state(self):
        return self.api.Management.DeviceGroup.get_full_load_on_sync_state(self.device_groups)

    def get_incremental_config_sync_size_maximum(self):
        return self.api.Management.DeviceGroup.get_incremental_config_sync_size_maximum(self.device_groups)

    def get_network_failover_enabled_state(self):
        return self.api.Management.DeviceGroup.get_network_failover_enabled_state(self.device_groups)

    def get_sync_status(self):
        return self.api.Management.DeviceGroup.get_sync_status(self.device_groups)

    def get_type(self):
        return self.api.Management.DeviceGroup.get_type(self.device_groups)


class TrafficGroups(object):
    """Traffic groups class.

    F5 BIG-IP traffic groups class.

    Attributes:
        api: iControl API instance.
        traffic_groups: List of traffic groups.
    """

    def __init__(self, api, regex=None):
        self.api = api
        self.traffic_groups = api.Management.TrafficGroup.get_list()
        if regex:
            re_filter = re.compile(regex)
            self.traffic_groups = filter(re_filter.search, self.traffic_groups)

    def get_list(self):
        return self.traffic_groups

    def get_auto_failback_enabled_state(self):
        return self.api.Management.TrafficGroup.get_auto_failback_enabled_state(self.traffic_groups)

    def get_auto_failback_time(self):
        return self.api.Management.TrafficGroup.get_auto_failback_time(self.traffic_groups)

    def get_default_device(self):
        return self.api.Management.TrafficGroup.get_default_device(self.traffic_groups)

    def get_description(self):
        return self.api.Management.TrafficGroup.get_description(self.traffic_groups)

    def get_ha_load_factor(self):
        return self.api.Management.TrafficGroup.get_ha_load_factor(self.traffic_groups)

    def get_ha_order(self):
        return self.api.Management.TrafficGroup.get_ha_order(self.traffic_groups)

    def get_is_floating(self):
        return self.api.Management.TrafficGroup.get_is_floating(self.traffic_groups)

    def get_mac_masquerade_address(self):
        return self.api.Management.TrafficGroup.get_mac_masquerade_address(self.traffic_groups)

    def get_unit_id(self):
        return self.api.Management.TrafficGroup.get_unit_id(self.traffic_groups)


class Rules(object):
    """Rules class.

    F5 BIG-IP iRules class.

    Attributes:
        api: iControl API instance.
        rules: List of iRules.
    """

    def __init__(self, api, regex=None):
        self.api = api
        self.rules = api.LocalLB.Rule.get_list()
        if regex:
            re_filter = re.compile(regex)
            self.traffic_groups = filter(re_filter.search, self.rules)

    def get_list(self):
        return self.rules

    def get_description(self):
        return self.api.LocalLB.Rule.get_description(rule_names=self.rules)

    def get_ignore_vertification(self):
        return self.api.LocalLB.Rule.get_ignore_vertification(rule_names=self.rules)

    def get_verification_status(self):
        return self.api.LocalLB.Rule.get_verification_status_v2(rule_names=self.rules)

    def get_definition(self):
        return [x['rule_definition'] for x in self.api.LocalLB.Rule.query_rule(rule_names=self.rules)]

class Nodes(object):
    """Nodes class.

    F5 BIG-IP nodes class.

    Attributes:
        api: iControl API instance.
        nodes: List of nodes.
    """

    def __init__(self, api, regex=None):
        self.api = api
        self.nodes = api.LocalLB.NodeAddressV2.get_list()
        if regex:
            re_filter = re.compile(regex)
            self.nodes = filter(re_filter.search, self.nodes)

    def get_list(self):
        return self.nodes

    def get_address(self):
        return self.api.LocalLB.NodeAddressV2.get_address(nodes=self.nodes)

    def get_connection_limit(self):
        return self.api.LocalLB.NodeAddressV2.get_connection_limit(nodes=self.nodes)

    def get_description(self):
        return self.api.LocalLB.NodeAddressV2.get_description(nodes=self.nodes)

    def get_dynamic_ratio(self):
        return self.api.LocalLB.NodeAddressV2.get_dynamic_ratio_v2(nodes=self.nodes)

    def get_monitor_instance(self):
        return self.api.LocalLB.NodeAddressV2.get_monitor_instance(nodes=self.nodes)

    def get_monitor_rule(self):
        return self.api.LocalLB.NodeAddressV2.get_monitor_rule(nodes=self.nodes)

    def get_monitor_status(self):
        return self.api.LocalLB.NodeAddressV2.get_monitor_status(nodes=self.nodes)

    def get_object_status(self):
        return self.api.LocalLB.NodeAddressV2.get_object_status(nodes=self.nodes)

    def get_rate_limit(self):
        return self.api.LocalLB.NodeAddressV2.get_rate_limit(nodes=self.nodes)

    def get_ratio(self):
        return self.api.LocalLB.NodeAddressV2.get_ratio(nodes=self.nodes)

    def get_session_status(self):
        return self.api.LocalLB.NodeAddressV2.get_session_status(nodes=self.nodes)


class VirtualAddresses(object):
    """Virtual addresses class.

    F5 BIG-IP virtual addresses class.

    Attributes:
        api: iControl API instance.
        virtual_addresses: List of virtual addresses.
    """

    def __init__(self, api, regex=None):
        self.api = api
        self.virtual_addresses = api.LocalLB.VirtualAddressV2.get_list()
        if regex:
            re_filter = re.compile(regex)
            self.virtual_addresses = filter(re_filter.search, self.virtual_addresses)

    def get_list(self):
        return self.virtual_addresses

    def get_address(self):
        return self.api.LocalLB.VirtualAddressV2.get_address(self.virtual_addresses)

    def get_arp_state(self):
        return self.api.LocalLB.VirtualAddressV2.get_arp_state(self.virtual_addresses)

    def get_auto_delete_state(self):
        return self.api.LocalLB.VirtualAddressV2.get_auto_delete_state(self.virtual_addresses)

    def get_connection_limit(self):
        return self.api.LocalLB.VirtualAddressV2.get_connection_limit(self.virtual_addresses)

    def get_description(self):
        return self.api.LocalLB.VirtualAddressV2.get_description(self.virtual_addresses)

    def get_enabled_state(self):
        return self.api.LocalLB.VirtualAddressV2.get_enabled_state(self.virtual_addresses)

    def get_icmp_echo_state(self):
        return self.api.LocalLB.VirtualAddressV2.get_icmp_echo_state(self.virtual_addresses)

    def get_is_floating_state(self):
        return self.api.LocalLB.VirtualAddressV2.get_is_floating_state(self.virtual_addresses)

    def get_netmask(self):
        return self.api.LocalLB.VirtualAddressV2.get_netmask(self.virtual_addresses)

    def get_object_status(self):
        return self.api.LocalLB.VirtualAddressV2.get_object_status(self.virtual_addresses)

    def get_route_advertisement_state(self):
        return self.api.LocalLB.VirtualAddressV2.get_route_advertisement_state(self.virtual_addresses)

    def get_traffic_group(self):
        return self.api.LocalLB.VirtualAddressV2.get_traffic_group(self.virtual_addresses)


class AddressClasses(object):
    """Address group/class class.

    F5 BIG-IP address group/class class.

    Attributes:
        api: iControl API instance.
        address_classes: List of address classes.
    """

    def __init__(self, api, regex=None):
        self.api = api
        self.address_classes = api.LocalLB.Class.get_address_class_list()
        if regex:
            re_filter = re.compile(regex)
            self.address_classes = filter(re_filter.search, self.address_classes)

    def get_list(self):
        return self.address_classes

    def get_address_class(self):
        key = self.api.LocalLB.Class.get_address_class(self.address_classes)
        value = self.api.LocalLB.Class.get_address_class_member_data_value(key)
        result = map(zip, [x['members'] for x in key], value)
        return result

    def get_description(self):
        return self.api.LocalLB.Class.get_description(self.address_classes)


class Certificates(object):
    """Certificates class.

    F5 BIG-IP certificates class.

    Attributes:
        api: iControl API instance.
        certificates: List of certificate identifiers.
        certificate_list: List of certificate information structures.
    """

    def __init__(self, api, regex=None, mode="MANAGEMENT_MODE_DEFAULT"):
        self.api = api
        self.certificate_list = api.Management.KeyCertificate.get_certificate_list(mode=mode)
        self.certificates = [x['certificate']['cert_info']['id'] for x in self.certificate_list]
        if regex:
            re_filter = re.compile(regex)
            self.certificates = filter(re_filter.search, self.certificates)
            self.certificate_list = [x for x in self.certificate_list if x['certificate']['cert_info']['id'] in self.certificates]

    def get_list(self):
        return self.certificates

    def get_certificate_list(self):
        return self.certificate_list


class Keys(object):
    """Keys class.

    F5 BIG-IP keys class.

    Attributes:
        api: iControl API instance.
        keys: List of key identifiers.
        key_list: List of key information structures.
    """

    def __init__(self, api, regex=None, mode="MANAGEMENT_MODE_DEFAULT"):
        self.api = api
        self.key_list = api.Management.KeyCertificate.get_key_list(mode=mode)
        self.keys = [x['key_info']['id'] for x in self.key_list]
        if regex:
            re_filter = re.compile(regex)
            self.keys = filter(re_filter.search, self.keys)
            self.key_list = [x for x in self.key_list if x['key_info']['id'] in self.keys]

    def get_list(self):
        return self.keys

    def get_key_list(self):
        return self.key_list


class ProfileClientSSL(object):
    """Client SSL profiles class.

    F5 BIG-IP client SSL profiles class.

    Attributes:
        api: iControl API instance.
        profiles: List of client SSL profiles.
    """

    def __init__(self, api, regex=None):
        self.api = api
        self.profiles = api.LocalLB.ProfileClientSSL.get_list()
        if regex:
            re_filter = re.compile(regex)
            self.profiles = filter(re_filter.search, self.profiles)

    def get_list(self):
        return self.profiles

    def get_alert_timeout(self):
        return self.api.LocalLB.ProfileClientSSL.get_alert_timeout(self.profiles)

    def get_allow_nonssl_state(self):
        return self.api.LocalLB.ProfileClientSSL.get_allow_nonssl_state(self.profiles)

    def get_authenticate_depth(self):
        return self.api.LocalLB.ProfileClientSSL.get_authenticate_depth(self.profiles)

    def get_authenticate_once_state(self):
        return self.api.LocalLB.ProfileClientSSL.get_authenticate_once_state(self.profiles)

    def get_ca_file(self):
        return self.api.LocalLB.ProfileClientSSL.get_ca_file_v2(self.profiles)

    def get_cache_size(self):
        return self.api.LocalLB.ProfileClientSSL.get_cache_size(self.profiles)

    def get_cache_timeout(self):
        return self.api.LocalLB.ProfileClientSSL.get_cache_timeout(self.profiles)

    def get_certificate_file(self):
        return self.api.LocalLB.ProfileClientSSL.get_certificate_file_v2(self.profiles)

    def get_chain_file(self):
        return self.api.LocalLB.ProfileClientSSL.get_chain_file_v2(self.profiles)

    def get_cipher_list(self):
        return self.api.LocalLB.ProfileClientSSL.get_cipher_list(self.profiles)

    def get_client_certificate_ca_file(self):
        return self.api.LocalLB.ProfileClientSSL.get_client_certificate_ca_file_v2(self.profiles)

    def get_crl_file(self):
        return self.api.LocalLB.ProfileClientSSL.get_crl_file_v2(self.profiles)

    def get_default_profile(self):
        return self.api.LocalLB.ProfileClientSSL.get_default_profile(self.profiles)

    def get_description(self):
        return self.api.LocalLB.ProfileClientSSL.get_description(self.profiles)

    def get_forward_proxy_ca_certificate_file(self):
        return self.api.LocalLB.ProfileClientSSL.get_forward_proxy_ca_certificate_file(self.profiles)

    def get_forward_proxy_ca_key_file(self):
        return self.api.LocalLB.ProfileClientSSL.get_forward_proxy_ca_key_file(self.profiles)

    def get_forward_proxy_ca_passphrase(self):
        return self.api.LocalLB.ProfileClientSSL.get_forward_proxy_ca_passphrase(self.profiles)

    def get_forward_proxy_certificate_extension_include(self):
        return self.api.LocalLB.ProfileClientSSL.get_forward_proxy_certificate_extension_include(self.profiles)

    def get_forward_proxy_certificate_lifespan(self):
        return self.api.LocalLB.ProfileClientSSL.get_forward_proxy_certificate_lifespan(self.profiles)

    def get_forward_proxy_enabled_state(self):
        return self.api.LocalLB.ProfileClientSSL.get_forward_proxy_enabled_state(self.profiles)

    def get_forward_proxy_lookup_by_ipaddr_port_state(self):
        return self.api.LocalLB.ProfileClientSSL.get_forward_proxy_lookup_by_ipaddr_port_state(self.profiles)

    def get_handshake_timeout(self):
        return self.api.LocalLB.ProfileClientSSL.get_handshake_timeout(self.profiles)

    def get_key_file(self):
        return self.api.LocalLB.ProfileClientSSL.get_key_file_v2(self.profiles)

    def get_modssl_emulation_state(self):
        return self.api.LocalLB.ProfileClientSSL.get_modssl_emulation_state(self.profiles)

    def get_passphrase(self):
        return self.api.LocalLB.ProfileClientSSL.get_passphrase(self.profiles)

    def get_peer_certification_mode(self):
        return self.api.LocalLB.ProfileClientSSL.get_peer_certification_mode(self.profiles)

    def get_profile_mode(self):
        return self.api.LocalLB.ProfileClientSSL.get_profile_mode(self.profiles)

    def get_renegotiation_maximum_record_delay(self):
        return self.api.LocalLB.ProfileClientSSL.get_renegotiation_maximum_record_delay(self.profiles)

    def get_renegotiation_period(self):
        return self.api.LocalLB.ProfileClientSSL.get_renegotiation_period(self.profiles)

    def get_renegotiation_state(self):
        return self.api.LocalLB.ProfileClientSSL.get_renegotiation_state(self.profiles)

    def get_renegotiation_throughput(self):
        return self.api.LocalLB.ProfileClientSSL.get_renegotiation_throughput(self.profiles)

    def get_retain_certificate_state(self):
        return self.api.LocalLB.ProfileClientSSL.get_retain_certificate_state(self.profiles)

    def get_secure_renegotiation_mode(self):
        return self.api.LocalLB.ProfileClientSSL.get_secure_renegotiation_mode(self.profiles)

    def get_server_name(self):
        return self.api.LocalLB.ProfileClientSSL.get_server_name(self.profiles)

    def get_session_ticket_state(self):
        return self.api.LocalLB.ProfileClientSSL.get_session_ticket_state(self.profiles)

    def get_sni_default_state(self):
        return self.api.LocalLB.ProfileClientSSL.get_sni_default_state(self.profiles)

    def get_sni_require_state(self):
        return self.api.LocalLB.ProfileClientSSL.get_sni_require_state(self.profiles)

    def get_ssl_option(self):
        return self.api.LocalLB.ProfileClientSSL.get_ssl_option(self.profiles)

    def get_strict_resume_state(self):
        return self.api.LocalLB.ProfileClientSSL.get_strict_resume_state(self.profiles)

    def get_unclean_shutdown_state(self):
        return self.api.LocalLB.ProfileClientSSL.get_unclean_shutdown_state(self.profiles)

    def get_is_base_profile(self):
        return self.api.LocalLB.ProfileClientSSL.is_base_profile(self.profiles)

    def get_is_system_profile(self):
        return self.api.LocalLB.ProfileClientSSL.is_system_profile(self.profiles)


class SystemInfo(object):
    """System information class.

    F5 BIG-IP system information class.

    Attributes:
        api: iControl API instance.
    """

    def __init__(self, api):
        self.api = api

    def get_base_mac_address(self):
        return self.api.System.SystemInfo.get_base_mac_address()

    def get_blade_temperature(self):
        return self.api.System.SystemInfo.get_blade_temperature()

    def get_chassis_slot_information(self):
        return self.api.System.SystemInfo.get_chassis_slot_information()

    def get_globally_unique_identifier(self):
        return self.api.System.SystemInfo.get_globally_unique_identifier()

    def get_group_id(self):
        return self.api.System.SystemInfo.get_group_id()

    def get_hardware_information(self):
        return self.api.System.SystemInfo.get_hardware_information()

    def get_marketing_name(self):
        return self.api.System.SystemInfo.get_marketing_name()

    def get_product_information(self):
        return self.api.System.SystemInfo.get_product_information()

    def get_pva_version(self):
        return self.api.System.SystemInfo.get_pva_version()

    def get_system_id(self):
        return self.api.System.SystemInfo.get_system_id()

    def get_system_information(self):
        return self.api.System.SystemInfo.get_system_information()

    def get_time(self):
        return self.api.System.SystemInfo.get_time()

    def get_time_zone(self):
        return self.api.System.SystemInfo.get_time_zone()

    def get_uptime(self):
        return self.api.System.SystemInfo.get_uptime()


def generate_dict(api_obj, fields):
    result_dict = {}
    lists = []
    supported_fields = []
    if api_obj.get_list():
        for field in fields:
            try:
                api_response = getattr(api_obj, "get_" + field)()
            except (MethodNotFound, WebFault):
                pass
            else:
                lists.append(api_response)
                supported_fields.append(field)
        for i, j in enumerate(api_obj.get_list()):
            temp = {}
            temp.update([(item[0], item[1][i]) for item in zip(supported_fields, lists)])
            result_dict[j] = temp
    return result_dict

def generate_simple_dict(api_obj, fields):
    result_dict = {}
    for field in fields:
        try:
            api_response = getattr(api_obj, "get_" + field)()
        except (MethodNotFound, WebFault):
            pass
        else:
            result_dict[field] = api_response
    return result_dict

def generate_interface_dict(f5, regex):
    interfaces = Interfaces(f5.get_api(), regex)
    fields = ['active_media', 'actual_flow_control', 'bundle_state',
              'description', 'dual_media_state', 'enabled_state', 'if_index',
              'learning_mode', 'lldp_admin_status', 'lldp_tlvmap',
              'mac_address', 'media', 'media_option', 'media_option_sfp',
              'media_sfp', 'media_speed', 'media_status', 'mtu',
              'phy_master_slave_mode', 'prefer_sfp_state', 'flow_control',
              'sflow_poll_interval', 'sflow_poll_interval_global',
              'sfp_media_state', 'stp_active_edge_port_state',
              'stp_enabled_state', 'stp_link_type',
              'stp_protocol_detection_reset_state']
    return generate_dict(interfaces, fields)

def generate_self_ip_dict(f5, regex):
    self_ips = SelfIPs(f5.get_api(), regex)
    fields = ['address', 'allow_access_list', 'description',
              'enforced_firewall_policy', 'floating_state', 'fw_rule',
              'netmask', 'staged_firewall_policy', 'traffic_group',
              'vlan', 'is_traffic_group_inherited']
    return generate_dict(self_ips, fields)

def generate_trunk_dict(f5, regex):
    trunks = Trunks(f5.get_api(), regex)
    fields = ['active_lacp_state', 'configured_member_count', 'description',
              'distribution_hash_option', 'interface', 'lacp_enabled_state',
              'lacp_timeout_option', 'link_selection_policy', 'media_speed',
              'media_status', 'operational_member_count', 'stp_enabled_state',
              'stp_protocol_detection_reset_state']
    return generate_dict(trunks, fields)

def generate_vlan_dict(f5, regex):
    vlans = Vlans(f5.get_api(), regex)
    fields = ['auto_lasthop', 'cmp_hash_algorithm', 'description',
              'dynamic_forwarding', 'failsafe_action', 'failsafe_state',
              'failsafe_timeout', 'if_index', 'learning_mode',
              'mac_masquerade_address', 'member', 'mtu',
              'sflow_poll_interval', 'sflow_poll_interval_global',
              'sflow_sampling_rate', 'sflow_sampling_rate_global',
              'source_check_state', 'true_mac_address', 'vlan_id']
    return generate_dict(vlans, fields)

def generate_vs_dict(f5, regex):
    virtual_servers = VirtualServers(f5.get_api(), regex)
    fields = ['actual_hardware_acceleration', 'authentication_profile',
              'auto_lasthop', 'bw_controller_policy', 'clone_pool',
              'cmp_enable_mode', 'connection_limit', 'connection_mirror_state',
              'default_pool_name', 'description', 'destination',
              'enabled_state', 'enforced_firewall_policy',
              'fallback_persistence_profile', 'fw_rule', 'gtm_score',
              'last_hop_pool', 'nat64_state', 'object_status',
              'persistence_profile', 'profile', 'protocol',
              'rate_class', 'rate_limit', 'rate_limit_destination_mask',
              'rate_limit_mode', 'rate_limit_source_mask', 'related_rule',
              'rule', 'security_log_profile', 'snat_pool', 'snat_type',
              'source_address', 'source_address_translation_lsn_pool',
              'source_address_translation_snat_pool',
              'source_address_translation_type', 'source_port_behavior',
              'staged_firewall_policy', 'translate_address_state',
              'translate_port_state', 'type', 'vlan', 'wildmask']
    return generate_dict(virtual_servers, fields)

def generate_pool_dict(f5, regex):
    pools = Pools(f5.get_api(), regex)
    fields = ['action_on_service_down', 'active_member_count',
              'aggregate_dynamic_ratio', 'allow_nat_state',
              'allow_snat_state', 'client_ip_tos', 'client_link_qos',
              'description', 'gateway_failsafe_device',
              'ignore_persisted_weight_state', 'lb_method', 'member',
              'minimum_active_member', 'minimum_up_member',
              'minimum_up_member_action', 'minimum_up_member_enabled_state',
              'monitor_association', 'monitor_instance', 'object_status',
              'profile', 'queue_depth_limit',
              'queue_on_connection_limit_state', 'queue_time_limit',
              'reselect_tries', 'server_ip_tos', 'server_link_qos',
              'simple_timeout', 'slow_ramp_time']
    return generate_dict(pools, fields)

def generate_device_dict(f5, regex):
    devices = Devices(f5.get_api(), regex)
    fields = ['active_modules', 'base_mac_address', 'blade_addresses',
              'build', 'chassis_id', 'chassis_type', 'comment',
              'configsync_address', 'contact', 'description', 'edition',
              'failover_state', 'hostname', 'inactive_modules', 'location',
              'management_address', 'marketing_name', 'multicast_address',
              'optional_modules', 'platform_id', 'primary_mirror_address',
              'product', 'secondary_mirror_address', 'software_version',
              'timelimited_modules', 'timezone', 'unicast_addresses']
    return generate_dict(devices, fields)

def generate_device_group_dict(f5, regex):
    device_groups = DeviceGroups(f5.get_api(), regex)
    fields = ['all_preferred_active', 'autosync_enabled_state','description',
              'device', 'full_load_on_sync_state',
              'incremental_config_sync_size_maximum',
              'network_failover_enabled_state', 'sync_status', 'type']
    return generate_dict(device_groups, fields)

def generate_traffic_group_dict(f5, regex):
    traffic_groups = TrafficGroups(f5.get_api(), regex)
    fields = ['auto_failback_enabled_state', 'auto_failback_time',
              'default_device', 'description', 'ha_load_factor',
              'ha_order', 'is_floating', 'mac_masquerade_address',
              'unit_id']
    return generate_dict(traffic_groups, fields)

def generate_rule_dict(f5, regex):
    rules = Rules(f5.get_api(), regex)
    fields = ['definition', 'description', 'ignore_vertification',
              'verification_status']
    return generate_dict(rules, fields)

def generate_node_dict(f5, regex):
    nodes = Nodes(f5.get_api(), regex)
    fields = ['address', 'connection_limit', 'description', 'dynamic_ratio',
              'monitor_instance', 'monitor_rule', 'monitor_status',
              'object_status', 'rate_limit', 'ratio', 'session_status']
    return generate_dict(nodes, fields)

def generate_virtual_address_dict(f5, regex):
    virtual_addresses = VirtualAddresses(f5.get_api(), regex)
    fields = ['address', 'arp_state', 'auto_delete_state', 'connection_limit',
              'description', 'enabled_state', 'icmp_echo_state',
              'is_floating_state', 'netmask', 'object_status',
              'route_advertisement_state', 'traffic_group']
    return generate_dict(virtual_addresses, fields)

def generate_address_class_dict(f5, regex):
    address_classes = AddressClasses(f5.get_api(), regex)
    fields = ['address_class', 'description']
    return generate_dict(address_classes, fields)

def generate_certificate_dict(f5, regex):
    certificates = Certificates(f5.get_api(), regex)
    return dict(zip(certificates.get_list(), certificates.get_certificate_list()))

def generate_key_dict(f5, regex):
    keys = Keys(f5.get_api(), regex)
    return dict(zip(keys.get_list(), keys.get_key_list()))

def generate_client_ssl_profile_dict(f5, regex):
    profiles = ProfileClientSSL(f5.get_api(), regex)
    fields = ['alert_timeout', 'allow_nonssl_state', 'authenticate_depth',
              'authenticate_once_state', 'ca_file', 'cache_size',
              'cache_timeout', 'certificate_file', 'chain_file',
              'cipher_list', 'client_certificate_ca_file', 'crl_file',
              'default_profile', 'description',
              'forward_proxy_ca_certificate_file', 'forward_proxy_ca_key_file',
              'forward_proxy_ca_passphrase',
              'forward_proxy_certificate_extension_include',
              'forward_proxy_certificate_lifespan',
              'forward_proxy_enabled_state',
              'forward_proxy_lookup_by_ipaddr_port_state', 'handshake_timeout',
              'key_file', 'modssl_emulation_state', 'passphrase',
              'peer_certification_mode', 'profile_mode',
              'renegotiation_maximum_record_delay', 'renegotiation_period',
              'renegotiation_state', 'renegotiation_throughput',
              'retain_certificate_state', 'secure_renegotiation_mode',
              'server_name', 'session_ticket_state', 'sni_default_state',
              'sni_require_state', 'ssl_option', 'strict_resume_state',
              'unclean_shutdown_state', 'is_base_profile', 'is_system_profile']
    return generate_dict(profiles, fields)

def generate_system_info_dict(f5):
    system_info = SystemInfo(f5.get_api())
    fields = ['base_mac_address',
              'blade_temperature', 'chassis_slot_information',
              'globally_unique_identifier', 'group_id',
              'hardware_information',
              'marketing_name',
              'product_information', 'pva_version', 'system_id',
              'system_information', 'time',
              'time_zone', 'uptime']
    return generate_simple_dict(system_info, fields)

def generate_software_list(f5):
    software = Software(f5.get_api())
    software_list = software.get_all_software_status()
    return software_list


def main():
    module = AnsibleModule(
        argument_spec = dict(
            server = dict(type='str', required=True),
            user = dict(type='str', required=True),
            password = dict(type='str', required=True),
            validate_certs = dict(default='yes', type='bool'),
            session = dict(type='bool', default=False),
            include = dict(type='list', required=True),
            filter = dict(type='str', required=False),
        )
    )

    if not bigsuds_found:
        module.fail_json(msg="the python suds and bigsuds modules are required")

    server = module.params['server']
    user = module.params['user']
    password = module.params['password']
    validate_certs = module.params['validate_certs']
    session = module.params['session']
    fact_filter = module.params['filter']

    if validate_certs:
        import ssl
        if not hasattr(ssl, 'SSLContext'):
            module.fail_json(msg='bigsuds does not support verifying certificates with python < 2.7.9.  Either update python or set validate_certs=False on the task')

    if fact_filter:
        regex = fnmatch.translate(fact_filter)
    else:
        regex = None
    include = map(lambda x: x.lower(), module.params['include'])
    valid_includes = ('address_class', 'certificate', 'client_ssl_profile',
                      'device', 'device_group', 'interface', 'key', 'node',
                      'pool', 'rule', 'self_ip', 'software', 'system_info',
                      'traffic_group', 'trunk', 'virtual_address',
                      'virtual_server', 'vlan')
    include_test = map(lambda x: x in valid_includes, include)
    if not all(include_test):
        module.fail_json(msg="value of include must be one or more of: %s, got: %s" % (",".join(valid_includes), ",".join(include)))

    try:
        facts = {}

        if len(include) > 0:
            f5 = F5(server, user, password, session, validate_certs)
            saved_active_folder = f5.get_active_folder()
            saved_recursive_query_state = f5.get_recursive_query_state()
            if saved_active_folder != "/":
                f5.set_active_folder("/")
            if saved_recursive_query_state != "STATE_ENABLED":
                f5.enable_recursive_query_state()

            if 'interface' in include:
                facts['interface'] = generate_interface_dict(f5, regex)
            if 'self_ip' in include:
                facts['self_ip'] = generate_self_ip_dict(f5, regex)
            if 'trunk' in include:
                facts['trunk'] = generate_trunk_dict(f5, regex)
            if 'vlan' in include:
                facts['vlan'] = generate_vlan_dict(f5, regex)
            if 'virtual_server' in include:
                facts['virtual_server'] = generate_vs_dict(f5, regex)
            if 'pool' in include:
                facts['pool'] = generate_pool_dict(f5, regex)
            if 'device' in include:
                facts['device'] = generate_device_dict(f5, regex)
            if 'device_group' in include:
                facts['device_group'] = generate_device_group_dict(f5, regex)
            if 'traffic_group' in include:
                facts['traffic_group'] = generate_traffic_group_dict(f5, regex)
            if 'rule' in include:
                facts['rule'] = generate_rule_dict(f5, regex)
            if 'node' in include:
                facts['node'] = generate_node_dict(f5, regex)
            if 'virtual_address' in include:
                facts['virtual_address'] = generate_virtual_address_dict(f5, regex)
            if 'address_class' in include:
                facts['address_class'] = generate_address_class_dict(f5, regex)
            if 'software' in include:
                facts['software'] = generate_software_list(f5)
            if 'certificate' in include:
                facts['certificate'] = generate_certificate_dict(f5, regex)
            if 'key' in include:
                facts['key'] = generate_key_dict(f5, regex)
            if 'client_ssl_profile' in include:
                facts['client_ssl_profile'] = generate_client_ssl_profile_dict(f5, regex)
            if 'system_info' in include:
                facts['system_info'] = generate_system_info_dict(f5)

            # restore saved state
            if saved_active_folder and saved_active_folder != "/":
                f5.set_active_folder(saved_active_folder)
            if saved_recursive_query_state and \
               saved_recursive_query_state != "STATE_ENABLED":
                f5.set_recursive_query_state(saved_recursive_query_state)

        result = {'ansible_facts': facts}

    except Exception, e:
        module.fail_json(msg="received exception: %s\ntraceback: %s" % (e, traceback.format_exc()))

    module.exit_json(**result)

# include magic from lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.f5 import *

if __name__ == '__main__':
    main()

