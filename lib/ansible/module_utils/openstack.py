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
        login_tenant_name=dict(required=False),
        login_tenant_id=dict(required=False),
        ca_cert=dict(required=False),
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

    if module.params.get('login_tenant_name'):
        result['tenant_name'] = module.params['login_tenant_name']
    elif module.params.get('login_tenant_id'):
        result['tenant_id'] = module.params['login_tenant_id']
    elif os.environ.get("OS_TENANT_ID"):
        result["tenant_id"] = os.environ.get("OS_TENANT_ID")
    elif os.environ.get("OS_TENANT_NAME"):
        result["tenant_name"] = os.environ.get("OS_TENANT_NAME")
    elif os.environ.get("OS_PROJECT_ID"):
        result["tenant_id"] = os.environ.get("OS_PROJECT_ID")
    elif os.environ.get("OS_PROJECT_NAME"):
        result["tenant_name"] = os.environ.get("OS_PROJECT_NAME")
    else:
        result["tenant_name"] = "admin"

    result["auth_url"] = (module.params.get("auth_url") or
                          os.environ.get("OS_AUTH_URL"))

    if module.params['region_name']:
        result['region_name'] = module.params['region_name']

    result['insecure'] = module.params['insecure']

    if module.params.get('ca_cert'):
        result['ca_cert'] = module.params['cacert']
    elif os.environ.get('OS_CACERT'):
        result['ca_cert'] = os.environ['OS_CACERT']

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


def get_auth_data(module, service_type, endpoint_type=None):
    keystone = get_keystone_client(module)

    kwargs = {"service_type": service_type}

    if endpoint_type:
        kwargs["endpoint_type"] = endpoint_type
    elif module.params.get('endpoint_type'):
        kwargs["endpoint_type"] = module.params['endpoint_type']

    result = os_auth_info(module)

    result["endpoint"] = keystone.service_catalog.url_for(**kwargs)
    result["token"] = keystone.auth_token

    if 'ca_cert' in kwargs:
        result['ca_cert'] = kwargs['ca_cert']

    return result


def get_nova_client(module):
    kwargs = os_auth_info(module)

    user = kwargs.pop("username")
    password = kwargs.pop("password")
    tenant = kwargs.pop("tenant_id")
    cacert = kwargs.pop("ca_cert")

    if module.params.get('endpoint_type'):
        kwargs['endpoint_type'] = module.params['endpoint_type']

    try:
        import novaclient.v1_1
        import novaclient.exceptions
    except ImportError:
        module.fail_json(msg="novaclient is required for this feature")

    nova = novaclient.v1_1.Client(user, password, tenant, cacert=cacert,
                                  **kwargs)
    try:
        nova.authenticate()
    except novaclient.exceptions.Unauthorized, e:
        module.fail_json(msg="Invalid OpenStack Nova credentials: %s" % e.message)
    except novaclient.exceptions.AuthorizationFailure, e:
        module.fail_json(msg="Unable to authorize user: %s" % e.message)

    return nova


def get_flavor(module, name=None, id=None, required=True, detailed=False,
               nova=None):
    if not nova:
        nova = get_nova_client(module)

    import novaclient.exceptions

    try:
        if name:
            return nova.flavors.find(name=name)
        else:
            return nova.flavors.find(id=id)
    except novaclient.exceptions.NotFound:
        if required:
            module.fail_json(msg="Server flavor not found")
        return None
    except Exception, e:
        module.fail_json(msg="Error in getting flavor: %s " % e.message)


def get_server(module, name=None, id=None, required=True, detailed=True,
               nova=None):
    if not nova:
        nova = get_nova_client(module)

    try:
        if name:
            servers = nova.servers.list(search_opts={"name": name},
                                        detailed=detailed)
            # the {'name': module.params['name']} will also return servers
            # with names that partially match the server name, so we have to
            # strictly filter here
            servers = [x for x in servers if x.name == name]
        else:
            servers = nova.servers.list(search_opts={"id": id},
                                        detailed=detailed)

    except Exception, e:
        module.fail_json(msg="Error in getting instance: %s " % e.message)

    if not servers:
        if required:
            module.fail_json(msg="Server not found")

        return None

    if len(servers) > 1:
        module.fail_json(msg="Ambigious servername")

    return servers[0]


def get_cinder_client(module):
    kwargs = os_auth_info(module)

    user = kwargs.pop("username")
    password = kwargs.pop("password")
    tenant_id = kwargs.pop("tenant_id") or kwargs.pop("tenant_name")

    if 'ca_cert' in kwargs:
        kwargs['cacert'] = kwargs.pop('ca_cert')

    if module.params.get('endpoint_type'):
        kwargs['endpoint_type'] = module.params['endpoint_type']

    try:
        import cinderclient.v1
        import cinderclient.exceptions
    except ImportError:
        module.fail_json(msg="cinderclient is required for this feature")

    cinder = cinderclient.v1.Client(user, password, tenant_id, **kwargs)
    try:
        cinder.authenticate()
    except cinderclient.exceptions.Unauthorized, e:
        module.fail_json(
            msg="Invalid OpenStack Cinder credentials: %s" % e.message,
            k=kwargs, f=(user, password, tenant_id))
    except cinderclient.exceptions.AuthorizationFailure, e:
        module.fail_json(msg="Unable to authorize user: %s" % e.message)

    return cinder


