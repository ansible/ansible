#!/usr/bin/python

# (c) 2016, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: netapp_e_name
short_description: Sets the name for a storage array.
description:
    - Sets the name for a storage array.
version_added: "2.2"
author:
options:
    validate_certs:
      required: false
      default: true
      description:
        - Should https certificates be validated?
    name:
      description:
        - The name of the storage array.
      required: True
    ssid:
      description:
        - the identifier of the storage array in the Web Services Proxy. Always 1 in case embedded WebServer
      required: True
    api_url:
      description:
        - The full API url.
        - "Example: http://ENDPOINT:8080/devmgr/v2"
        - This can optionally be set via an environment variable, API_URL
      required: False
    api_username:
      description:
        - The username used to authenticate against the API
        - This can optionally be set via an environment variable, API_USERNAME
      required: False
    api_password:
      description:
        - The password used to authenticate against the API
        - This can optionally be set via an environment variable, API_PASSWORD
      required: False
'''

EXAMPLES = '''
- name: Test module
  netapp_e_name:
    name: trex
    api_url: '{{ netapp_api_url }}'
    api_username: '{{ netapp_api_username }}'
    api_password: '{{ netapp_api_password }}'
'''

RETURN = '''
msg:
    description: Success message
    returned: success
    type: string
    sample: "Name Updated Successfully"
'''
import json

from ansible.module_utils.api import basic_auth_argument_spec
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import open_url


HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}


def request(url, data=None, headers=None, method='GET', use_proxy=True,
            force=False, last_mod_time=None, timeout=10, validate_certs=True,
            url_username=None, url_password=None, http_agent=None, force_basic_auth=True, ignore_errors=False):
    try:
        r = open_url(url=url, data=data, headers=headers, method=method, use_proxy=use_proxy,
                     force=force, last_mod_time=last_mod_time, timeout=timeout, validate_certs=validate_certs,
                     url_username=url_username, url_password=url_password, http_agent=http_agent,
                     force_basic_auth=force_basic_auth)
    except HTTPError as e:
        r = e.fp

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


def get_name(module, ssid, api_url, api_user, api_pwd, certs):
    name_status = "storage-systems/%s" % ssid
    url = api_url + name_status
    try:
        rc, data = request(url, headers=HEADERS, url_username=api_user, url_password=api_pwd, validate_certs=certs)
        return data['name']
    except HTTPError as e:
        module.fail_json(msg="There was an issue with connecting, please check that your "
                             "endpoint is properly defined and your credentials are correct: %s" % to_native(e))


def set_name(module, ssid, api_url, api_user, api_pwd, certs, name):
    update_name = 'storage-systems/%s/configuration' % ssid
    url = api_url + update_name
    post_body = json.dumps(dict(name=name))
    system_name = get_name(module, ssid, api_url, api_user, api_pwd, certs)
    if system_name == name:
        module.exit_json(changed=False, msg="System name was already set to [%s]" % (name))
    else:
        try:
            rc, data = request(url, data=post_body, method='POST', headers=HEADERS, url_username=api_user,
                               url_password=api_pwd, validate_certs=certs)
        except Exception as e:
            module.fail_json(msg="Failed to update system name. Id [%s].  Error [%s]" % (ssid, to_native(e)))

    if int(rc) == 200:
        return data
    else:
        module.fail_json(msg="%s:%s" % (rc, data))


def main():
    argument_spec = basic_auth_argument_spec()
    argument_spec.update(dict(
        name=dict(required=False, type='str'),
        ssid=dict(required=False, type='str'),
        validate_certs=dict(type='bool'),
        api_url=dict(required=True),
        api_username=dict(required=False),
        api_password=dict(required=False, no_log=True)
    )
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           required_together=[['name', 'ssid']])

    name = module.params['name']
    ssid = module.params['ssid']
    certs = module.params['validate_certs']
    api_user = module.params['api_username']
    api_pwd = module.params['api_password']
    api_url = module.params['api_url']

    if not api_url.endswith('/'):
        api_url += '/'

    success = set_name(module, ssid, api_url, api_user, api_pwd, certs, name)
    module.exit_json(changed=True, msg="Name Updated Successfully", **success)


if __name__ == '__main__':
    main()
