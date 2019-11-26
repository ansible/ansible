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
module: avi_gslb
author: Gaurav Rastogi (@grastogi23) <grastogi@avinetworks.com>

short_description: Module for setup of Gslb Avi RESTful Object
description:
    - This module is used to configure Gslb object
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
    async_interval:
        description:
            - Frequency with which messages are propagated to vs mgr.
            - Value of 0 disables async behavior and rpc are sent inline.
            - Allowed values are 0-5.
            - Field introduced in 18.2.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
        version_added: "2.9"
    clear_on_max_retries:
        description:
            - Max retries after which the remote site is treated as a fresh start.
            - In fresh start all the configs are downloaded.
            - Allowed values are 1-1024.
            - Default value when not specified in API or module is interpreted by Avi Controller as 20.
    client_ip_addr_group:
        description:
            - Group to specify if the client ip addresses are public or private.
            - Field introduced in 17.1.2.
        version_added: "2.4"
    description:
        description:
            - User defined description for the object.
    dns_configs:
        description:
            - Sub domain configuration for the gslb.
            - Gslb service's fqdn must be a match one of these subdomains.
    is_federated:
        description:
            - This field indicates that this object is replicated across gslb federation.
            - Field introduced in 17.1.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
        version_added: "2.4"
        type: bool
    leader_cluster_uuid:
        description:
            - Mark this site as leader of gslb configuration.
            - This site is the one among the avi sites.
        required: true
    maintenance_mode:
        description:
            - This field disables the configuration operations on the leader for all federated objects.
            - Cud operations on gslb, gslbservice, gslbgeodbprofile and other federated objects will be rejected.
            - The rest-api disabling helps in upgrade scenarios where we don't want configuration sync operations to the gslb member when the member is being
            - upgraded.
            - This configuration programmatically blocks the leader from accepting new gslb configuration when member sites are undergoing upgrade.
            - Field introduced in 17.2.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.5"
        type: bool
    name:
        description:
            - Name for the gslb object.
        required: true
    send_interval:
        description:
            - Frequency with which group members communicate.
            - Allowed values are 1-3600.
            - Default value when not specified in API or module is interpreted by Avi Controller as 15.
    send_interval_prior_to_maintenance_mode:
        description:
            - The user can specify a send-interval while entering maintenance mode.
            - The validity of this 'maintenance send-interval' is only during maintenance mode.
            - When the user leaves maintenance mode, the original send-interval is reinstated.
            - This internal variable is used to store the original send-interval.
            - Field introduced in 18.2.3.
        version_added: "2.9"
    sites:
        description:
            - Select avi site member belonging to this gslb.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    third_party_sites:
        description:
            - Third party site member belonging to this gslb.
            - Field introduced in 17.1.1.
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Uuid of the gslb object.
    view_id:
        description:
            - The view-id is used in change-leader mode to differentiate partitioned groups while they have the same gslb namespace.
            - Each partitioned group will be able to operate independently by using the view-id.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
- name: Example to create Gslb object
  avi_gslb:
    name: "test-gslb"
    avi_credentials:
      username: '{{ username }}'
      password: '{{ password }}'
      controller: '{{ controller }}'
    sites:
      - name: "test-site1"
        username: "gslb_username"
        password: "gslb_password"
        ip_addresses:
          - type: "V4"
            addr: "10.10.28.83"
        enabled: True
        member_type: "GSLB_ACTIVE_MEMBER"
        port: 443
        cluster_uuid: "cluster-d4ee5fcc-3e0a-4d4f-9ae6-4182bc605829"
      - name: "test-site2"
        username: "gslb_username"
        password: "gslb_password"
        ip_addresses:
          - type: "V4"
            addr: "10.10.28.86"
        enabled: True
        member_type: "GSLB_ACTIVE_MEMBER"
        port: 443
        cluster_uuid: "cluster-0c37ae8d-ab62-410c-ad3e-06fa831950b1"
    dns_configs:
      - domain_name: "test1.com"
      - domain_name: "test2.com"
    leader_cluster_uuid: "cluster-d4ee5fcc-3e0a-4d4f-9ae6-4182bc605829"

- name: Update Gslb site's configurations (Patch Add Operation)
  avi_gslb:
    avi_credentials:
      username: '{{ username }}'
      password: '{{ password }}'
      controller: '{{ controller }}'
    avi_api_update_method: patch
    avi_api_patch_op: add
    leader_cluster_uuid: "cluster-d4ee5fcc-3e0a-4d4f-9ae6-4182bc605829"
    name: "test-gslb"
    dns_configs:
      - domain_name: "temp1.com"
      - domain_name: "temp2.com"
    gslb_sites_config:
      - ip_addr: "10.10.28.83"
        dns_vses:
          - dns_vs_uuid: "virtualservice-f2a711cd-5e78-473f-8f47-d12de660fd62"
            domain_names:
              - "test1.com"
              - "test2.com"
      - ip_addr: "10.10.28.86"
        dns_vses:
          - dns_vs_uuid: "virtualservice-c1a63a16-f2a1-4f41-aab4-1e90f92a5e49"
            domain_names:
              - "temp1.com"
              - "temp2.com"

