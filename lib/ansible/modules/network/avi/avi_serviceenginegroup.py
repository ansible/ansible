#!/usr/bin/python
#
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
# Avi Version: 17.1.1
#
# Copyright: (c) 2017 Gaurav Rastogi, <grastogi@avinetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_serviceenginegroup
author: Gaurav Rastogi (@grastogi23) <grastogi@avinetworks.com>

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
        choices: ["absent", "present"]
    avi_api_update_method:
        description:
            - Default method for object update is HTTP PUT.
            - Setting to patch will override that behavior to use HTTP PATCH.
        version_added: "2.5"
        default: put
        choices: ["put", "patch"]
    avi_api_patch_op:
        description:
            - Patch operation to use when using avi_api_update_method as patch.
        version_added: "2.5"
        choices: ["add", "replace", "delete"]
    accelerated_networking:
        description:
            - Enable accelerated networking option for azure se.
            - Accelerated networking enables single root i/o virtualization (sr-iov) to a se vm.
            - This improves networking performance.
            - Field introduced in 17.2.14,18.1.5,18.2.1.
        version_added: "2.9"
        type: bool
    active_standby:
        description:
            - Service engines in active/standby mode for ha failover.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    additional_config_memory:
        description:
            - Indicates the percent of config memory used for config updates.
            - Allowed values are 0-90.
            - Field deprecated in 18.1.2.
            - Field introduced in 18.1.1.
        version_added: "2.9"
    advertise_backend_networks:
        description:
            - Advertise reach-ability of backend server networks via adc through bgp for default gateway feature.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    aggressive_failure_detection:
        description:
            - Enable aggressive failover configuration for ha.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    algo:
        description:
            - In compact placement, virtual services are placed on existing ses until max_vs_per_se limit is reached.
            - Enum options - PLACEMENT_ALGO_PACKED, PLACEMENT_ALGO_DISTRIBUTED.
            - Default value when not specified in API or module is interpreted by Avi Controller as PLACEMENT_ALGO_PACKED.
    allow_burst:
        description:
            - Allow ses to be created using burst license.
            - Field introduced in 17.2.5.
        version_added: "2.5"
        type: bool
    app_cache_percent:
        description:
            - A percent value of total se memory reserved for application caching.
            - This is an se bootup property and requires se restart.
            - Allowed values are 0 - 100.
            - Special values are 0- 'disable'.
            - Field introduced in 18.2.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
        version_added: "2.9"
    app_learning_memory_percent:
        description:
            - A percent value of total se memory reserved for application learning.
            - This is an se bootup property and requires se restart.
            - Allowed values are 0 - 10.
            - Field introduced in 18.2.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
        version_added: "2.9"
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
        type: bool
    async_ssl_threads:
        description:
            - Number of async ssl threads per se_dp.
            - Allowed values are 1-16.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.
        version_added: "2.4"
    auto_rebalance:
        description:
            - If set, virtual services will be automatically migrated when load on an se is less than minimum or more than maximum thresholds.
            - Only alerts are generated when the auto_rebalance is not set.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    auto_rebalance_capacity_per_se:
        description:
            - Capacities of se for auto rebalance for each criteria.
            - Field introduced in 17.2.4.
        version_added: "2.5"
    auto_rebalance_criteria:
        description:
            - Set of criteria for se auto rebalance.
            - Enum options - SE_AUTO_REBALANCE_CPU, SE_AUTO_REBALANCE_PPS, SE_AUTO_REBALANCE_MBPS, SE_AUTO_REBALANCE_OPEN_CONNS, SE_AUTO_REBALANCE_CPS.
            - Field introduced in 17.2.3.
        version_added: "2.5"
    auto_rebalance_interval:
        description:
            - Frequency of rebalance, if 'auto rebalance' is enabled.
            - Default value when not specified in API or module is interpreted by Avi Controller as 300.
    auto_redistribute_active_standby_load:
        description:
            - Redistribution of virtual services from the takeover se to the replacement se can cause momentary traffic loss.
            - If the auto-redistribute load option is left in its default off state, any desired rebalancing requires calls to rest api.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    bgp_state_update_interval:
        description:
            - Bgp peer state update interval.
            - Allowed values are 5-100.
            - Field introduced in 17.2.14,18.1.5,18.2.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as 10.
        version_added: "2.9"
    buffer_se:
        description:
            - Excess service engine capacity provisioned for ha failover.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.
    cloud_ref:
        description:
            - It is a reference to an object of type cloud.
    config_debugs_on_all_cores:
        description:
            - Enable config debugs on all cores of se.
            - Field introduced in 17.2.13,18.1.5,18.2.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.9"
        type: bool
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
        type: bool
    cpu_socket_affinity:
        description:
            - Allocate all the cpu cores for the service engine virtual machines  on the same cpu socket.
            - Applicable only for vcenter cloud.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
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
    data_network_id:
        description:
            - Subnet used to spin up the data nic for service engines, used only for azure cloud.
            - Overrides the cloud level setting for service engine subnet.
            - Field introduced in 18.2.3.
        version_added: "2.9"
    datascript_timeout:
        description:
            - Number of instructions before datascript times out.
            - Allowed values are 0-100000000.
            - Field introduced in 18.2.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1000000.
        version_added: "2.9"
    dedicated_dispatcher_core:
        description:
            - Dedicate the core that handles packet receive/transmit from the network to just the dispatching function.
            - Don't use it for tcp/ip and ssl functions.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    description:
        description:
            - User defined description for the object.
    disable_avi_securitygroups:
        description:
            - By default, avi creates and manages security groups along with custom sg provided by user.
            - Set this to true to disallow avi to create and manage new security groups.
            - Avi will only make use of custom security groups provided by user.
            - This option is only supported for aws cloud type.
            - Field introduced in 17.2.13,18.1.4,18.2.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.9"
        type: bool
    disable_csum_offloads:
        description:
            - Stop using tcp/udp and ip checksum offload features of nics.
            - Field introduced in 17.1.14, 17.2.5, 18.1.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.5"
        type: bool
    disable_gro:
        description:
            - Disable generic receive offload (gro) in dpdk poll-mode driver packet receive path.
            - Gro is on by default on nics that do not support lro (large receive offload) or do not gain performance boost from lro.
            - Field introduced in 17.2.5, 18.1.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
        version_added: "2.5"
        type: bool
    disable_se_memory_check:
        description:
            - If set, disable the config memory check done in service engine.
            - Field introduced in 18.1.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.9"
        type: bool
    disable_tso:
        description:
            - Disable tcp segmentation offload (tso) in dpdk poll-mode driver packet transmit path.
            - Tso is on by default on nics that support it.
            - Field introduced in 17.2.5, 18.1.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
        version_added: "2.5"
        type: bool
    disk_per_se:
        description:
            - Amount of disk space for each of the service engine virtual machines.
            - Default value when not specified in API or module is interpreted by Avi Controller as 10.
    distribute_load_active_standby:
        description:
            - Use both the active and standby service engines for virtual service placement in the legacy active standby ha mode.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    distribute_queues:
        description:
            - Distributes queue ownership among cores so multiple cores handle dispatcher duties.
            - Field introduced in 17.2.8.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.9"
        type: bool
    enable_hsm_priming:
        description:
            - (this is a beta feature).
            - Enable hsm key priming.
            - If enabled, key handles on the hsm will be synced to se before processing client connections.
            - Field introduced in 17.2.7, 18.1.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.6"
        type: bool
    enable_multi_lb:
        description:
            - Applicable only for azure cloud with basic sku lb.
            - If set, additional azure lbs will be automatically created if resources in existing lb are exhausted.
            - Field introduced in 17.2.10, 18.1.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.9"
        type: bool
    enable_routing:
        description:
            - Enable routing for this serviceenginegroup .
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    enable_vip_on_all_interfaces:
        description:
            - Enable vip on all interfaces of se.
            - Field introduced in 17.1.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
        type: bool
    enable_vmac:
        description:
            - Use virtual mac address for interfaces on which floating interface ips are placed.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    ephemeral_portrange_end:
        description:
            - End local ephemeral port number for outbound connections.
            - Field introduced in 17.2.13, 18.1.5, 18.2.1.
        version_added: "2.9"
    ephemeral_portrange_start:
        description:
            - Start local ephemeral port number for outbound connections.
            - Field introduced in 17.2.13, 18.1.5, 18.2.1.
        version_added: "2.9"
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
    flow_table_new_syn_max_entries:
        description:
            - Maximum number of flow table entries that have not completed tcp three-way handshake yet.
            - Field introduced in 17.2.5.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
        version_added: "2.5"
    free_list_size:
        description:
            - Number of entries in the free list.
            - Field introduced in 17.2.10, 18.1.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1024.
        version_added: "2.9"
    ha_mode:
        description:
            - High availability mode for all the virtual services using this service engine group.
            - Enum options - HA_MODE_SHARED_PAIR, HA_MODE_SHARED, HA_MODE_LEGACY_ACTIVE_STANDBY.
            - Default value when not specified in API or module is interpreted by Avi Controller as HA_MODE_SHARED.
    hardwaresecuritymodulegroup_ref:
        description:
            - It is a reference to an object of type hardwaresecuritymodulegroup.
    heap_minimum_config_memory:
        description:
            - Minimum required heap memory to apply any configuration.
            - Allowed values are 0-100.
            - Field introduced in 18.1.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as 8.
        version_added: "2.9"
    hm_on_standby:
        description:
            - Enable active health monitoring from the standby se for all placed virtual services.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
        type: bool
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
    host_gateway_monitor:
        description:
            - Enable the host gateway monitor when service engine is deployed as docker container.
            - Disabled by default.
            - Field introduced in 17.2.4.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.5"
        type: bool
    hypervisor:
        description:
            - Override default hypervisor.
            - Enum options - DEFAULT, VMWARE_ESX, KVM, VMWARE_VSAN, XEN.
    ignore_rtt_threshold:
        description:
            - Ignore rtt samples if it is above threshold.
            - Field introduced in 17.1.6,17.2.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as 5000.
        version_added: "2.5"
    ingress_access_data:
        description:
            - Program se security group ingress rules to allow vip data access from remote cidr type.
            - Enum options - SG_INGRESS_ACCESS_NONE, SG_INGRESS_ACCESS_ALL, SG_INGRESS_ACCESS_VPC.
            - Field introduced in 17.1.5.
            - Default value when not specified in API or module is interpreted by Avi Controller as SG_INGRESS_ACCESS_ALL.
        version_added: "2.5"
    ingress_access_mgmt:
        description:
            - Program se security group ingress rules to allow ssh/icmp management access from remote cidr type.
            - Enum options - SG_INGRESS_ACCESS_NONE, SG_INGRESS_ACCESS_ALL, SG_INGRESS_ACCESS_VPC.
            - Field introduced in 17.1.5.
            - Default value when not specified in API or module is interpreted by Avi Controller as SG_INGRESS_ACCESS_ALL.
        version_added: "2.5"
    instance_flavor:
        description:
            - Instance/flavor name for se instance.
    iptables:
        description:
            - Iptables rules.
    least_load_core_selection:
        description:
            - Select core with least load for new flow.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
        type: bool
    license_tier:
        description:
            - Specifies the license tier which would be used.
            - This field by default inherits the value from cloud.
            - Enum options - ENTERPRISE_16, ENTERPRISE_18.
            - Field introduced in 17.2.5.
        version_added: "2.5"
    license_type:
        description:
            - If no license type is specified then default license enforcement for the cloud type is chosen.
            - Enum options - LIC_BACKEND_SERVERS, LIC_SOCKETS, LIC_CORES, LIC_HOSTS, LIC_SE_BANDWIDTH, LIC_METERED_SE_BANDWIDTH.
            - Field introduced in 17.2.5.
        version_added: "2.5"
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
    max_memory_per_mempool:
        description:
            - Max bytes that can be allocated in a single mempool.
            - Field introduced in 18.1.5.
            - Default value when not specified in API or module is interpreted by Avi Controller as 64.
        version_added: "2.9"
    max_public_ips_per_lb:
        description:
            - Applicable to azure platform only.
            - Maximum number of public ips per azure lb.
            - Field introduced in 17.2.12, 18.1.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as 30.
        version_added: "2.9"
    max_rules_per_lb:
        description:
            - Applicable to azure platform only.
            - Maximum number of rules per azure lb.
            - Field introduced in 17.2.12, 18.1.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as 150.
        version_added: "2.9"
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
        type: bool
    memory_for_config_update:
        description:
            - Indicates the percent of memory reserved for config updates.
            - Allowed values are 0-100.
            - Field introduced in 18.1.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as 15.
        version_added: "2.9"
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
    min_se:
        description:
            - Minimum number of services engines in this group (relevant for se autorebalance only).
            - Allowed values are 0-1000.
            - Field introduced in 17.2.13,18.1.3,18.2.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.
        version_added: "2.9"
    minimum_connection_memory:
        description:
            - Indicates the percent of memory reserved for connections.
            - Allowed values are 0-100.
            - Field introduced in 18.1.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as 20.
        version_added: "2.9"
    minimum_required_config_memory:
        description:
            - Required available config memory to apply any configuration.
            - Allowed values are 0-90.
            - Field deprecated in 18.1.2.
            - Field introduced in 18.1.1.
        version_added: "2.9"
    n_log_streaming_threads:
        description:
            - Number of threads to use for log streaming.
            - Allowed values are 1-100.
            - Field introduced in 17.2.12, 18.1.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.
        version_added: "2.9"
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
    num_dispatcher_cores:
        description:
            - Number of dispatcher cores (0,1,2,4,8 or 16).
            - If set to 0, then number of dispatcher cores is deduced automatically.
            - Allowed values are 0,1,2,4,8,16.
            - Field introduced in 17.2.12, 18.1.3, 18.2.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
        version_added: "2.9"
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
        type: bool
    placement_mode:
        description:
            - If placement mode is 'auto', virtual services are automatically placed on service engines.
            - Enum options - PLACEMENT_MODE_AUTO.
            - Default value when not specified in API or module is interpreted by Avi Controller as PLACEMENT_MODE_AUTO.
    realtime_se_metrics:
        description:
            - Enable or disable real time se metrics.
    reboot_on_stop:
        description:
            - Reboot the system if the se is stopped.
            - Field introduced in 17.2.16,18.2.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.9"
        type: bool
    se_bandwidth_type:
        description:
            - Select the se bandwidth for the bandwidth license.
            - Enum options - SE_BANDWIDTH_UNLIMITED, SE_BANDWIDTH_25M, SE_BANDWIDTH_200M, SE_BANDWIDTH_1000M, SE_BANDWIDTH_10000M.
            - Field introduced in 17.2.5.
        version_added: "2.5"
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
    se_dpdk_pmd:
        description:
            - Determines if dpdk pool mode driver should be used or not   0  automatically determine based on hypervisor/nic type 1  unconditionally use dpdk
            - poll mode driver 2  don't use dpdk poll mode driver.
            - Allowed values are 0-2.
            - Field introduced in 18.1.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
        version_added: "2.9"
    se_flow_probe_retries:
        description:
            - Flow probe retry count if no replies are received.
            - Allowed values are 0-5.
            - Field introduced in 18.1.4, 18.2.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as 2.
        version_added: "2.9"
    se_flow_probe_timer:
        description:
            - Timeout in milliseconds for flow probe entries.
            - Allowed values are 10-200.
            - Field introduced in 18.1.4, 18.2.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as 100.
        version_added: "2.9"
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
    se_pcap_lookahead:
        description:
            - Enables lookahead mode of packet receive in pcap mode.
            - Introduced to overcome an issue with hv_netvsc driver.
            - Lookahead mode attempts to ensure that application and kernel's view of the receive rings are consistent.
            - Field introduced in 18.2.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.9"
        type: bool
    se_pcap_reinit_frequency:
        description:
            - Frequency in seconds at which periodically a pcap reinit check is triggered.
            - May be used in conjunction with the configuration pcap_reinit_threshold.
            - (valid range   15 mins - 12 hours, 0 - disables).
            - Allowed values are 900-43200.
            - Special values are 0- 'disable'.
            - Field introduced in 17.2.13, 18.1.3, 18.2.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
        version_added: "2.9"
    se_pcap_reinit_threshold:
        description:
            - Threshold for input packet receive errors in pcap mode exceeding which a pcap reinit is triggered.
            - If not set, an unconditional reinit is performed.
            - This value is checked every pcap_reinit_frequency interval.
            - Field introduced in 17.2.13, 18.1.3, 18.2.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
        version_added: "2.9"
    se_probe_port:
        description:
            - Tcp port on se where echo service will be run.
            - Field introduced in 17.2.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as 7.
        version_added: "2.5"
    se_remote_punt_udp_port:
        description:
            - Udp port for punted packets in docker bridge mode.
            - Field introduced in 17.1.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1501.
        version_added: "2.4"
    se_routing:
        description:
            - Enable routing via service engine datapath.
            - When disabled, routing is done by the linux kernel.
            - Ip routing needs to be enabled in service engine group for se routing to be effective.
            - Field introduced in 18.2.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
        version_added: "2.9"
        type: bool
    se_sb_dedicated_core:
        description:
            - Sideband traffic will be handled by a dedicated core.
            - Field introduced in 16.5.2, 17.1.9, 17.2.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.5"
        type: bool
    se_sb_threads:
        description:
            - Number of sideband threads per se.
            - Allowed values are 1-128.
            - Field introduced in 16.5.2, 17.1.9, 17.2.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.
        version_added: "2.5"
    se_thread_multiplier:
        description:
            - Multiplier for se threads based on vcpu.
            - Allowed values are 1-10.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.
    se_tracert_port_range:
        description:
            - Traceroute port range.
            - Field introduced in 17.2.8.
        version_added: "2.9"
    se_tunnel_mode:
        description:
            - Determines if dsr from secondary se is active or not  0  automatically determine based on hypervisor type.
            - 1  disable dsr unconditionally.
            - 2  enable dsr unconditionally.
            - Allowed values are 0-2.
            - Field introduced in 17.1.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
    se_tunnel_udp_port:
        description:
            - Udp port for tunneled packets from secondary to primary se in docker bridge mode.
            - Field introduced in 17.1.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1550.
    se_udp_encap_ipc:
        description:
            - Determines if se-se ipc messages are encapsulated in a udp header  0  automatically determine based on hypervisor type.
            - 1  use udp encap unconditionally.
            - Allowed values are 0-1.
            - Field introduced in 17.1.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
        version_added: "2.4"
    se_use_dpdk:
        description:
            - Determines if dpdk library should be used or not   0  automatically determine based on hypervisor type 1  use dpdk if pcap is not enabled 2
            - don't use dpdk.
            - Allowed values are 0-2.
            - Field introduced in 18.1.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
        version_added: "2.9"
    se_vs_hb_max_pkts_in_batch:
        description:
            - Maximum number of aggregated vs heartbeat packets to send in a batch.
            - Allowed values are 1-256.
            - Field introduced in 17.1.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as 64.
    se_vs_hb_max_vs_in_pkt:
        description:
            - Maximum number of virtualservices for which heartbeat messages are aggregated in one packet.
            - Allowed values are 1-1024.
            - Field introduced in 17.1.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as 256.
    self_se_election:
        description:
            - Enable ses to elect a primary amongst themselves in the absence of a connectivity to controller.
            - Field introduced in 18.1.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.9"
        type: bool
    service_ip6_subnets:
        description:
            - Ipv6 subnets assigned to the se group.
            - Required for vs group placement.
            - Field introduced in 18.1.1.
        version_added: "2.9"
    service_ip_subnets:
        description:
            - Subnets assigned to the se group.
            - Required for vs group placement.
            - Field introduced in 17.1.1.
    shm_minimum_config_memory:
        description:
            - Minimum required shared memory to apply any configuration.
            - Allowed values are 0-100.
            - Field introduced in 18.1.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as 4.
        version_added: "2.9"
    significant_log_throttle:
        description:
            - This setting limits the number of significant logs generated per second per core on this se.
            - Default is 100 logs per second.
            - Set it to zero (0) to disable throttling.
            - Field introduced in 17.1.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as 100.
    ssl_preprocess_sni_hostname:
        description:
            - (beta) preprocess ssl client hello for sni hostname extension.if set to true, this will apply sni child's ssl protocol(s), if they are different
            - from sni parent's allowed ssl protocol(s).
            - Field introduced in 17.2.12, 18.1.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
        version_added: "2.9"
        type: bool
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
    use_standard_alb:
        description:
            - Use standard sku azure load balancer.
            - By default cloud level flag is set.
            - If not set, it inherits/uses the use_standard_alb flag from the cloud.
            - Field introduced in 18.2.3.
        version_added: "2.9"
        type: bool
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
        type: bool
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
    vip_asg:
        description:
            - When vip_asg is set, vip configuration will be managed by avi.user will be able to configure vip_asg or vips individually at the time of create.
            - Field introduced in 17.2.12, 18.1.2.
        version_added: "2.9"
    vs_host_redundancy:
        description:
            - Ensure primary and secondary service engines are deployed on different physical hosts.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
        type: bool
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
            - Default value when not specified in API or module is interpreted by Avi Controller as 600.
    vs_se_scaleout_additional_wait_time:
        description:
            - Wait time for sending scaleout ready notification after virtual service is marked up.
            - In certain deployments, there may be an additional delay to accept traffic.
            - For example, for bgp, some time is needed for route advertisement.
            - Allowed values are 0-20.
            - Field introduced in 18.1.5,18.2.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
        version_added: "2.9"
    vs_se_scaleout_ready_timeout:
        description:
            - Timeout in seconds for service engine to sendscaleout ready notification of a virtual service.
            - Allowed values are 0-60.
            - Field introduced in 18.1.5,18.2.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as 25.
        version_added: "2.9"
    vs_switchover_timeout:
        description:
            - During se upgrade in a legacy active/standby segroup, time to wait for the new primary se to accept flows before marking the switchover done.
            - Field introduced in 17.2.13,18.1.4,18.2.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as 300.
        version_added: "2.9"
    vss_placement:
        description:
            - Parameters to place virtual services on only a subset of the cores of an se.
            - Field introduced in 17.2.5.
        version_added: "2.5"
    vss_placement_enabled:
        description:
            - If set, virtual services will be placed on only a subset of the cores of an se.
            - Field introduced in 18.1.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.9"
        type: bool
    waf_learning_interval:
        description:
            - Frequency with which se publishes waf learning.
            - Allowed values are 1-43200.
            - Field deprecated in 18.2.3.
            - Field introduced in 18.1.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as 10.
        version_added: "2.9"
    waf_learning_memory:
        description:
            - Amount of memory reserved on se for waf learning.
            - Cannot exceed 5% of se memory.
            - Field deprecated in 18.2.3.
            - Field introduced in 18.1.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
        version_added: "2.9"
    waf_mempool:
        description:
            - Enable memory pool for waf.
            - Field introduced in 17.2.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
        version_added: "2.5"
        type: bool
    waf_mempool_size:
        description:
            - Memory pool size used for waf.
            - Field introduced in 17.2.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as 64.
        version_added: "2.5"
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
    from ansible.module_utils.network.avi.avi import (
        avi_common_argument_spec, avi_ansible_api, HAS_AVI)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
        avi_api_update_method=dict(default='put',
                                   choices=['put', 'patch']),
        avi_api_patch_op=dict(choices=['add', 'replace', 'delete']),
        accelerated_networking=dict(type='bool',),
        active_standby=dict(type='bool',),
        additional_config_memory=dict(type='int',),
        advertise_backend_networks=dict(type='bool',),
        aggressive_failure_detection=dict(type='bool',),
        algo=dict(type='str',),
        allow_burst=dict(type='bool',),
        app_cache_percent=dict(type='int',),
        app_learning_memory_percent=dict(type='int',),
        archive_shm_limit=dict(type='int',),
        async_ssl=dict(type='bool',),
        async_ssl_threads=dict(type='int',),
        auto_rebalance=dict(type='bool',),
        auto_rebalance_capacity_per_se=dict(type='list',),
        auto_rebalance_criteria=dict(type='list',),
        auto_rebalance_interval=dict(type='int',),
        auto_redistribute_active_standby_load=dict(type='bool',),
        bgp_state_update_interval=dict(type='int',),
        buffer_se=dict(type='int',),
        cloud_ref=dict(type='str',),
        config_debugs_on_all_cores=dict(type='bool',),
        connection_memory_percentage=dict(type='int',),
        cpu_reserve=dict(type='bool',),
        cpu_socket_affinity=dict(type='bool',),
        custom_securitygroups_data=dict(type='list',),
        custom_securitygroups_mgmt=dict(type='list',),
        custom_tag=dict(type='list',),
        data_network_id=dict(type='str',),
        datascript_timeout=dict(type='int',),
        dedicated_dispatcher_core=dict(type='bool',),
        description=dict(type='str',),
        disable_avi_securitygroups=dict(type='bool',),
        disable_csum_offloads=dict(type='bool',),
        disable_gro=dict(type='bool',),
        disable_se_memory_check=dict(type='bool',),
        disable_tso=dict(type='bool',),
        disk_per_se=dict(type='int',),
        distribute_load_active_standby=dict(type='bool',),
        distribute_queues=dict(type='bool',),
        enable_hsm_priming=dict(type='bool',),
        enable_multi_lb=dict(type='bool',),
        enable_routing=dict(type='bool',),
        enable_vip_on_all_interfaces=dict(type='bool',),
        enable_vmac=dict(type='bool',),
        ephemeral_portrange_end=dict(type='int',),
        ephemeral_portrange_start=dict(type='int',),
        extra_config_multiplier=dict(type='float',),
        extra_shared_config_memory=dict(type='int',),
        floating_intf_ip=dict(type='list',),
        floating_intf_ip_se_2=dict(type='list',),
        flow_table_new_syn_max_entries=dict(type='int',),
        free_list_size=dict(type='int',),
        ha_mode=dict(type='str',),
        hardwaresecuritymodulegroup_ref=dict(type='str',),
        heap_minimum_config_memory=dict(type='int',),
        hm_on_standby=dict(type='bool',),
        host_attribute_key=dict(type='str',),
        host_attribute_value=dict(type='str',),
        host_gateway_monitor=dict(type='bool',),
        hypervisor=dict(type='str',),
        ignore_rtt_threshold=dict(type='int',),
        ingress_access_data=dict(type='str',),
        ingress_access_mgmt=dict(type='str',),
        instance_flavor=dict(type='str',),
        iptables=dict(type='list',),
        least_load_core_selection=dict(type='bool',),
        license_tier=dict(type='str',),
        license_type=dict(type='str',),
        log_disksz=dict(type='int',),
        max_cpu_usage=dict(type='int',),
        max_memory_per_mempool=dict(type='int',),
        max_public_ips_per_lb=dict(type='int',),
        max_rules_per_lb=dict(type='int',),
        max_scaleout_per_vs=dict(type='int',),
        max_se=dict(type='int',),
        max_vs_per_se=dict(type='int',),
        mem_reserve=dict(type='bool',),
        memory_for_config_update=dict(type='int',),
        memory_per_se=dict(type='int',),
        mgmt_network_ref=dict(type='str',),
        mgmt_subnet=dict(type='dict',),
        min_cpu_usage=dict(type='int',),
        min_scaleout_per_vs=dict(type='int',),
        min_se=dict(type='int',),
        minimum_connection_memory=dict(type='int',),
        minimum_required_config_memory=dict(type='int',),
        n_log_streaming_threads=dict(type='int',),
        name=dict(type='str', required=True),
        non_significant_log_throttle=dict(type='int',),
        num_dispatcher_cores=dict(type='int',),
        num_flow_cores_sum_changes_to_ignore=dict(type='int',),
        openstack_availability_zone=dict(type='str',),
        openstack_availability_zones=dict(type='list',),
        openstack_mgmt_network_name=dict(type='str',),
        openstack_mgmt_network_uuid=dict(type='str',),
        os_reserved_memory=dict(type='int',),
        per_app=dict(type='bool',),
        placement_mode=dict(type='str',),
        realtime_se_metrics=dict(type='dict',),
        reboot_on_stop=dict(type='bool',),
        se_bandwidth_type=dict(type='str',),
        se_deprovision_delay=dict(type='int',),
        se_dos_profile=dict(type='dict',),
        se_dpdk_pmd=dict(type='int',),
        se_flow_probe_retries=dict(type='int',),
        se_flow_probe_timer=dict(type='int',),
        se_ipc_udp_port=dict(type='int',),
        se_name_prefix=dict(type='str',),
        se_pcap_lookahead=dict(type='bool',),
        se_pcap_reinit_frequency=dict(type='int',),
        se_pcap_reinit_threshold=dict(type='int',),
        se_probe_port=dict(type='int',),
        se_remote_punt_udp_port=dict(type='int',),
        se_routing=dict(type='bool',),
        se_sb_dedicated_core=dict(type='bool',),
        se_sb_threads=dict(type='int',),
        se_thread_multiplier=dict(type='int',),
        se_tracert_port_range=dict(type='dict',),
        se_tunnel_mode=dict(type='int',),
        se_tunnel_udp_port=dict(type='int',),
        se_udp_encap_ipc=dict(type='int',),
        se_use_dpdk=dict(type='int',),
        se_vs_hb_max_pkts_in_batch=dict(type='int',),
        se_vs_hb_max_vs_in_pkt=dict(type='int',),
        self_se_election=dict(type='bool',),
        service_ip6_subnets=dict(type='list',),
        service_ip_subnets=dict(type='list',),
        shm_minimum_config_memory=dict(type='int',),
        significant_log_throttle=dict(type='int',),
        ssl_preprocess_sni_hostname=dict(type='bool',),
        tenant_ref=dict(type='str',),
        udf_log_throttle=dict(type='int',),
        url=dict(type='str',),
        use_standard_alb=dict(type='bool',),
        uuid=dict(type='str',),
        vcenter_clusters=dict(type='dict',),
        vcenter_datastore_mode=dict(type='str',),
        vcenter_datastores=dict(type='list',),
        vcenter_datastores_include=dict(type='bool',),
        vcenter_folder=dict(type='str',),
        vcenter_hosts=dict(type='dict',),
        vcpus_per_se=dict(type='int',),
        vip_asg=dict(type='dict',),
        vs_host_redundancy=dict(type='bool',),
        vs_scalein_timeout=dict(type='int',),
        vs_scalein_timeout_for_upgrade=dict(type='int',),
        vs_scaleout_timeout=dict(type='int',),
        vs_se_scaleout_additional_wait_time=dict(type='int',),
        vs_se_scaleout_ready_timeout=dict(type='int',),
        vs_switchover_timeout=dict(type='int',),
        vss_placement=dict(type='dict',),
        vss_placement_enabled=dict(type='bool',),
        waf_learning_interval=dict(type='int',),
        waf_learning_memory=dict(type='int',),
        waf_mempool=dict(type='bool',),
        waf_mempool_size=dict(type='int',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) or requests is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'serviceenginegroup',
                           set([]))


if __name__ == '__main__':
    main()
