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
module: pritunl_org
version_added: "2.4"
author: "Florian Dambrine (@Lowess)"
short_description: Manage Pritunl Organizations using the Pritunl API
description:
    - A module to manage Pritunl organizations using the Pritunl API.
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

    state:
        required: false
        default: list
        choices: [ list, present, absent ]
        description:
            - If C(list) is used, organizations will be retrieved from Pritunl,
              C(name) can be used to filter by name, by default all of them
              will be listed. If C(present), the organization C(name) will be
              added to Pritunl. If C(absent), the organization C(name) will be
              deleted from Pritunl.

    name:
        required: false
        default: null
        description:
            - Name of the Organization to manage in Pritunl.

requirements:
- requests
'''

EXAMPLES = '''
# List all existing organizations
- name: List all existing organizations
  pritunl_org:
    state: list

# Gather information about the organization named MyOrg
- name: Gather information about the organization named MyOrg
  pritunl_org:
    state: list
    name: MyOrg

# Make sure the organization named Org1 exists
- name: Make sure the organization named Org1 exists
  pritunl_org:
    state: present
    name: Org1

# Make sure the organization named Org1 does not exist
- name: Make sure the organization named Org1 does not exist
  pritunl_org:
    state: absent
    name: Org1
'''

RETURN = '''
response:
    description: JSON representation of Pritunl Organizations
    returned: success
    type: list of dictionaries
    sample: [
        {
            "auth_api": false,
            "auth_secret": null,
            "auth_token": null,
            "id": "58070daeec3a3b2e6e472c36",
            "name": "Org1",
            "user_count": 10
        },
        {
            "auth_api": false,
            "auth_secret": null,
            "auth_token": null,
            "id": "58070s38e63f3c2e6e4x2d5f",
            "name": "Org2",
            "user_count": 0
        },
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


def get_pritunl_organization(module):
    org_name = module.params.get('name')

    filters = None

    if org_name is not None:
        filters = {"name": org_name}

    orgs = _list_pritunl_organization(module, filters)

    result = {}
    result['changed'] = False
    result['response'] = orgs

    module.exit_json(**result)


def post_pritunl_organization(module):
    result = {}

    org_name = module.params.get('name')

    if org_name is None:
        module.fail_json(msg=("Please provide an organization name "
            "using name=<OrgName>"))

    # Grab existing orgs
    orgs = _list_pritunl_organization(module, {"name": org_name})

    # Check if the pritunl org already exists
    # If yes do nothing
    if len(orgs) > 0:
        result['changed'] = False
        result['response'] = orgs

    # Otherwise add the org to Pritunl
    else:
        response = pritunl_auth_request(module, 'POST', '/organization',
                                        headers={'Content-Type': 'application/json'},
                                        data=json.dumps({'name': org_name}))

        if response.getcode() != 200:
            module.fail_json(msg="Could not add organization %s to Pritunl" % (org_name))
        else:
            result['changed'] = True
            result['response'] = json.loads(response.read())

    module.exit_json(**result)


def delete_pritunl_organization(module):
    result = {}

    org_name = module.params.get('name')

    if org_name is None:
        module.fail_json(msg='Please provide an organization name using name=<OrgName>')

    # Grab existing orgs
    orgs = _list_pritunl_organization(module, {"name": org_name})

    # Check if the pritunl org exists, if not, do nothing
    if len(orgs) == 0:
        result['changed'] = False
        result['response'] = {}

    # Otherwise remove the org from Pritunl
    else:
        response = pritunl_auth_request(module, 'DELETE',
                                        "/organization/%s" % orgs[0]['id'])

        if response.getcode() != 200:
            module.fail_json(msg="Could not remove organization %s from Pritunl" % (org_name))
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
        state=dict(required=False, choices=['list', 'present', 'absent'], default=None),
        name=dict(required=False, type='str', default=None),
        validate_certs=dict(required=False, type='bool', default=True)
    )),

    module = AnsibleModule(
        argument_spec=argument_spec
    )

    state = module.params.get('state')

    if state == 'list' or state is None:
        get_pritunl_organization(module)
    elif state == 'present':
        post_pritunl_organization(module)
    elif state == 'absent':
        delete_pritunl_organization(module)


if __name__ == '__main__':
    main()
