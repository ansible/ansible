#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Kevin Breit (@kbreit) <kevin.breit@kevinbreit.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: meraki_admin
short_description: Manage administrators in the Meraki cloud
version_added: '2.6'
description:
- Allows for creation, management, and visibility into administrators within Meraki.
options:
    name:
        description:
        - Name of the dashboard administrator.
        - Required when creating a new administrator.
        type: str
    email:
        description:
        - Email address for the dashboard administrator.
        - Email cannot be updated.
        - Required when creating or editing an administrator.
        type: str
    org_access:
        description:
        - Privileges assigned to the administrator in the organization.
        aliases: [ orgAccess ]
        choices: [ full, none, read-only ]
        type: str
    tags:
        description:
        - Tags the administrator has privileges on.
        - When creating a new administrator, C(org_name), C(network), or C(tags) must be specified.
        - If C(none) is specified, C(network) or C(tags) must be specified.
        suboptions:
            tag:
                description:
                - Object tag which privileges should be assigned.
                type: str
            access:
                description:
                - The privilege of the dashboard administrator for the tag.
                type: str
    networks:
        description:
        - List of networks the administrator has privileges on.
        - When creating a new administrator, C(org_name), C(network), or C(tags) must be specified.
        suboptions:
            id:
                description:
                - Network ID for which administrator should have privileges assigned.
                type: str
            access:
                description:
                - The privilege of the dashboard administrator on the network.
                - Valid options are C(full), C(read-only), or C(none).
                type: str
    state:
        description:
        - Create or modify, or delete an organization
        - If C(state) is C(absent), name takes priority over email if both are specified.
        choices: [ absent, present, query ]
        required: true
        type: str
    org_name:
        description:
        - Name of organization.
        - Used when C(name) should refer to another object.
        - When creating a new administrator, C(org_name), C(network), or C(tags) must be specified.
        aliases: ['organization']
        type: str
    org_id:
        description:
        - ID of organization.
        type: str
author:
    - Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''
- name: Query information about all administrators associated to the organization
  meraki_admin:
    auth_key: abc12345
    org_name: YourOrg
    state: query
  delegate_to: localhost

- name: Query information about a single administrator by name
  meraki_admin:
    auth_key: abc12345
    org_id: 12345
    state: query
    name: Jane Doe

- name: Query information about a single administrator by email
  meraki_admin:
    auth_key: abc12345
    org_name: YourOrg
    state: query
    email: jane@doe.com

- name: Create new administrator with organization access
  meraki_admin:
    auth_key: abc12345
    org_name: YourOrg
    state: present
    name: Jane Doe
    org_access: read-only
    email: jane@doe.com

- name: Create new administrator with organization access
  meraki_admin:
    auth_key: abc12345
    org_name: YourOrg
    state: present
    name: Jane Doe
    org_access: read-only
    email: jane@doe.com

- name: Create a new administrator with organization access
  meraki_admin:
    auth_key: abc12345
    org_name: YourOrg
    state: present
    name: Jane Doe
    org_access: read-only
    email: jane@doe.com

- name: Revoke access to an organization for an administrator
  meraki_admin:
    auth_key: abc12345
    org_name: YourOrg
    state: absent
    email: jane@doe.com

- name: Create a new administrator with full access to two tags
  meraki_admin:
    auth_key: abc12345
    org_name: YourOrg
    state: present
    name: Jane Doe
    orgAccess: read-only
    email: jane@doe.com
    tags:
        - tag: tenant
          access: full
        - tag: corporate
          access: read-only

- name: Create a new administrator with full access to a network
  meraki_admin:
    auth_key: abc12345
    org_name: YourOrg
    state: present
    name: Jane Doe
    orgAccess: read-only
    email: jane@doe.com
    networks:
        - id: N_12345
          access: full
