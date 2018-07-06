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
# import pdb

#############################
# Variables
#############################

#
# API connections
#

# Constants
IMMUTABLE_MESSAGE = 'The current state is consistent with the desired configuration'
CHECK_MODE_MESSAGE = 'Change was only simulated, due to enabling verification mode'
ACTIONDELAY = 10 # number of seconds to wait for action apply

BASIC_HEADERS = { "Content-Type": "application/json" }
ANSIBLE_VERSION = '2.7'
BASIC_AUTH_SPEC = True
HTTP_AGENT_SPEC = None

# Seed the result
result = dict(
    changed = False,
    name = 'default',
    msg = 'good is coming'
)

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
# Class
#############################

class IDG_API(object):
    """ Class for managing communication with
        the IBM DataPower Gateway """

    SHORT_DELAY = 3
    MEDIUM_DELAY = 5
    LONG_DELAY = 8

    ERROR_GET_DOMAIN_LIST = 'Unable to retrieve domain settings'
    ERROR_RETRIEVING_STATUS = 'Error. Retrieving the status of "%s" over domain "%s".'
    ERROR_RETRIEVING_RESULT = 'Error. Retrieving the result of "%s" over domain "%s".'
    ERROR_ACCEPTING_ACTION = 'Error. Accepting "%s" over domain "%s".'
    ERROR_REACH_STATE = 'Unable to reach state "%s" in domain %s.'

    def __init__(self, **kwargs):
        # Initialize the common variables to all calls
        # Operations variables
        self.ansible_module = kwargs['ansible_module']
        self.idg_host = kwargs['idg_host']
        self.headers = kwargs['headers']
        self.force_basic_auth = kwargs['force_basic_auth']
        self.http_agent = kwargs['http_agent']
        self.timeout = kwargs['timeout']
        self.url_username = kwargs['user']
        self.url_password = kwargs['password']
        self.use_proxy = kwargs['use_proxy']
        self.validate_certs = kwargs['validate_certs']

    @staticmethod
    def get_operation_status(operations, location):
        # If have only one operation
        if isinstance(operations, dict):
            if operations['location'] == location:
                return operations['status']
            else:
                return None
        elif isinstance(operations, list):
            # multiple operations
            op = [o for o in operations if o.get('location') == location]
            if op:
                return op[0]['status']
            else:
                return None
        else:
            # Unknown structure
            return None

    @staticmethod
    def status_text(arg):
        # If exist the status field brings the status
        if isinstance(arg, six.string_types):
            return arg
        elif isinstance(arg['status'], six.string_types):
            return arg['status']
        else:
            return None

    def api_call(self, **kwargs):
        url = self.idg_host + kwargs['uri']

        try:

            resp = open_url(url,
                            method = kwargs['method'],
                            headers = self.headers,
                            timeout = self.timeout,
                            url_username = self.url_username,
                            url_password = self.url_password,
                            use_proxy = self.use_proxy,
                            force_basic_auth = self.force_basic_auth,
                            validate_certs = self.validate_certs,
                            http_agent = self.http_agent,
                            data = kwargs['data'])

        except HTTPError as e:
            # Get results with code different from 200
            return int(e.getcode()), e.msg, json.loads(e.read())
        except SSLValidationError as e:
            self.ansible_module.fail_json(msg="Error validating the server's certificate for (%s). %s" % (url, to_native(e)))
        except ConnectionError as e:
            self.ansible_module.fail_json(msg="Error connecting to (%s). %s" % (url, to_native(e)))
        except Exception as e:
            self.ansible_module.fail_json(msg="Unknown error for (%s). %s " % (url, to_native(e)))
        else:
            return int(resp.getcode()), resp.msg, json.loads(resp.read())

#############################
# Functions
#############################

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
