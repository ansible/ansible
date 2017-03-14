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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: avi_virtualservice
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of VirtualService Avi RESTful Object
description:
    - This module is used to configure VirtualService object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.3"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent","present"]
    active_standby_se_tag:
        description:
            - This configuration only applies if the virtualservice is in legacy active standby ha mode and load distribution among active standby is enabled.
            - This field is used to tag the virtualservice so that virtualservices with the same tag will share the same active serviceengine.
            - Virtualservices with different tags will have different active serviceengines.
            - If one of the serviceengine's in the serviceenginegroup fails, all virtualservices will end up using the same active serviceengine.
            - Redistribution of the virtualservices can be either manual or automated when the failed serviceengine recovers.
            - Redistribution is based on the auto redistribute property of the serviceenginegroup.
            - Default value when not specified in API or module is interpreted by Avi Controller as ACTIVE_STANDBY_SE_1.
    analytics_policy:
        description:
            - Determines analytics settings for the application.
    analytics_profile_ref:
        description:
            - Specifies settings related to analytics.
            - It is a reference to an object of type analyticsprofile.
    application_profile_ref:
        description:
            - Enable application layer specific features for the virtual service.
            - It is a reference to an object of type applicationprofile.
    auto_allocate_floating_ip:
        description:
            - Auto-allocate floating/elastic ip from the cloud infrastructure.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    auto_allocate_ip:
        description:
            - Auto-allocate vip from the provided subnet.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    availability_zone:
        description:
            - Availability-zone to place the virtual service.
    avi_allocated_fip:
        description:
            - (internal-use) fip allocated by avi in the cloud infrastructure.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    avi_allocated_vip:
        description:
            - (internal-use) vip allocated by avi in the cloud infrastructure.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    client_auth:
        description:
            - Http authentication configuration for protected resources.
    cloud_config_cksum:
        description:
            - Checksum of cloud configuration for vs.
            - Internally set by cloud connector.
    cloud_ref:
        description:
            - It is a reference to an object of type cloud.
    cloud_type:
        description:
            - Cloud_type of virtualservice.
            - Default value when not specified in API or module is interpreted by Avi Controller as CLOUD_NONE.
    connections_rate_limit:
        description:
            - Rate limit the incoming connections to this virtual service.
    content_rewrite:
        description:
            - Profile used to match and rewrite strings in request and/or response body.
    created_by:
        description:
            - Creator name.
    delay_fairness:
        description:
            - Select the algorithm for qos fairness.
            - This determines how multiple virtual services sharing the same service engines will prioritize traffic over a congested network.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    description:
        description:
            - User defined description for the object.
    discovered_network_ref:
        description:
            - (internal-use) discovered networks providing reachability for client facing virtual service ip.
            - This field is deprecated.
            - It is a reference to an object of type network.
    discovered_networks:
        description:
            - (internal-use) discovered networks providing reachability for client facing virtual service ip.
            - This field is used internally by avi, not editable by the user.
    discovered_subnet:
        description:
            - (internal-use) discovered subnets providing reachability for client facing virtual service ip.
            - This field is deprecated.
    dns_info:
        description:
            - Service discovery specific data including fully qualified domain name, type and time-to-live of the dns record.
            - Note that only one of fqdn and dns_info setting is allowed.
    east_west_placement:
        description:
            - Force placement on all se's in service group (mesos mode only).
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    enable_autogw:
        description:
            - Response traffic to clients will be sent back to the source mac address of the connection, rather than statically sent to a default gateway.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
    enable_rhi:
        description:
            - Enable route health injection using the bgp config in the vrf context.
    enable_rhi_snat:
        description:
            - Enable route health injection for source nat'ted floating ip address using the bgp config in the vrf context.
    enabled:
        description:
            - Enable or disable the virtual service.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
    floating_ip:
        description:
            - Floating ip to associate with this virtual service.
    floating_subnet_uuid:
        description:
            - If auto_allocate_floating_ip is true and more than one floating-ip subnets exist, then the subnet for the floating ip address allocation.
            - This field is applicable only if the virtualservice belongs to an openstack or aws cloud.
            - In openstack or aws cloud it is required when auto_allocate_floating_ip is selected.
    flow_dist:
        description:
            - Criteria for flow distribution among ses.
            - Default value when not specified in API or module is interpreted by Avi Controller as LOAD_AWARE.
    flow_label_type:
        description:
            - Criteria for flow labelling.
            - Default value when not specified in API or module is interpreted by Avi Controller as NO_LABEL.
    fqdn:
        description:
            - Dns resolvable, fully qualified domain name of the virtualservice.
            - Only one of 'fqdn' and 'dns_info' configuration is allowed.
    host_name_xlate:
        description:
            - Translate the host name sent to the servers to this value.
            - Translate the host name sent from servers back to the value used by the client.
    http_policies:
        description:
            - Http policies applied on the data traffic of the virtual service.
    ign_pool_net_reach:
        description:
            - Ignore pool servers network reachability constraints for virtual service placement.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    ip_address:
        description:
            - Ip address of the virtual service.
    ipam_network_subnet:
        description:
            - Subnet and/or network for allocating virtualservice ip by ipam provider module.
    limit_doser:
        description:
            - Limit potential dos attackers who exceed max_cps_per_client significantly to a fraction of max_cps_per_client for a while.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    max_cps_per_client:
        description:
            - Maximum connections per second per client ip.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
    microservice_ref:
        description:
            - Microservice representing the virtual service.
            - It is a reference to an object of type microservice.
    name:
        description:
            - Name for the virtual service.
        required: true
    network_profile_ref:
        description:
            - Determines network settings such as protocol, tcp or udp, and related options for the protocol.
            - It is a reference to an object of type networkprofile.
    network_ref:
        description:
            - Manually override the network on which the virtual service is placed.
            - It is a reference to an object of type network.
    network_security_policy_ref:
        description:
            - Network security policies for the virtual service.
            - It is a reference to an object of type networksecuritypolicy.
    performance_limits:
        description:
            - Optional settings that determine performance limits like max connections or bandwdith etc.
    pool_group_ref:
        description:
            - The pool group is an object that contains pools.
            - It is a reference to an object of type poolgroup.
    pool_ref:
        description:
            - The pool is an object that contains destination servers and related attributes such as load-balancing and persistence.
            - It is a reference to an object of type pool.
    port_uuid:
        description:
            - (internal-use) network port assigned to the virtual service ip address.
    remove_listening_port_on_vs_down:
        description:
            - Remove listening port if virtualservice is down.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    requests_rate_limit:
        description:
            - Rate limit the incoming requests to this virtual service.
    scaleout_ecmp:
        description:
            - Disable re-distribution of flows across service engines for a virtual service.
            - Enable if the network itself performs flow hashing with ecmp in environments such as gcp.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    se_group_ref:
        description:
            - The service engine group to use for this virtual service.
            - Moving to a new se group is disruptive to existing connections for this vs.
            - It is a reference to an object of type serviceenginegroup.
    server_network_profile_ref:
        description:
            - Determines the network settings profile for the server side of tcp proxied connections.
            - Leave blank to use the same settings as the client to vs side of the connection.
            - It is a reference to an object of type networkprofile.
    service_pool_select:
        description:
            - Select pool based on destination port.
    services:
        description:
            - List of services defined for this virtual service.
    snat_ip:
        description:
            - Nat'ted floating source ip address(es) for upstream connection to servers.
    ssl_key_and_certificate_refs:
        description:
            - Select or create one or two certificates, ec and/or rsa, that will be presented to ssl/tls terminated connections.
            - It is a reference to an object of type sslkeyandcertificate.
    ssl_profile_ref:
        description:
            - Determines the set of ssl versions and ciphers to accept for ssl/tls terminated connections.
            - It is a reference to an object of type sslprofile.
    ssl_sess_cache_avg_size:
        description:
            - Expected number of ssl session cache entries (may be exceeded).
            - Default value when not specified in API or module is interpreted by Avi Controller as 1024.
    static_dns_records:
        description:
            - List of static dns records applied to this virtual service.
            - These are static entries and no health monitoring is performed against the ip addresses.
    subnet:
        description:
            - Subnet providing reachability for client facing virtual service ip.
    subnet_uuid:
        description:
            - It represents subnet for the virtual service ip address allocation when auto_allocate_ip is true.it is only applicable in openstack or aws cloud.
            - This field is required if auto_allocate_ip is true.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    type:
        description:
            - Specify if this is a normal virtual service, or if it is the parent or child of an sni-enabled virtual hosted virtual service.
            - Default value when not specified in API or module is interpreted by Avi Controller as VS_TYPE_NORMAL.
    url:
        description:
            - Avi controller URL of the object.
    use_bridge_ip_as_vip:
        description:
            - Use bridge ip as vip on each host in mesos deployments.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    uuid:
        description:
            - Uuid of the virtualservice.
    vh_domain_name:
        description:
            - The exact name requested from the client's sni-enabled tls hello domain name field.
            - If this is a match, the parent vs will forward the connection to this child vs.
    vh_parent_vs_uuid:
        description:
            - Specifies the virtual service acting as virtual hosting (sni) parent.
    vrf_context_ref:
        description:
            - Virtual routing context that the virtual service is bound to.
            - This is used to provide the isolation of the set of networks the application is attached to.
            - It is a reference to an object of type vrfcontext.
    vs_datascripts:
        description:
            - Datascripts applied on the data traffic of the virtual service.
    weight:
        description:
            - The quality of service weight to assign to traffic transmitted from this virtual service.
            - A higher weight will prioritize traffic versus other virtual services sharing the same service engines.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.
