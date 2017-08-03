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
module: avi_pool
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of Pool Avi RESTful Object
description:
    - This module is used to configure Pool object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.3"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent","present"]
    a_pool:
        description:
            - Name of container cloud application that constitutes a pool in a a-b pool configuration, if different from vs app.
    ab_pool:
        description:
            - A/b pool configuration.
    ab_priority:
        description:
            - Priority of this pool in a a-b pool pair.
            - Internally used.
    apic_epg_name:
        description:
            - Synchronize cisco apic epg members with pool servers.
    application_persistence_profile_ref:
        description:
            - Persistence will ensure the same user sticks to the same server for a desired duration of time.
            - It is a reference to an object of type applicationpersistenceprofile.
    autoscale_launch_config_ref:
        description:
            - If configured then avi will trigger orchestration of pool server creation and deletion.
            - It is only supported for container clouds like mesos, opensift, kubernates, docker etc.
            - It is a reference to an object of type autoscalelaunchconfig.
    autoscale_networks:
        description:
            - Network ids for the launch configuration.
    autoscale_policy_ref:
        description:
            - Reference to server autoscale policy.
            - It is a reference to an object of type serverautoscalepolicy.
    capacity_estimation:
        description:
            - Inline estimation of capacity of servers.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    capacity_estimation_ttfb_thresh:
        description:
            - The maximum time-to-first-byte of a server.
            - Allowed values are 1-5000.
            - Special values are 0 - 'automatic'.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
    cloud_config_cksum:
        description:
            - Checksum of cloud configuration for pool.
            - Internally set by cloud connector.
    cloud_ref:
        description:
            - It is a reference to an object of type cloud.
    connection_ramp_duration:
        description:
            - Duration for which new connections will be gradually ramped up to a server recently brought online.
            - Useful for lb algorithms that are least connection based.
            - Allowed values are 1-300.
            - Special values are 0 - 'immediate'.
            - Default value when not specified in API or module is interpreted by Avi Controller as 10.
    created_by:
        description:
            - Creator name.
    default_server_port:
        description:
            - Traffic sent to servers will use this destination server port unless overridden by the server's specific port attribute.
            - The ssl checkbox enables avi to server encryption.
            - Allowed values are 1-65535.
            - Default value when not specified in API or module is interpreted by Avi Controller as 80.
    description:
        description:
            - A description of the pool.
    domain_name:
        description:
            - Comma separated list of domain names which will be used to verify the common names or subject alternative names presented by server certificates.
            - It is performed only when common name check host_check_enabled is enabled.
    east_west:
        description:
            - Inherited config from virtualservice.
    enabled:
        description:
            - Enable or disable the pool.
            - Disabling will terminate all open connections and pause health monitors.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
    external_autoscale_groups:
        description:
            - Names of external auto-scale groups for pool servers.
            - Currently available only for aws.
            - Field introduced in 17.1.2.
    fail_action:
        description:
            - Enable an action - close connection, http redirect or local http response - when a pool failure happens.
            - By default, a connection will be closed, in case the pool experiences a failure.
    fewest_tasks_feedback_delay:
        description:
            - Periodicity of feedback for fewest tasks server selection algorithm.
            - Allowed values are 1-300.
            - Default value when not specified in API or module is interpreted by Avi Controller as 10.
    graceful_disable_timeout:
        description:
            - Used to gracefully disable a server.
            - Virtual service waits for the specified time before terminating the existing connections  to the servers that are disabled.
            - Allowed values are 1-60.
            - Special values are 0 - 'immediate', -1 - 'infinite'.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.
    health_monitor_refs:
        description:
            - Verify server health by applying one or more health monitors.
            - Active monitors generate synthetic traffic from each service engine and mark a server up or down based on the response.
            - The passive monitor listens only to client to server communication.
            - It raises or lowers the ratio of traffic destined to a server based on successful responses.
            - It is a reference to an object of type healthmonitor.
    host_check_enabled:
        description:
            - Enable common name check for server certificate.
            - If enabled and no explicit domain name is specified, avi will use the incoming host header to do the match.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    inline_health_monitor:
        description:
            - The passive monitor will monitor client to server connections and requests and adjust traffic load to servers based on successful responses.
            - This may alter the expected behavior of the lb method, such as round robin.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
    ipaddrgroup_ref:
        description:
            - Use list of servers from ip address group.
            - It is a reference to an object of type ipaddrgroup.
    lb_algorithm:
        description:
            - The load balancing algorithm will pick a server within the pool's list of available servers.
            - Enum options - LB_ALGORITHM_LEAST_CONNECTIONS, LB_ALGORITHM_ROUND_ROBIN, LB_ALGORITHM_FASTEST_RESPONSE, LB_ALGORITHM_CONSISTENT_HASH,
            - LB_ALGORITHM_LEAST_LOAD, LB_ALGORITHM_FEWEST_SERVERS, LB_ALGORITHM_RANDOM, LB_ALGORITHM_FEWEST_TASKS, LB_ALGORITHM_NEAREST_SERVER,
            - LB_ALGORITHM_CORE_AFFINITY.
            - Default value when not specified in API or module is interpreted by Avi Controller as LB_ALGORITHM_LEAST_CONNECTIONS.
    lb_algorithm_consistent_hash_hdr:
        description:
            - Http header name to be used for the hash key.
    lb_algorithm_core_nonaffinity:
        description:
            - Degree of non-affinity for core afffinity based server selection.
            - Allowed values are 1-65535.
            - Field introduced in 17.1.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as 2.
        version_added: "2.4"
    lb_algorithm_hash:
        description:
            - Criteria used as a key for determining the hash between the client and  server.
            - Enum options - LB_ALGORITHM_CONSISTENT_HASH_SOURCE_IP_ADDRESS, LB_ALGORITHM_CONSISTENT_HASH_SOURCE_IP_ADDRESS_AND_PORT,
            - LB_ALGORITHM_CONSISTENT_HASH_URI, LB_ALGORITHM_CONSISTENT_HASH_CUSTOM_HEADER.
            - Default value when not specified in API or module is interpreted by Avi Controller as LB_ALGORITHM_CONSISTENT_HASH_SOURCE_IP_ADDRESS.
    max_concurrent_connections_per_server:
        description:
            - The maximum number of concurrent connections allowed to each server within the pool.
            - Note  applied value will be no less than the number of service engines that the pool is placed on.
            - If set to 0, no limit is applied.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
    max_conn_rate_per_server:
        description:
            - Rate limit connections to each server.
    name:
        description:
            - The name of the pool.
        required: true
    networks:
        description:
            - (internal-use) networks designated as containing servers for this pool.
            - The servers may be further narrowed down by a filter.
            - This field is used internally by avi, not editable by the user.
    nsx_securitygroup:
        description:
            - A list of nsx service groups where the servers for the pool are created.
            - Field introduced in 17.1.1.
    pki_profile_ref:
        description:
            - Avi will validate the ssl certificate present by a server against the selected pki profile.
            - It is a reference to an object of type pkiprofile.
    placement_networks:
        description:
            - Manually select the networks and subnets used to provide reachability to the pool's servers.
            - Specify the subnet using the following syntax  10-1-1-0/24.
            - Use static routes in vrf configuration when pool servers are not directly connected butroutable from the service engine.
    prst_hdr_name:
        description:
            - Header name for custom header persistence.
    request_queue_depth:
        description:
            - Minimum number of requests to be queued when pool is full.
            - Default value when not specified in API or module is interpreted by Avi Controller as 128.
    request_queue_enabled:
        description:
            - Enable request queue when pool is full.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    rewrite_host_header_to_server_name:
        description:
            - Rewrite incoming host header to server name of the server to which the request is proxied.
            - Enabling this feature rewrites host header for requests to all servers in the pool.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    rewrite_host_header_to_sni:
        description:
            - If sni server name is specified, rewrite incoming host header to the sni server name.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    server_auto_scale:
        description:
            - Server autoscale.
            - Not used anymore.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    server_count:
        description:
            - Number of server_count.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
    server_name:
        description:
            - Fully qualified dns hostname which will be used in the tls sni extension in server connections if sni is enabled.
            - If no value is specified, avi will use the incoming host header instead.
    server_reselect:
        description:
            - Server reselect configuration for http requests.
    servers:
        description:
            - The pool directs load balanced traffic to this list of destination servers.
            - The servers can be configured by ip address, name, network or via ip address group.
    sni_enabled:
        description:
            - Enable tls sni for server connections.
            - If disabled, avi will not send the sni extension as part of the handshake.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
    ssl_key_and_certificate_ref:
        description:
            - Service engines will present a client ssl certificate to the server.
            - It is a reference to an object of type sslkeyandcertificate.
    ssl_profile_ref:
        description:
            - When enabled, avi re-encrypts traffic to the backend servers.
            - The specific ssl profile defines which ciphers and ssl versions will be supported.
            - It is a reference to an object of type sslprofile.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    url:
        description:
            - Avi controller URL of the object.
    use_service_port:
        description:
            - Do not translate the client's destination port when sending the connection to the server.
            - The pool or servers specified service port will still be used for health monitoring.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    uuid:
        description:
            - Uuid of the pool.
    vrf_ref:
        description:
            - Virtual routing context that the pool is bound to.
            - This is used to provide the isolation of the set of networks the pool is attached to.
            - The pool inherits the virtual routing conext of the virtual service, and this field is used only internally, and is set by pb-transform.
            - It is a reference to an object of type vrfcontext.
