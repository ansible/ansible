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
module: avi_scheduler
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of Scheduler Avi RESTful Object
description:
    - This module is used to configure Scheduler object
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
            - Backup configuration to be executed by this scheduler.
            - It is a reference to an object of type backupconfiguration.
    enabled:
        description:
            - Boolean flag to set enabled.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
    end_date_time:
        description:
            - Scheduler end date and time.
    frequency:
        description:
            - Frequency at which custom scheduler will run.
            - Allowed values are 0-60.
    frequency_unit:
        description:
            - Unit at which custom scheduler will run.
            - Enum options - SCHEDULER_FREQUENCY_UNIT_MIN, SCHEDULER_FREQUENCY_UNIT_HOUR, SCHEDULER_FREQUENCY_UNIT_DAY, SCHEDULER_FREQUENCY_UNIT_WEEK,
            - SCHEDULER_FREQUENCY_UNIT_MONTH.
    name:
        description:
            - Name of scheduler.
        required: true
    run_mode:
        description:
            - Scheduler run mode.
            - Enum options - RUN_MODE_PERIODIC, RUN_MODE_AT, RUN_MODE_NOW.
    run_script_ref:
        description:
            - Control script to be executed by this scheduler.
            - It is a reference to an object of type alertscriptconfig.
    scheduler_action:
        description:
            - Define scheduler action.
            - Enum options - SCHEDULER_ACTION_RUN_A_SCRIPT, SCHEDULER_ACTION_BACKUP.
            - Default value when not specified in API or module is interpreted by Avi Controller as SCHEDULER_ACTION_BACKUP.
    start_date_time:
        description:
            - Scheduler start date and time.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
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
- name: Example to create Scheduler object
  avi_scheduler:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_scheduler
"""

RETURN = '''
obj:
    description: Scheduler (api/scheduler) object
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
        enabled=dict(type='bool',),
        end_date_time=dict(type='str',),
        frequency=dict(type='int',),
        frequency_unit=dict(type='str',),
        name=dict(type='str', required=True),
        run_mode=dict(type='str',),
        run_script_ref=dict(type='str',),
        scheduler_action=dict(type='str',),
        start_date_time=dict(type='str',),
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
    return avi_ansible_api(module, 'scheduler',
                           set([]))

if __name__ == '__main__':
    main()
