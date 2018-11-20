#!/usr/bin/python
#
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
# Avi Version: 17.1.2
#
# Copyright: (c) 2017 Gaurav Rastogi, <grastogi@avinetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_controllerproperties
author: Gaurav Rastogi (@grastogi23) <grastogi@avinetworks.com>

short_description: Module for setup of ControllerProperties Avi RESTful Object
description:
    - This module is used to configure ControllerProperties object
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
    allow_ip_forwarding:
        description:
            - Field introduced in 17.1.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    allow_unauthenticated_apis:
        description:
            - Allow unauthenticated access for special apis.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    allow_unauthenticated_nodes:
        description:
            - Boolean flag to set allow_unauthenticated_nodes.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    api_idle_timeout:
        description:
            - Allowed values are 0-1440.
            - Default value when not specified in API or module is interpreted by Avi Controller as 15.
            - Units(MIN).
    appviewx_compat_mode:
        description:
            - Export configuration in appviewx compatibility mode.
            - Field introduced in 17.1.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    attach_ip_retry_interval:
        description:
            - Number of attach_ip_retry_interval.
            - Default value when not specified in API or module is interpreted by Avi Controller as 360.
            - Units(SEC).
    attach_ip_retry_limit:
        description:
            - Number of attach_ip_retry_limit.
            - Default value when not specified in API or module is interpreted by Avi Controller as 4.
    bm_use_ansible:
        description:
            - Use ansible for se creation in baremetal.
            - Field introduced in 17.2.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
        version_added: "2.5"
        type: bool
    cluster_ip_gratuitous_arp_period:
        description:
            - Number of cluster_ip_gratuitous_arp_period.
            - Default value when not specified in API or module is interpreted by Avi Controller as 60.
            - Units(MIN).
    crashed_se_reboot:
        description:
            - Number of crashed_se_reboot.
            - Default value when not specified in API or module is interpreted by Avi Controller as 900.
            - Units(SEC).
    dead_se_detection_timer:
        description:
            - Number of dead_se_detection_timer.
            - Default value when not specified in API or module is interpreted by Avi Controller as 360.
            - Units(SEC).
    dns_refresh_period:
        description:
            - Number of dns_refresh_period.
            - Default value when not specified in API or module is interpreted by Avi Controller as 60.
            - Units(MIN).
    dummy:
        description:
            - Number of dummy.
    enable_memory_balancer:
        description:
            - Enable/disable memory balancer.
            - Field introduced in 17.2.8.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
        version_added: "2.6"
        type: bool
    fatal_error_lease_time:
        description:
            - Number of fatal_error_lease_time.
            - Default value when not specified in API or module is interpreted by Avi Controller as 120.
            - Units(SEC).
    max_dead_se_in_grp:
        description:
            - Number of max_dead_se_in_grp.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.
    max_pcap_per_tenant:
        description:
            - Maximum number of pcap files stored per tenant.
            - Default value when not specified in API or module is interpreted by Avi Controller as 4.
    max_seq_attach_ip_failures:
        description:
            - Maximum number of consecutive attach ip failures that halts vs placement.
            - Field introduced in 17.2.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as 3.
        version_added: "2.5"
    max_seq_vnic_failures:
        description:
            - Number of max_seq_vnic_failures.
            - Default value when not specified in API or module is interpreted by Avi Controller as 3.
    persistence_key_rotate_period:
        description:
            - Allowed values are 1-1051200.
            - Special values are 0 - 'disabled'.
            - Default value when not specified in API or module is interpreted by Avi Controller as 60.
            - Units(MIN).
    portal_token:
        description:
            - Token used for uploading tech-support to portal.
            - Field introduced in 16.4.6,17.1.2.
        version_added: "2.4"
    query_host_fail:
        description:
            - Number of query_host_fail.
            - Default value when not specified in API or module is interpreted by Avi Controller as 180.
            - Units(SEC).
    safenet_hsm_version:
        description:
            - Version of the safenet package installed on the controller.
            - Field introduced in 16.5.2,17.2.3.
        version_added: "2.5"
    se_create_timeout:
        description:
            - Number of se_create_timeout.
            - Default value when not specified in API or module is interpreted by Avi Controller as 900.
            - Units(SEC).
    se_failover_attempt_interval:
        description:
            - Interval between attempting failovers to an se.
            - Default value when not specified in API or module is interpreted by Avi Controller as 300.
            - Units(SEC).
    se_offline_del:
        description:
            - Number of se_offline_del.
            - Default value when not specified in API or module is interpreted by Avi Controller as 172000.
            - Units(SEC).
    se_vnic_cooldown:
        description:
            - Number of se_vnic_cooldown.
            - Default value when not specified in API or module is interpreted by Avi Controller as 120.
            - Units(SEC).
    secure_channel_cleanup_timeout:
        description:
            - Number of secure_channel_cleanup_timeout.
            - Default value when not specified in API or module is interpreted by Avi Controller as 60.
            - Units(MIN).
    secure_channel_controller_token_timeout:
        description:
            - Number of secure_channel_controller_token_timeout.
            - Default value when not specified in API or module is interpreted by Avi Controller as 60.
            - Units(MIN).
    secure_channel_se_token_timeout:
        description:
            - Number of secure_channel_se_token_timeout.
            - Default value when not specified in API or module is interpreted by Avi Controller as 60.
            - Units(MIN).
    seupgrade_fabric_pool_size:
        description:
            - Pool size used for all fabric commands during se upgrade.
            - Default value when not specified in API or module is interpreted by Avi Controller as 20.
    seupgrade_segroup_min_dead_timeout:
        description:
            - Time to wait before marking segroup upgrade as stuck.
            - Default value when not specified in API or module is interpreted by Avi Controller as 360.
            - Units(SEC).
    ssl_certificate_expiry_warning_days:
        description:
            - Number of days for ssl certificate expiry warning.
            - Units(DAYS).
    unresponsive_se_reboot:
        description:
            - Number of unresponsive_se_reboot.
            - Default value when not specified in API or module is interpreted by Avi Controller as 300.
            - Units(SEC).
    upgrade_dns_ttl:
        description:
            - Time to account for dns ttl during upgrade.
            - This is in addition to vs_scalein_timeout_for_upgrade in se_group.
            - Field introduced in 17.1.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as 5.
            - Units(SEC).
    upgrade_lease_time:
        description:
            - Number of upgrade_lease_time.
            - Default value when not specified in API or module is interpreted by Avi Controller as 360.
            - Units(SEC).
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Unique object identifier of the object.
    vnic_op_fail_time:
        description:
            - Number of vnic_op_fail_time.
            - Default value when not specified in API or module is interpreted by Avi Controller as 180.
            - Units(SEC).
    vs_apic_scaleout_timeout:
        description:
            - Time to wait for the scaled out se to become ready before marking the scaleout done, applies to apic configuration only.
            - Default value when not specified in API or module is interpreted by Avi Controller as 360.
            - Units(SEC).
    vs_awaiting_se_timeout:
        description:
            - Number of vs_awaiting_se_timeout.
            - Default value when not specified in API or module is interpreted by Avi Controller as 60.
            - Units(SEC).
    vs_key_rotate_period:
        description:
            - Allowed values are 1-1051200.
            - Special values are 0 - 'disabled'.
            - Default value when not specified in API or module is interpreted by Avi Controller as 60.
            - Units(MIN).
    vs_se_attach_ip_fail:
        description:
            - Time to wait before marking attach ip operation on an se as failed.
            - Field introduced in 17.2.2.
            - Default value when not specified in API or module is interpreted by Avi Controller as 3600.
            - Units(SEC).
        version_added: "2.5"
    vs_se_bootup_fail:
        description:
            - Number of vs_se_bootup_fail.
            - Default value when not specified in API or module is interpreted by Avi Controller as 480.
            - Units(SEC).
    vs_se_create_fail:
        description:
            - Number of vs_se_create_fail.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1500.
            - Units(SEC).
    vs_se_ping_fail:
        description:
            - Number of vs_se_ping_fail.
            - Default value when not specified in API or module is interpreted by Avi Controller as 60.
            - Units(SEC).
    vs_se_vnic_fail:
        description:
            - Number of vs_se_vnic_fail.
            - Default value when not specified in API or module is interpreted by Avi Controller as 300.
            - Units(SEC).
    vs_se_vnic_ip_fail:
        description:
            - Number of vs_se_vnic_ip_fail.
            - Default value when not specified in API or module is interpreted by Avi Controller as 120.
            - Units(SEC).
    warmstart_se_reconnect_wait_time:
        description:
            - Number of warmstart_se_reconnect_wait_time.
            - Default value when not specified in API or module is interpreted by Avi Controller as 300.
            - Units(SEC).
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
- name: Example to create ControllerProperties object
  avi_controllerproperties:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_controllerproperties
