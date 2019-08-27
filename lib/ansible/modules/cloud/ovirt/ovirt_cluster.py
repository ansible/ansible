#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovirt_cluster
short_description: Module to manage clusters in oVirt/RHV
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage clusters in oVirt/RHV"
options:
    id:
        description:
            - "ID of the cluster to manage."
        version_added: "2.8"
    name:
        description:
            - "Name of the cluster to manage."
        required: true
    state:
        description:
            - "Should the cluster be present or absent."
        choices: ['present', 'absent']
        default: present
    data_center:
        description:
            - "Datacenter name where cluster reside."
    description:
        description:
            - "Description of the cluster."
    comment:
        description:
            - "Comment of the cluster."
    network:
        description:
            - "Management network of cluster to access cluster hosts."
    ballooning:
        description:
            - "If I(True) enable memory balloon optimization. Memory balloon is used to
               re-distribute / reclaim the host memory based on VM needs
               in a dynamic way."
        type: bool
    virt:
        description:
            - "If I(True), hosts in this cluster will be used to run virtual machines."
        type: bool
    gluster:
        description:
            - "If I(True), hosts in this cluster will be used as Gluster Storage
               server nodes, and not for running virtual machines."
            - "By default the cluster is created for virtual machine hosts."
        type: bool
    threads_as_cores:
        description:
            - "If I(True) the exposed host threads would be treated as cores
               which can be utilized by virtual machines."
        type: bool
    ksm:
        description:
            - "I I(True) MoM enables to run Kernel Same-page Merging I(KSM) when
               necessary and when it can yield a memory saving benefit that
               outweighs its CPU cost."
        type: bool
    ksm_numa:
        description:
            - "If I(True) enables KSM C(ksm) for best performance inside NUMA nodes."
        type: bool
    ha_reservation:
        description:
            - "If I(True) enables the oVirt/RHV to monitor cluster capacity for highly
               available virtual machines."
        type: bool
    trusted_service:
        description:
            - "If I(True) enables integration with an OpenAttestation server."
        type: bool
    vm_reason:
        description:
            - "If I(True) enables an optional reason field when a virtual machine
               is shut down from the Manager, allowing the administrator to
               provide an explanation for the maintenance."
        type: bool
    host_reason:
        description:
            - "If I(True) enables an optional reason field when a host is placed
               into maintenance mode from the Manager, allowing the administrator
               to provide an explanation for the maintenance."
        type: bool
    memory_policy:
        description:
            - "I(disabled) - Disables memory page sharing."
            - "I(server) - Sets the memory page sharing threshold to 150% of the system memory on each host."
            - "I(desktop) - Sets the memory page sharing threshold to 200% of the system memory on each host."
        choices: ['disabled', 'server', 'desktop']
    rng_sources:
        description:
            - "List that specify the random number generator devices that all hosts in the cluster will use."
            - "Supported generators are: I(hwrng) and I(random)."
    spice_proxy:
        description:
            - "The proxy by which the SPICE client will connect to virtual machines."
            - "The address must be in the following format: I(protocol://[host]:[port])"
    fence_enabled:
        description:
            - "If I(True) enables fencing on the cluster."
            - "Fencing is enabled by default."
        type: bool
    fence_skip_if_gluster_bricks_up:
        description:
            - "A flag indicating if fencing should be skipped if Gluster bricks are up and running in the host being fenced."
            - "This flag is optional, and the default value is `false`."
        type: bool
        version_added: "2.8"
    fence_skip_if_gluster_quorum_not_met:
        description:
            - "A flag indicating if fencing should be skipped if Gluster bricks are up and running and Gluster quorum will not
               be met without those bricks."
            - "This flag is optional, and the default value is `false`."
        type: bool
        version_added: "2.8"
    fence_skip_if_sd_active:
        description:
            - "If I(True) any hosts in the cluster that are Non Responsive
               and still connected to storage will not be fenced."
        type: bool
    fence_skip_if_connectivity_broken:
        description:
            - "If I(True) fencing will be temporarily disabled if the percentage
               of hosts in the cluster that are experiencing connectivity issues
               is greater than or equal to the defined threshold."
            - "The threshold can be specified by C(fence_connectivity_threshold)."
        type: bool
    fence_connectivity_threshold:
        description:
            - "The threshold used by C(fence_skip_if_connectivity_broken)."
    resilience_policy:
        description:
            - "The resilience policy defines how the virtual machines are prioritized in the migration."
            - "Following values are supported:"
            - "C(do_not_migrate) -  Prevents virtual machines from being migrated. "
            - "C(migrate) - Migrates all virtual machines in order of their defined priority."
            - "C(migrate_highly_available) - Migrates only highly available virtual machines to prevent overloading other hosts."
        choices: ['do_not_migrate', 'migrate', 'migrate_highly_available']
    migration_bandwidth:
        description:
            - "The bandwidth settings define the maximum bandwidth of both outgoing and incoming migrations per host."
            - "Following bandwidth options are supported:"
            - "C(auto) - Bandwidth is copied from the I(rate limit) [Mbps] setting in the data center host network QoS."
            - "C(hypervisor_default) - Bandwidth is controlled by local VDSM setting on sending host."
            - "C(custom) - Defined by user (in Mbps)."
        choices: ['auto', 'hypervisor_default', 'custom']
    migration_bandwidth_limit:
        description:
            - "Set the I(custom) migration bandwidth limit."
            - "This parameter is used only when C(migration_bandwidth) is I(custom)."
    migration_auto_converge:
        description:
            - "If I(True) auto-convergence is used during live migration of virtual machines."
            - "Used only when C(migration_policy) is set to I(legacy)."
            - "Following options are supported:"
            - "C(true) - Override the global setting to I(true)."
            - "C(false) - Override the global setting to I(false)."
            - "C(inherit) - Use value which is set globally."
        choices: ['true', 'false', 'inherit']
    migration_compressed:
        description:
            - "If I(True) compression is used during live migration of the virtual machine."
            - "Used only when C(migration_policy) is set to I(legacy)."
            - "Following options are supported:"
            - "C(true) - Override the global setting to I(true)."
            - "C(false) - Override the global setting to I(false)."
            - "C(inherit) - Use value which is set globally."
        choices: ['true', 'false', 'inherit']
    migration_policy:
        description:
            - "A migration policy defines the conditions for live migrating
               virtual machines in the event of host failure."
            - "Following policies are supported:"
            - "C(legacy) - Legacy behavior of 3.6 version."
            - "C(minimal_downtime) - Virtual machines should not experience any significant downtime."
            - "C(suspend_workload) - Virtual machines may experience a more significant downtime."
            - "C(post_copy) - Virtual machines should not experience any significant downtime.
               If the VM migration is not converging for a long time, the migration will be switched to post-copy.
               Added in version I(2.4)."
        choices: ['legacy', 'minimal_downtime', 'suspend_workload', 'post_copy']
    serial_policy:
        description:
            - "Specify a serial number policy for the virtual machines in the cluster."
            - "Following options are supported:"
            - "C(vm) - Sets the virtual machine's UUID as its serial number."
            - "C(host) - Sets the host's UUID as the virtual machine's serial number."
            - "C(custom) - Allows you to specify a custom serial number in C(serial_policy_value)."
    serial_policy_value:
        description:
            - "Allows you to specify a custom serial number."
            - "This parameter is used only when C(serial_policy) is I(custom)."
    scheduling_policy:
        description:
            - "Name of the scheduling policy to be used for cluster."
    scheduling_policy_properties:
        description:
            - "Custom scheduling policy properties of the cluster."
            - "These optional properties override the properties of the
               scheduling policy specified by the C(scheduling_policy) parameter."
        version_added: "2.6"
    cpu_arch:
        description:
            - "CPU architecture of cluster."
        choices: ['x86_64', 'ppc64', 'undefined']
    cpu_type:
        description:
            - "CPU codename. For example I(Intel SandyBridge Family)."
    switch_type:
        description:
            - "Type of switch to be used by all networks in given cluster.
               Either I(legacy) which is using linux bridge or I(ovs) using
               Open vSwitch."
        choices: ['legacy', 'ovs']
    compatibility_version:
        description:
            - "The compatibility version of the cluster. All hosts in this
               cluster must support at least this compatibility version."
    mac_pool:
        description:
            - "MAC pool to be used by this cluster."
            - "C(Note:)"
            - "This is supported since oVirt version 4.1."
        version_added: 2.4
    external_network_providers:
        description:
            - "List of references to the external network providers available
               in the cluster. If the automatic deployment of the external
               network provider is supported, the networks of the referenced
               network provider are available on every host in the cluster."
            - "This is supported since oVirt version 4.2."
        suboptions:
            name:
                description:
                    - Name of the external network provider. Either C(name) or C(id) is required.
            id:
                description:
                    - ID of the external network provider. Either C(name) or C(id) is required.
        version_added: 2.5
    firewall_type:
        description:
            - "The type of firewall to be used on hosts in this cluster."
            - "Up to version 4.1, it was always I(iptables). Since version 4.2, you can choose between I(iptables) and I(firewalld).
               For clusters with a compatibility version of 4.2 and higher, the default firewall type is I(firewalld)."
        type: str
        version_added: 2.8
        choices: ['firewalld', 'iptables']
    gluster_tuned_profile:
        description:
            - "The name of the U(https://fedorahosted.org/tuned) to set on all the hosts in the cluster. This is not mandatory
               and relevant only for clusters with Gluster service."
            - "Could be for example I(virtual-host), I(rhgs-sequential-io), I(rhgs-random-io)"
        version_added: 2.8
        type: str
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Create cluster
- ovirt_cluster:
    data_center: mydatacenter
    name: mycluster
    cpu_type: Intel SandyBridge Family
    description: mycluster
    compatibility_version: 4.0

