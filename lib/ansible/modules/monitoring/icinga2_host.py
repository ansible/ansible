#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Raphaël Biancone <raphb.bis@gmail.com>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.
#

DOCUMENTATION = '''
---
module: icinga2_host
short_description: Add, delete or modify an host in Icinga2.
description:
    - Add, delete or modify an host in Icinga2 using the API.
version_added: "2.2"
author: "Raphaël BIANCONE, @tux-00"
notes:
    - You need to enable the Icinga2 API feature to use this module.
    - This module bypass the ca certificate validation.
requirements:
    - Icinga2.
    - Icinga2 API feature enabled.
options:
    state:
        description:
            - Whether the host should exist or not. If the host exist and state=present, the host attributes are updated.
        required: false
        default: present
        choices: [present, absent]
    name:
        description:
            - The name of the host.
        required: true
        default: null
    auto_update:
        description:
            - When the option is set to 'yes' and the host exists an update will take place, otherwise nothing happens. The update never removes any attribute.
        required: false
        default: yes
        choices: [ "yes", "no" ]
    display_name:
        description:
            - A short description of the host (e.g. displayed by external interfaces instead of the name if set).
        required: false
        default: null
    api_user:
        description:
            - Icinga2 API feature user.
        required: true
        default: null
    api_password:
        description:
            - Icinga2 API feature password.
        required: true
        default: null
    api_ip:
        description:
            - Icinga2 API server IP address.
        required: false
        default: 127.0.0.1
    api_port:
        description:
            - Icinga2 API listening port.
        required: false
        default: 5665
    address:
        description:
            - The host's address. Available as command runtime macro $address$ if set.
        required: false
        default: null
    address6:
        description:
            - The host's address. Available as command runtime macro $address6$ if set.
        required: false
        default: null
    groups:
        description:
            - A list of host groups this host belongs to.
        required: false
        default: null
    vars:
        description:
            - A dictionary containing custom attributes that are specific to this host.
        required: false
        default: null
    check_command:
        description:
            - The name of the check command.
        required: true
        default: null
    max_check_attempts:
        description:
            - The number of times a host is re-checked before changing into a hard state.
        required: false
        default: null
    check_period:
        description:
            - The name of a time period which determines when this host should be checked.
        required: false
        default: null
    check_timeout:
        description:
            - Check command timeout in seconds. Overrides the CheckCommand's timeout attribute.
        required: false
        default: null
    check_interval:
        description:
            - The check interval (in seconds). This interval is used for checks when the host is in a HARD state.
        required: false
        default: null
    retry_interval:
        description:
            - The retry interval (in seconds). This interval is used for checks when the host is in a SOFT state.
        required: false
        default: null
    enable_notifications:
        description:
            - Whether notifications are enabled.
        required: false
        default: null
        choices: [ "yes", "no" ]
    enable_active_checks:
        description:
            - Whether active checks are enabled.
        required: false
        default: null
        choices: [ "yes", "no" ]
    enable_passive_checks:
        description:
            - Whether passive checks are enabled.
        required: false
        default: null
        choices: [ "yes", "no" ]
    enable_event_handler:
        description:
            - Enables event handlers for this host.
        required: false
        default: null
        choices: [ "yes", "no" ]
    enable_flapping:
        description:
            - Whether flap detection is enabled.
        required: false
        default: null
        choices: [ "yes", "no" ]
    enable_perfdata:
        description:
            - Whether performance data processing is enabled.
        required: false
        default: null
        choices: [ "yes", "no" ]
    event_command:
        description:
            - The name of an event command that should be executed every time the host's state changes or the host is in a SOFT state.
        required: false
        default: null
    flapping_threshold:
        description:
            - The flapping threshold in percent when a host is considered to be flapping.
        required: false
        default: null
    volatile:
        description:
            - The volatile setting enables always HARD state types if NOT-OK state changes occur.
        required: false
        default: null
        choices: [ "yes", "no" ]
    zone:
        description:
            - The zone the object is a member of.
        required: false
        default: null
    command_endpoint:
        description:
            - The endpoint where commands are executed on.
        required: false
        default: null
    notes:
        description:
            - Notes for the host.
        required: false
        default: null
    notes_url:
        description:
            - Url for notes for the host (for example, in notification commands).
        required: false
        default: null
    action_url:
        description:
            - Url for actions for the host (for example, an external graphing tool).
        required: false
        default: null
    icon_image:
        description:
            - Icon image for the host. Used by external interfaces only.
        required: false
        default: null
    icon_image_alt:
        description:
            - Icon image description for the host. Used by external interface only.
        required: false
        default: null
'''

EXAMPLES = '''
- name: Create a new host or update an existing host's info
  icinga2_host:
    state=present
    name=docker-mysql
    display_name="Docker MySQL"
    auto_update=yes
    address=192.168.0.100
    api_user=root
    api_password=pass
    check_command=hostalive
    vars='{"disk":"/", "os":"Linux"}'
    groups="linux-servers"

- name: Delete an host
  icinga2_host:
    state=absent
    name=docker-mysql
    address=192.168.138.16
'''


from ansible.module_utils.basic import *
from ansible.module_utils.urls import open_url
import urllib2

BUILD_JSON_DATA_EXCEPTIONS = ['api_user', 'api_password', 'state', 'name', 'auto_update']