extends_documentation_fragment:
    - avi
'''


EXAMPLES = '''
- name: Create SSL Virtual Service using Pool testpool2
  avi_virtualservice:
    controller: 10.10.27.90
    username: admin
    password: AviNetworks123!
    name: newtestvs
    state: present
    performance_limits:
    max_concurrent_connections: 1000
    services:
        - port: 443
          enable_ssl: true
        - port: 80
    ssl_profile_ref: '/api/sslprofile?name=System-Standard'
    application_profile_ref: '/api/applicationprofile?name=System-Secure-HTTP'
    ssl_key_and_certificate_refs:
        - '/api/sslkeyandcertificate?name=System-Default-Cert'
    ip_address:
    addr: 10.90.131.103
    type: V4
    pool_ref: '/api/pool?name=testpool2'
'''
RETURN = '''
obj:
    description: VirtualService (api/virtualservice) object
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
        active_standby_se_tag=dict(type='str',),
        analytics_policy=dict(type='dict',),
        analytics_profile_ref=dict(type='str',),
        application_profile_ref=dict(type='str',),
        auto_allocate_floating_ip=dict(type='bool',),
        auto_allocate_ip=dict(type='bool',),
        availability_zone=dict(type='str',),
        avi_allocated_fip=dict(type='bool',),
        avi_allocated_vip=dict(type='bool',),
        client_auth=dict(type='dict',),
        cloud_config_cksum=dict(type='str',),
        cloud_ref=dict(type='str',),
        cloud_type=dict(type='str',),
        connections_rate_limit=dict(type='dict',),
        content_rewrite=dict(type='dict',),
        created_by=dict(type='str',),
        delay_fairness=dict(type='bool',),
        description=dict(type='str',),
        discovered_network_ref=dict(type='list',),
        discovered_networks=dict(type='list',),
        discovered_subnet=dict(type='list',),
        dns_info=dict(type='list',),
        east_west_placement=dict(type='bool',),
        enable_autogw=dict(type='bool',),
        enable_rhi=dict(type='bool',),
        enable_rhi_snat=dict(type='bool',),
        enabled=dict(type='bool',),
        floating_ip=dict(type='dict',),
        floating_subnet_uuid=dict(type='str',),
        flow_dist=dict(type='str',),
        flow_label_type=dict(type='str',),
        fqdn=dict(type='str',),
        host_name_xlate=dict(type='str',),
        http_policies=dict(type='list',),
        ign_pool_net_reach=dict(type='bool',),
        ip_address=dict(type='dict',),
        ipam_network_subnet=dict(type='dict',),
        limit_doser=dict(type='bool',),
        max_cps_per_client=dict(type='int',),
        microservice_ref=dict(type='str',),
        name=dict(type='str', required=True),
        network_profile_ref=dict(type='str',),
        network_ref=dict(type='str',),
        network_security_policy_ref=dict(type='str',),
        performance_limits=dict(type='dict',),
        pool_group_ref=dict(type='str',),
        pool_ref=dict(type='str',),
        port_uuid=dict(type='str',),
        remove_listening_port_on_vs_down=dict(type='bool',),
        requests_rate_limit=dict(type='dict',),
        scaleout_ecmp=dict(type='bool',),
        se_group_ref=dict(type='str',),
        server_network_profile_ref=dict(type='str',),
        service_pool_select=dict(type='list',),
        services=dict(type='list',),
        snat_ip=dict(type='list',),
        ssl_key_and_certificate_refs=dict(type='list',),
        ssl_profile_ref=dict(type='str',),
        ssl_sess_cache_avg_size=dict(type='int',),
        static_dns_records=dict(type='list',),
        subnet=dict(type='dict',),
        subnet_uuid=dict(type='str',),
        tenant_ref=dict(type='str',),
        type=dict(type='str',),
        url=dict(type='str',),
        use_bridge_ip_as_vip=dict(type='bool',),
        uuid=dict(type='str',),
        vh_domain_name=dict(type='list',),
        vh_parent_vs_uuid=dict(type='str',),
        vrf_context_ref=dict(type='str',),
        vs_datascripts=dict(type='list',),
        weight=dict(type='int',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=16.3.5.post1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'virtualservice',
                           set([]))


if __name__ == '__main__':
    main()
