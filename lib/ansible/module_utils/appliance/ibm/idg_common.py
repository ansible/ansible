# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Tecnologías Gallo Rojo.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import open_url, ConnectionError, SSLValidationError, url_argument_spec

import six
import json

#############################
# Variables
#############################

#
# API connections
#

# Constants
IMMUTABLE_MESSAGE = 'The current state is consistent with the desired configuration'
ACTIONDELAY = 10 # number of seconds to wait for action apply

BASIC_HEADERS = { "Content-Type": "application/json" }
ANSIBLE_VERSION = '2.7'
BASIC_AUTH_SPEC = True
HTTP_AGENT_SPEC = None

# Socket information
idg_endpoint_spec = url_argument_spec()
idg_endpoint_spec.update(
    timeout = dict(type = 'int', default = 10), # The socket level timeout in seconds
    server = dict(type = 'str', required = True), # Remote IDG will be used.
    server_port = dict(type = 'int', default = 5554), # Remote IDG port be used.
    url_username=dict(required=False, aliases=['user']),
    url_password=dict(required=False, aliases=['password'], no_log=True),
)

#############################
# Functions
#############################

def do_open_url(ansible_module, url, **kwargs):
    try:
        resp = open_url(url,
                        method = kwargs['method'],
                        headers = kwargs['headers'],
                        timeout = kwargs['timeout'],
                        url_username = kwargs['user'],
                        url_password = kwargs['password'],
                        use_proxy = kwargs['use_proxy'],
                        force_basic_auth = BASIC_AUTH_SPEC,
                        validate_certs = kwargs['validate_certs'],
                        http_agent = HTTP_AGENT_SPEC,
                        data = kwargs['data'])
    except HTTPError as e:
        # Get results with code different from 200
        return int(e.getcode()), e.msg, json.loads(e.read())
    except SSLValidationError as e:
        ansible_module.fail_json(msg="Error validating the server's certificate for (%s). %s" % (url, to_native(e)))
    except ConnectionError as e:
        ansible_module.fail_json(msg="Error connecting to (%s). %s" % (url, to_native(e)))
    except Exception as e:
        ansible_module.fail_json(msg="Unknown error for (%s). %s " % (url, to_native(e)))
    else:
        return int(resp.getcode()), resp.msg, json.loads(resp.read())

def parse_to_dict(data, desc, ver):
    # Interpret data as a dictionary
    if isinstance(data, dict):
        return data
    elif data:
        # data is NOT empty
        try:
            # Show warning
            module.deprecate('Supplying `{0}` as a string is deprecated. Please use dict/hash format.'.format(desc), version = ver)
            # Parse key:value,key:value,... string
            return dict(item.split(':', 1) for item in data.split(','))
        except Exception:
            # Can't parse
            module.fail_json(msg='The string representation for the `{0}` requires a key:value,key:value,... syntax to be properly parsed.'.format(desc))
    else:
        # data is empty
        return None

def on_off(arg):
    # Translate boolean to: on, off
    return "on" if arg else "off"

def text_message(arg):
    # If exist the status field brings the status
    if isinstance(arg, six.string_types):
        return arg
    elif isinstance(arg['status'], six.string_types):
        return arg['status']
    else:
        return 'Response with undefined structure'