def host_add(name):
    data = build_json_data()

    try:
        res = json.load(open_url(url="https://%s:%s/v1/objects/hosts/%s" % (api_ip, api_port, name),
                                 force=True,
                                 data=data,
                                 headers={"Accept": "application/json"},
                                 method="PUT",
                                 validate_certs=False,
                                 url_username=module.params['api_user'],
                                 url_password=module.params['api_password']))
    except urllib2.URLError:
        e = get_exception()
        try:
            # Try to load json API result
            msg = json.load(e)
        except (AttributeError, ValueError):
            msg = "%s" % e.reason
            module.fail_json(msg=msg, changed=False)

        module.exit_json(msg=msg, changed=False)
    except Exception:
        module.fail_json(msg=get_exception(), changed=False)

    module.exit_json(msg=res, changed=True)


def host_del(name):
    try:
        res = json.load(open_url(url="https://%s:%s/v1/objects/hosts/%s?cascade=1" % (api_ip, api_port, name),
                                 force=True,
                                 headers={"Accept": "application/json"},
                                 method="DELETE",
                                 validate_certs=False,
                                 url_username=module.params['api_user'],
                                 url_password=module.params['api_password']))
    except urllib2.URLError:
        e = get_exception()
        try:
            # Try to load json API result
            msg = json.load(e)
        except (AttributeError, ValueError):
            msg = "%s" % e.reason
            module.fail_json(msg=msg, changed=False)

        module.exit_json(msg=msg, changed=False)
    except Exception:
        e = get_exception()
        msg = "Unexpected error when trying to delete '%s': %s" % (e.reason, name)
        module.fail_json(msg=msg, changed=False)

    module.exit_json(msg=res, changed=True)


def host_modify(name):
    data = build_json_data()

    try:
        res = json.load(open_url(url="https://%s:%s/v1/objects/hosts/%s" % (api_ip, api_port, name),
                                 force=True,
                                 data=data,
                                 headers={"Accept": "application/json"},
                                 method="POST",
                                 validate_certs=False,
                                 url_username=module.params['api_user'],
                                 url_password=module.params['api_password']))
    except urllib2.URLError:
        e = get_exception()
        try:
            # Try to load json API result
            msg = json.load(e)
        except (AttributeError, ValueError):
            msg = "%s" % e.reason
            module.fail_json(msg=msg, changed=False)

        module.exit_json(msg=msg, changed=False)
    except Exception:
        e = get_exception()
        msg = "Unexpected error when trying to modify '%s': %s" % (e.reason, name)
        module.fail_json(msg=msg, changed=False)

    module.exit_json(msg=res, changed=True)


def check_host_exists(name):
    try:
        res = json.load(open_url(url="https://%s:%s/v1/objects/hosts/%s" % (api_ip, api_port, name),
                                 force=True,
                                 headers={"Accept": "application/json"},
                                 method="GET",
                                 validate_certs=False,
                                 url_username=module.params['api_user'],
                                 url_password=module.params['api_password']))

    except urllib2.HTTPError:
        e = get_exception()
        try:
            msg = json.load(e)
        except (AttributeError, ValueError):
            msg = "%s" % e.reason
            module.fail_json(msg=msg, changed=False)

        if e.code == 404:
            return False
        else:
            return True

    except Exception:
        e = get_exception()
        msg = "Unexpected error when trying to check host existence: %s" % e.reason
        module.fail_json(msg=msg, changed=False)

    return True


def build_json_data():
    data = {}
    data['attrs'] = {}
    for key in module.params:
        if module.params[key] and (key not in BUILD_JSON_DATA_EXCEPTIONS):
            data['attrs'][key] = module.params[key]

    return json.dumps(data)


def main():
    global module

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            name=dict(required=True),
            auto_update=dict(default='yes', type='bool'),
            display_name=dict(),
            api_user=dict(required=True),
            api_password=dict(required=True),
            api_ip=dict(default='127.0.0.1'),
            api_port=dict(default='5665', type='int'),
            address=dict(),
            address6=dict(),
            groups=dict(type='list'),
            vars=dict(type='dict'),
            check_command=dict(required=True),
            max_check_attempts=dict(type='int'),
            check_period=dict(),
            check_timeout=dict(type='int'),
            check_interval=dict(type='int'),
            retry_interval=dict(type='int'),
            enable_notifications=dict(type='bool'),
            enable_active_checks=dict(type='bool'),
            enable_passive_checks=dict(type='bool'),
            enable_event_handler=dict(type='bool'),
            enable_flapping=dict(type='bool'),
            enable_perfdata=dict(type='bool'),
            event_command=dict(),
            flapping_threshold=dict(type='int'),
            volatile=dict(type='bool'),
            zone=dict(),
            command_endpoint=dict(),
            notes=dict(),
            notes_url=dict(),
            action_url=dict(),
            icon_image=dict(),
            icon_image_alt=dict(),
        )
    )

    # Get parameters
    host_name = module.params['name']
    state = module.params['state']
    auto_update = module.params['auto_update']

    host_exists = check_host_exists(host_name)

    # Add/modify host
    if state == 'present':
        if auto_update and host_exists:
            host_modify(host_name)
        else:
            host_add(host_name)

    # Delete host
    if state == 'absent':
        host_del(host_name)

    module.exit_json(changed=False)

if __name__ == '__main__':
    main()
