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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_useraccountprofile
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of UserAccountProfile Avi RESTful Object
description:
    - This module is used to configure UserAccountProfile object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.4"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent","present"]
    account_lock_timeout:
        description:
            - Lock timeout period (in minutes).
            - Default is 30 minutes.
            - Default value when not specified in API or module is interpreted by Avi Controller as 30.
    credentials_timeout_threshold:
        description:
            - The time period after which credentials expire.
            - Default is 180 days.
            - Default value when not specified in API or module is interpreted by Avi Controller as 180.
    max_concurrent_sessions:
        description:
            - Maximum number of concurrent sessions allowed.
            - There are unlimited sessions by default.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
    max_login_failure_count:
        description:
            - Number of login attempts before lockout.
            - Default is 3 attempts.
            - Default value when not specified in API or module is interpreted by Avi Controller as 3.
    max_password_history_count:
        description:
            - Maximum number of passwords to be maintained in the password history.
            - Default is 4 passwords.
            - Default value when not specified in API or module is interpreted by Avi Controller as 4.
    name:
        description:
            - Name of the object.
        required: true
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Unique object identifier of the object.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
- name: Example to create UserAccountProfile object
  avi_useraccountprofile:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_useraccountprofile
"""

RETURN = '''
obj:
    description: UserAccountProfile (api/useraccountprofile) object
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
        account_lock_timeout=dict(type='int',),
        credentials_timeout_threshold=dict(type='int',),
        max_concurrent_sessions=dict(type='int',),
        max_login_failure_count=dict(type='int',),
        max_password_history_count=dict(type='int',),
        name=dict(type='str', required=True),
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
    return avi_ansible_api(module, 'useraccountprofile',
                           set([]))

if __name__ == '__main__':
    main()
