# (c) 2014, Koert van der Veer <koert@cloudvps.com>
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

#############################################

import os


def os_argument_spec():
    return dict(
        auth_url=dict(required=False),
        login_user=dict(required=False),
        login_username=dict(required=False),
        login_password=dict(required=False),
        login_tenant_name=dict(required=False, default="admin"),
        login_tenant_id=dict(required=False),
        token=dict(required=False),
        region_name=dict(default=None),
        endpoint_type=dict(default="publicURL"),
        insecure=dict(default="no", type="bool"),
    )


def os_mutually_exclusive():
    return [
        ['login_username', 'login_user'],
        ['token', 'login_user'],
        ['token', 'login_password'],
        ['token', 'login_tenant_name'],
        ['token', 'login_tenant_id'],
        ['login_tenant_name', 'login_tenant_id'],
        ['endpoint_type', 'endpoint'],
        ['region_name', 'endpoint'],
    ]


def os_auth_info(module):
    result = {}

    result["username"] = (module.params.get("login_user") or
                          module.params.get("login_username") or
                          os.environ.get("OS_USERNAME", 'admin'))

    result["password"] = (module.params.get("login_password") or
                          os.environ.get("OS_PASSWORD"))

    if module.params.get('tenant_name'):
        result['tenant_name'] = module.params['tenant_name']
    elif module.params.get('tenant_id'):
        result['tenant_id'] = module.params['tenant_id']
    elif os.environ.get("OS_TENANT_ID"):
        result["tenant_id"] = os.environ.get("OS_TENANT_ID")
    elif os.environ.get("OS_TENANT_NAME"):
        result["tenant_name"] = os.environ.get("OS_TENANT_NAME")
    elif os.environ.get("OS_PROJECT_ID"):
        result["tenant_id"] = os.environ.get("OS_PROJECT_ID")
    elif os.environ.get("OS_PROJECT_NAME"):
        result["tenant_name"] = os.environ.get("OS_PROJECT_NAME")

    result["auth_url"] = (module.params.get("auth_url") or
                          os.environ.get("OS_AUTH_URL"))

    if module.params['region_name']:
        result['region_name'] = module.params['region_name']

    result['insecure'] = module.params['insecure']

    return result


def get_keystone_client(module):
    # interpret the authentication paramers from keystone
    kwargs = os_auth_info(module)

    if module.params.get('token'):
        kwargs.pop("username")
        kwargs.pop("password")
        kwargs['token'] = module.params['token']

    if not kwargs['auth_url']:
        # Admins can also authenticate against the admin endpoint,
        # so that's an excelent alternative to auth_url
        kwargs['auth_url'] = module.params['endpoint']

    try:
        import keystoneclient.v2_0.client
    except ImportError:
        module.fail_json(msg="keystoneclient is required for this feature")

    return keystoneclient.v2_0.client.Client(**kwargs)


def get_nova_client(module):
    kwargs = os_auth_info(module)

    user = kwargs.pop("username")
    password = kwargs.pop("password")
    tenant_id = kwargs.pop("tenant_name", None) or kwargs.pop("tenant_id")

    try:
        import novaclient.v1_1.client
        import novaclient.exceptions
    except ImportError:
        module.fail_json(msg="keystoneclient is required for this feature")

    nova = novaclient.v1_1.client.Client(user, password, tenant_id, **kwargs)
    try:
        nova.authenticate()
    except novaclient.exceptions.Unauthorized, e:
        module.fail_json(msg="Invalid OpenStack Nova credentials: %s" % e.message)
    except novaclient.exceptions.AuthorizationFailure, e:
        module.fail_json(msg="Unable to authorize user: %s" % e.message)

    return nova
