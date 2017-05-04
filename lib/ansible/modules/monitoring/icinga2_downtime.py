#!/usr/bin/python

# (c) 2016, Walid Shaita <walid.shaita@gmail.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: icinga2_downtime
version_added: "2.4"
author: "Walid Shaita (@Shaita-KrZ)"
short_description: Manage downtime for icinga2 using Icinga2 API.
description:
    - A module to manage downtime for icinga2 using Icinga2 API.
    - This module is able to schedule or remove downtime for hosts or/and services (can be used with regex).
options:
    icinga2_url:
        required: true
        description:
            - URL of the icinga2 server on which the API is enabled.
    icinga2_port:
        required: false
        default: 5665
        description:
            - Port of the icinga2 server on which the API is enabled.
    icinga2_api_user:
        required: true
        description:
            - Icinga2 admin user.
    icinga2_api_password:
        required: true
        description:
            - Icinga2 admin password.
    state:
        required: false
        default: present
        choices: [ present, absent ]
        description:
            - C(present) to schedule a downtime.
            - C(absent) to remove a downtime.
    hostname:
        required: false
        description:
            - Name of the hostname you want to schedule a downtime. The hostname can be specified with regex.
            - If you specify services, it will schedule a downtime for the services related to the hostname.
            - If you don't specify services, it will schedule a downtime only for the host.
            - One of hostname or services are required at least.
    services:
        required: false
        description:
            - List of the services you want to schedule a downtime. The services can be specified with regex.
            - If you specify a hostname, it will schedule a downtime for the services related to a hostname.
            - If you don't specify a hostname, it will schedule a downtime for the all the services listed.
            - One of hostname or services are required at least.
    start_time:
        required: false
        default: current datetime
        description:
            - Correspond to the datetime you want to schedule your downtime. If you don't specify one, it will take the current datetime.
            - The format of the datetime is YYYY-mm-dd HH:MM:SS.
    end_time:
        required: false
        description:
            - Correspond to the time you want to end your downtime. The format of the datetime is YYYY-mm-dd HH:MM:SS.
            - You can either use the end_time or the days, hours, minutes, seconds attributes.
    days:
        required: false
        description:
            - Number of days you want to schedule your downtime (start from the start_time). You can either use days or specify an end_time.
    hours:
        required: false
        description:
            - Number of hours you want to schedule your downtime (starting from the start_time). You can either use hours or specify an end_time.
    minutes:
        required: false
        description:
            - Number of minutes you want to schedule your downtime (starting from the start_time). You can either use minutes or specify an end_time.
    seconds:
        required: false
        description:
            - Number of seconds you want to schedule your downtime (starting from the start_time). You can either use seconds or specify an end_time.
    duration:
        required: false
        description:
            - Duration of the downtime in seconds if fixed is set to false. Duration is required if fixed is set to false.
    fixed:
        required: false
        default: true
        description:
            - Default to true. If true, the downtime is fixed otherwise flexible.
    author:
        required: false
        default: Ansible
        description:
            - Name of the author. The author can be used to remove all the downtime scheduled by the C(author).
    comment:
        required: false
        default: Downtime scheduled by Ansible
        description:
            - Comment text.
    validate_certs:
        required: false
        default : true
        description:
            - if certificates should be validated or not.
'''

EXAMPLES = '''
# Schedule downtimes for all the hosts starting by "redshift-*" (downtime will start at 2017-04-13 12:00:04 and end at 2017-04-13 14:00:04).

- name: Schedule downtime
  icinga2_downtime:
    icinga2_url: http://localhost
    icinga2_api_user: root
    icinga2_api_password: icinga2
    state: present
    hostname: redshift-*
    comment: schedule maintenance
    author: Walid
    start-time: "2017-04-13 12:00:04"
    end_time: "2017-04-13 14:00:04"

# Schedule downtimes for all services starting by "nrpe-" and "redshift-", related to all the hosts starting by "redshift-*".
# (downtime will start at the current time and end 2h 30m and 30s later)

- name: Schedule downtime
  icinga2_downtime:
    icinga2_url: http://localhost
    icinga2_api_user: root
    icinga2_api_password: icinga2
    state: present
    hostname: redshift-*
    comment: schedule maintenance
    author: Walid
    hours: 2
    minutes: 30
    seconds: 30
    services:
      - nrpe-*
      - redshift-*

# Remove downtimes for all services starting by "nrpe-" and "redshift-" related to the "redshift-warehouse" hostname (on port 3000).