'''

RETURN = r'''
data:
    description: List of administrators.
    returned: success
    type: complex
    contains:
        email:
            description: Email address of administrator.
            returned: success
            type: str
            sample: your@email.com
        id:
            description: Unique identification number of administrator.
            returned: success
            type: str
            sample: 1234567890
        name:
            description: Given name of administrator.
            returned: success
            type: str
            sample: John Doe
        accountStatus:
            description: Status of account.
            returned: success
            type: str
            sample: ok
        twoFactorAuthEnabled:
            description: Enabled state of two-factor authentication for administrator.
            returned: success
            type: bool
            sample: false
        hasApiKey:
            description: Defines whether administrator has an API assigned to their account.
            returned: success
            type: bool
            sample: false
        lastActive:
            description: Date and time of time the administrator was active within Dashboard.
            returned: success
            type: str
            sample: 2019-01-28 14:58:56 -0800
        networks:
            description: List of networks administrator has access on.
            returned: success
            type: complex
            contains:
                id:
                     description: The network ID.
                     returned: when network permissions are set
                     type: str
                     sample: N_0123456789
                access:
                     description: Access level of administrator. Options are 'full', 'read-only', or 'none'.
                     returned: when network permissions are set
                     type: str
                     sample: read-only
        tags:
            description: Tags the administrator has access on.
            returned: success
            type: complex
            contains:
                tag:
                    description: Tag name.
                    returned: when tag permissions are set
                    type: str
                    sample: production
                access:
                    description: Access level of administrator. Options are 'full', 'read-only', or 'none'.
                    returned: when tag permissions are set
                    type: str
                    sample: full
        orgAccess:
            description: The privilege of the dashboard administrator on the organization. Options are 'full', 'read-only', or 'none'.
            returned: success
            type: str
            sample: full

'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native
from ansible.module_utils.network.meraki.meraki import MerakiModule, meraki_argument_spec


def get_admins(meraki, org_id):
    admins = meraki.request(
        meraki.construct_path(
            'query',
            function='admin',
            org_id=org_id
        ),
        method='GET'
    )
    if meraki.status == 200:
        return admins


def get_admin_id(meraki, data, name=None, email=None):
    admin_id = None
    for a in data:
        if meraki.params['name'] is not None:
            if meraki.params['name'] == a['name']:
                if admin_id is not None:
                    meraki.fail_json(msg='There are multiple administrators with the same name')
                else:
                    admin_id = a['id']
        elif meraki.params['email']:
            if meraki.params['email'] == a['email']:
                return a['id']
    if admin_id is None:
        meraki.fail_json(msg='No admin_id found')
    return admin_id


def get_admin(meraki, data, id):
    for a in data:
        if a['id'] == id:
            return a
    meraki.fail_json(msg='No admin found by specified name or email')


def find_admin(meraki, data, email):
    for a in data:
        if a['email'] == email:
            return a
    return None


def delete_admin(meraki, org_id, admin_id):
    path = meraki.construct_path('revoke', 'admin', org_id=org_id) + admin_id
    r = meraki.request(path,
                       method='DELETE'
                       )
    if meraki.status == 204:
        return r


def network_factory(meraki, networks, nets):
    networks = json.loads(networks)
    networks_new = []
    for n in networks:
        networks_new.append({'id': meraki.get_net_id(org_name=meraki.params['org_name'],
                                                     net_name=n['network'],
                                                     data=nets),
                             'access': n['access']
                             })
    return networks_new


def create_admin(meraki, org_id, name, email):
    payload = dict()
    payload['name'] = name
    payload['email'] = email

    is_admin_existing = find_admin(meraki, get_admins(meraki, org_id), email)

    if meraki.params['org_access'] is not None:
        payload['orgAccess'] = meraki.params['org_access']
    if meraki.params['tags'] is not None:
        payload['tags'] = json.loads(meraki.params['tags'])
    if meraki.params['networks'] is not None:
        nets = meraki.get_nets(org_id=org_id)
        networks = network_factory(meraki, meraki.params['networks'], nets)
        # meraki.fail_json(msg=str(type(networks)), data=networks)
        payload['networks'] = networks
    if is_admin_existing is None:  # Create new admin
        path = meraki.construct_path('create', function='admin', org_id=org_id)
        r = meraki.request(path,
                           method='POST',
                           payload=json.dumps(payload)
                           )
        if meraki.status == 201:
            meraki.result['changed'] = True
            return r
    elif is_admin_existing is not None:  # Update existing admin
        if not meraki.params['tags']:
            payload['tags'] = []
        if not meraki.params['networks']:
            payload['networks'] = []
        if meraki.is_update_required(is_admin_existing, payload) is True:
            # meraki.fail_json(msg='Update is required!!!', original=is_admin_existing, proposed=payload)
            path = meraki.construct_path('update', function='admin', org_id=org_id) + is_admin_existing['id']
            r = meraki.request(path,
                               method='PUT',
                               payload=json.dumps(payload)
                               )
            if meraki.status == 200:
                meraki.result['changed'] = True
                return r
        else:
            # meraki.fail_json(msg='No update is required!!!')
            return -1


