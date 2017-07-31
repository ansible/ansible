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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_backup
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of Backup Avi RESTful Object
description:
    - This module is used to configure Backup object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.4"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent","present"]
    backup_config_ref:
        description:
            - Backupconfiguration information.
            - It is a reference to an object of type backupconfiguration.
    file_name:
        description:
            - The file name of backup.
        required: true
    local_file_url:
        description:
            - Url to download the backup file.
    remote_file_url:
        description:
            - Url to download the backup file.
    scheduler_ref:
        description:
            - Scheduler information.
            - It is a reference to an object of type scheduler.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    timestamp:
        description:
            - Unix timestamp of when the backup file is created.
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
- name: Example to create Backup object
  avi_backup:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_backup
"""

RETURN = '''
obj:
    description: Backup (api/backup) object
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
        backup_config_ref=dict(type='str',),
        file_name=dict(type='str', required=True),
        local_file_url=dict(type='str',),
        remote_file_url=dict(type='str',),
        scheduler_ref=dict(type='str',),
        tenant_ref=dict(type='str',),
        timestamp=dict(type='str',),
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
    return avi_ansible_api(module, 'backup',
                           set([]))

if __name__ == '__main__':
    main()
