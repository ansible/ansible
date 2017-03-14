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
module: avi_poolgroup
author: Gaurav Rastogi (grastogi@avinetworks.com)

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
        choices: ["absent","present"]
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
    members:
        description:
            - List of pool group members object of type poolgroupmember.
    min_servers:
        description:
            - The minimum number of servers to distribute traffic to.
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
    from ansible.module_utils.avi import (
        avi_common_argument_spec, HAS_AVI, avi_ansible_api)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
        cloud_config_cksum=dict(type='str',),
        cloud_ref=dict(type='str',),
        created_by=dict(type='str',),
        deployment_policy_ref=dict(type='str',),
        description=dict(type='str',),
        fail_action=dict(type='dict',),
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
            'Avi python API SDK (avisdk>=16.3.5.post1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'poolgroup',
                           set([]))


if __name__ == '__main__':
    main()
