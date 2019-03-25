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
            - Units(SEC).
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
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_gslb
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
        clear_on_max_retries=dict(type='int',),
        client_ip_addr_group=dict(type='dict',),
        description=dict(type='str',),
        dns_configs=dict(type='list',),
        is_federated=dict(type='bool',),
        leader_cluster_uuid=dict(type='str', required=True),
        maintenance_mode=dict(type='bool',),
        name=dict(type='str', required=True),
        send_interval=dict(type='int',),
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
            'Avi python API SDK (avisdk>=17.1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'gslb',
                           set([]))


if __name__ == '__main__':
    main()
