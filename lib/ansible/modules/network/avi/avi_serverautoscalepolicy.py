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
module: avi_serverautoscalepolicy
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of ServerAutoScalePolicy Avi RESTful Object
description:
    - This module is used to configure ServerAutoScalePolicy object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.4"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent","present"]
    description:
        description:
            - User defined description for the object.
    intelligent_autoscale:
        description:
            - Use avi intelligent autoscale algorithm where autoscale is performed by comparing load on the pool against estimated capacity of all the servers.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    intelligent_scalein_margin:
        description:
            - Maximum extra capacity as percentage of load used by the intelligent scheme.
            - Scalein is triggered when available capacity is more than this margin.
            - Allowed values are 1-99.
            - Default value when not specified in API or module is interpreted by Avi Controller as 40.
    intelligent_scaleout_margin:
        description:
            - Minimum extra capacity as percentage of load used by the intelligent scheme.
            - Scaleout is triggered when available capacity is less than this margin.
            - Allowed values are 1-99.
            - Default value when not specified in API or module is interpreted by Avi Controller as 20.
    max_scalein_adjustment_step:
        description:
            - Maximum number of servers to scalein simultaneously.
            - The actual number of servers to scalein is chosen such that target number of servers is always more than or equal to the min_size.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.
    max_scaleout_adjustment_step:
        description:
            - Maximum number of servers to scaleout simultaneously.
            - The actual number of servers to scaleout is chosen such that target number of servers is always less than or equal to the max_size.
            - Default value when not specified in API or module is interpreted by Avi Controller as 1.
    max_size:
        description:
            - Maximum number of servers after scaleout.
            - Allowed values are 0-400.
    min_size:
        description:
            - No scale-in happens once number of operationally up servers reach min_servers.
            - Allowed values are 0-400.
    name:
        description:
            - Name of the object.
        required: true
    scalein_alertconfig_refs:
        description:
            - Trigger scalein when alerts due to any of these alert configurations are raised.
            - It is a reference to an object of type alertconfig.
    scalein_cooldown:
        description:
            - Cooldown period during which no new scalein is triggered to allow previous scalein to successfully complete.
            - Default value when not specified in API or module is interpreted by Avi Controller as 300.
    scaleout_alertconfig_refs:
        description:
            - Trigger scaleout when alerts due to any of these alert configurations are raised.
            - It is a reference to an object of type alertconfig.
    scaleout_cooldown:
        description:
            - Cooldown period during which no new scaleout is triggered to allow previous scaleout to successfully complete.
            - Default value when not specified in API or module is interpreted by Avi Controller as 300.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    url:
        description:
            - Avi controller URL of the object.
    use_predicted_load:
        description:
            - Use predicted load rather than current load.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    uuid:
        description:
            - Unique object identifier of the object.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
- name: Example to create ServerAutoScalePolicy object
  avi_serverautoscalepolicy:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_serverautoscalepolicy
"""

RETURN = '''
obj:
    description: ServerAutoScalePolicy (api/serverautoscalepolicy) object
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
        description=dict(type='str',),
        intelligent_autoscale=dict(type='bool',),
        intelligent_scalein_margin=dict(type='int',),
        intelligent_scaleout_margin=dict(type='int',),
        max_scalein_adjustment_step=dict(type='int',),
        max_scaleout_adjustment_step=dict(type='int',),
        max_size=dict(type='int',),
        min_size=dict(type='int',),
        name=dict(type='str', required=True),
        scalein_alertconfig_refs=dict(type='list',),
        scalein_cooldown=dict(type='int',),
        scaleout_alertconfig_refs=dict(type='list',),
        scaleout_cooldown=dict(type='int',),
        tenant_ref=dict(type='str',),
        url=dict(type='str',),
        use_predicted_load=dict(type='bool',),
        uuid=dict(type='str',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'serverautoscalepolicy',
                           set([]))

if __name__ == '__main__':
    main()