def get_volume(module, name=None, id=None, required=True, cinder=None):
    if not cinder:
        cinder = get_cinder_client(module)

    import cinderclient.exceptions

    try:
        if name:
            volumes = cinder.volumes.list(search_opts={'name': name})
            volumes = [x for x in volumes if x.display_name == name]
        elif id:
            try:
                volumes = [cinder.volumes.get(id)]
            except cinderclient.exceptions.NotFound:
                volumes = []

        else:
            module.fail_json(msg="No name? no id?")
    except Exception, e:
        module.fail_json(msg="Error in getting instance: %s " % e.message)

    if not volumes:
        if required:
            module.fail_json(msg="Volume not found")

        return None

    if len(volumes) > 1:
        module.fail_json(msg="Ambigious volume name", name=name, id=id,)

    return volumes[0]


def get_snapshot(module, name=None, id=None, required=True, cinder=None):
    if not cinder:
        cinder = get_cinder_client(module)

    try:
        if name:
            snapshots = cinder.volume_snapshots.list(
                search_opts={'name': name})
        else:
            snapshots = cinder.volume_snapshots.list(search_opts={'id': id})
    except Exception, e:
        module.fail_json(msg="Error in getting instance: %s " % e.message)

    if not snapshots:
        if required:
            module.fail_json(msg="Snapshot not found")

        return None

    if len(snapshots) > 1:
        module.fail_json(msg="Ambigious snapshot name", name=name)

    return snapshots[0]


def get_glance_client(module):
    try:
        import glanceclient.v1.client
    except ImportError:
        module.fail_json(msg="glanceclient is required for this feature")

    kwargs = get_auth_data(module, 'image')

    return glanceclient.v1.client.Client(kwargs['endpoint'],
                                         token=kwargs['token'],
                                         ca_cert=kwargs.get('ca_cert'))


def get_glance_image(module, name, required=True, glance=None):
    if not glance:
        glance = get_glance_client(module)

    try:
        for image in glance.images.list():
            if image.name == name:
                return image
    except Exception, e:
        module.fail_json(msg="Error in fetching image list: %s" % str(e))

    if required:
        module.fail_json(msg="image not found")


def get_neutron_client(module):
    try:
        try:
            from neutronclient.neutron import client as nclient
        except ImportError:
            from quantumclient.quantum import client as nclient
    except ImportError, e:
        import sys
        module.fail_json(msg="quantumclient or neutronclient are required")

    kwargs = get_auth_data(module, 'network')

    try:
        neutron = nclient.Client('2.0',
                                 token=kwargs['token'],
                                 endpoint_url=kwargs['endpoint'],
                                 ca_cert=kwargs.get('ca_cert'))
    except Exception, e:
        module.fail_json(msg="Error in connecting to neutron: %s " % e.message)

    return neutron


def get_network(module, name=None, id=None, tenant_id=None, required=True,
                neutron=None):
    if not neutron:
        neutron = get_neutron_client(module)

    kwargs = {}
    if tenant_id:
        kwargs['tenant_id'] = tenant_id

    try:
        if name:
            networks = neutron.list_networks(name=name, **kwargs)
        else:
            networks = neutron.list_networks(name=id, **kwargs)
    except Exception, e:
        module.fail_json(
            msg="Error in listing neutron networks: %s" % e.message)

    if not networks['networks']:
        if required:
            module.fail_json(msg="Network not found", network_name=name,
                             network_id=id, tenant_id=tenant_id)
        return None

    if len(networks['networks']) > 1:
        module.fail_json(msg="Multiple networks found, use tenant_id to "
                         "disambiguate")

    return networks['networks'][0]


def get_subnet(module, name=None, id=None, tenant_id=None, required=True,
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


def get_router(module, name=None, id=None, tenant_id=None, required=True,
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
            module.fail_json(msg="Router not found", name=name, id=id)

        return None

    if len(routers['routers']) > 1:
        module.fail_json(msg="Multiple router not found, specify tenant to "
                             "disambiguate")

    return routers['routers'][0]


def get_port(module, network_id, device_id, subnet_id=None, neutron=None,
             required=True):
    if not neutron:
        neutron = get_neutron_client(module)

    try:
        ports = neutron.list_ports(device_id=device_id, network_id=network_id)
    except Exception, e:
        module.fail_json(msg="Error in listing ports: %s" % e.message)

    if not ports['ports']:
        if required:
            module.fail_json(msg="Port not found", net=network_id, dev=device_id)

        return None

    if subnet_id:
        for port in ports['ports']:
            if any(ip["subnet_id"] == subnet_id for ip in port['fixed_ips']):
                return port

        if required:
            module.fail_json(msg="Port not found")

        return None
    else:
        return ports['ports'][0]
