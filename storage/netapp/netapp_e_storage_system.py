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
DOCUMENTATION = '''
module: netapp_e_storage_system
version_added: "2.2"
short_description: Add/remove arrays from the Web Services Proxy
description:
- Manage the arrays accessible via a NetApp Web Services Proxy for NetApp E-series storage arrays.
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
    required: true
    description:
    - The ID of the array to manage. This value must be unique for each array.
  state:
    required: true
    description:
    - Whether the specified array should be configured on the Web Services Proxy or not.
    choices: ['present', 'absent']
  controller_addresses:
    required: true
    description:
    - The list addresses for the out-of-band management adapter or the agent host. Mutually exclusive of array_wwn parameter.
  array_wwn:
    required: false
    description:
    - The WWN of the array to manage. Only necessary if in-band managing multiple arrays on the same agent host.  Mutually exclusive of controller_addresses parameter.
  array_password:
    required: false
    description:
    - The management password of the array to manage, if set.
  enable_trace:
    required: false
    default: false
    description:
    - Enable trace logging for SYMbol calls to the storage system.
  meta_tags:
    required: false
    default: None
    description:
    - Optional meta tags to associate to this storage system
author: Kevin Hulquest (@hulquest)
'''

EXAMPLES = '''
---
    - name:  Presence of storage system
      netapp_e_storage_system:
        ssid: "{{ item.key }}"
        state: present
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
        controller_addresses:
          - "{{ item.value.address1 }}"
          - "{{ item.value.address2 }}"
      with_dict: "{{ storage_systems }}"
      when: check_storage_system
'''

RETURN = '''
msg: Storage system removed.
msg: Storage system added.
'''
import json
from datetime import datetime as dt, timedelta
from time import sleep

from ansible.module_utils.api import basic_auth_argument_spec
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.error import HTTPError


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


def do_post(ssid, api_url, post_headers, api_usr, api_pwd, validate_certs, request_body, timeout):
    (rc, resp) = request(api_url + "/storage-systems", data=request_body, headers=post_headers,
                         method='POST', url_username=api_usr, url_password=api_pwd,
                         validate_certs=validate_certs)
    status = None
    return_resp = resp
    if 'status' in resp:
        status = resp['status']

    if rc == 201:
        status = 'neverContacted'
        fail_after_time = dt.utcnow() + timedelta(seconds=timeout)

        while status == 'neverContacted':
            if dt.utcnow() > fail_after_time:
                raise Exception("web proxy timed out waiting for array status")

            sleep(1)
            (rc, system_resp) = request(api_url + "/storage-systems/%s" % ssid,
                                        headers=dict(Accept="application/json"), url_username=api_usr,
                                        url_password=api_pwd, validate_certs=validate_certs,
                                        ignore_errors=True)
            status = system_resp['status']
            return_resp = system_resp

    return status, return_resp


def main():
    argument_spec = basic_auth_argument_spec()
    argument_spec.update(dict(
        state=dict(required=True, choices=['present', 'absent']),
        ssid=dict(required=True, type='str'),
        controller_addresses=dict(type='list'),
        array_wwn=dict(required=False, type='str'),
        array_password=dict(required=False, type='str', no_log=True),
        array_status_timeout_sec=dict(default=60, type='int'),
        enable_trace=dict(default=False, type='bool'),
        meta_tags=dict(type='list')
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[['controller_addresses', 'array_wwn']],
        required_if=[('state', 'present', ['controller_addresses'])]
    )

    p = module.params

    state = p['state']
    ssid = p['ssid']
    controller_addresses = p['controller_addresses']
    array_wwn = p['array_wwn']
    array_password = p['array_password']
    array_status_timeout_sec = p['array_status_timeout_sec']
    validate_certs = p['validate_certs']
    meta_tags = p['meta_tags']
    enable_trace = p['enable_trace']

    api_usr = p['api_username']
    api_pwd = p['api_password']
    api_url = p['api_url']

    changed = False
    array_exists = False

    try:
        (rc, resp) = request(api_url + "/storage-systems/%s" % ssid, headers=dict(Accept="application/json"),
                             url_username=api_usr, url_password=api_pwd, validate_certs=validate_certs,
                             ignore_errors=True)
    except:
        err = get_exception()
        module.fail_json(msg="Error accessing storage-system with id [%s]. Error [%s]" % (ssid, str(err)))

    array_exists = True
    array_detail = resp

    if rc == 200:
        if state == 'absent':
            changed = True
            array_exists = False
        elif state == 'present':
            current_addresses = frozenset(i for i in (array_detail['ip1'], array_detail['ip2']) if i)
            if set(controller_addresses) != current_addresses:
                changed = True
            if array_detail['wwn'] != array_wwn and array_wwn is not None:
                module.fail_json(
                    msg='It seems you may have specified a bad WWN. The storage system ID you specified, %s, currently has the WWN of %s' % (ssid, array_detail['wwn']))
    elif rc == 404:
        if state == 'present':
            changed = True
            array_exists = False
        else:
            changed = False
            module.exit_json(changed=changed, msg="Storage system was not present.")

    if changed and not module.check_mode:
        if state == 'present':
            if not array_exists:
                # add the array
                array_add_req = dict(
                    id=ssid,
                    controllerAddresses=controller_addresses,
                    metaTags=meta_tags,
                    enableTrace=enable_trace
                )

                if array_wwn:
                    array_add_req['wwn'] = array_wwn

                if array_password:
                    array_add_req['password'] = array_password

                post_headers = dict(Accept="application/json")
                post_headers['Content-Type'] = 'application/json'
                request_data = json.dumps(array_add_req)

                try:
                    (rc, resp) = do_post(ssid, api_url, post_headers, api_usr, api_pwd, validate_certs, request_data,
                                         array_status_timeout_sec)
                except:
                    err = get_exception()
                    module.fail_json(msg="Failed to add storage system. Id[%s]. Request body [%s]. Error[%s]." %
                                         (ssid, request_data, str(err)))

            else:  # array exists, modify...
                post_headers = dict(Accept="application/json")
                post_headers['Content-Type'] = 'application/json'
                post_body = dict(
                    controllerAddresses=controller_addresses,
                    removeAllTags=True,
                    enableTrace=enable_trace,
                    metaTags=meta_tags
                )

                try:
                    (rc, resp) = do_post(ssid, api_url, post_headers, api_usr, api_pwd, validate_certs, post_body,
                                         array_status_timeout_sec)
                except:
                    err = get_exception()
                    module.fail_json(msg="Failed to update storage system. Id[%s]. Request body [%s]. Error[%s]." %
                                         (ssid, post_body, str(err)))

        elif state == 'absent':
            # delete the array
            try:
                (rc, resp) = request(api_url + "/storage-systems/%s" % ssid, method='DELETE',
                                     url_username=api_usr,
                                     url_password=api_pwd, validate_certs=validate_certs)
            except:
                err = get_exception()
                module.fail_json(msg="Failed to remove storage array. Id[%s]. Error[%s]." % (ssid, str(err)))

            if rc == 422:
                module.exit_json(changed=changed, msg="Storage system was not presnt.")
            if rc == 204:
                module.exit_json(changed=changed, msg="Storage system removed.")

    module.exit_json(changed=changed, **resp)


if __name__ == '__main__':
    main()
