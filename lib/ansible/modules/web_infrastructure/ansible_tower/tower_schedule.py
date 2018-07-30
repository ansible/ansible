#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2018, Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: tower_schedule
author:
    - Blair Morrison
    - David Moreau-Simard (@dmsimard)
version_added: 2.7
short_description: Create, update, or destroy Ansible Tower schedules
description:
    - Create, update, or destroy Ansible Tower schedules. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
        description:
            - The name to use for the schedule.
        required: true
    state:
        description:
            - Desired state of the schedule.
        choices: ["present", "absent", "disabled"]
        default: "present"
    description:
        description:
            - The description to use for the schedule.
        required: false
    job_template:
        description:
            - The name of the job template this schedule applies to.
        required: false
    project:
        description:
            - The name of the project this schedule applies to.
        required: false
    inventory_source:
            - The name of the inventory source this schedule applies to.
        required: false
    start:
        description:
            - The date and time when the schedule should be effective.
              This must be in the ISO 8601 format and in the UTC timezone,
              e.g. '2018-01-01T00:00:00Z'.
              The module will fail if dates are provided in any other format.
        required: false
        default: immediately, equivalent to the ansible_date_time.iso8601 fact
    frequency:
        description:
            - The number of frequency_unit intervals between each execution of the specified resource
              (job template, project or inventory source)
        type: int
        required: false
    frequency_unit:
        description:
            - The duration of each time interval.
        choices: ["runonce", "minute", "hour", "day"]
        required: false
        default: runonce
extends_documentation_fragment: tower
'''

EXAMPLES = '''
- name: Create a schedule to update a project every 30 minutes
  tower_schedule:
    state: present
    project: git project
    frequency: 30
    frequency_unit: minute

- name: Disable the schedule for an inventory source
  tower_schedule:
    state: disabled
    inventory_source: cloud
    frequency: 30
    frequency_unit: minute

- name: Create a schedule to run a job template once at a specific time
  tower_schedule:
    state: present
    job_template: upgrade something
    start: 2018-01-01T00:00:00Z
    frequency_unit: runonce
'''

from datetime import datetime

try:
    import json
    import tower_cli
    import tower_cli.utils.exceptions as exc

    from tower_cli.conf import settings
    from ansible.module_utils.ansible_tower import tower_auth_config, tower_check_mode

    HAS_TOWER_CLI = True
except:
    HAS_TOWER_CLI = False

def parse_datetime_string(module, dt_string):
    """
    This accepts a datetime string in ISO 8601 format in UTC time and returns
    a string representation of that datetime that can be used to construct the rrule
    string that is used by Ansible Tower.
    """
    try:
        dt = datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%SZ")
        result = datetime.strftime(dt, "%Y%m%dT%H%M%SZ")
    except ValueError as excinfo:
        module.fail_json(
            msg="Failed to update schedule, unable to parse datetime {0}: {1}".format(dt_string, excinfo),
            changed=False
        )
    return result

def build_rrule(startdate, freq, freq_unit):
    """
    Generate the RRULE string.
    Currently only supports the units: MINUTELY, HOURLY, DAILY, and RUNONCE
    """
    unit_map = {
                'minute': 'MINUTELY',
                'day': 'DAILY',
                'hour': 'HOURLY',
                'runonce': 'DAILY'
    }
    result = 'DTSTART:{0} RRULE:FREQ={1};INTERVAL={2}'.format(startdate, unit_map[freq_unit], freq)
    if freq_unit == 'runonce':
        result += 'COUNT=1'

    return result

def get_resource_id(kind, name):
    """
    Attempts to find a <kind> resource named <name> and return it's id.
    """
    try:
        resource = tower_cli.get_resource(kind)
        item = resource.get(name=name)
        return item['id']
    except (exc.NotFound) as excinfo:
        module.fail_json(
            msg="Could not update schedule, {0} not found: {1}".format(kind, name),
            changed=False
        )

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            state=dict(choices=['present', 'absent', 'disabled'], default='present'),
            description=dict(default=''),
            job_template=dict(),
            project=dict(),
            inventory_source=dict(),
            start=dict(default=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")),
            frequency=dict(type='int'),
            frequency_unit=dict(choices=['runonce', 'minute', 'hour', 'day'], default='runonce'),
            tower_host=dict(),
            tower_username=dict(),
            tower_password=dict(no_log=True),
            tower_verify_ssl=dict(type='bool', default=True),
            tower_config_file=dict(type='path')
        ),
        mutually_exclusive=['job_template', 'project', 'inventory_source'],
        supports_check_mode=True
    )

    if not HAS_TOWER_CLI:
        module.fail_json(msg='ansible-tower-cli required for this module')

    name = module.params.get('name')
    state = module.params.get('state')
    description = module.params.get('description')
    job_template = module.params.get('job_template')
    project = module.params.get('project')
    inventory_source = module.params.get('inventory_source')
    start = module.params.get('start')
    frequency = module.params.get('frequency')
    frequency_unit = module.params.get('frequency_unit')

    json_output = {
        'name': name,
        'description': description,
        'state': state,
        'start': start,
        'frequency_unit': frequency_unit
    }
    if frequency:
        json_output['frequency'] = frequency

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        schedule = tower_cli.get_resource('schedule')

        params = {
            'name': name,
            'description': description,
        }

        if job_template:
            params['job_template'] = get_resource_id('job_template', job_template)
            json_output['job_template'] = job_template
        if project:
            params['project'] = get_resource_id('project', project)
            json_output['project'] = project
        if inventory_source:
            params['inventory_source'] = get_resource_id('inventory_source', inventory_source)
            json_output['inventory_source'] = inventory_source

        dtstart = parse_datetime_string(module, start)
        params['rrule'] = build_rrule(dtstart, frequency, frequency_unit)

        try:
            if state == 'absent':
                result = schedule.delete(**params)
            else:
                params['enabled'] = False if state == 'disabled' else True
                json_output['enabled'] = params['enabled']
                # TODO: Figure out why modify with create_on_missing fails with MethodNotAllowed
                # https://github.com/ansible/tower-cli/issues/578
                result = schedule.create(**params)
                result = schedule.modify(**params)
        except (exc.ConnectionError, exc.BadRequest, exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update schedule: {0}'.format(excinfo), changed=False)

        json_output['changed'] = result['changed']
        module.exit_json(**json_output)


from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()