"""

RETURN = '''
obj:
    description: ControllerProperties (api/controllerproperties) object
    returned: success, changed
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible.module_utils.network.avi.avi import (
        avi_common_argument_spec, HAS_AVI, avi_ansible_api)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
        avi_api_update_method=dict(default='put',
                                   choices=['put', 'patch']),
        avi_api_patch_op=dict(choices=['add', 'replace', 'delete']),
        allow_ip_forwarding=dict(type='bool',),
        allow_unauthenticated_apis=dict(type='bool',),
        allow_unauthenticated_nodes=dict(type='bool',),
        api_idle_timeout=dict(type='int',),
        appviewx_compat_mode=dict(type='bool',),
        attach_ip_retry_interval=dict(type='int',),
        attach_ip_retry_limit=dict(type='int',),
        bm_use_ansible=dict(type='bool',),
        cluster_ip_gratuitous_arp_period=dict(type='int',),
        crashed_se_reboot=dict(type='int',),
        dead_se_detection_timer=dict(type='int',),
        dns_refresh_period=dict(type='int',),
        dummy=dict(type='int',),
        enable_memory_balancer=dict(type='bool',),
        fatal_error_lease_time=dict(type='int',),
        max_dead_se_in_grp=dict(type='int',),
        max_pcap_per_tenant=dict(type='int',),
        max_seq_attach_ip_failures=dict(type='int',),
        max_seq_vnic_failures=dict(type='int',),
        persistence_key_rotate_period=dict(type='int',),
        portal_token=dict(type='str', no_log=True,),
        query_host_fail=dict(type='int',),
        safenet_hsm_version=dict(type='str',),
        se_create_timeout=dict(type='int',),
        se_failover_attempt_interval=dict(type='int',),
        se_offline_del=dict(type='int',),
        se_vnic_cooldown=dict(type='int',),
        secure_channel_cleanup_timeout=dict(type='int',),
        secure_channel_controller_token_timeout=dict(type='int',),
        secure_channel_se_token_timeout=dict(type='int',),
        seupgrade_fabric_pool_size=dict(type='int',),
        seupgrade_segroup_min_dead_timeout=dict(type='int',),
        ssl_certificate_expiry_warning_days=dict(type='list',),
        unresponsive_se_reboot=dict(type='int',),
        upgrade_dns_ttl=dict(type='int',),
        upgrade_lease_time=dict(type='int',),
        url=dict(type='str',),
        uuid=dict(type='str',),
        vnic_op_fail_time=dict(type='int',),
        vs_apic_scaleout_timeout=dict(type='int',),
        vs_awaiting_se_timeout=dict(type='int',),
        vs_key_rotate_period=dict(type='int',),
        vs_se_attach_ip_fail=dict(type='int',),
        vs_se_bootup_fail=dict(type='int',),
        vs_se_create_fail=dict(type='int',),
        vs_se_ping_fail=dict(type='int',),
        vs_se_vnic_fail=dict(type='int',),
        vs_se_vnic_ip_fail=dict(type='int',),
        warmstart_se_reconnect_wait_time=dict(type='int',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'controllerproperties',
                           set(['portal_token']))


if __name__ == '__main__':
    main()
