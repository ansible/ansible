#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
---
module: iam
short_description: Manage IAM users, groups, roles and keys
description:
     - Allows for the management of IAM users, user API keys, groups, roles.
version_added: "2.0"
options:
  iam_type:
    description:
      - Type of IAM resource
    choices: ["user", "group", "role"]
  name:
    description:
      - Name of IAM resource to create or identify
    required: true
  new_name:
    description:
      - When state is update, will replace name with new_name on IAM resource
  new_path:
    description:
      - When state is update, will replace the path with new_path on the IAM resource
  state:
    description:
      - Whether to create, delete or update the IAM resource. Note, roles cannot be updated.
    required: true
    choices: [ "present", "absent", "update" ]
  path:
    description:
      - When creating or updating, specify the desired path of the resource. If state is present,
        it will replace the current path to match what is passed in when they do not match.
    default: "/"
  trust_policy:
    description:
      - The inline (JSON or YAML) trust policy document that grants an entity permission to assume the role. Mutually exclusive with C(trust_policy_filepath).
    version_added: "2.2"
  trust_policy_filepath:
    description:
      - The path to the trust policy document that grants an entity permission to assume the role. Mutually exclusive with C(trust_policy).
    version_added: "2.2"
  access_key_state:
    description:
      - When type is user, it creates, removes, deactivates or activates a user's access key(s). Note that actions apply only to keys specified.
    choices: [ "create", "remove", "active", "inactive"]
  key_count:
    description:
      - When access_key_state is create it will ensure this quantity of keys are present. Defaults to 1.
    default: '1'
  access_key_ids:
    description:
      - A list of the keys that you want impacted by the access_key_state parameter.
  groups:
    description:
      - A list of groups the user should belong to. When update, will gracefully remove groups not listed.
  password:
    description:
      - When type is user and state is present, define the users login password. Also works with update. Note that always returns changed.
  update_password:
    default: always
    choices: ['always', 'on_create']
    description:
     - C(always) will update passwords if they differ.  C(on_create) will only set the password for newly created users.
notes:
  - 'Currently boto does not support the removal of Managed Policies, the module will error out if your
    user/group/role has managed policies when you try to do state=absent. They will need to be removed manually.'
author:
    - "Jonathan I. Davila (@defionscode)"
    - "Paul Seiffert (@seiffert)"
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
# Basic user creation example
tasks:
- name: Create two new IAM users with API keys
  iam:
    iam_type: user
    name: "{{ item }}"
    state: present
    password: "{{ temp_pass }}"
    access_key_state: create
  with_items:
    - jcleese
    - mpython

# Advanced example, create two new groups and add the pre-existing user
# jdavila to both groups.
task:
- name: Create Two Groups, Mario and Luigi
  iam:
    iam_type: group
    name: "{{ item }}"
    state: present
  with_items:
     - Mario
     - Luigi
  register: new_groups

- name:
  iam:
    iam_type: user
    name: jdavila
    state: update
    groups: "{{ item.created_group.group_name }}"
  with_items: "{{ new_groups.results }}"

# Example of role with custom trust policy for Lambda service
- name: Create IAM role with custom trust relationship
  iam:
    iam_type: role
    name: AAALambdaTestRole
    state: present
    trust_policy:
      Version: '2012-10-17'
      Statement:
      - Action: sts:AssumeRole
        Effect: Allow
        Principal:
          Service: lambda.amazonaws.com

'''
RETURN = '''
role_result:
    description: the IAM.role dict returned by Boto
    type: string
    returned: if iam_type=role and state=present
    sample: {
                "arn": "arn:aws:iam::A1B2C3D4E5F6:role/my-new-role",
                "assume_role_policy_document": "...truncated...",
                "create_date": "2017-09-02T14:32:23Z",
                "path": "/",
                "role_id": "AROAA1B2C3D4E5F6G7H8I",
                "role_name": "my-new-role"
            }
roles:
    description: a list containing the name of the currently defined roles
    type: list
    returned: if iam_type=role and state=present
    sample: [
        "my-new-role",
        "my-existing-role-1",
        "my-existing-role-2",
        "my-existing-role-3",
        "my-existing-role-...",
    ]