def main():
    # define the available arguments/parameters that a user can pass to
    # the module
    argument_spec = meraki_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['present', 'query', 'absent'], required=True),
                         name=dict(type='str'),
                         email=dict(type='str'),
                         org_access=dict(type='str', aliases=['orgAccess'], choices=['full', 'read-only', 'none']),
                         tags=dict(type='json'),
                         networks=dict(type='json'),
                         org_name=dict(type='str', aliases=['organization']),
                         org_id=dict(type='str'),
                         )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False,
                           )
    meraki = MerakiModule(module, function='admin')

    meraki.function = 'admin'
    meraki.params['follow_redirects'] = 'all'

    query_urls = {'admin': '/organizations/{org_id}/admins',
                  }
    create_urls = {'admin': '/organizations/{org_id}/admins',
                   }
    update_urls = {'admin': '/organizations/{org_id}/admins/',
                   }
    revoke_urls = {'admin': '/organizations/{org_id}/admins/',
                   }

    meraki.url_catalog['query'] = query_urls
    meraki.url_catalog['create'] = create_urls
    meraki.url_catalog['update'] = update_urls
    meraki.url_catalog['revoke'] = revoke_urls

    try:
        meraki.params['auth_key'] = os.environ['MERAKI_KEY']
    except KeyError:
        pass

    if meraki.params['auth_key'] is None:
        module.fail_json(msg='Meraki Dashboard API key not set')

    payload = None

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    # execute checks for argument completeness
    if meraki.params['state'] == 'query':
        meraki.mututally_exclusive = ['name', 'email']
        if not meraki.params['org_name'] and not meraki.params['org_id']:
            meraki.fail_json(msg='org_name or org_id required')
    meraki.required_if = [(['state'], ['absent'], ['email']),
                          ]

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    org_id = meraki.params['org_id']
    if not meraki.params['org_id']:
        org_id = meraki.get_org_id(meraki.params['org_name'])
    if meraki.params['state'] == 'query':
        admins = get_admins(meraki, org_id)
        if not meraki.params['name'] and not meraki.params['email']:  # Return all admins for org
            meraki.result['data'] = admins
        if meraki.params['name'] is not None:  # Return a single admin for org
            admin_id = get_admin_id(meraki, admins, name=meraki.params['name'])
            meraki.result['data'] = admin_id
            admin = get_admin(meraki, admins, admin_id)
            meraki.result['data'] = admin
        elif meraki.params['email'] is not None:
            admin_id = get_admin_id(meraki, admins, email=meraki.params['email'])
            meraki.result['data'] = admin_id
            admin = get_admin(meraki, admins, admin_id)
            meraki.result['data'] = admin
    elif meraki.params['state'] == 'present':
        r = create_admin(meraki,
                         org_id,
                         meraki.params['name'],
                         meraki.params['email'],
                         )
        if r != -1:
            meraki.result['data'] = r
    elif meraki.params['state'] == 'absent':
        admin_id = get_admin_id(meraki,
                                get_admins(meraki, org_id),
                                email=meraki.params['email']
                                )
        r = delete_admin(meraki, org_id, admin_id)

        if r != -1:
            meraki.result['data'] = r
            meraki.result['changed'] = True

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
