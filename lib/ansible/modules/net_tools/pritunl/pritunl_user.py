#!/usr/bin/python

# (c) 2016, Florian Dambrine <android.florian@gmail.com>
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
module: pritunl_user
version_added: "2.4"
author: "Florian Dambrine (@Lowess)"
short_description: Manage Pritunl Users using the Pritunl API
description:
    - A module to manage Pritunl users using the Pritunl API.
options:
    pritunl_url:
        required: true
        description:
            - URL and port of the pritunl server on which the API is enabled

    pritunl_api_token:
        required: true
        description:
            - API Token of a Pritunl admin user (It needs to be enabled in
              Administrators > USERNAME > Enable Token Authentication).

    pritunl_api_secret:
        required: true
        description:
            - API Secret found in Administrators > USERNAME > API Secret.

    organization:
        required: true
        aliases: ['org']
        description:
            - The name of the organization the user is part of.

    state:
        required: false
        default: list
        choices: [ list, present, absent ]
        description:
            - If C(list) is used, users from the C(organization) will be
              retrieved from Pritunl, C(user_name) can be used to filter by
              name, by default all of them will be listed. If C(present), the
              user C(user_name) will be added to the Pritunl C(organization).
              If C(absent), the user C(user_name) will be deleted from the
              Pritunl C(organization).

    user_name:
        required: false
        default: null
        description:
            - Name of the user to create in Pritunl. The C(user_name) is used
              when the module is used with C(state=list).

    user_email:
        required: false
        default: null
        description:
            - Email address associated with the user C(user_name).

    user_type:
        required: false
        default: client
        choices: [ client, server]
        description:
            - Type of the user C(user_name).

    user_groups:
        required: false
        default: []
        description:
            - List of groups associated with the user C(user_name).

    user_disabled:
        required: false
        default: False
        description:
            - Enable/Disable the user C(user_name).

    user_gravatar:
        required: false
        default: True
        description:
            - Enable/Disable Gravatar usage for the user C(user_name).
'''

EXAMPLES = '''
# List all existing users part of the organization MyOrg
- name: List all existing users part of the organization MyOrg
  pritunl_user:
    state: list
    organization: MyOrg

# Search for the user named Florian part of the rganization MyOrg
- name: Search for the user named Florian part of the rganization MyOrg
  pritunl_user:
    state: list
    organization: MyOrg
    user_name: Florian

# Make sure the user named Foo with email address foo@bar.com is part of MyOrg
- name: Create the user Foo with email address foo@bar.com in MyOrg
  pritunl_user:
    state: present
    name: MyOrg
    user_name: Foo
    user_email: foo@bar.com

# Make sure the user named Foo with email address foo@bar.com is part of MyOrg
- name: Disable the user Foo but keep it in Pritunl
  pritunl_user:
    state: present
    name: MyOrg
    user_name: Foo
    user_email: foo@bar.com
    user_disabled: yes

# Make sure the user Foo is not part of MyOrg anymore
- name: Make sure the user Foo is not part of MyOrg anymore
  pritunl_user:
    state: absent
    name: MyOrg
    user_name: Foo
