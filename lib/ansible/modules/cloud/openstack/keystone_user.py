#!/usr/bin/python
# -*- coding: utf-8 -*-
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

# Based on Jimmy Tang's implementation

DOCUMENTATION = '''
---
module: keystone_user
version_added: "1.2"
short_description: Manage OpenStack Identity (keystone) users, tenants and roles
description:
   - Manage users,tenants, roles from OpenStack.
options:
   login_user:
     description:
        - login username to authenticate to keystone
     required: false
     default: admin
   login_password:
     description:
        - Password of login user
     required: false
     default: 'yes'
   login_tenant_name:
     description:
        - The tenant login_user belongs to
     required: false
     default: None
     version_added: "1.3"
   token:
     description:
        - The token to be uses in case the password is not specified
     required: false
     default: None
   endpoint:
     description:
        - The keystone url for authentication
     required: false
     default: 'http://127.0.0.1:35357/v2.0/'
   user:
     description:
        - The name of the user that has to added/removed from OpenStack
     required: false
     default: None
   password:
     description:
        - The password to be assigned to the user
     required: false
     default: None
   tenant:
     description:
        - The tenant name that has be added/removed
     required: false
     default: None
   tenant_description:
     description:
        - A description for the tenant
     required: false
     default: None
   email:
     description:
        - An email address for the user
     required: false
     default: None
   role:
     description:
        - The name of the role to be assigned or created
     required: false
     default: None
   state:
     description:
        - Indicate desired state of the resource
     choices: ['present', 'absent']
     default: present
requirements:
    - "python >= 2.6"
    -  python-keystoneclient
author: "Lorin Hochstein (@lorin)"
'''

EXAMPLES = '''
# Create a tenant
- keystone_user: tenant=demo tenant_description="Default Tenant"

# Create a user
- keystone_user: user=john tenant=demo password=secrete

# Apply the admin role to the john user in the demo tenant
- keystone_user: role=admin user=john tenant=demo
'''

try:
    from keystoneclient.v2_0 import client
except ImportError:
    keystoneclient_found = False
else:
    keystoneclient_found = True


def authenticate(endpoint, token, login_user, login_password, login_tenant_name):
    """Return a keystone client object"""

    if token:
        return client.Client(endpoint=endpoint, token=token)
    else:
        return client.Client(auth_url=endpoint, username=login_user,
                             password=login_password, tenant_name=login_tenant_name)


def tenant_exists(keystone, tenant):
    """ Return True if tenant already exists"""
    return tenant in [x.name for x in keystone.tenants.list()]


def user_exists(keystone, user):
    """" Return True if user already exists"""
    return user in [x.name for x in keystone.users.list()]


def get_tenant(keystone, name):
    """ Retrieve a tenant by name"""
    tenants = [x for x in keystone.tenants.list() if x.name == name]
    count = len(tenants)
    if count == 0:
        raise KeyError("No keystone tenants with name %s" % name)
    elif count > 1:
        raise ValueError("%d tenants with name %s" % (count, name))
    else:
        return tenants[0]


def get_user(keystone, name):
    """ Retrieve a user by name"""
    users = [x for x in keystone.users.list() if x.name == name]
    count = len(users)
    if count == 0:
        raise KeyError("No keystone users with name %s" % name)
    elif count > 1:
        raise ValueError("%d users with name %s" % (count, name))
    else:
        return users[0]


def get_role(keystone, name):
    """ Retrieve a role by name"""
    roles = [x for x in keystone.roles.list() if x.name == name]
    count = len(roles)
    if count == 0:
        raise KeyError("No keystone roles with name %s" % name)
    elif count > 1:
        raise ValueError("%d roles with name %s" % (count, name))
    else:
        return roles[0]


def get_tenant_id(keystone, name):
    return get_tenant(keystone, name).id


def get_user_id(keystone, name):
    return get_user(keystone, name).id


def ensure_tenant_exists(keystone, tenant_name, tenant_description,
                         check_mode):
    """ Ensure that a tenant exists.

        Return (True, id) if a new tenant was created, (False, None) if it
        already existed.
    """

    # Check if tenant already exists
    try:
        tenant = get_tenant(keystone, tenant_name)
    except KeyError:
        # Tenant doesn't exist yet
        pass
    else:
        if tenant.description == tenant_description:
            return (False, tenant.id)
        else:
            # We need to update the tenant description
            if check_mode:
                return (True, tenant.id)
            else:
                tenant.update(description=tenant_description)
                return (True, tenant.id)

    # We now know we will have to create a new tenant
    if check_mode:
        return (True, None)

    ks_tenant = keystone.tenants.create(tenant_name=tenant_name,
                                        description=tenant_description,
                                        enabled=True)
    return (True, ks_tenant.id)


def ensure_tenant_absent(keystone, tenant, check_mode):
    """ Ensure that a tenant does not exist

         Return True if the tenant was removed, False if it didn't exist
         in the first place
    """
    if not tenant_exists(keystone, tenant):
        return False

    # We now know we will have to delete the tenant
    if check_mode:
        return True


def ensure_user_exists(keystone, user_name, password, email, tenant_name,
                       check_mode):
    """ Check if user exists

        Return (True, id) if a new user was created, (False, id) user alrady
        exists
    """

    # Check if tenant already exists
    try:
        user = get_user(keystone, user_name)
    except KeyError:
        # Tenant doesn't exist yet
        pass
    else:
        # User does exist, we're done
        return (False, user.id)

    # We now know we will have to create a new user
    if check_mode:
        return (True, None)

    tenant = get_tenant(keystone, tenant_name)

    user = keystone.users.create(name=user_name, password=password,
                                 email=email, tenant_id=tenant.id)
    return (True, user.id)

