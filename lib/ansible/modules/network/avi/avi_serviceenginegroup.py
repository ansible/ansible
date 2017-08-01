#!/usr/bin/python
#
# Created on Aug 25, 2016
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
# Avi Version: 17.1.1
#
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
#

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_serviceenginegroup
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of ServiceEngineGroup Avi RESTful Object
description:
    - This module is used to configure ServiceEngineGroup object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.4"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent","present"]
    active_standby:
        description:
            - Service engines in active/standby mode for ha failover.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    advertise_backend_networks:
        description:
            - Advertise reach-ability of backend server networks via adc through bgp for default gateway feature.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    aggressive_failure_detection:
        description:
            - Enable aggressive failover configuration for ha.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    algo:
        description:
            - In compact placement, virtual services are placed on existing ses until max_vs_per_se limit is reached.
            - Enum options - PLACEMENT_ALGO_PACKED, PLACEMENT_ALGO_DISTRIBUTED.
            - Default value when not specified in API or module is interpreted by Avi Controller as PLACEMENT_ALGO_PACKED.
    archive_shm_limit:
        description:
            - Amount of se memory in gb until which shared memory is collected in core archive.
            - Field introduced in 17.1.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as 8.
    async_ssl:
        description:
            - Ssl handshakes will be handled by dedicated ssl threads.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.4"
    async_ssl_threads:
        description:
            - Number of async ssl threads per se_dp.
            - Allowed values are 1-4.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.
        version_added: "2.4"
    auto_rebalance:
        description:
            - If set, virtual services will be automatically migrated when load on an se is less than minimum or more than maximum thresholds.
            - Only alerts are generated when the auto_rebalance is not set.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    auto_rebalance_interval:
        description:
            - Frequency of rebalance, if 'auto rebalance' is enabled.
            - Default value when not specified in API or module is interpreted by Avi Controller as 300.
    auto_redistribute_active_standby_load:
        description:
            - Redistribution of virtual services from the takeover se to the replacement se can cause momentary traffic loss.
            - If the auto-redistribute load option is left in its default off state, any desired rebalancing requires calls to rest api.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    buffer_se:
        description:
            - Excess service engine capacity provisioned for ha failover.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.
    cloud_ref:
        description:
            - It is a reference to an object of type cloud.
    connection_memory_percentage:
        description:
            - Percentage of memory for connection state.
            - This will come at the expense of memory used for http in-memory cache.
            - Allowed values are 10-90.
            - Default value when not specified in API or module is interpreted by Avi Controller as 50.
    cpu_reserve:
        description:
            - Boolean flag to set cpu_reserve.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    cpu_socket_affinity:
        description:
            - Allocate all the cpu cores for the service engine virtual machines  on the same cpu socket.
            - Applicable only for vcenter cloud.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    custom_securitygroups_data:
        description:
            - Custom security groups to be associated with data vnics for se instances in openstack and aws clouds.
            - Field introduced in 17.1.3.
    custom_securitygroups_mgmt:
        description:
            - Custom security groups to be associated with management vnic for se instances in openstack and aws clouds.
            - Field introduced in 17.1.3.
    custom_tag:
        description:
            - Custom tag will be used to create the tags for se instance in aws.
            - Note this is not the same as the prefix for se name.
    dedicated_dispatcher_core:
        description:
            - Dedicate the core that handles packet receive/transmit from the network to just the dispatching function.
            - Don't use it for tcp/ip and ssl functions.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    description:
        description:
            - User defined description for the object.
    disk_per_se:
        description:
            - Amount of disk space for each of the service engine virtual machines.
            - Default value when not specified in API or module is interpreted by Avi Controller as 10.
    distribute_load_active_standby:
        description:
            - Use both the active and standby service engines for virtual service placement in the legacy active standby ha mode.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    enable_routing:
        description:
            - Enable routing for this serviceenginegroup .
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    enable_vip_on_all_interfaces:
        description:
            - Enable vip on all interfaces of se.
            - Field introduced in 17.1.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
    enable_vmac:
        description:
            - Use virtual mac address for interfaces on which floating interface ips are placed.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    extra_config_multiplier:
        description:
            - Multiplier for extra config to support large vs/pool config.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.0.
    extra_shared_config_memory:
        description:
            - Extra config memory to support large geo db configuration.
            - Field introduced in 17.1.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
    floating_intf_ip:
        description:
            - If serviceenginegroup is configured for legacy 1+1 active standby ha mode, floating ip's will be advertised only by the active se in the pair.
            - Virtual services in this group must be disabled/enabled for any changes to the floating ip's to take effect.
            - Only active se hosting vs tagged with active standby se 1 tag will advertise this floating ip when manual load distribution is enabled.
    floating_intf_ip_se_2:
        description:
            - If serviceenginegroup is configured for legacy 1+1 active standby ha mode, floating ip's will be advertised only by the active se in the pair.
            - Virtual services in this group must be disabled/enabled for any changes to the floating ip's to take effect.
            - Only active se hosting vs tagged with active standby se 2 tag will advertise this floating ip when manual load distribution is enabled.
    ha_mode:
        description:
            - High availability mode for all the virtual services using this service engine group.
            - Enum options - HA_MODE_SHARED_PAIR, HA_MODE_SHARED, HA_MODE_LEGACY_ACTIVE_STANDBY.
            - Default value when not specified in API or module is interpreted by Avi Controller as HA_MODE_SHARED.
    hardwaresecuritymodulegroup_ref:
        description:
            - It is a reference to an object of type hardwaresecuritymodulegroup.
    hm_on_standby:
        description:
            - Enable active health monitoring from the standby se for all placed virtual services.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
    host_attribute_key:
        description:
            - Key of a (key, value) pair identifying a label for a set of nodes usually in container clouds.
            - Needs to be specified together with host_attribute_value.
            - Ses can be configured differently including ha modes across different se groups.
            - May also be used for isolation between different classes of virtualservices.
            - Virtualservices' se group may be specified via annotations/labels.
            - A openshift/kubernetes namespace maybe annotated with a matching se group label as openshift.io/node-selector  apptype=prod.
            - When multiple se groups are used in a cloud with host attributes specified,just a single se group can exist as a match-all se group without a
            - host_attribute_key.
    host_attribute_value:
        description:
            - Value of a (key, value) pair identifying a label for a set of nodes usually in container clouds.
            - Needs to be specified together with host_attribute_key.
    hypervisor:
        description:
            - Override default hypervisor.
            - Enum options - DEFAULT, VMWARE_ESX, KVM, VMWARE_VSAN, XEN.
    instance_flavor:
        description:
            - Instance/flavor type for se instance.
    iptables:
        description:
            - Iptable rules.
    least_load_core_selection:
        description:
            - Select core with least load for new flow.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
    log_disksz:
        description:
            - Maximum disk capacity (in mb) to be allocated to an se.
            - This is exclusively used for debug and log data.
            - Default value when not specified in API or module is interpreted by Avi Controller as 10000.
    max_cpu_usage:
        description:
            - When cpu usage on an se exceeds this threshold, virtual services hosted on this se may be rebalanced to other ses to reduce load.
            - A new se may be created as part of this process.
            - Allowed values are 40-90.
            - Default value when not specified in API or module is interpreted by Avi Controller as 80.
    max_scaleout_per_vs:
        description:
            - Maximum number of active service engines for the virtual service.
            - Allowed values are 1-64.
            - Default value when not specified in API or module is interpreted by Avi Controller as 4.
    max_se:
        description:
            - Maximum number of services engines in this group.
            - Allowed values are 0-1000.
            - Default value when not specified in API or module is interpreted by Avi Controller as 10.
    max_vs_per_se:
        description:
            - Maximum number of virtual services that can be placed on a single service engine.
            - East west virtual services are excluded from this limit.
            - Allowed values are 1-1000.
            - Default value when not specified in API or module is interpreted by Avi Controller as 10.
    mem_reserve:
        description:
            - Boolean flag to set mem_reserve.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
    memory_per_se:
        description:
            - Amount of memory for each of the service engine virtual machines.
            - Default value when not specified in API or module is interpreted by Avi Controller as 2048.
    mgmt_network_ref:
        description:
            - Management network to use for avi service engines.
            - It is a reference to an object of type network.
    mgmt_subnet:
        description:
            - Management subnet to use for avi service engines.
    min_cpu_usage:
        description:
            - When cpu usage on an se falls below the minimum threshold, virtual services hosted on the se may be consolidated onto other underutilized ses.
            - After consolidation, unused service engines may then be eligible for deletion.
            - Allowed values are 20-60.
            - Default value when not specified in API or module is interpreted by Avi Controller as 30.
    min_scaleout_per_vs:
        description:
            - Minimum number of active service engines for the virtual service.
            - Allowed values are 1-64.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.
    name:
        description:
            - Name of the object.
        required: true
    non_significant_log_throttle:
        description:
            - This setting limits the number of non-significant logs generated per second per core on this se.
            - Default is 100 logs per second.
            - Set it to zero (0) to disable throttling.
            - Field introduced in 17.1.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as 100.
    num_flow_cores_sum_changes_to_ignore:
        description:
            - Number of changes in num flow cores sum to ignore.
            - Default value when not specified in API or module is interpreted by Avi Controller as 8.
    openstack_availability_zone:
        description:
            - Field deprecated in 17.1.1.
    openstack_availability_zones:
        description:
            - Field introduced in 17.1.1.
    openstack_mgmt_network_name:
        description:
            - Avi management network name.
    openstack_mgmt_network_uuid:
        description:
            - Management network uuid.
    os_reserved_memory:
        description:
            - Amount of extra memory to be reserved for use by the operating system on a service engine.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
    per_app:
        description:
            - Per-app se mode is designed for deploying dedicated load balancers per app (vs).
            - In this mode, each se is limited to a max of 2 vss.
            - Vcpus in per-app ses count towards licensing usage at 25% rate.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    placement_mode:
        description:
            - If placement mode is 'auto', virtual services are automatically placed on service engines.
            - Enum options - PLACEMENT_MODE_AUTO.
            - Default value when not specified in API or module is interpreted by Avi Controller as PLACEMENT_MODE_AUTO.
    realtime_se_metrics:
        description:
            - Enable or disable real time se metrics.
    se_deprovision_delay:
        description:
            - Duration to preserve unused service engine virtual machines before deleting them.
            - If traffic to a virtual service were to spike up abruptly, this se would still be available to be utilized again rather than creating a new se.
            - If this value is set to 0, controller will never delete any ses and administrator has to manually cleanup unused ses.
            - Allowed values are 0-525600.
            - Default value when not specified in API or module is interpreted by Avi Controller as 120.
    se_dos_profile:
        description:
            - Dosthresholdprofile settings for serviceenginegroup.
    se_ipc_udp_port:
        description:
            - Udp port for se_dp ipc in docker bridge mode.
            - Field introduced in 17.1.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1500.
        version_added: "2.4"
    se_name_prefix:
        description:
            - Prefix to use for virtual machine name of service engines.
            - Default value when not specified in API or module is interpreted by Avi Controller as Avi.
    se_remote_punt_udp_port:
        description:
            - Udp port for punted packets in docker bridge mode.
            - Field introduced in 17.1.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1501.
        version_added: "2.4"
    se_thread_multiplier:
        description:
            - Multiplier for se threads based on vcpu.
            - Allowed values are 1-10.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.
    se_tunnel_mode:
        description:
            - Determines if dsr from secondary se is active or not.
            - 0  automatically determine based on hypervisor type.
            - 1  disable dsr unconditionally.
            - ~[0,1]  enable dsr unconditionally.
            - Field introduced in 17.1.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
    se_tunnel_udp_port:
        description:
            - Udp port for tunneled packets from secondary to primary se in docker bridge mode.
            - Field introduced in 17.1.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1550.
    se_udp_encap_ipc:
        description:
            - Determines if se-se ipc messages are encapsulated in an udp header.
            - 0  automatically determine based on hypervisor type.
            - 1  use udp encap unconditionally.
            - ~[0,1]  don't use udp encap.
            - Field introduced in 17.1.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
        version_added: "2.4"
    se_vs_hb_max_pkts_in_batch:
        description:
            - Maximum number of aggregated vs heartbeat packets to send in a batch.
            - Allowed values are 1-256.
            - Field introduced in 17.1.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as 8.
    se_vs_hb_max_vs_in_pkt:
        description:
            - Maximum number of virtualservices for which heartbeat messages are aggregated in one packet.
            - Allowed values are 1-1024.
            - Field introduced in 17.1.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as 256.
    service_ip_subnets:
        description:
            - Subnets assigned to the se group.
            - Required for vs group placement.
            - Field introduced in 17.1.1.
    significant_log_throttle:
        description:
            - This setting limits the number of significant logs generated per second per core on this se.
            - Default is 100 logs per second.
            - Set it to zero (0) to disable throttling.
            - Field introduced in 17.1.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as 100.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    udf_log_throttle:
        description:
            - This setting limits the number of udf logs generated per second per core on this se.
            - Udf logs are generated due to the configured client log filters or the rules with logging enabled.
            - Default is 100 logs per second.
            - Set it to zero (0) to disable throttling.
            - Field introduced in 17.1.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as 100.
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Unique object identifier of the object.
    vcenter_clusters:
        description:
            - Vcenterclusters settings for serviceenginegroup.
    vcenter_datastore_mode:
        description:
            - Enum options - vcenter_datastore_any, vcenter_datastore_local, vcenter_datastore_shared.
            - Default value when not specified in API or module is interpreted by Avi Controller as VCENTER_DATASTORE_ANY.
    vcenter_datastores:
        description:
            - List of vcenterdatastore.
    vcenter_datastores_include:
        description:
            - Boolean flag to set vcenter_datastores_include.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    vcenter_folder:
        description:
            - Folder to place all the service engine virtual machines in vcenter.
            - Default value when not specified in API or module is interpreted by Avi Controller as AviSeFolder.
    vcenter_hosts:
        description:
            - Vcenterhosts settings for serviceenginegroup.
    vcpus_per_se:
        description:
            - Number of vcpus for each of the service engine virtual machines.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.
    vs_host_redundancy:
        description:
            - Ensure primary and secondary service engines are deployed on different physical hosts.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
    vs_scalein_timeout:
        description:
            - Time to wait for the scaled in se to drain existing flows before marking the scalein done.
            - Default value when not specified in API or module is interpreted by Avi Controller as 30.
    vs_scalein_timeout_for_upgrade:
        description:
            - During se upgrade, time to wait for the scaled-in se to drain existing flows before marking the scalein done.
            - Default value when not specified in API or module is interpreted by Avi Controller as 30.
    vs_scaleout_timeout:
        description:
            - Time to wait for the scaled out se to become ready before marking the scaleout done.
            - Default value when not specified in API or module is interpreted by Avi Controller as 30.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
