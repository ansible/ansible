#!/usr/bin/python
#
# Created on Aug 25, 2016
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
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
module: avi_poolgroupdeploymentpolicy
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of PoolGroupDeploymentPolicy Avi RESTful Object
description:
    - This module is used to configure PoolGroupDeploymentPolicy object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.4"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent","present"]
    auto_disable_old_prod_pools:
        description:
            - It will automatically disable old production pools once there is a new production candidate.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
    cloud_ref:
        description:
            - It is a reference to an object of type cloud.
    description:
        description:
            - User defined description for the object.
    evaluation_duration:
        description:
            - Duration of evaluation period for automatic deployment.
            - Allowed values are 60-86400.
            - Default value when not specified in API or module is interpreted by Avi Controller as 300.
    name:
        description:
            - The name of the pool group deployment policy.
        required: true
    rules:
        description:
            - List of pgdeploymentrule.
    scheme:
        description:
            - Deployment scheme.
            - Enum options - BLUE_GREEN, CANARY.
            - Default value when not specified in API or module is interpreted by Avi Controller as BLUE_GREEN.
    target_test_traffic_ratio:
        description:
            - Target traffic ratio before pool is made production.
            - Allowed values are 1-100.
            - Default value when not specified in API or module is interpreted by Avi Controller as 100.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    test_traffic_ratio_rampup:
        description:
            - Ratio of the traffic that is sent to the pool under test.
            - Test ratio of 100 means blue green.
            - Allowed values are 1-100.
            - Default value when not specified in API or module is interpreted by Avi Controller as 100.
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Uuid of the pool group deployment policy.
    webhook_ref:
        description:
            - Webhook configured with url that avi controller will pass back information about pool group, old and new pool information and current deployment
            - rule results.
            - It is a reference to an object of type webhook.
            - Field introduced in 17.1.1.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
- name: Example to create PoolGroupDeploymentPolicy object
  avi_poolgroupdeploymentpolicy:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_poolgroupdeploymentpolicy
"""

RETURN = '''
obj:
    description: PoolGroupDeploymentPolicy (api/poolgroupdeploymentpolicy) object
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
        auto_disable_old_prod_pools=dict(type='bool',),
        cloud_ref=dict(type='str',),
        description=dict(type='str',),
        evaluation_duration=dict(type='int',),
        name=dict(type='str', required=True),
        rules=dict(type='list',),
        scheme=dict(type='str',),
        target_test_traffic_ratio=dict(type='int',),
        tenant_ref=dict(type='str',),
        test_traffic_ratio_rampup=dict(type='int',),
        url=dict(type='str',),
        uuid=dict(type='str',),
        webhook_ref=dict(type='str',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'poolgroupdeploymentpolicy',
                           set([]))

if __name__ == '__main__':
    main()
