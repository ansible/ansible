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

    keystone = keystoneclient.v2_0.client.Client(**kwargs)
    return keystone


def get_tenant_id(module, tenant_name, keystone=None):
    if not keystone:
        keystone = get_keystone_client(module)

    tenant_name = module.params['tenant_name']

    for tenant in keystone.tenants.list():
        if tenant.name == tenant_name:
            return tenant.id


def get_token_and_endpoint(module, service_type, endpoint_type=None):
    keystone = get_keystone_client(module)

    kwargs = {"service_type": service_type}

    if endpoint_type:
        kwargs["endpoint_type"] = endpoint_type
    elif module.params.get('endpoint_type'):
        kwargs["endpoint_type"] = module.params['endpoint_type']

    return keystone.auth_token, keystone.service_catalog.url_for(**kwargs)


def get_nova_client(module):
    kwargs = os_auth_info(module)

    user = kwargs.pop("username")
    password = kwargs.pop("password")
    tenant_id = kwargs.pop("tenant_name", None) or kwargs.pop("tenant_id")

    if module.params.get('endpoint_type'):
        kwargs['endpoint_type'] = module.params['endpoint_type']

    try:
        import novaclient.v1_1.client
        import novaclient.exceptions
    except ImportError:
        module.fail_json(msg="novaclient is required for this feature")

    nova = novaclient.v1_1.client.Client(user, password, tenant_id, **kwargs)
    try:
        nova.authenticate()
    except novaclient.exceptions.Unauthorized, e:
        module.fail_json(msg="Invalid OpenStack Nova credentials: %s" % e.message)
    except novaclient.exceptions.AuthorizationFailure, e:
        module.fail_json(msg="Unable to authorize user: %s" % e.message)

    return nova


def get_glance_client(module):
    try:
        import glanceclient.v1.client
    except ImportError:
        module.fail_json(msg="glanceclient is required for this feature")

    token, endpoint = get_token_and_endpoint(module, 'image')

    return glanceclient.v1.client.Client(endpoint, token=token)


def get_glance_image_id(module, name, glance=None):
    if not glance:
        glance = get_glance_client(module)

    try:
        for image in glance.images.list():
            if image.name == name:
                return image.id
    except Exception, e:
        module.fail_json(msg="Error in fetching image list: %s" % e.message)


def get_neutron_client(module):
    try:
        try:
            from neutronclient.neutron import client as nclient
        except ImportError:
            from quantumclient.quantum import client as nclient
    except ImportError, e:
        import sys
        module.fail_json(msg="quantumclient or neutronclient are required")

    token, endpoint = get_token_and_endpoint(module, 'network')

    try:
        neutron = nclient.Client('2.0', token=token, endpoint_url=endpoint)
    except Exception, e:
        module.fail_json(msg="Error in connecting to neutron: %s " % e.message)
    return neutron


def get_network_id(module, name, tenant_id=None, neutron=None):
    if not neutron:
        neutron = get_neutron_client(module)

    kwargs = {'name': name}

    if tenant_id:
        kwargs['tenant_id'] = tenant_id

    try:
        networks = neutron.list_networks(**kwargs)
    except Exception, e:
        module.fail_json(
            msg="Error in listing neutron networks: %s" % e.message)

    if not networks['networks']:
        module.fail_json(
            msg="Not found",
            network_name=name,
            tenant_id=tenant_id,
            kwargs=kwargs)
        return None

    return networks['networks'][0]['id']


def get_subnet(module, name=None, id=None, tenant_id=None, required=False,
               neutron=None):
    if not neutron:
        neutron = get_neutron_client(module)

    kwargs = {}
    if tenant_id:
        kwargs['tenant_id'] = tenant_id

    try:
        if name:
            subnets = neutron.list_subnets(name=name, **kwargs)
        else:
            subnets = neutron.list_subnets(id=id, **kwargs)
    except Exception, e:
        module.fail_json(msg="Error in getting the subnet list: %s" % e.message)
    
    if not subnets['subnets']:
        if required:
            module.fail_json(msg="Subnet not found")
        return None

    if len(subnets['subnets']) > 1:
        module.fail_json(msg="Multiple subnets not found, specify tenant to "
                             "disambiguate")

    return subnets['subnets'][0]


def get_router(module, name=None, id=None, tenant_id=None, required=False,
               neutron=None):
    if not neutron:
        neutron = get_neutron_client(module)

    kwargs = {}
    if tenant_id:
        kwargs['tenant_id'] = tenant_id

    try:
        if name:
            routers = neutron.list_routers(name=name, **kwargs)
        elif id:
            routers = neutron.list_routers(id=id, **kwargs)
    except Exception, e:
        module.fail_json(msg="Error in getting the router list: %s " % e.message)

    if not routers['routers']:
        if required:
            module.fail_json(msg="Router not found")
        return None

    if len(routers['routers']) > 1:
        module.fail_json(msg="Multiple router not found, specify tenant to "
                             "disambiguate")

    return routers['routers'][0]


def get_port_id(module, network_id, device_id, subnet_id=None, neutron=None):
    if not neutron:
        neutron = get_neutron_client(module)

    try:
        ports = neutron.list_ports(device_id=device_id, network_id=network_id)
    except Exception, e:
        module.fail_json(msg="Error in listing ports: %s" % e.message)
    if not ports['ports']:
        return None

    if subnet_id:
        for port in ports['ports']:
            if any(ip["subnet_id"] == subnet_id for ip in port['fixed_ips']):
                return port['id']
        return None

    return ports['ports'][0]['id']