- name: Example to create ServiceEngineGroup object
  avi_serviceenginegroup:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_serviceenginegroup
"""

RETURN = '''
obj:
    description: ServiceEngineGroup (api/serviceenginegroup) object
    returned: success, changed
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible.module_utils.avi import (
        avi_common_argument_spec, HAS_AVI, avi_ansible_api)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
        active_standby=dict(type='bool',),
        advertise_backend_networks=dict(type='bool',),
        aggressive_failure_detection=dict(type='bool',),
        algo=dict(type='str',),
        archive_shm_limit=dict(type='int',),
        async_ssl=dict(type='bool',),
        async_ssl_threads=dict(type='int',),
        auto_rebalance=dict(type='bool',),
        auto_rebalance_interval=dict(type='int',),
        auto_redistribute_active_standby_load=dict(type='bool',),
        buffer_se=dict(type='int',),
        cloud_ref=dict(type='str',),
        connection_memory_percentage=dict(type='int',),
        cpu_reserve=dict(type='bool',),
        cpu_socket_affinity=dict(type='bool',),
        custom_securitygroups_data=dict(type='list',),
        custom_securitygroups_mgmt=dict(type='list',),
        custom_tag=dict(type='list',),
        dedicated_dispatcher_core=dict(type='bool',),
        description=dict(type='str',),
        disk_per_se=dict(type='int',),
        distribute_load_active_standby=dict(type='bool',),
        enable_routing=dict(type='bool',),
        enable_vip_on_all_interfaces=dict(type='bool',),
        enable_vmac=dict(type='bool',),
        extra_config_multiplier=dict(type='float',),
        extra_shared_config_memory=dict(type='int',),
        floating_intf_ip=dict(type='list',),
        floating_intf_ip_se_2=dict(type='list',),
        ha_mode=dict(type='str',),
        hardwaresecuritymodulegroup_ref=dict(type='str',),
        hm_on_standby=dict(type='bool',),
        host_attribute_key=dict(type='str',),
        host_attribute_value=dict(type='str',),
        hypervisor=dict(type='str',),
        instance_flavor=dict(type='str',),
        iptables=dict(type='list',),
        least_load_core_selection=dict(type='bool',),
        log_disksz=dict(type='int',),
        max_cpu_usage=dict(type='int',),
        max_scaleout_per_vs=dict(type='int',),
        max_se=dict(type='int',),
        max_vs_per_se=dict(type='int',),
        mem_reserve=dict(type='bool',),
        memory_per_se=dict(type='int',),
        mgmt_network_ref=dict(type='str',),
        mgmt_subnet=dict(type='dict',),
        min_cpu_usage=dict(type='int',),
        min_scaleout_per_vs=dict(type='int',),
        name=dict(type='str', required=True),
        non_significant_log_throttle=dict(type='int',),
        num_flow_cores_sum_changes_to_ignore=dict(type='int',),
        openstack_availability_zone=dict(type='str',),
        openstack_availability_zones=dict(type='list',),
        openstack_mgmt_network_name=dict(type='str',),
        openstack_mgmt_network_uuid=dict(type='str',),
        os_reserved_memory=dict(type='int',),
        per_app=dict(type='bool',),
        placement_mode=dict(type='str',),
        realtime_se_metrics=dict(type='dict',),
        se_deprovision_delay=dict(type='int',),
        se_dos_profile=dict(type='dict',),
        se_ipc_udp_port=dict(type='int',),
        se_name_prefix=dict(type='str',),
        se_remote_punt_udp_port=dict(type='int',),
        se_thread_multiplier=dict(type='int',),
        se_tunnel_mode=dict(type='int',),
        se_tunnel_udp_port=dict(type='int',),
        se_udp_encap_ipc=dict(type='int',),
        se_vs_hb_max_pkts_in_batch=dict(type='int',),
        se_vs_hb_max_vs_in_pkt=dict(type='int',),
        service_ip_subnets=dict(type='list',),
        significant_log_throttle=dict(type='int',),
        tenant_ref=dict(type='str',),
        udf_log_throttle=dict(type='int',),
        url=dict(type='str',),
        uuid=dict(type='str',),
        vcenter_clusters=dict(type='dict',),
        vcenter_datastore_mode=dict(type='str',),
        vcenter_datastores=dict(type='list',),
        vcenter_datastores_include=dict(type='bool',),
        vcenter_folder=dict(type='str',),
        vcenter_hosts=dict(type='dict',),
        vcpus_per_se=dict(type='int',),
        vs_host_redundancy=dict(type='bool',),
        vs_scalein_timeout=dict(type='int',),
        vs_scalein_timeout_for_upgrade=dict(type='int',),
        vs_scaleout_timeout=dict(type='int',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'serviceenginegroup',
                           set([]))

if __name__ == '__main__':
    main()