def ensure_role_exists(keystone, role_name):
    # Get the role if it exists
    try:
        role = get_role(keystone, role_name)
        # Role does exist, we're done
        return (False, role.id)
    except KeyError:
        # Role doesn't exist yet
        pass

    role = keystone.roles.create(role_name)
    return (True, role.id)

def ensure_user_role_exists(keystone, user_name, tenant_name, role_name,
                       check_mode):
    """ Check if role exists

        Return (True, id) if a new role was created or if the role was newly
        assigned to the user for the tenant. (False, id) if the role already
        exists and was already assigned to the user ofr the tenant.

    """
    # Check if the user has the role in the tenant
    user = get_user(keystone, user_name)
    tenant = get_tenant(keystone, tenant_name)
    roles = [x for x in keystone.roles.roles_for_user(user, tenant)
                     if x.name == role_name]
    count = len(roles)

    if count == 1:
        # If the role is in there, we are done
        role = roles[0]
        return (False, role.id)
    elif count > 1:
        # Too many roles with the same name, throw an error
        raise ValueError("%d roles with name %s" % (count, role_name))

    # At this point, we know we will need to make changes
    if check_mode:
        return (True, None)

    # Get the role if it exists
    try:
        role = get_role(keystone, role_name)
    except KeyError:
        # Role doesn't exist yet
        role = keystone.roles.create(role_name)

    # Associate the role with the user in the admin
    keystone.roles.add_user_role(user, role, tenant)
    return (True, role.id)


def ensure_user_absent(keystone, user, check_mode):
    raise NotImplementedError("Not yet implemented")


def ensure_user_role_absent(keystone, uesr, tenant, role, check_mode):
    raise NotImplementedError("Not yet implemented")

def ensure_role_absent(keystone, role_name):
    raise NotImplementedError("Not yet implemented")

def main():

    argument_spec = openstack_argument_spec()
    argument_spec.update(dict(
            tenant_description=dict(required=False),
            email=dict(required=False),
            user=dict(required=False),
            tenant=dict(required=False),
            password=dict(required=False),
            role=dict(required=False),
            state=dict(default='present', choices=['present', 'absent']),
            endpoint=dict(required=False,
                          default="http://127.0.0.1:35357/v2.0"),
            token=dict(required=False),
            login_user=dict(required=False),
            login_password=dict(required=False),
            login_tenant_name=dict(required=False)
    ))
    # keystone operations themselves take an endpoint, not a keystone auth_url
    del(argument_spec['auth_url'])
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[['token', 'login_user'],
                            ['token', 'login_password'],
                            ['token', 'login_tenant_name']]
    )

    if not keystoneclient_found:
        module.fail_json(msg="the python-keystoneclient module is required")

    user = module.params['user']
    password = module.params['password']
    tenant = module.params['tenant']
    tenant_description = module.params['tenant_description']
    email = module.params['email']
    role = module.params['role']
    state = module.params['state']
    endpoint = module.params['endpoint']
    token = module.params['token']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    login_tenant_name = module.params['login_tenant_name']

    keystone = authenticate(endpoint, token, login_user, login_password, login_tenant_name)

    check_mode = module.check_mode

    try:
        d = dispatch(keystone, user, password, tenant, tenant_description,
                     email, role, state, endpoint, token, login_user,
                     login_password, check_mode)
    except Exception, e:
        if check_mode:
            # If we have a failure in check mode
            module.exit_json(changed=True,
                             msg="exception: %s" % e)
        else:
            module.fail_json(msg="exception: %s" % e)
    else:
        module.exit_json(**d)


def dispatch(keystone, user=None, password=None, tenant=None,
             tenant_description=None, email=None, role=None,
             state="present", endpoint=None, token=None, login_user=None,
             login_password=None, check_mode=False):
    """ Dispatch to the appropriate method.

        Returns a dict that will be passed to exit_json

        tenant  user  role   state
        ------  ----  ----  --------
          X                  present     ensure_tenant_exists
          X                  absent      ensure_tenant_absent
          X      X           present     ensure_user_exists
          X      X           absent      ensure_user_absent
          X      X     X     present     ensure_user_role_exists
          X      X     X     absent      ensure_user_role_absent
                       X     present     ensure_role_exists
                       X     absent      ensure_role_absent
        """
    changed = False
    id = None
    if not tenant and not user and role and state == "present":
        changed, id = ensure_role_exists(keystone, role)
    elif not tenant and not user and role and state == "absent":
        changed = ensure_role_absent(keystone, role)
    elif tenant and not user and not role and state == "present":
        changed, id = ensure_tenant_exists(keystone, tenant,
                                           tenant_description, check_mode)
    elif tenant and not user and not role and state == "absent":
        changed = ensure_tenant_absent(keystone, tenant, check_mode)
    elif tenant and user and not role and state == "present":
        changed, id = ensure_user_exists(keystone, user, password,
                                         email, tenant, check_mode)
    elif tenant and user and not role and state == "absent":
        changed = ensure_user_absent(keystone, user, check_mode)
    elif tenant and user and role and state == "present":
        changed, id = ensure_user_role_exists(keystone, user, tenant, role,
                                         check_mode)
    elif tenant and user and role and state == "absent":
        changed = ensure_user_role_absent(keystone, user, tenant, role, check_mode)
    else:
        # Should never reach here
        raise ValueError("Code should never reach here")

    return dict(changed=changed, id=id)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
