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
module: avi_autoscalelaunchconfig
author: Chaitanya Deshpande (@chaitanyaavi) <chaitanya.deshpande@avinetworks.com>

short_description: Module for setup of AutoScaleLaunchConfig Avi RESTful Object
description:
    - This module is used to configure AutoScaleLaunchConfig object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.6"
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
        default: put
        choices: ["put", "patch"]
    avi_api_patch_op:
        description:
            - Patch operation to use when using avi_api_update_method as patch.
        choices: ["add", "replace", "delete"]
    description:
        description:
            - User defined description for the object.
    image_id:
        description:
            - Unique id of the amazon machine image (ami)  or openstack vm id.
    mesos:
        description:
            - Autoscalemesossettings settings for autoscalelaunchconfig.
    name:
        description:
            - Name of the object.
        required: true
    openstack:
        description:
            - Autoscaleopenstacksettings settings for autoscalelaunchconfig.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    url:
        description:
            - Avi controller URL of the object.
    use_external_asg:
        description:
            - If set to true, serverautoscalepolicy will use the autoscaling group (external_autoscaling_groups) from pool to perform scale up and scale down.
            - Pool should have single autoscaling group configured.
            - Field introduced in 17.2.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
        type: bool
    uuid:
        description:
            - Unique object identifier of the object.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
  - name: Create an Autoscale Launch configuration.
    avi_autoscalelaunchconfig:
      controller: '{{ controller }}'
      username: '{{ username }}'
      password: '{{ password }}'
      image_id: default
      name: default-autoscalelaunchconfig
      tenant_ref: admin
"""

RETURN = '''
obj:
    description: AutoScaleLaunchConfig (api/autoscalelaunchconfig) object
    returned: success, changed
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible.module_utils.network.avi.avi import (
        avi_common_argument_spec, avi_ansible_api, HAS_AVI)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
        avi_api_update_method=dict(default='put',
                                   choices=['put', 'patch']),
        avi_api_patch_op=dict(choices=['add', 'replace', 'delete']),
        description=dict(type='str',),
        image_id=dict(type='str',),
        mesos=dict(type='dict',),
        name=dict(type='str', required=True),
        openstack=dict(type='dict',),
        tenant_ref=dict(type='str',),
        url=dict(type='str',),
        use_external_asg=dict(type='bool',),
        uuid=dict(type='str',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) or requests is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'autoscalelaunchconfig',
                           set([]))


if __name__ == '__main__':
    main()