'''

RETURN = '''
response:
    description: JSON representation of Pritunl Users
    returned: success
    type: list
    sample:

        "users": [
            {
                "audit": false,
                "auth_type": "google",
                "bypass_secondary": false,
                "client_to_client": false,
                "disabled": false,
                "dns_mapping": null,
                "dns_servers": null,
                "dns_suffix": null,
                "email": "foo@bar.com",
                "gravatar": true,
                "groups": [
                    "foo", "bar"
                ],
                "id": "5d070dafe63q3b2e6s472c3b",
                "name": "foo@acme.com",
                "network_links": [],
                "organization": "58070daee6sf342e6e4s2c36",
                "organization_name": "Acme",
                "otp_auth": true,
                "otp_secret": "35H5EJA3XB2$4CWG",
                "pin": false,
                "port_forwarding": [],
                "servers": [],
            }
        ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import json
from ansible.module_utils.pritunl import pritunl_auth_request


def _list_pritunl_organization(module, filters=None):
    orgs = []

    response = pritunl_auth_request(module, 'GET', '/organization')

    if response.getcode() != 200:
        module.fail_json(msg='Could not retrive organizations from Pritunl')
    else:
        for org in json.loads(response.read()):
            # No filtering
            if filters is None:
                orgs.append(org)

            else:
                filtered_flag = False

                for filter_key, filter_val in filters.iteritems():
                    if filter_val != org[filter_key]:
                        filtered_flag = True

                if not filtered_flag:
                    orgs.append(org)

    return orgs


def _list_pritunl_user(module, organization_id, user_id=None, filters=None):
    users = []

    response = pritunl_auth_request(module, 'GET', "/user/%s" % organization_id)

    if response.getcode() != 200:
        module.fail_json(msg='Could not retrive users from Pritunl')
    else:
        for user in json.loads(response.read()):
            # No filtering
            if filters is None:
                users.append(user)

            else:
                filtered_flag = False

                for filter_key, filter_val in filters.iteritems():
                    if filter_val != user[filter_key]:
                        filtered_flag = True

                if not filtered_flag:
                    users.append(user)

    return users


def get_pritunl_user(module):
    user_name = module.params.get('user_name')
    user_type = module.params.get('user_type')

    org_name = module.params.get('organization')

    org_obj_list = _list_pritunl_organization(module, {"name": org_name})

    if len(org_obj_list) == 0:
        module.fail_json(msg="Can not list users from the organization '%s' which does not exist" % org_name)

    org_id = org_obj_list[0]['id']

    users = _list_pritunl_user(module, org_id, filters=({"type": user_type} if user_name is None else {"name": user_name, "type": user_type}))

    result = {}
    result['changed'] = False
    result['users'] = users

    module.exit_json(**result)


def post_pritunl_user(module):
    result = {}

    org_name = module.params.get('organization')
    user_name = module.params.get('user_name')

    if user_name is None:
        module.fail_json(msg='Please provide a user name using user_name=<username>')

    user_params = {
        'name': user_name,
        'email': module.params.get('user_email'),
        'groups': module.params.get('user_groups'),
        'disabled': module.params.get('user_disabled'),
        'gravatar': module.params.get('user_gravatar'),
        'type': module.params.get('user_type'),
    }

    org_obj_list = _list_pritunl_organization(module, {"name": org_name})

    if len(org_obj_list) == 0:
        module.fail_json(msg="Can not add user to organization '%s' which does not exist" % org_name)

    org_id = org_obj_list[0]['id']

    # Grab existing users from this org
    users = _list_pritunl_user(module, org_id, filters={"name": user_name})

    # Check if the pritunl user already exists
    # If yes do nothing
    if len(users) > 0:
        # Compare remote user params with local user_params and trigger update if needed
        user_params_changed = False
        for key in user_params.keys():
            # When a param is not specified grab the existing one to prevent from changing it with the PUT request
            if user_params[key] is None:
                user_params[key] = users[0][key]

            # groups is a list comparison
            if key == 'groups':
                if set(users[0][key]) != set(user_params[key]):
                    user_params_changed = True

            # otherwise it is either a boolean or a string
            else:
                if users[0][key] != user_params[key]:
                    user_params_changed = True

        # Trigger a PUT on the API to update the current user if settings have changed
        if user_params_changed:
            response = pritunl_auth_request(module, 'PUT',
                                            "/user/%s/%s" % (org_id, users[0]['id']),
                                            headers={'Content-Type': 'application/json'},
                                            data=json.dumps(user_params))

            if response.getcode() != 200:
                module.fail_json(msg="Could not update Pritunl user %s from %s organization" % (user_name, org_name))
            else:
                result['changed'] = True
                result['response'] = json.loads(response.read())
        else:
            result['changed'] = False
            result['response'] = users
    else:
        response = pritunl_auth_request(module, 'POST', "/user/%s" % org_id,
                                        headers={'Content-Type': 'application/json'},
                                        data=json.dumps(user_params))

        if response.getcode() != 200:
            module.fail_json(msg="Could not add Pritunl user %s to %s organization" % (user_params['name'], org_name))
        else:
            result['changed'] = True
            result['response'] = json.loads(response.read())

    module.exit_json(**result)


def delete_pritunl_user(module):
    result = {}

    org_name = module.params.get('organization')
    user_name = module.params.get('user_name')

    org_obj_list = _list_pritunl_organization(module, {"name": org_name})

    if len(org_obj_list) == 0:
        module.fail_json(msg="Can not remove user from the organization '%s' which does not exist" % org_name)

    org_id = org_obj_list[0]['id']

    # Grab existing users from this org
    users = _list_pritunl_user(module, org_id, filters={"name": user_name})

    # Check if the pritunl user exists, if not, do nothing
    if len(users) == 0:
        result['changed'] = False
        result['response'] = {}

    # Otherwise remove the org from Pritunl
    else:
        response = pritunl_auth_request(module, 'DELETE',
                                        "/user/%s/%s" % (org_id, users[0]['id']))

        if response.getcode() != 200:
            module.fail_json(msg="Could not remove user %s from organization %s from Pritunl" % (users[0]['name'], org_name))
        else:
            result['changed'] = True
            result['response'] = json.loads(response.read())

    module.exit_json(**result)


def main():
    argument_spec = {}

    argument_spec.update(dict(
        pritunl_url=dict(required=True, type='str', defaults='https://localhost:443'),
        pritunl_api_token=dict(required=True, type='str'),
        pritunl_api_secret=dict(required=True, type='str'),
        organization=dict(required=True, type='str', default=None, aliases=['org']),
        state=dict(required=False, choices=['list', 'present', 'absent'], default=None),
        user_name=dict(required=False, type='str', default=None),
        user_type=dict(required=False, choices=['client', 'server'], default='client'),
        user_email=dict(required=False, type='str', default=None),
        user_groups=dict(required=False, type='list', default=None),
        user_disabled=dict(required=False, type='bool', default=None),
        user_gravatar=dict(required=False, type='bool', default=None),
        validate_certs=dict(required=False, type='bool', default=True)
    )),

    module = AnsibleModule(
        argument_spec=argument_spec
    )

    state = module.params.get('state')

    if state == 'list' or state is None:
        get_pritunl_user(module)
    elif state == 'present':
        post_pritunl_user(module)
    elif state == 'absent':
        delete_pritunl_user(module)


if __name__ == '__main__':
    main()