extends_documentation_fragment:
    - avi
'''


EXAMPLES = '''
- name: Create a Pool with two servers and HTTP monitor
  avi_pool:
    controller: 10.10.1.20
    username: avi_user
    password: avi_password
    name: testpool1
    description: testpool1
    state: present
    health_monitor_refs:
        - '/api/healthmonitor?name=System-HTTP'
    servers:
        - ip:
            addr: 10.10.2.20
            type: V4
        - ip:
            addr: 10.10.2.21
            type: V4
'''
RETURN = '''
obj:
    description: Pool (api/pool) object
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
        a_pool=dict(type='str',),
        ab_pool=dict(type='dict',),
        ab_priority=dict(type='int',),
        apic_epg_name=dict(type='str',),
        application_persistence_profile_ref=dict(type='str',),
        autoscale_launch_config_ref=dict(type='str',),
        autoscale_networks=dict(type='list',),
        autoscale_policy_ref=dict(type='str',),
        capacity_estimation=dict(type='bool',),
        capacity_estimation_ttfb_thresh=dict(type='int',),
        cloud_config_cksum=dict(type='str',),
        cloud_ref=dict(type='str',),
        connection_ramp_duration=dict(type='int',),
        created_by=dict(type='str',),
        default_server_port=dict(type='int',),
        description=dict(type='str',),
        domain_name=dict(type='list',),
        east_west=dict(type='bool',),
        enabled=dict(type='bool',),
        external_autoscale_groups=dict(type='list',),
        fail_action=dict(type='dict',),
        fewest_tasks_feedback_delay=dict(type='int',),
        graceful_disable_timeout=dict(type='int',),
        health_monitor_refs=dict(type='list',),
        host_check_enabled=dict(type='bool',),
        inline_health_monitor=dict(type='bool',),
        ipaddrgroup_ref=dict(type='str',),
        lb_algorithm=dict(type='str',),
        lb_algorithm_consistent_hash_hdr=dict(type='str',),
        lb_algorithm_core_nonaffinity=dict(type='int',),
        lb_algorithm_hash=dict(type='str',),
        max_concurrent_connections_per_server=dict(type='int',),
        max_conn_rate_per_server=dict(type='dict',),
        name=dict(type='str', required=True),
        networks=dict(type='list',),
        nsx_securitygroup=dict(type='list',),
        pki_profile_ref=dict(type='str',),
        placement_networks=dict(type='list',),
        prst_hdr_name=dict(type='str',),
        request_queue_depth=dict(type='int',),
        request_queue_enabled=dict(type='bool',),
        rewrite_host_header_to_server_name=dict(type='bool',),
        rewrite_host_header_to_sni=dict(type='bool',),
        server_auto_scale=dict(type='bool',),
        server_count=dict(type='int',),
        server_name=dict(type='str',),
        server_reselect=dict(type='dict',),
        servers=dict(type='list',),
        sni_enabled=dict(type='bool',),
        ssl_key_and_certificate_ref=dict(type='str',),
        ssl_profile_ref=dict(type='str',),
        tenant_ref=dict(type='str',),
        url=dict(type='str',),
        use_service_port=dict(type='bool',),
        uuid=dict(type='str',),
        vrf_ref=dict(type='str',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'pool',
                           set([]))

if __name__ == '__main__':
    main()
