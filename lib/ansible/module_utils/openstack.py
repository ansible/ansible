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

import keystoneclient.v2_0.client
import os

# TODO: implement CA cert
# TODO: implement token caching


def os_argument_spec():
    return dict(
        auth_url=dict(required=False),
        login_user=dict(required=False),
        login_password=dict(required=False),
        login_tenant_name=dict(required=False, default="admin"),
        login_tenant_id=dict(required=False),
        token=dict(required=False),
        region_name=dict(default=None),
        endpoint_type=dict(default="publicURL"),
        insecure=dict(default="no", type="bool"),
        endpoint=dict(default=None),
    )


def os_mutually_exclusive():
    return [
        ['token', 'login_user'],
        ['token', 'login_password'],
        ['token', 'login_tenant_name'],
        ['token', 'login_tenant_id'],
        ['login_tenant_name', 'login_tenant_id'],
        ['endpoint_type', 'endpoint'],
        ['region_name', 'endpoint'],
    ]


def os_authenticate(module, service_type):
    if module.params.get('token') and module.params.get('endpoint'):
        # User already provided token and endpoint, no further auth required
        return module.params['token'], module.params.get['endpoint']

    kwargs = {}

    if module.params.get("token"):
        kwargs["token"] = module.params["token"]
    else:
        kwargs["username"] = (module.params.get("login_user") or
                              os.environ.get("OS_USERNAME", 'admin'))

        kwargs["password"] = (module.params.get("login_password") or
                              os.environ.get("OS_PASSWORD"))

        if not kwargs["password"]:
            module.fail_json(msg="Please provide either a token or a password", env=dict(os.environ))

    if module.params.get('tenant_name'):
        kwargs['tenant_name'] = module.params['tenant_name']
    elif module.params.get('tenant_id'):
        kwargs['tenant_id'] = module.params['tenant_id']
    elif os.environ.get("OS_TENANT_ID"):
        kwargs["tenant_id"] = os.environ.get("OS_TENANT_ID")
    elif os.environ.get("OS_TENANT_NAME"):
        kwargs["tenant_name"] = os.environ.get("OS_TENANT_NAME")
    elif os.environ.get("OS_PROJECT_ID"):
        kwargs["tenant_id"] = os.environ.get("OS_PROJECT_ID")
    elif os.environ.get("OS_PROJECT_NAME"):
        kwargs["tenant_name"] = os.environ.get("OS_PROJECT_NAME")

    kwargs["auth_url"] = (module.params.get("auth_url") or
                          os.environ.get("OS_AUTH_URL"))

    if module.params['region_name']:
        kwargs['region_name'] = module.params['region_name']

    kwargs['insecure'] = module.params['insecure']

    ksclient = keystoneclient.v2_0.client.Client(**kwargs)
    ksclient.authenticate()

    endpoint = ksclient.service_catalog.url_for(service_type=service_type,
                                                endpoint_type='admin')

    return ksclient.auth_token, endpoint