'''

import json
import traceback

try:
    import boto.exception
    import boto.iam
    import boto.iam.connection
except ImportError:
    pass  # Taken care of by ec2.HAS_BOTO

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (HAS_BOTO, boto_exception, connect_to_aws, ec2_argument_spec,
                                      get_aws_connection_info)


def _paginate(func, attr):
    '''
    paginates the results from func by continuously passing in
    the returned marker if the results were truncated. this returns
    an iterator over the items in the returned response. `attr` is
    the name of the attribute to iterate over in the response.
    '''
    finished, marker = False, None
    while not finished:
        res = func(marker=marker)
        for item in getattr(res, attr):
            yield item

        finished = res.is_truncated == 'false'
        if not finished:
            marker = res.marker


def list_all_groups(iam):
    return [item['group_name'] for item in _paginate(iam.get_all_groups, 'groups')]


def list_all_users(iam):
    return [item['user_name'] for item in _paginate(iam.get_all_users, 'users')]


def list_all_roles(iam):
    return [item['role_name'] for item in _paginate(iam.list_roles, 'roles')]


def list_all_instance_profiles(iam):
    return [item['instance_profile_name'] for item in _paginate(iam.list_instance_profiles, 'instance_profiles')]


def create_user(module, iam, name, pwd, path, key_state, key_count):
    key_qty = 0
    keys = []
    try:
        user_meta = iam.create_user(
            name, path).create_user_response.create_user_result.user
        changed = True
        if pwd is not None:
            pwd = iam.create_login_profile(name, pwd)
        if key_state in ['create']:
            if key_count:
                while key_count > key_qty:
                    keys.append(iam.create_access_key(
                        user_name=name).create_access_key_response.
                        create_access_key_result.
                        access_key)
                    key_qty += 1
        else:
            keys = None
    except boto.exception.BotoServerError as err:
        module.fail_json(changed=False, msg=str(err))
    else:
        user_info = dict(created_user=user_meta, password=pwd, access_keys=keys)
        return (user_info, changed)


def delete_dependencies_first(module, iam, name):
    changed = False
    # try to delete any keys
    try:
        current_keys = [ck['access_key_id'] for ck in
                        iam.get_all_access_keys(name).list_access_keys_result.access_key_metadata]
        for key in current_keys:
            iam.delete_access_key(key, name)
        changed = True
    except boto.exception.BotoServerError as err:
        module.fail_json(changed=changed, msg="Failed to delete keys: %s" % err, exception=traceback.format_exc())

    # try to delete login profiles
    try:
        login_profile = iam.get_login_profiles(name).get_login_profile_response
        iam.delete_login_profile(name)
        changed = True
    except boto.exception.BotoServerError as err:
        error_msg = boto_exception(err)
        if 'Cannot find Login Profile' not in error_msg:
            module.fail_json(changed=changed, msg="Failed to delete login profile: %s" % err, exception=traceback.format_exc())

    # try to detach policies
    try:
        for policy in iam.get_all_user_policies(name).list_user_policies_result.policy_names:
            iam.delete_user_policy(name, policy)
        changed = True
    except boto.exception.BotoServerError as err:
        error_msg = boto_exception(err)
        if 'must detach all policies first' in error_msg:
            module.fail_json(changed=changed, msg="All inline polices have been removed. Though it appears"
                                                  "that %s has Managed Polices. This is not "
                                                  "currently supported by boto. Please detach the polices "
                                                  "through the console and try again." % name)
        module.fail_json(changed=changed, msg="Failed to delete policies: %s" % err, exception=traceback.format_exc())

    # try to deactivate associated MFA devices
    try:
        mfa_devices = iam.get_all_mfa_devices(name).get('list_mfa_devices_response', {}).get('list_mfa_devices_result', {}).get('mfa_devices', [])
        for device in mfa_devices:
            iam.deactivate_mfa_device(name, device['serial_number'])
        changed = True
    except boto.exception.BotoServerError as err:
        module.fail_json(changed=changed, msg="Failed to deactivate associated MFA devices: %s" % err, exception=traceback.format_exc())

    return changed


def delete_user(module, iam, name):
    changed = delete_dependencies_first(module, iam, name)
    try:
        iam.delete_user(name)
    except boto.exception.BotoServerError as ex:
        module.fail_json(changed=changed, msg="Failed to delete user %s: %s" % (name, ex), exception=traceback.format_exc())
    else:
        changed = True
    return name, changed


def update_user(module, iam, name, new_name, new_path, key_state, key_count, keys, pwd, updated):
    changed = False
    name_change = False
    if updated and new_name:
        name = new_name
    try:
        current_keys = [ck['access_key_id'] for ck in
                        iam.get_all_access_keys(name).list_access_keys_result.access_key_metadata]
        status = [ck['status'] for ck in
                  iam.get_all_access_keys(name).list_access_keys_result.access_key_metadata]
        key_qty = len(current_keys)
    except boto.exception.BotoServerError as err:
        error_msg = boto_exception(err)
        if 'cannot be found' in error_msg and updated:
            current_keys = [ck['access_key_id'] for ck in
                            iam.get_all_access_keys(new_name).list_access_keys_result.access_key_metadata]
            status = [ck['status'] for ck in
                      iam.get_all_access_keys(new_name).list_access_keys_result.access_key_metadata]
            name = new_name
        else:
            module.fail_json(changed=False, msg=str(err))

    updated_key_list = {}

    if new_name or new_path:
        c_path = iam.get_user(name).get_user_result.user['path']
        if (name != new_name) or (c_path != new_path):
            changed = True
            try:
                if not updated:
                    user = iam.update_user(
                        name, new_user_name=new_name, new_path=new_path).update_user_response.response_metadata
                else:
                    user = iam.update_user(
                        name, new_path=new_path).update_user_response.response_metadata
                user['updates'] = dict(
                    old_username=name, new_username=new_name, old_path=c_path, new_path=new_path)
            except boto.exception.BotoServerError as err:
                error_msg = boto_exception(err)
                module.fail_json(changed=False, msg=str(err))
            else:
                if not updated:
                    name_change = True

    if pwd:
        try:
            iam.update_login_profile(name, pwd)
            changed = True
        except boto.exception.BotoServerError:
            try:
                iam.create_login_profile(name, pwd)
                changed = True
            except boto.exception.BotoServerError as err:
                error_msg = boto_exception(str(err))
                if 'Password does not conform to the account password policy' in error_msg:
                    module.fail_json(changed=False, msg="Password doesn't conform to policy")
                else:
                    module.fail_json(msg=error_msg)

    try:
        current_keys = [ck['access_key_id'] for ck in
                        iam.get_all_access_keys(name).list_access_keys_result.access_key_metadata]
        status = [ck['status'] for ck in
                  iam.get_all_access_keys(name).list_access_keys_result.access_key_metadata]
        key_qty = len(current_keys)
    except boto.exception.BotoServerError as err:
        error_msg = boto_exception(err)
        if 'cannot be found' in error_msg and updated:
            current_keys = [ck['access_key_id'] for ck in
                            iam.get_all_access_keys(new_name).list_access_keys_result.access_key_metadata]
            status = [ck['status'] for ck in
                      iam.get_all_access_keys(new_name).list_access_keys_result.access_key_metadata]
            name = new_name
        else:
            module.fail_json(changed=False, msg=str(err))

    new_keys = []
    if key_state == 'create':
        try:
            while key_count > key_qty:
                new_keys.append(iam.create_access_key(
                    user_name=name).create_access_key_response.create_access_key_result.access_key)
                key_qty += 1
                changed = True

        except boto.exception.BotoServerError as err:
            module.fail_json(changed=False, msg=str(err))

    if keys and key_state:
        for access_key in keys:
            if key_state in ('active', 'inactive'):
                if access_key in current_keys:
                    for current_key, current_key_state in zip(current_keys, status):
                        if key_state != current_key_state.lower():
                            try:
                                iam.update_access_key(access_key, key_state.capitalize(), user_name=name)
                                changed = True
                            except boto.exception.BotoServerError as err:
                                module.fail_json(changed=False, msg=str(err))
                else:
                    module.fail_json(msg="Supplied keys not found for %s. "
                                         "Current keys: %s. "
                                         "Supplied key(s): %s" %
                                         (name, current_keys, keys)
                                     )

            if key_state == 'remove':
                if access_key in current_keys:
                    try:
                        iam.delete_access_key(access_key, user_name=name)
                    except boto.exception.BotoServerError as err:
                        module.fail_json(changed=False, msg=str(err))
                    else:
                        changed = True

    try:
        final_keys, final_key_status = \
            [ck['access_key_id'] for ck in
             iam.get_all_access_keys(name).
             list_access_keys_result.
             access_key_metadata],\
            [ck['status'] for ck in
                iam.get_all_access_keys(name).
                list_access_keys_result.
                access_key_metadata]
    except boto.exception.BotoServerError as err:
        module.fail_json(changed=changed, msg=str(err))

    for fk, fks in zip(final_keys, final_key_status):
        updated_key_list.update({fk: fks})

    return name_change, updated_key_list, changed, new_keys


def set_users_groups(module, iam, name, groups, updated=None,
                     new_name=None):
    """ Sets groups for a user, will purge groups not explicitly passed, while
        retaining pre-existing groups that also are in the new list.
    """
    changed = False

    if updated:
        name = new_name

    try:
        orig_users_groups = [og['group_name'] for og in iam.get_groups_for_user(
            name).list_groups_for_user_result.groups]
        remove_groups = [
            rg for rg in frozenset(orig_users_groups).difference(groups)]
        new_groups = [
            ng for ng in frozenset(groups).difference(orig_users_groups)]
    except boto.exception.BotoServerError as err:
        module.fail_json(changed=changed, msg=str(err))
    else:
        if len(orig_users_groups) > 0:
            for new in new_groups:
                iam.add_user_to_group(new, name)
            for rm in remove_groups:
                iam.remove_user_from_group(rm, name)
        else:
            for group in groups:
                try:
                    iam.add_user_to_group(group, name)
                except boto.exception.BotoServerError as err:
                    error_msg = boto_exception(err)
                    if ('The group with name %s cannot be found.' % group) in error_msg:
                        module.fail_json(changed=False, msg="Group %s doesn't exist" % group)

    if len(remove_groups) > 0 or len(new_groups) > 0:
        changed = True

    return (groups, changed)


def create_group(module=None, iam=None, name=None, path=None):
    changed = False
    try:
        iam.create_group(
            name, path).create_group_response.create_group_result.group
    except boto.exception.BotoServerError as err:
        module.fail_json(changed=changed, msg=str(err))
    else:
        changed = True
    return name, changed


def delete_group(module=None, iam=None, name=None):
    changed = False
    try:
        iam.delete_group(name)
    except boto.exception.BotoServerError as err:
        error_msg = boto_exception(err)
        if ('must delete policies first') in error_msg:
            for policy in iam.get_all_group_policies(name).list_group_policies_result.policy_names:
                iam.delete_group_policy(name, policy)
            try:
                iam.delete_group(name)
            except boto.exception.BotoServerError as err:
                error_msg = boto_exception(err)
                if ('must delete policies first') in error_msg:
                    module.fail_json(changed=changed, msg="All inline polices have been removed. Though it appears"
                                                          "that %s has Managed Polices. This is not "
                                                          "currently supported by boto. Please detach the polices "
                                                          "through the console and try again." % name)
                else:
                    module.fail_json(changed=changed, msg=str(error_msg))
            else:
                changed = True
        else:
            module.fail_json(changed=changed, msg=str(error_msg))
    else:
        changed = True
    return changed, name


def update_group(module=None, iam=None, name=None, new_name=None, new_path=None):
    changed = False
    try:
        current_group_path = iam.get_group(
            name).get_group_response.get_group_result.group['path']
        if new_path:
            if current_group_path != new_path:
                iam.update_group(name, new_path=new_path)
                changed = True
        if new_name:
            if name != new_name:
                iam.update_group(name, new_group_name=new_name, new_path=new_path)
                changed = True
                name = new_name
    except boto.exception.BotoServerError as err:
        module.fail_json(changed=changed, msg=str(err))

    return changed, name, new_path, current_group_path


def create_role(module, iam, name, path, role_list, prof_list, trust_policy_doc):
    changed = False
    iam_role_result = None
    instance_profile_result = None
    try:
        if name not in role_list:
            changed = True
            iam_role_result = iam.create_role(name,
                                              assume_role_policy_document=trust_policy_doc,
                                              path=path).create_role_response.create_role_result.role

            if name not in prof_list:
                instance_profile_result = iam.create_instance_profile(name, path=path) \
                    .create_instance_profile_response.create_instance_profile_result.instance_profile
                iam.add_role_to_instance_profile(name, name)
        else:
            instance_profile_result = iam.get_instance_profile(name).get_instance_profile_response.get_instance_profile_result.instance_profile
    except boto.exception.BotoServerError as err:
        module.fail_json(changed=changed, msg=str(err))
    else:
        updated_role_list = list_all_roles(iam)
        iam_role_result = iam.get_role(name).get_role_response.get_role_result.role
    return changed, updated_role_list, iam_role_result, instance_profile_result


def delete_role(module, iam, name, role_list, prof_list):
    changed = False
    iam_role_result = None
    instance_profile_result = None
    try:
        if name in role_list:
            cur_ins_prof = [rp['instance_profile_name'] for rp in
                            iam.list_instance_profiles_for_role(name).
                            list_instance_profiles_for_role_result.
                            instance_profiles]
            for profile in cur_ins_prof:
                iam.remove_role_from_instance_profile(profile, name)
            try:
                iam.delete_role(name)
            except boto.exception.BotoServerError as err:
                error_msg = boto_exception(err)
                if ('must detach all policies first') in error_msg:
                    for policy in iam.list_role_policies(name).list_role_policies_result.policy_names:
                        iam.delete_role_policy(name, policy)
                try:
                    iam_role_result = iam.delete_role(name)
                except boto.exception.BotoServerError as err:
                    error_msg = boto_exception(err)
                    if ('must detach all policies first') in error_msg:
                        module.fail_json(changed=changed, msg="All inline polices have been removed. Though it appears"
                                                              "that %s has Managed Polices. This is not "
                                                              "currently supported by boto. Please detach the polices "
                                                              "through the console and try again." % name)
                    else:
                        module.fail_json(changed=changed, msg=str(err))
                else:
                    changed = True

            else:
                changed = True

        for prof in prof_list:
            if name == prof:
                instance_profile_result = iam.delete_instance_profile(name)
    except boto.exception.BotoServerError as err:
        module.fail_json(changed=changed, msg=str(err))
    else:
        updated_role_list = list_all_roles(iam)
    return changed, updated_role_list, iam_role_result, instance_profile_result


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        iam_type=dict(
            default=None, required=True, choices=['user', 'group', 'role']),
        groups=dict(type='list', default=None, required=False),
        state=dict(
            default=None, required=True, choices=['present', 'absent', 'update']),
        password=dict(default=None, required=False, no_log=True),
        update_password=dict(default='always', required=False, choices=['always', 'on_create']),
        access_key_state=dict(default=None, required=False, choices=[
            'active', 'inactive', 'create', 'remove',
            'Active', 'Inactive', 'Create', 'Remove']),
        access_key_ids=dict(type='list', default=None, required=False),
        key_count=dict(type='int', default=1, required=False),
        name=dict(default=None, required=False),
        trust_policy_filepath=dict(default=None, required=False),
        trust_policy=dict(type='dict', default=None, required=False),
        new_name=dict(default=None, required=False),
        path=dict(default='/', required=False),
        new_path=dict(default=None, required=False)
    )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[['trust_policy', 'trust_policy_filepath']],
    )

    if not HAS_BOTO:
        module.fail_json(msg='This module requires boto, please install it')

    state = module.params.get('state').lower()
    iam_type = module.params.get('iam_type').lower()
    groups = module.params.get('groups')
    name = module.params.get('name')
    new_name = module.params.get('new_name')
    password = module.params.get('password')
    update_pw = module.params.get('update_password')
    path = module.params.get('path')
    new_path = module.params.get('new_path')
    key_count = module.params.get('key_count')
    key_state = module.params.get('access_key_state')
    trust_policy = module.params.get('trust_policy')
    trust_policy_filepath = module.params.get('trust_policy_filepath')
    key_ids = module.params.get('access_key_ids')

    if key_state:
        key_state = key_state.lower()
        if any([n in key_state for n in ['active', 'inactive']]) and not key_ids:
            module.fail_json(changed=False, msg="At least one access key has to be defined in order"
                                                " to use 'active' or 'inactive'")

    if iam_type == 'user' and module.params.get('password') is not None:
        pwd = module.params.get('password')
    elif iam_type != 'user' and module.params.get('password') is not None:
        module.fail_json(msg="a password is being specified when the iam_type "
                             "is not user. Check parameters")
    else:
        pwd = None

    if iam_type != 'user' and (module.params.get('access_key_state') is not None or
                               module.params.get('access_key_id') is not None):
        module.fail_json(msg="the IAM type must be user, when IAM access keys "
                             "are being modified. Check parameters")

    if iam_type == 'role' and state == 'update':
        module.fail_json(changed=False, msg="iam_type: role, cannot currently be updated, "
                         "please specify present or absent")

    # check if trust_policy is present -- it can be inline JSON or a file path to a JSON file
    if trust_policy_filepath:
        try:
            with open(trust_policy_filepath, 'r') as json_data:
                trust_policy_doc = json.dumps(json.load(json_data))
        except Exception as e:
            module.fail_json(msg=str(e) + ': ' + trust_policy_filepath)
    elif trust_policy:
        try:
            trust_policy_doc = json.dumps(trust_policy)
        except Exception as e:
            module.fail_json(msg=str(e) + ': ' + trust_policy)
    else:
        trust_policy_doc = None

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)

    try:
        if region:
            iam = connect_to_aws(boto.iam, region, **aws_connect_kwargs)
        else:
            iam = boto.iam.connection.IAMConnection(**aws_connect_kwargs)
    except boto.exception.NoAuthHandlerFound as e:
        module.fail_json(msg=str(e))

    result = {}
    changed = False

    try:
        orig_group_list = list_all_groups(iam)

        orig_user_list = list_all_users(iam)

        orig_role_list = list_all_roles(iam)

        orig_prof_list = list_all_instance_profiles(iam)
    except boto.exception.BotoServerError as err:
        module.fail_json(msg=err.message)

    if iam_type == 'user':
        been_updated = False
        user_groups = None
        user_exists = any([n in [name, new_name] for n in orig_user_list])
        if user_exists:
            current_path = iam.get_user(name).get_user_result.user['path']
            if not new_path and current_path != path:
                new_path = path
                path = current_path

        if state == 'present' and not user_exists and not new_name:
            (meta, changed) = create_user(
                module, iam, name, password, path, key_state, key_count)
            keys = iam.get_all_access_keys(name).list_access_keys_result.\
                access_key_metadata
            if groups:
                (user_groups, changed) = set_users_groups(
                    module, iam, name, groups, been_updated, new_name)
            module.exit_json(
                user_meta=meta, groups=user_groups, keys=keys, changed=changed)

        elif state in ['present', 'update'] and user_exists:
            if update_pw == 'on_create':
                password = None
            if name not in orig_user_list and new_name in orig_user_list:
                been_updated = True
            name_change, key_list, user_changed, new_key = update_user(
                module, iam, name, new_name, new_path, key_state, key_count, key_ids, password, been_updated)
            if new_key:
                user_meta = {'access_keys': list(new_key)}
                user_meta['access_keys'].extend(
                    [{'access_key_id': key, 'status': value} for key, value in key_list.items() if
                     key not in [it['access_key_id'] for it in new_key]])
            else:
                user_meta = {
                    'access_keys': [{'access_key_id': key, 'status': value} for key, value in key_list.items()]}

            if name_change and new_name:
                orig_name = name
                name = new_name
            if isinstance(groups, list):
                user_groups, groups_changed = set_users_groups(
                    module, iam, name, groups, been_updated, new_name)
                if groups_changed == user_changed:
                    changed = groups_changed
                else:
                    changed = True
            else:
                changed = user_changed
            if new_name and new_path:
                module.exit_json(changed=changed, groups=user_groups, old_user_name=orig_name,
                                 new_user_name=new_name, old_path=path, new_path=new_path, keys=key_list,
                                 created_keys=new_key, user_meta=user_meta)
            elif new_name and not new_path and not been_updated:
                module.exit_json(
                    changed=changed, groups=user_groups, old_user_name=orig_name, new_user_name=new_name, keys=key_list,
                    created_keys=new_key, user_meta=user_meta)
            elif new_name and not new_path and been_updated:
                module.exit_json(
                    changed=changed, groups=user_groups, user_name=new_name, keys=key_list, key_state=key_state,
                    created_keys=new_key, user_meta=user_meta)
            elif not new_name and new_path:
                module.exit_json(
                    changed=changed, groups=user_groups, user_name=name, old_path=path, new_path=new_path,
                    keys=key_list, created_keys=new_key, user_meta=user_meta)
            else:
                module.exit_json(
                    changed=changed, groups=user_groups, user_name=name, keys=key_list, created_keys=new_key,
                    user_meta=user_meta)

        elif state == 'update' and not user_exists:
            module.fail_json(
                msg="The user %s does not exist. No update made." % name)

        elif state == 'absent':
            if user_exists:
                try:
                    set_users_groups(module, iam, name, '')
                    name, changed = delete_user(module, iam, name)
                    module.exit_json(deleted_user=name, changed=changed)

                except Exception as ex:
                    module.fail_json(changed=changed, msg=str(ex))
            else:
                module.exit_json(
                    changed=False, msg="User %s is already absent from your AWS IAM users" % name)

    elif iam_type == 'group':
        group_exists = name in orig_group_list

        if state == 'present' and not group_exists:
            new_group, changed = create_group(module=module, iam=iam, name=name, path=path)
            module.exit_json(changed=changed, group_name=new_group)
        elif state in ['present', 'update'] and group_exists:
            changed, updated_name, updated_path, cur_path = update_group(
                module=module, iam=iam, name=name, new_name=new_name,
                new_path=new_path)

            if new_path and new_name:
                module.exit_json(changed=changed, old_group_name=name,
                                 new_group_name=updated_name, old_path=cur_path,
                                 new_group_path=updated_path)

            if new_path and not new_name:
                module.exit_json(changed=changed, group_name=name,
                                 old_path=cur_path,
                                 new_group_path=updated_path)

            if not new_path and new_name:
                module.exit_json(changed=changed, old_group_name=name,
                                 new_group_name=updated_name, group_path=cur_path)

            if not new_path and not new_name:
                module.exit_json(
                    changed=changed, group_name=name, group_path=cur_path)

        elif state == 'update' and not group_exists:
            module.fail_json(
                changed=changed, msg="Update Failed. Group %s doesn't seem to exist!" % name)

        elif state == 'absent':
            if name in orig_group_list:
                removed_group, changed = delete_group(module=module, iam=iam, name=name)
                module.exit_json(changed=changed, delete_group=removed_group)
            else:
                module.exit_json(changed=changed, msg="Group already absent")

    elif iam_type == 'role':
        role_list = []
        if state == 'present':
            changed, role_list, role_result, instance_profile_result = create_role(
                module, iam, name, path, orig_role_list, orig_prof_list, trust_policy_doc)
        elif state == 'absent':
            changed, role_list, role_result, instance_profile_result = delete_role(
                module, iam, name, orig_role_list, orig_prof_list)
        elif state == 'update':
            module.fail_json(
                changed=False, msg='Role update not currently supported by boto.')
        module.exit_json(changed=changed, roles=role_list, role_result=role_result,
                         instance_profile_result=instance_profile_result)


if __name__ == '__main__':
    main()
