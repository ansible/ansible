# -*- coding: utf-8 -*-

# Copyright (c) 2018, Ingate Systems AB
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


try:
    from ingate import ingatesdk
    HAS_INGATESDK = True
except ImportError:
    HAS_INGATESDK = False


def ingate_argument_spec(**kwargs):
    client_options = dict(
        version=dict(choices=['v1'], required=True),
        scheme=dict(choices=['http', 'https'], required=True),
        address=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        port=dict(type='int'),
        timeout=dict(type='int'),
        verify_ssl=dict(default=True, type='bool'),
    )
    argument_spec = dict(
        client=dict(type='dict', required=True,
                    options=client_options),
    )
    argument_spec.update(kwargs)
    return argument_spec


def ingate_create_client(**kwargs):
    if not HAS_INGATESDK:
        raise ImportError("The Ingate Python SDK module is required")

    client_params = kwargs['client']

    # Create API client.
    api_client = ingatesdk.Client(client_params['version'],
                                  client_params['scheme'],
                                  client_params['address'],
                                  client_params['username'],
                                  client_params['password'],
                                  port=client_params['port'],
                                  timeout=client_params['timeout'])

    # Check if we should skip SSL Certificate verification.
    verify_ssl = client_params.get('verify_ssl')
    if verify_ssl is not None and not verify_ssl:
        api_client.skip_verify_certificate()

    # Authenticate and get hold of a security token.
    api_client.authenticate()

    # Return the client.
    return api_client


def ingate_create_client_noauth(**kwargs):
    if not HAS_INGATESDK:
        raise ImportError("The Ingate Python SDK module is required")

    client_params = kwargs['client']

    # Create API client.
    api_client = ingatesdk.Client(client_params['version'],
                                  client_params['scheme'],
                                  client_params['address'],
                                  client_params['username'],
                                  client_params['password'],
                                  port=client_params['port'],
                                  timeout=client_params['timeout'])

    # Check if we should skip SSL Certificate verification.
    verify_ssl = client_params.get('verify_ssl')
    if verify_ssl and not verify_ssl:
        api_client.skip_verify_certificate()

    # Return the client.
    return api_client