- name: Remove downtime
  icinga2_downtime:
    icinga2_url: http://localhost
    icinga2_port: 3000
    icinga2_api_user: root
    icinga2_api_password: icinga2
    state: absent
    hostname: redshift-warehouse
    services:
      - nrpe-*
      - redshift-*

# Remove downtimes scheduled by the author named "Walid".

- name: Remove downtime
  icinga2_downtime:
    icinga2_url: http://localhost
    icinga2_api_user: root
    icinga2_api_password: icinga2
    state: absent
    author: Walid
'''

RETURN = '''
code:
    description: http status code returned by icinga2.
    returned: changed
    type: int
    sample: 200
name:
    description: name of the hostname or/and the services affected.
    returned: changed
    type: string
    sample: test-ansible-v2-172-XX-X-XX!ip-XX-X-XX-XXX
status:
    description: status returned by icinga2.
    returned: changed
    type: string
    sample: Successfully scheduled downtime test-ansible-v2-172-XX-X-XX!ip-172-XX-X-XX-XXX for object test-ansible-v2-172-XX-X-XX.
response:
    description: response returned by icinga2.
    returned: always
    type: string
    sample: Services or hostname not found.
'''

import time
import uuid
import hmac
import hashlib
import base64
import time
import calendar
import datetime
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import json
from ansible.module_utils.urls import open_url


def _convert_duration(module):
    days = module.params.get('days')
    hours = module.params.get('hours')
    minutes = module.params.get('minutes')
    seconds = module.params.get('seconds')
    duration = 0
    if days is not None:
        duration = duration + days * 86400
    if hours is not None:
        duration = duration + hours * 3600
    if minutes is not None:
        duration = duration + minutes * 60
    if seconds is not None:
        duration = duration + seconds
    if days is None and hours is None and minutes is None and seconds is None:
        duration = 0
    return duration


def _create_filter(services):
    filter = "("
    length = len(services)
    for i in range(0, length):
        filter += "match(\"" + services[i] + "\",service.name)"
        if i < length - 1:
            filter += " || "
    filter += ")"
    return filter


def _call_icinga2_api(module, payload, state):
    # At the top of the function
    icinga2_api_downtime_endpoint = "/v1/actions/%s" % (state)
    icinga2_url = module.params.get('icinga2_url')
    icinga2_port = module.params.get('icinga2_port')
    icinga2_api_user = module.params.get('icinga2_api_user')
    icinga2_api_password = module.params.get('icinga2_api_password')
    validate_certs = module.params.get('validate_certs')

    headers = {"Accept": "application/json"}
    uri = "%s:%s%s" % (icinga2_url, icinga2_port, icinga2_api_downtime_endpoint)

    r = None
    try:
        r = open_url(uri, method="POST", headers=headers, url_username=icinga2_api_user,
                     url_password=icinga2_api_password, force_basic_auth=True, data=json.dumps(payload), validate_certs=validate_certs)
        results = json.loads(r.read())
        if len(results['results']) > 0:
            _return_result(module, True, False, results['results'])
        else:
            _return_result(module, False, False, "Services or hostname not found.")
    except ValueError as e:
        if r is not None:
            _return_result(module, False, True, results['results'])
        else:
            _return_result(module, False, True, 'An unexpected exception occurred while scheduling downtime on Icinga2.')
    except Exception as e:
        _return_result(module, False, True, str(e))


def _return_result(module, changed, failed, message):
    result = {}
    if changed:
        result['code'] = message[0]["code"]
        result['name'] = message[0]['name']
        result['status'] = message[0]['status']

    result['response'] = message
    result['changed'] = changed
    result['failed'] = failed
    module.exit_json(**result)


def schedule_downtime(module, start_time, end_time):
    state = module.params.get('state')

    hostname = module.params.get('hostname')
    services = module.params.get('services')

    author = module.params.get('author')
    comment = module.params.get('comment')
    fixed = module.params.get('fixed')
    duration = module.params.get('duration')

    if services is not None:
        filter = _create_filter(services)

    if services is None and hostname is not None:
        # Schedule downtime on the host
        payload = {'start_time': start_time, 'end_time': end_time, 'duration': duration, 'author': author,
                   'comment': comment, "filter": "match(\"" + hostname + "\",host.name)", "type": "Host", "fixed": fixed}
    elif hostname is None and services is not None:
        # Schedule downtime on a service across one or multiple hosts
        payload = {'start_time': start_time, 'end_time': end_time, 'duration': duration,
                   'author': author, 'comment': comment, 'type': 'Service', "filter": filter, "fixed": fixed}
    elif hostname is not None and services is not None:
        # Schedule downtime on a service for a specific host
        payload = {'start_time': start_time, 'end_time': end_time, 'duration': duration, 'author': author, 'comment': comment,
                   'type': 'Service', 'filter': filter + " && match(\"" + hostname + "\",host.name)", "fixed": fixed}
    else:
        module.fail_json(msg="You have to specify either a host or service")

    _call_icinga2_api(module, payload, "schedule-downtime")


def remove_downtime(module):
    state = module.params.get('state')
    hostname = module.params.get('hostname')
    services = module.params.get('services')
    author = module.params.get('author')
    comment = module.params.get('comment')

    if services is not None:
        filter = _create_filter(services)

    if hostname is not None and services is None:
        # Remove downtime related to a specific host
        payload = {"filter": "match(\"" + hostname + "\",host.name)", "type": "Host", 'downtime.author': author}
    elif hostname is None and services is not None:
        # Remove downtime related to specific services
        payload = {'type': 'Service', "filter": filter, 'downtime.author': author}
    elif hostname is not None and services is not None:
        # Remove downtime related to services within a specific host
        payload = {'type': 'Service', 'filter': filter + " && match(\"" + hostname + "\",host.name)", 'downtime.author': author}
    elif hostname is None and services is None:
        # Remove downtime related to the author
        payload = {'type': 'Downtime', 'downtime.author': author}
    else:
        module.fail_json(msg="You have to specify either a host or service")

    _call_icinga2_api(module, payload, "remove-downtime")


def check_input(module):
    fixed = module.params.get('fixed')
    start_time = module.params.get('start_time')
    end_time = module.params.get('end_time')
    end_time_duration = _convert_duration(module)
    duration = module.params.get('duration')
    state = module.params.get('state')
    hostname = module.params.get('hostname')
    services = module.params.get('services')

    # for flexible downtime, duration is required
    if duration is None and fixed is False:
        module.fail_json(msg="duration is required for flexible downtime")

    if state == 'present':
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if (start_time < now or end_time < now) and end_time_duration == 0:
            module.fail_json(msg="start_time or/and end_time can't be lower than current datetime")

        if start_time > end_time and end_time_duration == 0:
            module.fail_json(msg="end_time can't be lower than start_time")

        if hostname is None and services is None:
            module.fail_json(msg="one of the following is required: hostname,services")

        if end_time_duration == 0 and end_time is None:
            module.fail_json(msg="end_time is required for scheduling downtime")


def main():
    argument_spec = {}

    argument_spec.update(dict(
        icinga2_url=dict(required=True, type='str', defaults='https://localhost:5666'),
        icinga2_port=dict(required=False, type='str', default='5665'),
        icinga2_api_user=dict(required=True, type='str'),
        icinga2_api_password=dict(required=True, type='str'),
        state=dict(required=False, choices=['present', 'absent'], default='present'),
        hostname=dict(required=False, type='str', default=None),
        services=dict(required=False, type='list', default=None),
        start_time=dict(required=False, type='str', default=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        end_time=dict(required=False, type='str', default=None),
        days=dict(required=False, type='int', default=None),
        hours=dict(required=False, type='int', default=None),
        minutes=dict(required=False, type='int', default=None),
        seconds=dict(required=False, type='int', default=None),
        duration=dict(required=False, type='int', default=None),
        author=dict(required=False, type='str', default='Ansible'),
        comment=dict(required=False, type='str', default='Downtime scheduled by Ansible'),
        fixed=dict(required=False, type='bool', default=True),
        validate_certs=dict(required=False, type='bool', default=True)
    )),

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    start_time = module.params.get('start_time')
    end_time = module.params.get('end_time')
    end_time_duration = _convert_duration(module)
    state = module.params.get('state')

    # Check inputs
    check_input(module)

    if state == 'present':

        if end_time is not None:
            try:
                end_time = time.mktime(datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S").timetuple())
            except (ValueError, TypeError):
                module.fail_json(msg="start time does not match format '%Y-%m-%d %H:%M:%S'")

        try:
            start_time = time.mktime(datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").timetuple())
        except (ValueError, TypeError):
            module.fail_json(msg="start time does not match format '%Y-%m-%d %H:%M:%S'")

        if end_time is None:
            end_time = start_time + datetime.timedelta(seconds=end_time_duration).total_seconds()

        schedule_downtime(module, start_time, end_time)

    elif state == 'absent':
        remove_downtime(module)


if __name__ == '__main__':
    main()
