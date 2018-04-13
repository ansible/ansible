#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Benjamin Copeland (@bhcopeland) <ben@copeland.me.uk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: statusio_maintenance
short_description: Create maintenance windows for your status.io dashboard
description:
  - Creates a maintenance window for status.io
  - Deletes a maintenance window for status.io
notes:
  - You can use the apiary API url (http://docs.statusio.apiary.io/) to
    capture API traffic
  - Use start_date and start_time with minutes to set future maintenance window
version_added: "2.2"
author: Benjamin Copeland (@bhcopeland) <ben@copeland.me.uk>
options:
    title:
        description:
            - A descriptive title for the maintenance window
        default: "A new maintenance window"
    desc:
        description:
            - Message describing the maintenance window
        default: "Created by Ansible"
    state:
        description:
            - Desired state of the package.
        default: "present"
        choices: ["present", "absent"]
    api_id:
        description:
            - Your unique API ID from status.io
        required: true
    api_key:
        description:
            - Your unique API Key from status.io
        required: true
    statuspage:
        description:
            - Your unique StatusPage ID from status.io
        required: true
    url:
        description:
            - Status.io API URL. A private apiary can be used instead.
        default: "https://api.status.io"
    components:
        description:
            - The given name of your component (server name)
        aliases: ['component']
    containers:
        description:
            - The given name of your container (data center)
        aliases: ['container']
    all_infrastructure_affected:
        description:
            - If it affects all components and containers
        type: bool
        default: 'no'
    automation:
        description:
            - Automatically start and end the maintenance window
        type: bool
        default: 'no'
    maintenance_notify_now:
        description:
            - Notify subscribers now
        type: bool
        default: 'no'
    maintenance_notify_72_hr:
        description:
            - Notify subscribers 72 hours before maintenance start time
        type: bool
        default: 'no'
    maintenance_notify_24_hr:
        description:
            - Notify subscribers 24 hours before maintenance start time
        type: bool
        default: 'no'
    maintenance_notify_1_hr:
        description:
            - Notify subscribers 1 hour before maintenance start time
        type: bool
        default: 'no'
    maintenance_id:
        description:
            - The maintenance id number when deleting a maintenance window
    minutes:
        description:
            - The length of time in UTC that the maintenance will run \
            (starting from playbook runtime)
        default: 10
    start_date:
        description:
            - Date maintenance is expected to start (Month/Day/Year) (UTC)
            - End Date is worked out from start_date + minutes
    start_time:
        description:
            - Time maintenance is expected to start (Hour:Minutes) (UTC)
            - End Time is worked out from start_time + minutes
'''

EXAMPLES = '''
- name: Create a maintenance window for 10 minutes on server1, with automation to stop the maintenance
  statusio_maintenance:
    title: Router Upgrade from ansible
    desc: Performing a Router Upgrade
    components: server1.example.com
    api_id: api_id
    api_key: api_key
    statuspage: statuspage_id
    maintenance_notify_1_hr: True
    automation: True

- name: Create a maintenance window for 60 minutes on server1 and server2
  statusio_maintenance:
    title: Routine maintenance
    desc: Some security updates
    components:
      - server1.example.com
      - server2.example.com
    minutes: 60
    api_id: api_id
    api_key: api_key
    statuspage: statuspage_id
    maintenance_notify_1_hr: True
    automation: True
  delegate_to: localhost

- name: Create a future maintenance window for 24 hours to all hosts inside the Primary Data Center
  statusio_maintenance:
    title: Data center downtime
    desc: Performing a Upgrade to our data center
    components: Primary Data Center
    api_id: api_id
    api_key: api_key
    statuspage: statuspage_id
    start_date: 01/01/2016
    start_time: 12:00
    minutes: 1440

- name: Delete a maintenance window
  statusio_maintenance:
    title: Remove a maintenance window
    maintenance_id: 561f90faf74bc94a4700087b
    statuspage: statuspage_id
    api_id: api_id
    api_key: api_key
    state: absent

'''
# TODO: Add RETURN documentation.
RETURN = ''' # '''

import datetime
import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import open_url


def get_api_auth_headers(api_id, api_key, url, statuspage):

    headers = {
        "x-api-id": api_id,
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = open_url(
            url + "/v2/component/list/" + statuspage, headers=headers)
        data = json.loads(response.read())
        if data['status']['message'] == 'Authentication failed':
            return 1, None, None, "Authentication failed: " \
                                  "Check api_id/api_key and statuspage id."
        else:
            auth_headers = headers
            auth_content = data
    except Exception as e:
        return 1, None, None, to_native(e)
    return 0, auth_headers, auth_content, None


def get_component_ids(auth_content, components):
    host_ids = []
    lower_components = [x.lower() for x in components]
    for result in auth_content["result"]:
        if result['name'].lower() in lower_components:
            data = {
                "component_id": result["_id"],
                "container_id": result["containers"][0]["_id"]
            }
            host_ids.append(data)
            lower_components.remove(result['name'].lower())
    if len(lower_components):
        # items not found in the api
        return 1, None, lower_components
    return 0, host_ids, None


def get_container_ids(auth_content, containers):
    host_ids = []
    lower_containers = [x.lower() for x in containers]
    for result in auth_content["result"]:
        if result["containers"][0]["name"].lower() in lower_containers:
            data = {
                "component_id": result["_id"],
                "container_id": result["containers"][0]["_id"]
            }
            host_ids.append(data)
            lower_containers.remove(result["containers"][0]["name"].lower())

    if len(lower_containers):
        # items not found in the api
        return 1, None, lower_containers
    return 0, host_ids, None


def get_date_time(start_date, start_time, minutes):
    returned_date = []
    if start_date and start_time:
        try:
            datetime.datetime.strptime(start_date, '%m/%d/%Y')
            returned_date.append(start_date)
        except (NameError, ValueError):
            return 1, None, "Not a valid start_date format."
        try:
            datetime.datetime.strptime(start_time, '%H:%M')
            returned_date.append(start_time)
        except (NameError, ValueError):
            return 1, None, "Not a valid start_time format."
        try:
            # Work out end date/time based on minutes
            date_time_start = datetime.datetime.strptime(
                start_time + start_date, '%H:%M%m/%d/%Y')
            delta = date_time_start + datetime.timedelta(minutes=minutes)
            returned_date.append(delta.strftime("%m/%d/%Y"))
            returned_date.append(delta.strftime("%H:%M"))
        except (NameError, ValueError):
            return 1, None, "Couldn't work out a valid date"
    else:
        now = datetime.datetime.utcnow()
        delta = now + datetime.timedelta(minutes=minutes)
        # start_date
        returned_date.append(now.strftime("%m/%d/%Y"))
        returned_date.append(now.strftime("%H:%M"))
        # end_date
        returned_date.append(delta.strftime("%m/%d/%Y"))
        returned_date.append(delta.strftime("%H:%M"))
    return 0, returned_date, None


def create_maintenance(auth_headers, url, statuspage, host_ids,
                       all_infrastructure_affected, automation, title, desc,
                       returned_date, maintenance_notify_now,
                       maintenance_notify_72_hr, maintenance_notify_24_hr,
                       maintenance_notify_1_hr):
    returned_dates = [[x] for x in returned_date]
    component_id = []
    container_id = []
    for val in host_ids:
        component_id.append(val['component_id'])
        container_id.append(val['container_id'])
    try:
        values = json.dumps({
            "statuspage_id": statuspage,
            "components": component_id,
            "containers": container_id,
            "all_infrastructure_affected": str(int(all_infrastructure_affected)),
            "automation": str(int(automation)),
            "maintenance_name": title,
            "maintenance_details": desc,
            "date_planned_start": returned_dates[0],
            "time_planned_start": returned_dates[1],
            "date_planned_end": returned_dates[2],
            "time_planned_end": returned_dates[3],
            "maintenance_notify_now": str(int(maintenance_notify_now)),
            "maintenance_notify_72_hr": str(int(maintenance_notify_72_hr)),
            "maintenance_notify_24_hr": str(int(maintenance_notify_24_hr)),
            "maintenance_notify_1_hr": str(int(maintenance_notify_1_hr))
        })
        response = open_url(
            url + "/v2/maintenance/schedule", data=values,
            headers=auth_headers)
        data = json.loads(response.read())

        if data["status"]["error"] == "yes":
            return 1, None, data["status"]["message"]
    except Exception as e:
        return 1, None, to_native(e)
    return 0, None, None


def delete_maintenance(auth_headers, url, statuspage, maintenance_id):
    try:
        values = json.dumps({
            "statuspage_id": statuspage,
            "maintenance_id": maintenance_id,
        })
        response = open_url(
            url=url + "/v2/maintenance/delete",
            data=values,
            headers=auth_headers)
        data = json.loads(response.read())
        if data["status"]["error"] == "yes":
            return 1, None, "Invalid maintenance_id"
    except Exception as e:
        return 1, None, to_native(e)
    return 0, None, None


def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_id=dict(required=True),
            api_key=dict(required=True, no_log=True),
            statuspage=dict(required=True),
            state=dict(required=False, default='present',
                       choices=['present', 'absent']),
            url=dict(default='https://api.status.io', required=False),
            components=dict(type='list', required=False, default=None,
                            aliases=['component']),
            containers=dict(type='list', required=False, default=None,
                            aliases=['container']),
            all_infrastructure_affected=dict(type='bool', default=False,
                                             required=False),
            automation=dict(type='bool', default=False, required=False),
            title=dict(required=False, default='A new maintenance window'),
            desc=dict(required=False, default='Created by Ansible'),
            minutes=dict(type='int', required=False, default=10),
            maintenance_notify_now=dict(type='bool', default=False,
                                        required=False),
            maintenance_notify_72_hr=dict(type='bool', default=False,
                                          required=False),
            maintenance_notify_24_hr=dict(type='bool', default=False,
                                          required=False),
            maintenance_notify_1_hr=dict(type='bool', default=False,
                                         required=False),
            maintenance_id=dict(required=False, default=None),
            start_date=dict(default=None, required=False),
            start_time=dict(default=None, required=False)
        ),
        supports_check_mode=True,
    )

    api_id = module.params['api_id']
    api_key = module.params['api_key']
    statuspage = module.params['statuspage']
    state = module.params['state']
    url = module.params['url']
    components = module.params['components']
    containers = module.params['containers']
    all_infrastructure_affected = module.params['all_infrastructure_affected']
    automation = module.params['automation']
    title = module.params['title']
    desc = module.params['desc']
    minutes = module.params['minutes']
    maintenance_notify_now = module.params['maintenance_notify_now']
    maintenance_notify_72_hr = module.params['maintenance_notify_72_hr']
    maintenance_notify_24_hr = module.params['maintenance_notify_24_hr']
    maintenance_notify_1_hr = module.params['maintenance_notify_1_hr']
    maintenance_id = module.params['maintenance_id']
    start_date = module.params['start_date']
    start_time = module.params['start_time']

    if state == "present":

        if api_id and api_key:
            (rc, auth_headers, auth_content, error) = \
                get_api_auth_headers(api_id, api_key, url, statuspage)
            if rc != 0:
                module.fail_json(msg="Failed to get auth keys: %s" % error)
        else:
            auth_headers = {}
            auth_content = {}

        if minutes or start_time and start_date:
            (rc, returned_date, error) = get_date_time(
                start_date, start_time, minutes)
            if rc != 0:
                module.fail_json(msg="Failed to set date/time: %s" % error)

        if not components and not containers:
            return module.fail_json(msg="A Component or Container must be "
                                        "defined")
        elif components and containers:
            return module.fail_json(msg="Components and containers cannot "
                                        "be used together")
        else:
            if components:
                (rc, host_ids, error) = get_component_ids(auth_content,
                                                          components)
                if rc != 0:
                    module.fail_json(msg="Failed to find component %s" % error)

            if containers:
                (rc, host_ids, error) = get_container_ids(auth_content,
                                                          containers)
                if rc != 0:
                    module.fail_json(msg="Failed to find container %s" % error)

        if module.check_mode:
            module.exit_json(changed=True)
        else:
            (rc, _, error) = create_maintenance(
                auth_headers, url, statuspage, host_ids,
                all_infrastructure_affected, automation,
                title, desc, returned_date, maintenance_notify_now,
                maintenance_notify_72_hr, maintenance_notify_24_hr,
                maintenance_notify_1_hr)
            if rc == 0:
                module.exit_json(changed=True, result="Successfully created "
                                                      "maintenance")
            else:
                module.fail_json(msg="Failed to create maintenance: %s"
                                 % error)

    if state == "absent":

        if api_id and api_key:
            (rc, auth_headers, auth_content, error) = \
                get_api_auth_headers(api_id, api_key, url, statuspage)
            if rc != 0:
                module.fail_json(msg="Failed to get auth keys: %s" % error)
        else:
            auth_headers = {}

        if module.check_mode:
            module.exit_json(changed=True)
        else:
            (rc, _, error) = delete_maintenance(
                auth_headers, url, statuspage, maintenance_id)
            if rc == 0:
                module.exit_json(
                    changed=True,
                    result="Successfully deleted maintenance"
                )
            else:
                module.fail_json(
                    msg="Failed to delete maintenance: %s" % error)


if __name__ == '__main__':
    main()
