# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ingate Systems AB
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


try:
    from ingate import ingatesdk
    HAS_INGATESDK = True
except ImportError:
    HAS_INGATESDK = False


def ingate_argument_spec(**kwargs):
    client_options = dict(
        version=dict(choices=['v1'], default='v1'),
        scheme=dict(choices=['http', 'https'], required=True),
        address=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        port=dict(type='int'),
        timeout=dict(type='int'),
        validate_certs=dict(default=True, type='bool', aliases=['verify_ssl']),
    )
    argument_spec = dict(
        client=dict(type='dict', required=True,
                    options=client_options),
    )
    argument_spec.update(kwargs)
    return argument_spec


def ingate_create_client(**kwargs):
    api_client = ingate_create_client_noauth(**kwargs)

    # Authenticate and get hold of a security token.
    api_client.authenticate()

    # Return the client.
    return api_client


def ingate_create_client_noauth(**kwargs):
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
    verify_ssl = client_params.get('validate_certs')
    if not verify_ssl:
        api_client.skip_verify_certificate()

    # Return the client.
    return api_client


def is_ingatesdk_installed(module):
    if not HAS_INGATESDK:
        module.fail_json(msg="The Ingate Python SDK module is required for this module.")
