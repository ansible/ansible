# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os

HAVE_NOVACLIENT = True
try:
    from novaclient.v1_1 import client as nova_client
    from novaclient import exceptions as nova_exceptions
except:
    HAVE_NOVACLIENT = False


def openstack_argument_spec():
    # Consume standard OpenStack environment variables.
    # This is mainly only useful for ad-hoc command line operation as
    # in playbooks one would assume variables would be used appropriately
    OS_AUTH_URL=os.environ.get('OS_AUTH_URL', 'http://127.0.0.1:35357/v2.0/')
    OS_PASSWORD=os.environ.get('OS_PASSWORD', None)
    OS_REGION_NAME=os.environ.get('OS_REGION_NAME', None)
    OS_USERNAME=os.environ.get('OS_USERNAME', 'admin')
    OS_TENANT_NAME=os.environ.get('OS_TENANT_NAME', OS_USERNAME)

    spec = dict(
        login_username                  = dict(default=OS_USERNAME),
        auth_url                        = dict(default=OS_AUTH_URL),
        region_name                     = dict(default=OS_REGION_NAME),
        availability_zone               = dict(default=None),
    )
    if OS_PASSWORD:
        spec['login_password'] = dict(default=OS_PASSWORD)
    else:
        spec['login_password'] = dict(required=True)
    if OS_TENANT_NAME:
        spec['login_tenant_name'] = dict(default=OS_TENANT_NAME)
    else:
        spec['login_tenant_name'] = dict(required=True)
    return spec

def openstack_find_nova_addresses(addresses, ext_tag, key_name=None):

    ret = []
    for (k, v) in addresses.iteritems():
        if key_name and k == key_name:
            ret.extend([addrs['addr'] for addrs in v])
        else:
            for interface_spec in v:
                if 'OS-EXT-IPS:type' in interface_spec and interface_spec['OS-EXT-IPS:type'] == ext_tag:
                    ret.append(interface_spec['addr'])
    return ret


class OpenStackAnsibleException(Exception):
    pass


class OpenStackCloud(object):

    def __init__(self, name, username, password, project_id, auth_url,
                 region_name, service_type, insecure, private=False,
                 image_cache=dict(), flavor_cache=None):

        if not HAVE_NOVACLIENT:
            raise OpenStackAnsibleException(
                "novaclient is required. Install python-novaclient and try again")
        self.name = name
        self.username = username
        self.password = password
        self.project_id = project_id
        self.auth_url = auth_url
        self.region_name = region_name
        self.service_type = service_type
        self.insecure = insecure
        self.private = private
        self.image_cache = image_cache
        self.flavor_cache = flavor_cache

        self._nova_client = None

    @classmethod
    def from_module(klass, module):
        return klass(
            name='openstack',
            username=module.params['login_username'],
            password=module.params['login_password'],
            project_id=module.params['login_tenant_name'],
            auth_url=module.params['auth_url'],
            region_name=module.params['region_name'],
            service_type='compute')

    def get_name(self):
        return self.name

    def get_region(self):
        return self.region_name

    def get_flavor_name(self, flavor_id):
        if not self.flavor_cache:
            self.flavor_cache = dict([(flavor.id, flavor.name) for flavor in self.nova_client.flavors.list()])
        return self.flavor_cache.get(flavor_id, None)

    @property
    def nova_client(self):
        if self._nova_client is None:
            # Make the connection
            self._nova_client = nova_client.Client(
                self.username,
                self.password,
                self.project_id,
                self.auth_url,
                region_name=self.region_name,
                service_type=self.service_type,
                insecure=self.insecure
            )

            try:
                self._nova_client.authenticate()
            except nova_exceptions.Unauthorized, e:
                raise OpenStackAnsibleException(
                    "Invalid OpenStack Nova credentials.: %s" % e.message)
            except nova_exceptions.AuthorizationFailure, e:
                raise OpenStackAnsibleException(
                    "Unable to authorize user: %s" % e.message)

            if self._nova_client is None:
                raise OpenStackAnsibleException(
                    "Failed to instantiate nova client. This could mean that your"
                    " credentials are wrong.")

        return self._nova_client

    def list_servers(self):
        return self.nova_client.servers.list()

    def list_keypairs(self):
        return self.nova_client.keypairs.list()

    def create_keypair(self, name, public_key):
        return self.nova_client.keypairs.create(name, public_key)

    def delete_keypair(self, name):
        return self.nova_client.keypairs.delete(name)

    def get_image_name(self, image_id):
        if image_id not in self.image_cache:
            try:
                self.image_cache[image_id] = self.nova_client.images.get(image_id).name
            except Exception:
                self.image_cache[image_id] = None
        return self.image_cache[image_id]
