#!/usr/bin/python
#
# Created on Aug 25, 2016
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
# Avi Version: 16.3.8
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

ANSIBLE_METADATA = {'status': ['preview'], 'supported_by': 'community', 'version': '1.0'}

DOCUMENTATION = '''
---
module: avi_serviceenginegroup
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of ServiceEngineGroup Avi RESTful Object
description:
    - This module is used to configure ServiceEngineGroup object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.3"
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
            - In compact placement virtual services are placed on existing service engines until they all have the max_vs_per_se limit is reached.
            - Otherwise, virtual services are distributed to as many service engines as possible.
            - Default value when not specified in API or module is interpreted by Avi Controller as PLACEMENT_ALGO_PACKED.
    auto_rebalance:
        description:
            - Virtualservices will be automatically migrated based on the load on service engines outside of range determined by minimum and maximum thresholds.
            - Otherwise, an alert is generated instead of automatically performing the migration.
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
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    enable_vmac:
        description:
            - Use virtual mac address for interfaces on which floating interface ips are placed.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    extra_config_multiplier:
        description:
            - Multiplier for extra config to support large vs/pool config.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.0.
    floating_intf_ip:
        description:
            - If serviceenginegroup is configured for legacy 1+1 active standby ha mode, floating ip's will be advertised only by the active se in the pair.
            - Virtual services in this group must be disabled/enabled for any changes to the floating ip's to take effect.
            - Only active se hosting vs tagged with active standby se 1 tag will advertise this floating ip when manual load distribution is enabled.
    floating_intf_ip_se_2:
        description:
            - This field is applicable only if the serviceenginegroup is configured for legacy 1+1 active standby ha mode and manual load distribution.
            - Floating ip's provided here will be advertised only by the active se hosting all the virtualservices tagged with active standby se 2 tag.
    ha_mode:
        description:
            - High availability mode for all the virtual services using this service engine group.
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
            - Key of a key,value pair identifying a set of hosts.
            - Currently used to separate north-south and east-west serviceengine sizing requirements.
            - Specifically in container ecosystems, where ses on east-west traffic nodes are typically smaller than those on north-south traffic nodes.
    host_attribute_value:
        description:
            - Value of a key,value pair identifying a set of hosts.
            - Currently used to separate north-south and east-west serviceengine sizing requirements.
            - Specifically in container ecosystems, where ses on east-west traffic nodes are typically smaller than those on north-south traffic nodes.
    hypervisor:
        description:
            - Override default hypervisor.
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
            - When cpu utilization exceeds this maximum threshold, virtual services hosted on this se may be rebalanced to other se to reduce load.
            - A new service engine may be created as part of this process.
            - Default value when not specified in API or module is interpreted by Avi Controller as 80.
    max_scaleout_per_vs:
        description:
            - Maximum number of active service engines for the virtual service.
            - Default value when not specified in API or module is interpreted by Avi Controller as 4.
    max_se:
        description:
            - Maximum number of services engines in this group.
            - Default value when not specified in API or module is interpreted by Avi Controller as 10.
    max_vs_per_se:
        description:
            - Maximum number of virtual services that can be placed on a single service engine.
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
            - When cpu usage falls below the minimum threshold, virtual services hosted on this se may be consolidated onto other underutilized ses.
            - After consolidation, unused service engines may then be eligible for deletion.
            - When cpu usage exceeds the maximum threshold, virtual services hosted on an se may be migrated to other ses to reduce load.
            - A new service engine may be created as part of this process.
            - Default value when not specified in API or module is interpreted by Avi Controller as 30.
    min_scaleout_per_vs:
        description:
            - Minimum number of active service engines for the virtual service.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.
    name:
        description:
            - Name of the object.
        required: true
    num_flow_cores_sum_changes_to_ignore:
        description:
            - Number of changes in num flow cores sum to ignore.
            - Default value when not specified in API or module is interpreted by Avi Controller as 8.
    openstack_availability_zone:
        description:
            - Openstack_availability_zone of serviceenginegroup.
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
            - Default value when not specified in API or module is interpreted by Avi Controller as PLACEMENT_MODE_AUTO.
    realtime_se_metrics:
        description:
            - Enable or disable real time se metrics.
    se_deprovision_delay:
        description:
            - Duration to preserve unused service engine virtual machines before deleting them.
            - If traffic to a virtual service were to spike up abruptly, this se would still be available to be utilized again rather than creating a new se.
            - If this value is set to 0, controller will never delete any ses, administrator has to manually cleanup unused ses.
            - Default value when not specified in API or module is interpreted by Avi Controller as 120.
    se_dos_profile:
        description:
            - Dosthresholdprofile settings for serviceenginegroup.
    se_name_prefix:
        description:
            - Prefix to use for virtual machine name of service engines.
            - Default value when not specified in API or module is interpreted by Avi Controller as Avi.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
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
            - Vcenter_datastore_mode of serviceenginegroup.
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
            - Default value when not specified in API or module is interpreted by Avi Controller as 2.
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
        auto_rebalance=dict(type='bool',),
        auto_rebalance_interval=dict(type='int',),
        auto_redistribute_active_standby_load=dict(type='bool',),
        buffer_se=dict(type='int',),
        cloud_ref=dict(type='str',),
        connection_memory_percentage=dict(type='int',),
        cpu_reserve=dict(type='bool',),
        cpu_socket_affinity=dict(type='bool',),
        custom_tag=dict(type='list',),
        dedicated_dispatcher_core=dict(type='bool',),
        description=dict(type='str',),
        disk_per_se=dict(type='int',),
        distribute_load_active_standby=dict(type='bool',),
        enable_routing=dict(type='bool',),
        enable_vip_on_all_interfaces=dict(type='bool',),
        enable_vmac=dict(type='bool',),
        extra_config_multiplier=dict(type='float',),
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
        num_flow_cores_sum_changes_to_ignore=dict(type='int',),
        openstack_availability_zone=dict(type='str',),
        openstack_mgmt_network_name=dict(type='str',),
        openstack_mgmt_network_uuid=dict(type='str',),
        os_reserved_memory=dict(type='int',),
        per_app=dict(type='bool',),
        placement_mode=dict(type='str',),
        realtime_se_metrics=dict(type='dict',),
        se_deprovision_delay=dict(type='int',),
        se_dos_profile=dict(type='dict',),
        se_name_prefix=dict(type='str',),
        tenant_ref=dict(type='str',),
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
            'Avi python API SDK (avisdk>=16.3.5.post1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'serviceenginegroup',
                           set([]))


if __name__ == '__main__':
    main()