# Create virt service cluster:
- ovirt_cluster:
    data_center: mydatacenter
    name: mycluster
    cpu_type: Intel Nehalem Family
    description: mycluster
    switch_type: legacy
    compatibility_version: 4.0
    ballooning: true
    gluster: false
    threads_as_cores: true
    ha_reservation: true
    trusted_service: false
    host_reason: false
    vm_reason: true
    ksm_numa: true
    memory_policy: server
    rng_sources:
      - hwrng
      - random

# Create cluster with default network provider
- ovirt_cluster:
    name: mycluster
    data_center: Default
    cpu_type: Intel SandyBridge Family
    external_network_providers:
      - name: ovirt-provider-ovn

# Remove cluster
- ovirt_cluster:
    state: absent
    name: mycluster

# Change cluster Name
- ovirt_cluster:
    id: 00000000-0000-0000-0000-000000000000
    name: "new_cluster_name"
'''

RETURN = '''
id:
    description: ID of the cluster which is managed
    returned: On success if cluster is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
cluster:
    description: "Dictionary of all the cluster attributes. Cluster attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/cluster."
    type: dict
    returned: On success if cluster is found.
'''

import traceback

try:
    import ovirtsdk4.types as otypes
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    BaseModule,
    check_sdk,
    create_connection,
    equal,
    ovirt_full_argument_spec,
    search_by_name,
    get_id_by_name,
)


class ClustersModule(BaseModule):

    def __get_major(self, full_version):
        if full_version is None:
            return None
        if isinstance(full_version, otypes.Version):
            return full_version.major
        return int(full_version.split('.')[0])

    def __get_minor(self, full_version):
        if full_version is None:
            return None
        if isinstance(full_version, otypes.Version):
            return full_version.minor
        return int(full_version.split('.')[1])

    def param(self, name, default=None):
        return self._module.params.get(name, default)

    def _get_memory_policy(self):
        memory_policy = self.param('memory_policy')
        if memory_policy == 'desktop':
            return 200
        elif memory_policy == 'server':
            return 150
        elif memory_policy == 'disabled':
            return 100

    def _get_policy_id(self):
        # These are hardcoded IDs, once there is API, please fix this.
        # legacy - 00000000-0000-0000-0000-000000000000
        # minimal downtime - 80554327-0569-496b-bdeb-fcbbf52b827b
        # suspend workload if needed - 80554327-0569-496b-bdeb-fcbbf52b827c
        # post copy - a7aeedb2-8d66-4e51-bb22-32595027ce71
        migration_policy = self.param('migration_policy')
        if migration_policy == 'legacy':
            return '00000000-0000-0000-0000-000000000000'
        elif migration_policy == 'minimal_downtime':
            return '80554327-0569-496b-bdeb-fcbbf52b827b'
        elif migration_policy == 'suspend_workload':
            return '80554327-0569-496b-bdeb-fcbbf52b827c'
        elif migration_policy == 'post_copy':
            return 'a7aeedb2-8d66-4e51-bb22-32595027ce71'

    def _get_sched_policy(self):
        sched_policy = None
        if self.param('scheduling_policy'):
            sched_policies_service = self._connection.system_service().scheduling_policies_service()
            sched_policy = search_by_name(sched_policies_service, self.param('scheduling_policy'))
            if not sched_policy:
                raise Exception("Scheduling policy '%s' was not found" % self.param('scheduling_policy'))

        return sched_policy

    def _get_mac_pool(self):
        mac_pool = None
        if self._module.params.get('mac_pool'):
            mac_pool = search_by_name(
                self._connection.system_service().mac_pools_service(),
                self._module.params.get('mac_pool'),
            )

        return mac_pool

    def _get_external_network_providers(self):
        return self.param('external_network_providers') or []

    def _get_external_network_provider_id(self, external_provider):
        return external_provider.get('id') or get_id_by_name(
            self._connection.system_service().openstack_network_providers_service(),
            external_provider.get('name')
        )

    def _get_external_network_providers_entity(self):
        if self.param('external_network_providers') is not None:
            return [otypes.ExternalProvider(id=self._get_external_network_provider_id(external_provider))
                    for external_provider in self.param('external_network_providers')]

    def build_entity(self):
        sched_policy = self._get_sched_policy()
        return otypes.Cluster(
            id=self.param('id'),
            name=self.param('name'),
            comment=self.param('comment'),
            description=self.param('description'),
            ballooning_enabled=self.param('ballooning'),
            gluster_service=self.param('gluster'),
            virt_service=self.param('virt'),
            threads_as_cores=self.param('threads_as_cores'),
            ha_reservation=self.param('ha_reservation'),
            trusted_service=self.param('trusted_service'),
            optional_reason=self.param('vm_reason'),
            maintenance_reason_required=self.param('host_reason'),
            scheduling_policy=otypes.SchedulingPolicy(
                id=sched_policy.id,
            ) if sched_policy else None,
            serial_number=otypes.SerialNumber(
                policy=otypes.SerialNumberPolicy(self.param('serial_policy')),
                value=self.param('serial_policy_value'),
            ) if (
                self.param('serial_policy') is not None or
                self.param('serial_policy_value') is not None
            ) else None,
            migration=otypes.MigrationOptions(
                auto_converge=otypes.InheritableBoolean(
                    self.param('migration_auto_converge'),
                ) if self.param('migration_auto_converge') else None,
                bandwidth=otypes.MigrationBandwidth(
                    assignment_method=otypes.MigrationBandwidthAssignmentMethod(
                        self.param('migration_bandwidth'),
                    ) if self.param('migration_bandwidth') else None,
                    custom_value=self.param('migration_bandwidth_limit'),
                ) if (
                    self.param('migration_bandwidth') or
                    self.param('migration_bandwidth_limit')
                ) else None,
                compressed=otypes.InheritableBoolean(
                    self.param('migration_compressed'),
                ) if self.param('migration_compressed') else None,
                policy=otypes.MigrationPolicy(
                    id=self._get_policy_id()
                ) if self.param('migration_policy') else None,
            ) if (
                self.param('migration_bandwidth') is not None or
                self.param('migration_bandwidth_limit') is not None or
                self.param('migration_auto_converge') is not None or
                self.param('migration_compressed') is not None or
                self.param('migration_policy') is not None
            ) else None,
            error_handling=otypes.ErrorHandling(
                on_error=otypes.MigrateOnError(
                    self.param('resilience_policy')
                ),
            ) if self.param('resilience_policy') else None,
            fencing_policy=otypes.FencingPolicy(
                enabled=self.param('fence_enabled'),
                skip_if_gluster_bricks_up=self.param('fence_skip_if_gluster_bricks_up'),
                skip_if_gluster_quorum_not_met=self.param('fence_skip_if_gluster_quorum_not_met'),
                skip_if_connectivity_broken=otypes.SkipIfConnectivityBroken(
                    enabled=self.param('fence_skip_if_connectivity_broken'),
                    threshold=self.param('fence_connectivity_threshold'),
                ) if (
                    self.param('fence_skip_if_connectivity_broken') is not None or
                    self.param('fence_connectivity_threshold') is not None
                ) else None,
                skip_if_sd_active=otypes.SkipIfSdActive(
                    enabled=self.param('fence_skip_if_sd_active'),
                ) if self.param('fence_skip_if_sd_active') is not None else None,
            ) if (
                self.param('fence_enabled') is not None or
                self.param('fence_skip_if_sd_active') is not None or
                self.param('fence_skip_if_connectivity_broken') is not None or
                self.param('fence_skip_if_gluster_bricks_up') is not None or
                self.param('fence_skip_if_gluster_quorum_not_met') is not None or
                self.param('fence_connectivity_threshold') is not None
            ) else None,
            display=otypes.Display(
                proxy=self.param('spice_proxy'),
            ) if self.param('spice_proxy') else None,
            required_rng_sources=[
                otypes.RngSource(rng) for rng in self.param('rng_sources')
            ] if self.param('rng_sources') else None,
            memory_policy=otypes.MemoryPolicy(
                over_commit=otypes.MemoryOverCommit(
                    percent=self._get_memory_policy(),
                ),
            ) if self.param('memory_policy') else None,
            ksm=otypes.Ksm(
                enabled=self.param('ksm'),
                merge_across_nodes=not self.param('ksm_numa'),
            ) if (
                self.param('ksm_numa') is not None or
                self.param('ksm') is not None
            ) else None,
            data_center=otypes.DataCenter(
                name=self.param('data_center'),
            ) if self.param('data_center') else None,
            management_network=otypes.Network(
                name=self.param('network'),
            ) if self.param('network') else None,
            cpu=otypes.Cpu(
                architecture=otypes.Architecture(
                    self.param('cpu_arch')
                ) if self.param('cpu_arch') else None,
                type=self.param('cpu_type'),
            ) if (
                self.param('cpu_arch') or self.param('cpu_type')
            ) else None,
            version=otypes.Version(
                major=self.__get_major(self.param('compatibility_version')),
                minor=self.__get_minor(self.param('compatibility_version')),
            ) if self.param('compatibility_version') else None,
            switch_type=otypes.SwitchType(
                self.param('switch_type')
            ) if self.param('switch_type') else None,
            mac_pool=otypes.MacPool(
                id=get_id_by_name(self._connection.system_service().mac_pools_service(), self.param('mac_pool'))
            ) if self.param('mac_pool') else None,
            external_network_providers=self._get_external_network_providers_entity(),
            custom_scheduling_policy_properties=[
                otypes.Property(
                    name=sp.get('name'),
                    value=str(sp.get('value')),
                ) for sp in self.param('scheduling_policy_properties') if sp
            ] if self.param('scheduling_policy_properties') is not None else None,
            firewall_type=otypes.FirewallType(
                self.param('firewall_type')
            ) if self.param('firewall_type') else None,
            gluster_tuned_profile=self.param('gluster_tuned_profile'),
        )

    def _matches_entity(self, item, entity):
        return equal(item.get('id'), entity.id) and equal(item.get('name'), entity.name)

    def _update_check_external_network_providers(self, entity):
        if self.param('external_network_providers') is None:
            return True
        if entity.external_network_providers is None:
            return not self.param('external_network_providers')
        entity_providers = self._connection.follow_link(entity.external_network_providers)
        entity_provider_ids = [provider.id for provider in entity_providers]
        entity_provider_names = [provider.name for provider in entity_providers]
        for provider in self._get_external_network_providers():
            if provider.get('id'):
                if provider.get('id') not in entity_provider_ids:
                    return False
            elif provider.get('name') and provider.get('name') not in entity_provider_names:
                return False
        for entity_provider in entity_providers:
            if not any([self._matches_entity(provider, entity_provider)
                        for provider in self._get_external_network_providers()]):
                return False
        return True

    def update_check(self, entity):
        sched_policy = self._get_sched_policy()
        migration_policy = getattr(entity.migration, 'policy', None)
        cluster_cpu = getattr(entity, 'cpu', dict())

        def check_custom_scheduling_policy_properties():
            if self.param('scheduling_policy_properties'):
                current = []
                if entity.custom_scheduling_policy_properties:
                    current = [(sp.name, str(sp.value)) for sp in entity.custom_scheduling_policy_properties]
                passed = [(sp.get('name'), str(sp.get('value'))) for sp in self.param('scheduling_policy_properties') if sp]
                for p in passed:
                    if p not in current:
                        return False
            return True

        return (
            check_custom_scheduling_policy_properties() and
            equal(self.param('name'), entity.name) and
            equal(self.param('comment'), entity.comment) and
            equal(self.param('description'), entity.description) and
            equal(self.param('switch_type'), str(entity.switch_type)) and
            equal(self.param('cpu_arch'), str(getattr(cluster_cpu, 'architecture', None))) and
            equal(self.param('cpu_type'), getattr(cluster_cpu, 'type', None)) and
            equal(self.param('ballooning'), entity.ballooning_enabled) and
            equal(self.param('gluster'), entity.gluster_service) and
            equal(self.param('virt'), entity.virt_service) and
            equal(self.param('threads_as_cores'), entity.threads_as_cores) and
            equal(self.param('ksm_numa'), not entity.ksm.merge_across_nodes) and
            equal(self.param('ksm'), entity.ksm.enabled) and
            equal(self.param('ha_reservation'), entity.ha_reservation) and
            equal(self.param('trusted_service'), entity.trusted_service) and
            equal(self.param('host_reason'), entity.maintenance_reason_required) and
            equal(self.param('vm_reason'), entity.optional_reason) and
            equal(self.param('spice_proxy'), getattr(entity.display, 'proxy', None)) and
            equal(self.param('fence_enabled'), entity.fencing_policy.enabled) and
            equal(self.param('fence_skip_if_gluster_bricks_up'), entity.fencing_policy.skip_if_gluster_bricks_up) and
            equal(self.param('fence_skip_if_gluster_quorum_not_met'), entity.fencing_policy.skip_if_gluster_quorum_not_met) and
            equal(self.param('fence_skip_if_sd_active'), entity.fencing_policy.skip_if_sd_active.enabled) and
            equal(self.param('fence_skip_if_connectivity_broken'), entity.fencing_policy.skip_if_connectivity_broken.enabled) and
            equal(self.param('fence_connectivity_threshold'), entity.fencing_policy.skip_if_connectivity_broken.threshold) and
            equal(self.param('resilience_policy'), str(entity.error_handling.on_error)) and
            equal(self.param('migration_bandwidth'), str(entity.migration.bandwidth.assignment_method)) and
            equal(self.param('migration_auto_converge'), str(entity.migration.auto_converge)) and
            equal(self.param('migration_compressed'), str(entity.migration.compressed)) and
            equal(self.param('serial_policy'), str(getattr(entity.serial_number, 'policy', None))) and
            equal(self.param('serial_policy_value'), getattr(entity.serial_number, 'value', None)) and
            equal(self.param('scheduling_policy'), getattr(self._connection.follow_link(entity.scheduling_policy), 'name', None)) and
            equal(self.param('firewall_type'), str(entity.firewall_type)) and
            equal(self.param('gluster_tuned_profile'), getattr(entity, 'gluster_tuned_profile', None)) and
            equal(self._get_policy_id(), getattr(migration_policy, 'id', None)) and
            equal(self._get_memory_policy(), entity.memory_policy.over_commit.percent) and
            equal(self.__get_minor(self.param('compatibility_version')), self.__get_minor(entity.version)) and
            equal(self.__get_major(self.param('compatibility_version')), self.__get_major(entity.version)) and
            equal(
                self.param('migration_bandwidth_limit') if self.param('migration_bandwidth') == 'custom' else None,
                entity.migration.bandwidth.custom_value
            ) and
            equal(
                sorted(self.param('rng_sources')) if self.param('rng_sources') else None,
                sorted([
                    str(source) for source in entity.required_rng_sources
                ])
            ) and
            equal(
                get_id_by_name(self._connection.system_service().mac_pools_service(), self.param('mac_pool'), raise_error=False),
                entity.mac_pool.id
            ) and
            self._update_check_external_network_providers(entity)
        )


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent'],
            default='present',
        ),
        name=dict(default=None, required=True),
        id=dict(default=None),
        ballooning=dict(default=None, type='bool', aliases=['balloon']),
        gluster=dict(default=None, type='bool'),
        virt=dict(default=None, type='bool'),
        threads_as_cores=dict(default=None, type='bool'),
        ksm_numa=dict(default=None, type='bool'),
        ksm=dict(default=None, type='bool'),
        ha_reservation=dict(default=None, type='bool'),
        trusted_service=dict(default=None, type='bool'),
        vm_reason=dict(default=None, type='bool'),
        host_reason=dict(default=None, type='bool'),
        memory_policy=dict(default=None, choices=['disabled', 'server', 'desktop'], aliases=['performance_preset']),
        rng_sources=dict(default=None, type='list'),
        spice_proxy=dict(default=None),
        fence_enabled=dict(default=None, type='bool'),
        fence_skip_if_gluster_bricks_up=dict(default=None, type='bool'),
        fence_skip_if_gluster_quorum_not_met=dict(default=None, type='bool'),
        fence_skip_if_sd_active=dict(default=None, type='bool'),
        fence_skip_if_connectivity_broken=dict(default=None, type='bool'),
        fence_connectivity_threshold=dict(default=None, type='int'),
        resilience_policy=dict(default=None, choices=['migrate_highly_available', 'migrate', 'do_not_migrate']),
        migration_bandwidth=dict(default=None, choices=['auto', 'hypervisor_default', 'custom']),
        migration_bandwidth_limit=dict(default=None, type='int'),
        migration_auto_converge=dict(default=None, choices=['true', 'false', 'inherit']),
        migration_compressed=dict(default=None, choices=['true', 'false', 'inherit']),
        migration_policy=dict(
            default=None,
            choices=['legacy', 'minimal_downtime', 'suspend_workload', 'post_copy']
        ),
        serial_policy=dict(default=None, choices=['vm', 'host', 'custom']),
        serial_policy_value=dict(default=None),
        scheduling_policy=dict(default=None),
        data_center=dict(default=None),
        description=dict(default=None),
        comment=dict(default=None),
        network=dict(default=None),
        cpu_arch=dict(default=None, choices=['ppc64', 'undefined', 'x86_64']),
        cpu_type=dict(default=None),
        switch_type=dict(default=None, choices=['legacy', 'ovs']),
        compatibility_version=dict(default=None),
        mac_pool=dict(default=None),
        external_network_providers=dict(default=None, type='list'),
        scheduling_policy_properties=dict(type='list'),
        firewall_type=dict(choices=['iptables', 'firewalld'], default=None),
        gluster_tuned_profile=dict(default=None),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        clusters_service = connection.system_service().clusters_service()
        clusters_module = ClustersModule(
            connection=connection,
            module=module,
            service=clusters_service,
        )

        state = module.params['state']
        if state == 'present':
            ret = clusters_module.create()
        elif state == 'absent':
            ret = clusters_module.remove()

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
