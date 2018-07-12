# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Tecnologías Gallo Rojo.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import open_url, ConnectionError, SSLValidationError

import six
import json
from time import sleep
# import pdb

#############################
# Class
#############################

class IDG_API(object):
    """ Class for managing communication with
        the IBM DataPower Gateway """

    SHORT_DELAY = 3
    MEDIUM_DELAY = 5
    LONG_DELAY = 8

    # REST api management
    # Domains
    URI_DOMAIN_LIST = "/mgmt/domains/config/"
    # Management
    URI_DOMAIN_CONFIG = "/mgmt/config/default/Domain/{0}"
    URI_DOMAIN_STATUS = "/mgmt/status/default/DomainStatus"
    # Actions
    URI_ACTION = "/mgmt/actionqueue/{0}"

    # Errors strings
    ERROR_GET_DOMAIN_LIST = 'Unable to retrieve domain settings'
    ERROR_RETRIEVING_STATUS = 'Retrieving the status of "{0}" over domain "{1}".'
    ERROR_RETRIEVING_RESULT = 'Retrieving the result of "{0}" over domain "{1}".'
    ERROR_ACCEPTING_ACTION = 'Accepting "{0}" over domain "{1}".'
    ERROR_REACH_STATE = 'Unable to reach state "{0}" in domain {1}.'

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

    def api_call(self, uri, **kwargs):
        try:

            url = self.idg_host + uri
            data = None
            try:
                data = kwargs['data']
            except:
                pass

            resp = open_url(url,
                            method=kwargs['method'],
                            headers=self.headers,
                            timeout=self.timeout,
                            url_username=self.url_username,
                            url_password=self.url_password,
                            use_proxy=self.use_proxy,
                            force_basic_auth=self.force_basic_auth,
                            validate_certs=self.validate_certs,
                            http_agent=self.http_agent,
                            data=data)

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

    def wait_for_action_end(self, uri, **kwargs):

        str_results = ['processed', 'completed']
        max_steps = 30
        count = 0
        action_result = ''
        # pdb.set_trace()

        while (action_result not in str_results) and (count < max_steps):
            # Wait to complete
            code, msg, data = self.api_call(uri + '/pending',
                                                method='GET', data=None)
            count += 1
            if code == 200 and msg == 'OK':
                action_result = self.get_operation_status(data['operations'], kwargs['href'])
                if action_result not in str_results: sleep(self.SHORT_DELAY)
            else:
                # Opps can't get status
                self.ansible_module.fail_json(msg=to_native(self.ERROR_RETRIEVING_STATUS % (kwargs['state'], uri.rsplit('/', 1)[-1])))

        if count == max_steps:
            self.ansible_module.fail_json(msg=to_native((self.ERROR_RETRIEVING_STATUS + 'Reached the maximum level of interactions') % (kwargs['state'], uri.rsplit('/', 1)[-1])))
        else:
            return action_result.capitalize()
