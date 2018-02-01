#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2018, Adam Goossens <adam.goossens@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: keycloak_group

short_description: Allows administration of Keycloak groups via Keycloak API

description:
    - This module allows you to add, remove or modify Keycloak groups via the Keycloak REST API.
      It requires access to the REST API via OpenID Connect; the user connecting and the client being
      used must have the requisite access rights. In a default Keycloak installation, admin-cli
      and an admin user would work, as would a separate client definition with the scope tailored
      to your needs and a user having the expected roles.

    - The names of module options are snake_cased versions of the camelCase ones found in the
      Keycloak API and its documentation at U(http://www.keycloak.org/docs-api/3.3/rest-api/).

    - The Keycloak API returns and expects group attribute values to be provided as lists. This
      module will transparently convert any non-list attribute values into a list before providing it to the API.
      When retrieving a group, expect the attribute values to be returned in a list.

    - When updating a group, where possible provide the group ID to the module. This removes a lookup
      to the API to translate the name into the group ID.

options:
    state:
        description:
            - State of the group.
            - On C(present), the group will be created if it does not yet exist.
            - On C(absent), the group will be removed if it exists.
            - On C(updated), the group will be updated or created based on the parameters you provide.
        required: true
        default: 'present'

    name:
        description:
            - Name of the group.
            - This parameter is required only when creating or updating the group.
        required: false
        type: 'str'

    realm:
        description:
            - They Keycloak realm under which this group resides.
        required: false
        type: 'str'
        default: 'master'

    id:
        description:
            - The unique identifier for this group. 
            - This parameter is not required for updating or deleting a group but
              providing it will reduce the number of API calls required.
        required: false
        type: 'str'

    attributes:
        description:
            - A list of key/value pairs to set as custom attributes for the group.
            - Values may be single values (e.g. a string) or a list of strings.
        required: false
        type: 'dict'

extends_documentation_fragment:
    - keycloak

author:
    - Adam Goossens (@adamgoossens)
'''

EXAMPLES = '''
- name: Create a Keycloak group
  local_action:
    module: keycloak_group
    name: my-new-kc-group
    realm: MyCustomRealm
    state: present
    auth_client_id: admin-cli
    auth_keycloak_url: https://auth.example.com/auth
    auth_realm: master
    auth_username: USERNAME
    auth_password: PASSWORD
  register: kc_group_id

- name: Delete a keycloak group
  local_action:
    module: keycloak_group
    id: '9d59aa76-2755-48c6-b1af-beb70a82c3cd'
    state: absent
    realm: MyCustomRealm
    auth_client_id: admin-cli
    auth_keycloak_url: https://auth.example.com/auth
    auth_realm: master
    auth_username: USERNAME
    auth_password: PASSWORD

- name: Delete a Keycloak group based on name
  local_action:
    module: keycloak_group
    name: my-group-for-deletion
    auth_client_id: admin-cli
    auth_keycloak_url: https://auth.example.com/auth
    auth_realm: master
    auth_username: USERNAME
    auth_password: PASSWORD

- name: Update the name of a Keycloak group
  local_action:
    module: keycloak_group
    id: '9d59aa76-2755-48c6-b1af-beb70a82c3cd'
    name: an-updated-kc-group-name
    state: present
    auth_client_id: admin-cli
    auth_keycloak_url: https://auth.example.com/auth
    auth_realm: master
    auth_username: USERNAME
    auth_password: PASSWORD

- name: Create a keycloak group with some custom attributes
  local_action:
    module: keycloak_group
    auth_client_id: admin-cli
    auth_keycloak_url: https://auth.example.com/auth
    auth_realm: master
    auth_username: USERNAME
    auth_password: PASSWORD
    name: my-new_group
    attributes:
        attrib1: value1
        attrib2: value2
        attrib3:
            - with
            - numerous
            - individual
            - list
            - items
'''

RETURN = '''
msg:
  description: Message as to what action was taken
  returned: always
  type: string
  sample: "Group my-new-sso-group has been created with ID '9d59aa76-2755-48c6-b1af-beb70a82c3cd'"

proposed:
  description: Group representation of proposed changes to group (sample is truncated)
  returned: always
  type: dict
  sample: {
    "attributes": {
        "day_of_week": [
            "friday"
        ],
        "expiry_date": [
            "2018-01-01"
        ]
    },
    "name": "new-name"
}

existing:
  description: Group representation of the existing group, before modification or deletion. Sample is truncated.
  returned: always
  type: dict
  sample: {
    "name": "group-name",
    "id": "2ac24fe7-cec6-4fc4-8c32-a17f79e3365e",
    "path": "/group-name",
    "realmRoles": []
  }

end_state:
  description: Group representation of the group after module execution (sample is truncated).
  returned: always
  type: dict
  sample: {
    "name": "my-new-group",
    "attributes": {
       "weather": [ "sunny" ],
       "cnames": [ "foo.bar.com", "bar.bar.com", "baz.bar.com" ]
    }
    "id": "1aedffb3-7501-4863-8dfc-f42951649aa9"
  }
'''

from ansible.module_utils.keycloak import KeycloakAPI, camel, keycloak_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    """
    Module execution

    :return:
    """
    argument_spec = keycloak_argument_spec()
    meta_args = dict(
        state=dict(default='present', choices=['present','absent']),
        realm=dict(default='master'),

        id=dict(type='str'),
        name=dict(type='str'),
        attributes=dict(type='dict')
    )

    argument_spec.update(meta_args)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_one_of=([['id', 'name']]))

    result = dict(changed=False, msg='', diff={}, group_id='')

    # Obtain access token, initialize API
    kc = KeycloakAPI(module)

    realm = module.params.get('realm')
    state = module.params.get('state')
    gid = module.params.get('id')
    name = module.params.get('name')
    attributes = module.params.get('attributes')

    before_group = None         # current state of the group, for merging.

    # does the group already exist?
    if gid is None:
        before_group = kc.get_group_by_name(name, realm=realm)
    else:
        before_group = kc.get_group_by_groupid(gid, realm=realm)

    before_group = {} if before_group is None else before_group

    # attributes in Keycloak have their values returned as lists
    # via the API. attributes is a dict, so we'll transparently convert
    # the values to lists.
    if attributes is not None:
        for key,val in module.params['attributes'].iteritems():
            module.params['attributes'][key] = [val] if type(val) != list else val

    group_params = [x for x in module.params
                    if x not in list(keycloak_argument_spec().keys()) + ['state', 'realm'] and
                    module.params.get(x) is not None]

    # build a changeset
    changeset = {}
    for param in group_params:
        new_param_value = module.params.get(param)
        old_value = before_group[param] if param in before_group else None
        if new_param_value != old_value:
            changeset[camel(param)] = new_param_value

    # prepare the new group
    updated_group = before_group.copy()
    updated_group.update(changeset)

    result['proposed'] = changeset if state != 'absent' else {}
    result['existing'] = before_group

    # if before_group is none, the group doesn't exist.
    if before_group == {}:
        if state == 'absent':
            # nothing to do.
            if module._diff:
                result['diff'] = dict(before='', after='')
            result['msg'] = 'Group does not exist; doing nothing.'
            result['end_state'] = dict()
            module.exit_json(**result)

        # for 'present', create a new group.
        result['changed'] = True
        if name is None:
            module.fail_json(msg='name must be specified when creating a new group')

        if module._diff:
            result['diff'] = dict(before='', after=after_group)

        if module.check_mode:
            module.exit_json(**result)

        # do it for real!
        kc.create_group(updated_group, realm=realm)
        after_group = kc.get_group_by_name(name, realm)

        result['end_state'] = after_group
        result['msg'] = 'Group {} has been created with ID {}'.format(after_group['name'], after_group['id'])

    else:
        if state == 'present':
            # no changes
            if updated_group == before_group:
                result['changed'] = False
                result['end_state'] = updated_group
                result['msg'] = "No changes required to group {}.".format(before_group['name'])
                module.exit_json(**result)

            # update the existing group
            result['changed'] = True

            if module._diff:
                result['diff'] = dict(before=before_group, after=updated_group)

            if module.check_mode:
                module.exit_json(**result)

            # do the update
            kc.update_group(updated_group, realm=realm)

            after_group = kc.get_group_by_groupid(updated_group['id'], realm=realm)

            result['end_state'] = after_group
            result['msg'] = "Group {} has been updated".format(after_group['id'])

            module.exit_json(**result)

        elif state == 'absent':
            result['proposed'] = dict()
            result['end_state'] = dict()

            if module._diff:
                result['diff'] = dict(before=before_group, after='')

            if module.check_mode:
                module.exit_json(**result)

            # delete for real
            gid = before_group['id']
            kc.delete_group(groupid=gid, realm=realm)

            result['changed'] = True
            result['msg'] = "Group {} has been deleted".format(before_group['name'])

            module.exit_json(**result)

        else:
            module.fail_json(msg='Unknown state {}'.format(state))

    module.exit_json(**result)

if __name__ == '__main__':
    main()
