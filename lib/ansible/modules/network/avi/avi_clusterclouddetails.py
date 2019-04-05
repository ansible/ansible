#!/usr/bin/python
#
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
#
# Copyright: (c) 2017 Gaurav Rastogi, <grastogi@avinetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_clusterclouddetails
author: Gaurav Rastogi (@grastogi23) <grastogi@avinetworks.com>

short_description: Module for setup of ClusterCloudDetails Avi RESTful Object
description:
    - This module is used to configure ClusterCloudDetails object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.5"
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
    azure_info:
        description:
            - Azure info to configure cluster_vip on the controller.
            - Field introduced in 17.2.5.
    name:
        description:
            - Field introduced in 17.2.5.
        required: true
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
            - Field introduced in 17.2.5.
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Field introduced in 17.2.5.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
- name: Example to create ClusterCloudDetails object
  avi_clusterclouddetails:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_clusterclouddetails
"""

RETURN = '''
obj:
    description: ClusterCloudDetails (api/clusterclouddetails) object
    returned: success, changed
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
HAS_AVI = True
from ansible.module_utils.network.avi.avi import (
    avi_common_argument_spec, avi_ansible_api)


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
        avi_api_update_method=dict(default='put',
                                   choices=['put', 'patch']),
        avi_api_patch_op=dict(choices=['add', 'replace', 'delete']),
        azure_info=dict(type='dict',),
        name=dict(type='str', required=True),
        tenant_ref=dict(type='str',),
        url=dict(type='str',),
        uuid=dict(type='str',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    return avi_ansible_api(module, 'clusterclouddetails',
                           set([]))


if __name__ == '__main__':
    main()
