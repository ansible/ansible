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
module: avi_poolgroup
author: Gaurav Rastogi (@grastogi23) <grastogi@avinetworks.com>

short_description: Module for setup of PoolGroup Avi RESTful Object
description:
    - This module is used to configure PoolGroup object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.3"
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
    cloud_config_cksum:
        description:
            - Checksum of cloud configuration for poolgroup.
            - Internally set by cloud connector.
    cloud_ref:
        description:
            - It is a reference to an object of type cloud.
    created_by:
        description:
            - Name of the user who created the object.
    deployment_policy_ref:
        description:
            - When setup autoscale manager will automatically promote new pools into production when deployment goals are met.
            - It is a reference to an object of type poolgroupdeploymentpolicy.
    description:
        description:
            - Description of pool group.
    fail_action:
        description:
            - Enable an action - close connection, http redirect, or local http response - when a pool group failure happens.
            - By default, a connection will be closed, in case the pool group experiences a failure.
    implicit_priority_labels:
        description:
            - Whether an implicit set of priority labels is generated.
            - Field introduced in 17.1.9,17.2.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.5"
        type: bool
    members:
        description:
            - List of pool group members object of type poolgroupmember.
    min_servers:
        description:
            - The minimum number of servers to distribute traffic to.
            - Allowed values are 1-65535.
            - Special values are 0 - 'disable'.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
    name:
        description:
            - The name of the pool group.
        required: true
    priority_labels_ref:
        description:
            - Uuid of the priority labels.
            - If not provided, pool group member priority label will be interpreted as a number with a larger number considered higher priority.
            - It is a reference to an object of type prioritylabels.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Uuid of the pool group.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
- name: Example to create PoolGroup object
  avi_poolgroup:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_poolgroup
"""

RETURN = '''
obj:
    description: PoolGroup (api/poolgroup) object
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
        cloud_config_cksum=dict(type='str',),
        cloud_ref=dict(type='str',),
        created_by=dict(type='str',),
        deployment_policy_ref=dict(type='str',),
        description=dict(type='str',),
        fail_action=dict(type='dict',),
        implicit_priority_labels=dict(type='bool',),
        members=dict(type='list',),
        min_servers=dict(type='int',),
        name=dict(type='str', required=True),
        priority_labels_ref=dict(type='str',),
        tenant_ref=dict(type='str',),
        url=dict(type='str',),
        uuid=dict(type='str',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'poolgroup',
                           set([]))


if __name__ == '__main__':
    main()
