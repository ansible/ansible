#!/usr/bin/python

# (c) 2016, NetApp, Inc
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
DOCUMENTATION = """
---
module: netapp_e_amg_role
short_description: Update the role of a storage array within an Asynchronous Mirror Group (AMG).
description:
    - Update a storage array to become the primary or secondary instance in an asynchronous mirror group
version_added: '2.2'
author: Kevin Hulquest (@hulquest)
options:
    api_username:
        required: true
        description:
        - The username to authenticate with the SANtricity WebServices Proxy or embedded REST API.
    api_password:
        required: true
        description:
        - The password to authenticate with the SANtricity WebServices Proxy or embedded REST API.
    api_url:
        required: true
        description:
        - The url to the SANtricity WebServices Proxy or embedded REST API.
        example:
        - https://prod-1.wahoo.acme.com/devmgr/v2
    validate_certs:
        required: false
        default: true
        description:
        - Should https certificates be validated?
    ssid:
        description:
            - The ID of the primary storage array for the async mirror action
        required: yes
    role:
        description:
            - Whether the array should be the primary or secondary array for the AMG
        required: yes
        choices: ['primary', 'secondary']
    noSync:
        description:
            - Whether to avoid synchronization prior to role reversal
        required: no
        default: no
        choices: [yes, no]
    force:
        description:
            - Whether to force the role reversal regardless of the online-state of the primary
        required: no
        default: no
"""

EXAMPLES = """
    - name: Update the role of a storage array
      netapp_e_amg_role:
        name: updating amg role
        role: primary
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
"""

RETURN = """
msg:
    description: Failure message
    returned: failure
    type: string
    sample: "No Async Mirror Group with the name."
"""
import json

from ansible.module_utils.api import basic_auth_argument_spec
from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.error import HTTPError

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def request(url, data=None, headers=None, method='GET', use_proxy=True,
            force=False, last_mod_time=None, timeout=10, validate_certs=True,
            url_username=None, url_password=None, http_agent=None, force_basic_auth=True, ignore_errors=False):
    try:
        r = open_url(url=url, data=data, headers=headers, method=method, use_proxy=use_proxy,
                     force=force, last_mod_time=last_mod_time, timeout=timeout, validate_certs=validate_certs,
                     url_username=url_username, url_password=url_password, http_agent=http_agent,
                     force_basic_auth=force_basic_auth)
    except HTTPError:
        err = get_exception()
        r = err.fp

    try:
        raw_data = r.read()
        if raw_data:
            data = json.loads(raw_data)
        else:
            raw_data = None
    except:
        if ignore_errors:
            pass
        else:
            raise Exception(raw_data)

    resp_code = r.getcode()

    if resp_code >= 400 and not ignore_errors:
        raise Exception(resp_code, data)
    else:
        return resp_code, data


def has_match(module, ssid, api_url, api_pwd, api_usr, body, name):
    amg_exists = False
    has_desired_role = False
    amg_id = None
    amg_data = None
    get_amgs = 'storage-systems/%s/async-mirrors' % ssid
    url = api_url + get_amgs
    try:
        amg_rc, amgs = request(url, url_username=api_usr, url_password=api_pwd,
                               headers=HEADERS)
    except:
        module.fail_json(msg="Failed to find AMGs on storage array. Id [%s]" % (ssid))

    for amg in amgs:
        if amg['label'] == name:
            amg_exists = True
            amg_id = amg['id']
            amg_data = amg
            if amg['localRole'] == body.get('role'):
                has_desired_role = True

    return amg_exists, has_desired_role, amg_id, amg_data


def update_amg(module, ssid, api_url, api_usr, api_pwd, body, amg_id):
    endpoint = 'storage-systems/%s/async-mirrors/%s/role' % (ssid, amg_id)
    url = api_url + endpoint
    post_data = json.dumps(body)
    try:
        request(url, data=post_data, method='POST', url_username=api_usr,
                url_password=api_pwd, headers=HEADERS)
    except:
        err = get_exception()
        module.fail_json(
            msg="Failed to change role of AMG. Id [%s].  AMG Id [%s].  Error [%s]" % (ssid, amg_id, str(err)))

    status_endpoint = 'storage-systems/%s/async-mirrors/%s' % (ssid, amg_id)
    status_url = api_url + status_endpoint
    try:
        rc, status = request(status_url, method='GET', url_username=api_usr,
                             url_password=api_pwd, headers=HEADERS)
    except:
        err = get_exception()
        module.fail_json(
            msg="Failed to check status of AMG after role reversal. " +
                "Id [%s].  AMG Id [%s].  Error [%s]" % (ssid, amg_id, str(err)))

    # Here we wait for the role reversal to complete
    if 'roleChangeProgress' in status:
        while status['roleChangeProgress'] != "none":
            try:
                rc, status = request(status_url, method='GET',
                                     url_username=api_usr, url_password=api_pwd, headers=HEADERS)
            except:
                err = get_exception()
                module.fail_json(
                    msg="Failed to check status of AMG after role reversal. " +
                        "Id [%s].  AMG Id [%s].  Error [%s]" % (ssid, amg_id, str(err)))
    return status


def main():
    argument_spec = basic_auth_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True, type='str'),
        role=dict(required=True, choices=['primary', 'secondary']),
        noSync=dict(required=False, type='bool', default=False),
        force=dict(required=False, type='bool', default=False),
        ssid=dict(required=True, type='str'),
        api_url=dict(required=True),
        api_username=dict(required=False),
        api_password=dict(required=False, no_log=True),
    ))

    module = AnsibleModule(argument_spec=argument_spec)

    p = module.params

    ssid = p.pop('ssid')
    api_url = p.pop('api_url')
    user = p.pop('api_username')
    pwd = p.pop('api_password')
    name = p.pop('name')

    if not api_url.endswith('/'):
        api_url += '/'

    agm_exists, has_desired_role, async_id, amg_data = has_match(module, ssid, api_url, pwd, user, p, name)

    if not agm_exists:
        module.fail_json(msg="No Async Mirror Group with the name: '%s' was found" % name)
    elif has_desired_role:
        module.exit_json(changed=False, **amg_data)

    else:
        amg_data = update_amg(module, ssid, api_url, user, pwd, p, async_id)
        if amg_data:
            module.exit_json(changed=True, **amg_data)
        else:
            module.exit_json(changed=True, msg="AMG role changed.")


if __name__ == '__main__':
    main()
