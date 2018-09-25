#
# Copyright (c) 2017, Daniel Korn <korndaniel1@gmail.com>
#
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
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

try:
    from manageiq_client.api import ManageIQClient
    HAS_CLIENT = True
except ImportError:
    HAS_CLIENT = False


def manageiq_argument_spec():
    options = dict(
        url=dict(default=os.environ.get('MIQ_URL', None)),
        username=dict(default=os.environ.get('MIQ_USERNAME', None)),
        password=dict(default=os.environ.get('MIQ_PASSWORD', None), no_log=True),
        token=dict(default=os.environ.get('MIQ_TOKEN', None), no_log=True),
        verify_ssl=dict(default=True, type='bool'),
        ca_bundle_path=dict(required=False, default=None),
    )

    return dict(
        manageiq_connection=dict(type='dict',
                                 apply_defaults=True,
                                 options=options),
    )


def check_client(module):
    if not HAS_CLIENT:
        module.fail_json(msg='manageiq_client.api is required for this module')


def validate_connection_params(module):
    params = module.params['manageiq_connection']
    error_str = "missing required argument: manageiq_connection[{}]"
    url = params['url']
    token = params['token']
    username = params['username']
    password = params['password']

    if (url and username and password) or (url and token):
        return params
    for arg in ['url', 'username', 'password']:
        if params[arg] in (None, ''):
            module.fail_json(msg=error_str.format(arg))


def manageiq_entities():
    return {
        'provider': 'providers', 'host': 'hosts', 'vm': 'vms',
        'category': 'categories', 'cluster': 'clusters', 'data store': 'data_stores',
        'group': 'groups', 'resource pool': 'resource_pools', 'service': 'services',
        'service template': 'service_templates', 'template': 'templates',
        'tenant': 'tenants', 'user': 'users', 'blueprint': 'blueprints'
    }


class ManageIQ(object):
    """
        class encapsulating ManageIQ API client.
    """

    def __init__(self, module):
        # handle import errors
        check_client(module)

        params = validate_connection_params(module)

        url = params['url']
        username = params['username']
        password = params['password']
        token = params['token']
        verify_ssl = params['verify_ssl']
        ca_bundle_path = params['ca_bundle_path']

        self._module = module
        self._api_url = url + '/api'
        self._auth = dict(user=username, password=password, token=token)
        try:
            self._client = ManageIQClient(self._api_url, self._auth, verify_ssl=verify_ssl, ca_bundle_path=ca_bundle_path)
        except Exception as e:
            self.module.fail_json(msg="failed to open connection (%s): %s" % (url, str(e)))

    @property
    def module(self):
        """ Ansible module module

        Returns:
            the ansible module
        """
        return self._module

    @property
    def api_url(self):
        """ Base ManageIQ API

        Returns:
            the base ManageIQ API
        """
        return self._api_url

    @property
    def client(self):
        """ ManageIQ client

        Returns:
            the ManageIQ client
        """
        return self._client

    def find_collection_resource_by(self, collection_name, **params):
        """ Searches the collection resource by the collection name and the param passed.

        Returns:
            the resource as an object if it exists in manageiq, None otherwise.
        """
        try:
            entity = self.client.collections.__getattribute__(collection_name).get(**params)
        except ValueError:
            return None
        except Exception as e:
            self.module.fail_json(msg="failed to find resource {error}".format(error=e))
        return vars(entity)

    def find_collection_resource_or_fail(self, collection_name, **params):
        """ Searches the collection resource by the collection name and the param passed.

        Returns:
            the resource as an object if it exists in manageiq, Fail otherwise.
        """
        resource = self.find_collection_resource_by(collection_name, **params)
        if resource:
            return resource
        else:
            msg = "{collection_name} where {params} does not exist in manageiq".format(
                collection_name=collection_name, params=str(params))
            self.module.fail_json(msg=msg)