- name: Update Gslb site's configurations (Patch Replace Operation)
  avi_gslb:
    avi_credentials:
      username: "{{ username }}"
      password: "{{ password }}"
      controller: "{{ controller }}"
    # On basis of cluster leader uuid dns_configs is set for that particular leader cluster
    leader_cluster_uuid: "cluster-84aa795f-8f09-42bb-97a4-5103f4a53da9"
    name: "test-gslb"
    avi_api_update_method: patch
    avi_api_patch_op: replace
    dns_configs:
      - domain_name: "test3.com"
      - domain_name: "temp3.com"
    gslb_sites_config:
      # Ip address is mapping key for dns_vses field update. For the given IP address,
      # dns_vses is updated.
      - ip_addr: "10.10.28.83"
        dns_vses:
          - dns_vs_uuid: "virtualservice-7c947ed4-77f3-4a52-909c-4f12afaf5bb0"
            domain_names:
              - "test3.com"
      - ip_addr: "10.10.28.86"
        dns_vses:
          - dns_vs_uuid: "virtualservice-799b2c6d-7f2d-4c3f-94c6-6e813b20b674"
            domain_names:
              - "temp3.com"

- name: Update Gslb site's configurations (Patch Delete Operation)
  avi_gslb:
    avi_credentials:
      username: "{{ username }}"
      password: "{{ password }}"
      controller: "{{ controller }}"
    # On basis of cluster leader uuid dns_configs is set for that particular leader cluster
    leader_cluster_uuid: "cluster-84aa795f-8f09-42bb-97a4-5103f4a53da9"
    name: "test-gslb"
    avi_api_update_method: patch
    avi_api_patch_op: delete
    dns_configs:
    gslb_sites_config:
      - ip_addr: "10.10.28.83"
      - ip_addr: "10.10.28.86"
"""

RETURN = '''
obj:
    description: Gslb (api/gslb) object
    returned: success, changed
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible.module_utils.network.avi.avi import (
        avi_common_argument_spec, avi_ansible_api, HAS_AVI)
    from ansible.module_utils.network.avi.avi_api import ApiSession, AviCredentials
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
        avi_api_update_method=dict(default='put',
                                   choices=['put', 'patch']),
        avi_api_patch_op=dict(choices=['add', 'replace', 'delete']),
        async_interval=dict(type='int',),
        clear_on_max_retries=dict(type='int',),
        client_ip_addr_group=dict(type='dict',),
        description=dict(type='str',),
        dns_configs=dict(type='list',),
        is_federated=dict(type='bool',),
        leader_cluster_uuid=dict(type='str', required=True),
        maintenance_mode=dict(type='bool',),
        name=dict(type='str', required=True),
        send_interval=dict(type='int',),
        send_interval_prior_to_maintenance_mode=dict(type='int',),
        sites=dict(type='list',),
        tenant_ref=dict(type='str',),
        third_party_sites=dict(type='list',),
        url=dict(type='str',),
        uuid=dict(type='str',),
        view_id=dict(type='int',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) or requests is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    api_method = module.params['avi_api_update_method']
    if str(api_method).lower() == 'patch':
        patch_op = module.params['avi_api_patch_op']
        # Create controller session
        api_creds = AviCredentials()
        api_creds.update_from_ansible_module(module)
        api = ApiSession.get_session(
            api_creds.controller, api_creds.username, password=api_creds.password,
            timeout=api_creds.timeout, tenant=api_creds.tenant,
            tenant_uuid=api_creds.tenant_uuid, token=api_creds.token,
            port=api_creds.port)
        # Get existing gslb objects
        rsp = api.get('gslb', api_version=api_creds.api_version)
        existing_gslb = rsp.json()
        gslb = existing_gslb['results']
        sites = module.params['gslb_sites_config']
        for gslb_obj in gslb:
            # Update/Delete domain names in dns_configs fields in gslb object.
            if 'dns_configs' in module.params:
                if gslb_obj['leader_cluster_uuid'] == module.params['leader_cluster_uuid']:
                    if str(patch_op).lower() == 'delete':
                        gslb_obj['dns_configs'] = []
                    elif str(patch_op).lower() == 'add':
                        if module.params['dns_configs'] not in gslb_obj['dns_configs']:
                            gslb_obj['dns_configs'].extend(module.params['dns_configs'])
                    else:
                        gslb_obj['dns_configs'] = module.params['dns_configs']
            # Update/Delete sites configuration
            if sites:
                for site_obj in gslb_obj['sites']:
                    dns_vses = site_obj.get('dns_vses', [])
                    for obj in sites:
                        config_for = obj.get('ip_addr', None)
                        if not config_for:
                            return module.fail_json(msg=(
                                "ip_addr of site in a configuration is mandatory. "
                                "Please provide ip_addr i.e. gslb site's ip."))
                        if config_for == site_obj['ip_addresses'][0]['addr']:
                            if str(patch_op).lower() == 'delete':
                                site_obj['dns_vses'] = []
                            else:
                                # Modify existing gslb sites object
                                for key, val in obj.items():
                                    if key == 'dns_vses' and str(patch_op).lower() == 'add':
                                        found = False
                                        # Check dns_vses field already exists on the controller
                                        for v in dns_vses:
                                            if val[0]['dns_vs_uuid'] != v['dns_vs_uuid']:
                                                found = True
                                                break
                                        if not found:
                                            dns_vses.extend(val)
                                    else:
                                        site_obj[key] = val
                                if str(patch_op).lower() == 'add':
                                    site_obj['dns_vses'] = dns_vses
            uni_dns_configs = [dict(tupleized) for tupleized in set(tuple(item.items())
                                                                    for item in gslb_obj['dns_configs'])]
            gslb_obj['dns_configs'] = uni_dns_configs
            module.params.update(gslb_obj)
        module.params.update(
            {
                'avi_api_update_method': 'put',
                'state': 'present'
            }
        )
    return avi_ansible_api(module, 'gslb',
                           set([]))


if __name__ == '__main__':
    main()
