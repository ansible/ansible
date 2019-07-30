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
module: netapp_e_auth
short_description: NetApp E-Series set or update the password for a storage array.
description:
    - Sets or updates the password for a storage array.  When the password is updated on the storage array, it must be updated on the SANtricity Web
      Services proxy. Note, all storage arrays do not have a Monitor or RO role.
version_added: "2.2"
author: Kevin Hulquest (@hulquest)
options:
    validate_certs:
        required: false
        default: true
        description:
        - Should https certificates be validated?
        type: bool
    name:
      description:
        - The name of the storage array. Note that if more than one storage array with this name is detected, the task will fail and you'll have to use
          the ID instead.
      required: False
    ssid:
      description:
        - the identifier of the storage array in the Web Services Proxy.
      required: False
    set_admin:
      description:
        - Boolean value on whether to update the admin password. If set to false then the RO account is updated.
      type: bool
      default: False
    current_password:
      description:
        - The current admin password. This is not required if the password hasn't been set before.
      required: False
    new_password:
      description:
        - The password you would like to set. Cannot be more than 30 characters.
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
  netapp_e_auth:
    name: trex
    current_password: OldPasswd
    new_password: NewPasswd
    set_admin: yes
    api_url: '{{ netapp_api_url }}'
    api_username: '{{ netapp_api_username }}'
    api_password: '{{ netapp_api_password }}'
'''

RETURN = '''
msg:
    description: Success message
    returned: success
    type: str
    sample: "Password Updated Successfully"
'''
import json
import traceback

from ansible.module_utils.api import basic_auth_argument_spec
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import open_url

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "x-netapp-password-validate-method": "none"

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
    except Exception:
        if ignore_errors:
            pass
        else:
            raise Exception(raw_data)

    resp_code = r.getcode()

    if resp_code >= 400 and not ignore_errors:
        raise Exception(resp_code, data)
    else:
        return resp_code, data


def get_ssid(module, name, api_url, user, pwd):
    count = 0
    all_systems = 'storage-systems'
    systems_url = api_url + all_systems
    rc, data = request(systems_url, headers=HEADERS, url_username=user, url_password=pwd,
                       validate_certs=module.validate_certs)
    for system in data:
        if system['name'] == name:
            count += 1
            if count > 1:
                module.fail_json(
                    msg="You supplied a name for the Storage Array but more than 1 array was found with that name. " +
                        "Use the id instead")
            else:
                ssid = system['id']
        else:
            continue

    if count == 0:
        module.fail_json(msg="No storage array with the name %s was found" % name)

    else:
        return ssid


def get_pwd_status(module, ssid, api_url, user, pwd):
    pwd_status = "storage-systems/%s/passwords" % ssid
    url = api_url + pwd_status
    try:
        rc, data = request(url, headers=HEADERS, url_username=user, url_password=pwd,
                           validate_certs=module.validate_certs)
        return data['readOnlyPasswordSet'], data['adminPasswordSet']
    except HTTPError as e:
        module.fail_json(msg="There was an issue with connecting, please check that your "
                             "endpoint is properly defined and your credentials are correct: %s" % to_native(e))


def update_storage_system_pwd(module, ssid, pwd, api_url, api_usr, api_pwd):
    """Update the stored storage-system password"""
    update_pwd = 'storage-systems/%s' % ssid
    url = api_url + update_pwd
    post_body = json.dumps(dict(storedPassword=pwd))
    try:
        rc, data = request(url, data=post_body, method='POST', headers=HEADERS, url_username=api_usr,
                           url_password=api_pwd, validate_certs=module.validate_certs)
        return rc, data
    except Exception as e:
        module.fail_json(msg="Failed to update system password. Id [%s].  Error [%s]" % (ssid, to_native(e)))


def set_password(module, ssid, api_url, user, pwd, current_password=None, new_password=None, set_admin=False):
    """Set the storage-system password"""
    set_pass = "storage-systems/%s/passwords" % ssid
    url = api_url + set_pass

    if not current_password:
        current_password = ""

    post_body = json.dumps(
        dict(currentAdminPassword=current_password, adminPassword=set_admin, newPassword=new_password))

    try:
        rc, data = request(url, method='POST', data=post_body, headers=HEADERS, url_username=user, url_password=pwd,
                           ignore_errors=True, validate_certs=module.validate_certs)
    except Exception as e:
        module.fail_json(msg="Failed to set system password. Id [%s].  Error [%s]" % (ssid, to_native(e)),
                         exception=traceback.format_exc())

    if rc == 422:
        post_body = json.dumps(dict(currentAdminPassword='', adminPassword=set_admin, newPassword=new_password))
        try:
            rc, data = request(url, method='POST', data=post_body, headers=HEADERS, url_username=user, url_password=pwd,
                               validate_certs=module.validate_certs)
        except Exception:
            # TODO(lorenp): Resolve ignored rc, data
            module.fail_json(msg="Wrong or no admin password supplied. Please update your playbook and try again")

    if int(rc) >= 300:
        module.fail_json(msg="Failed to set system password. Id [%s] Code [%s].  Error [%s]" % (ssid, rc, data))

    rc, update_data = update_storage_system_pwd(module, ssid, new_password, api_url, user, pwd)

    if int(rc) < 300:
        return update_data
    else:
        module.fail_json(msg="%s:%s" % (rc, update_data))


def main():
    argument_spec = basic_auth_argument_spec()
    argument_spec.update(dict(
        name=dict(required=False, type='str'),
        ssid=dict(required=False, type='str'),
        current_password=dict(required=False, no_log=True),
        new_password=dict(required=True, no_log=True),
        set_admin=dict(required=True, type='bool'),
        api_url=dict(required=True),
        api_username=dict(required=False),
        api_password=dict(required=False, no_log=True)
    )
    )
    module = AnsibleModule(argument_spec=argument_spec, mutually_exclusive=[['name', 'ssid']],
                           required_one_of=[['name', 'ssid']])

    name = module.params['name']
    ssid = module.params['ssid']
    current_password = module.params['current_password']
    new_password = module.params['new_password']
    set_admin = module.params['set_admin']
    user = module.params['api_username']
    pwd = module.params['api_password']
    api_url = module.params['api_url']
    module.validate_certs = module.params['validate_certs']

    if not api_url.endswith('/'):
        api_url += '/'

    if name:
        ssid = get_ssid(module, name, api_url, user, pwd)

    ro_pwd, admin_pwd = get_pwd_status(module, ssid, api_url, user, pwd)

    if admin_pwd and not current_password:
        module.fail_json(
            msg="Admin account has a password set. " +
                "You must supply current_password in order to update the RO or Admin passwords")

    if len(new_password) > 30:
        module.fail_json(msg="Passwords must not be greater than 30 characters in length")

    result = set_password(module, ssid, api_url, user, pwd, current_password=current_password,
                          new_password=new_password, set_admin=set_admin)

    module.exit_json(changed=True, msg="Password Updated Successfully",
                     password_set=result['passwordSet'],
                     password_status=result['passwordStatus'])


if __name__ == '__main__':
    main()
