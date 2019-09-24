# -*- coding: utf-8 -*-

# This code is part of Ansible, but is an independent component

# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.

# Copyright: (c) 2017, Dag Wieers <dag@wieers.com>
# Copyright: (c) 2017, Jacob McGill (@jmcgill298)
# Copyright: (c) 2017, Swetha Chunduri (@schunduri)
# Copyright: (c) 2019, Rob Huelga (@RobW3LGA)
# All rights reserved.

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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import base64
import json
import os
from copy import deepcopy

from ansible.module_utils.parsing.convert_bool import boolean
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_bytes, to_native

# Optional, only used for APIC signature-based authentication
try:
    from OpenSSL.crypto import FILETYPE_PEM, load_privatekey, sign
    HAS_OPENSSL = True
except ImportError:
    HAS_OPENSSL = False

# Optional, only used for XML payload
try:
    import lxml.etree
    HAS_LXML_ETREE = True
except ImportError:
    HAS_LXML_ETREE = False

# Optional, only used for XML payload
try:
    from xmljson import cobra
    HAS_XMLJSON_COBRA = True
except ImportError:
    HAS_XMLJSON_COBRA = False


def aci_argument_spec():
    return dict(
        host=dict(type='str', required=True, aliases=['hostname']),
        port=dict(type='int', required=False),
        username=dict(type='str', default='admin', aliases=['user']),
        password=dict(type='str', no_log=True),
        private_key=dict(type='str', aliases=['cert_key'], no_log=True),  # Beware, this is not the same as client_key !
        certificate_name=dict(type='str', aliases=['cert_name']),  # Beware, this is not the same as client_cert !
        output_level=dict(type='str', default='normal', choices=['debug', 'info', 'normal']),
        timeout=dict(type='int', default=30),
        use_proxy=dict(type='bool', default=True),
        use_ssl=dict(type='bool', default=True),
        validate_certs=dict(type='bool', default=True),
    )


class ACIModule(object):

    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.result = dict(changed=False)
        self.headers = dict()
        self.child_classes = set()

        # error output
        self.error = dict(code=None, text=None)

        # normal output
        self.existing = None

        # info output
        self.config = dict()
        self.original = None
        self.proposed = dict()

        # debug output
        self.filter_string = ''
        self.method = None
        self.path = None
        self.response = None
        self.status = None
        self.url = None

        # aci_rest output
        self.imdata = None
        self.totalCount = None

        # Ensure protocol is set
        self.define_protocol()

        if self.module._debug:
            self.module.warn('Enable debug output because ANSIBLE_DEBUG was set.')
            self.params['output_level'] = 'debug'

        if self.params['private_key']:
            # Perform signature-based authentication, no need to log on separately
            if not HAS_OPENSSL:
                self.module.fail_json(msg='Cannot use signature-based authentication because pyopenssl is not available')
            elif self.params['password'] is not None:
                self.module.warn("When doing ACI signatured-based authentication, providing parameter 'password' is not required")
        elif self.params['password']:
            # Perform password-based authentication, log on using password
            self.login()
        else:
            self.module.fail_json(msg="Either parameter 'password' or 'private_key' is required for authentication")

    def boolean(self, value, true='yes', false='no'):
        ''' Return an acceptable value back '''

        # When we expect value is of type=bool
        if value is None:
            return None
        elif value is True:
            return true
        elif value is False:
            return false

        # If all else fails, escalate back to user
        self.module.fail_json(msg="Boolean value '%s' is an invalid ACI boolean value.")

    def iso8601_format(self, dt):
        ''' Return an ACI-compatible ISO8601 formatted time: 2123-12-12T00:00:00.000+00:00 '''
        try:
            return dt.isoformat(timespec='milliseconds')
        except Exception:
            tz = dt.strftime('%z')
            return '%s.%03d%s:%s' % (dt.strftime('%Y-%m-%dT%H:%M:%S'), dt.microsecond / 1000, tz[:3], tz[3:])

    def define_protocol(self):
        ''' Set protocol based on use_ssl parameter '''

        # Set protocol for further use
        self.params['protocol'] = 'https' if self.params.get('use_ssl', True) else 'http'

    def define_method(self):
        ''' Set method based on state parameter '''

        # Set method for further use
        state_map = dict(absent='delete', present='post', query='get')
        self.params['method'] = state_map[self.params['state']]

    def login(self):
        ''' Log in to APIC '''

        # Perform login request
        if 'port' in self.params and self.params['port'] is not None:
            url = '%(protocol)s://%(host)s:%(port)s/api/aaaLogin.json' % self.params
        else:
            url = '%(protocol)s://%(host)s/api/aaaLogin.json' % self.params
        payload = {'aaaUser': {'attributes': {'name': self.params['username'], 'pwd': self.params['password']}}}
        resp, auth = fetch_url(self.module, url,
                               data=json.dumps(payload),
                               method='POST',
                               timeout=self.params['timeout'],
                               use_proxy=self.params['use_proxy'])

        # Handle APIC response
        if auth['status'] != 200:
            self.response = auth['msg']
            self.status = auth['status']
            try:
                # APIC error
                self.response_json(auth['body'])
                self.fail_json(msg='Authentication failed: %(code)s %(text)s' % self.error)
            except KeyError:
                # Connection error
                self.fail_json(msg='Connection failed for %(url)s. %(msg)s' % auth)

        # Retain cookie for later use
        self.headers['Cookie'] = resp.headers['Set-Cookie']

    def cert_auth(self, path=None, payload='', method=None):
        ''' Perform APIC signature-based authentication, not the expected SSL client certificate authentication. '''

        if method is None:
            method = self.params['method'].upper()

        # NOTE: ACI documentation incorrectly uses complete URL
        if path is None:
            path = self.path
        path = '/' + path.lstrip('/')

        if payload is None:
            payload = ''

        # Check if we got a private key. This allows the use of vaulting the private key.
        if self.params['private_key'].startswith('-----BEGIN PRIVATE KEY-----'):
            try:
                sig_key = load_privatekey(FILETYPE_PEM, self.params['private_key'])
            except Exception:
                self.module.fail_json(msg="Cannot load provided 'private_key' parameter.")
            # Use the username as the certificate_name value
            if self.params['certificate_name'] is None:
                self.params['certificate_name'] = self.params['username']
        elif self.params['private_key'].startswith('-----BEGIN CERTIFICATE-----'):
            self.module.fail_json(msg="Provided 'private_key' parameter value appears to be a certificate. Please correct.")
        else:
            # If we got a private key file, read from this file.
            # NOTE: Avoid exposing any other credential as a filename in output...
            if not os.path.exists(self.params['private_key']):
                self.module.fail_json(msg="The provided private key file does not appear to exist. Is it a filename?")
            try:
                with open(self.params['private_key'], 'r') as fh:
                    private_key_content = fh.read()
            except Exception:
                self.module.fail_json(msg="Cannot open private key file '%s'." % self.params['private_key'])
            if private_key_content.startswith('-----BEGIN PRIVATE KEY-----'):
                try:
                    sig_key = load_privatekey(FILETYPE_PEM, private_key_content)
                except Exception:
                    self.module.fail_json(msg="Cannot load private key file '%s'." % self.params['private_key'])
                # Use the private key basename (without extension) as certificate_name
                if self.params['certificate_name'] is None:
                    self.params['certificate_name'] = os.path.basename(os.path.splitext(self.params['private_key'])[0])
            elif private_key_content.startswith('-----BEGIN CERTIFICATE-----'):
                self.module.fail_json(msg="Provided private key file %s appears to be a certificate. Please correct." % self.params['private_key'])
            else:
                self.module.fail_json(msg="Provided private key file '%s' does not appear to be a private key. Please correct." % self.params['private_key'])

        # NOTE: ACI documentation incorrectly adds a space between method and path
        sig_request = method + path + payload
        sig_signature = base64.b64encode(sign(sig_key, sig_request, 'sha256'))
        sig_dn = 'uni/userext/user-%s/usercert-%s' % (self.params['username'], self.params['certificate_name'])
        self.headers['Cookie'] = 'APIC-Certificate-Algorithm=v1.0; ' +\
                                 'APIC-Certificate-DN=%s; ' % sig_dn +\
                                 'APIC-Certificate-Fingerprint=fingerprint; ' +\
                                 'APIC-Request-Signature=%s' % to_native(sig_signature)

    def response_json(self, rawoutput):
        ''' Handle APIC JSON response output '''
        try:
            jsondata = json.loads(rawoutput)
        except Exception as e:
            # Expose RAW output for troubleshooting
            self.error = dict(code=-1, text="Unable to parse output as JSON, see 'raw' output. %s" % e)
            self.result['raw'] = rawoutput
            return

        # Extract JSON API output
        try:
            self.imdata = jsondata['imdata']
        except KeyError:
            self.imdata = dict()
        self.totalCount = int(jsondata['totalCount'])

        # Handle possible APIC error information
        self.response_error()

    def response_xml(self, rawoutput):
        ''' Handle APIC XML response output '''

        # NOTE: The XML-to-JSON conversion is using the "Cobra" convention
        try:
            xml = lxml.etree.fromstring(to_bytes(rawoutput))
            xmldata = cobra.data(xml)
        except Exception as e:
            # Expose RAW output for troubleshooting
            self.error = dict(code=-1, text="Unable to parse output as XML, see 'raw' output. %s" % e)
            self.result['raw'] = rawoutput
            return

        # Reformat as ACI does for JSON API output
        try:
            self.imdata = xmldata['imdata']['children']
        except KeyError:
            self.imdata = dict()
        self.totalCount = int(xmldata['imdata']['attributes']['totalCount'])

        # Handle possible APIC error information
        self.response_error()

    def response_error(self):
        ''' Set error information when found '''

        # Handle possible APIC error information
        if self.totalCount != '0':
            try:
                self.error = self.imdata[0]['error']['attributes']
            except (KeyError, IndexError):
                pass

    def request(self, path, payload=None):
        ''' Perform a REST request '''

        # Ensure method is set (only do this once)
        self.define_method()
        self.path = path

        if 'port' in self.params and self.params['port'] is not None:
            self.url = '%(protocol)s://%(host)s:%(port)s/' % self.params + path.lstrip('/')
        else:
            self.url = '%(protocol)s://%(host)s/' % self.params + path.lstrip('/')

        # Sign and encode request as to APIC's wishes
        if self.params['private_key']:
            self.cert_auth(path=path, payload=payload)

        # Perform request
        resp, info = fetch_url(self.module, self.url,
                               data=payload,
                               headers=self.headers,
                               method=self.params['method'].upper(),
                               timeout=self.params['timeout'],
                               use_proxy=self.params['use_proxy'])

        self.response = info['msg']
        self.status = info['status']

        # Handle APIC response
        if info['status'] != 200:
            try:
                # APIC error
                self.response_json(info['body'])
                self.fail_json(msg='APIC Error %(code)s: %(text)s' % self.error)
            except KeyError:
                # Connection error
                self.fail_json(msg='Connection failed for %(url)s. %(msg)s' % info)

        self.response_json(resp.read())

    def query(self, path):
        ''' Perform a query with no payload '''

        self.path = path

        if 'port' in self.params and self.params['port'] is not None:
            self.url = '%(protocol)s://%(host)s:%(port)s/' % self.params + path.lstrip('/')
        else:
            self.url = '%(protocol)s://%(host)s/' % self.params + path.lstrip('/')

        # Sign and encode request as to APIC's wishes
        if self.params['private_key']:
            self.cert_auth(path=path, method='GET')

        # Perform request
        resp, query = fetch_url(self.module, self.url,
                                data=None,
                                headers=self.headers,
                                method='GET',
                                timeout=self.params['timeout'],
                                use_proxy=self.params['use_proxy'])

        # Handle APIC response
        if query['status'] != 200:
            self.response = query['msg']
            self.status = query['status']
            try:
                # APIC error
                self.response_json(query['body'])
                self.fail_json(msg='APIC Error %(code)s: %(text)s' % self.error)
            except KeyError:
                # Connection error
                self.fail_json(msg='Connection failed for %(url)s. %(msg)s' % query)

        query = json.loads(resp.read())

        return json.dumps(query['imdata'], sort_keys=True, indent=2) + '\n'

    def request_diff(self, path, payload=None):
        ''' Perform a request, including a proper diff output '''
        self.result['diff'] = dict()
        self.result['diff']['before'] = self.query(path)
        self.request(path, payload=payload)
        # TODO: Check if we can use the request output for the 'after' diff
        self.result['diff']['after'] = self.query(path)

        if self.result['diff']['before'] != self.result['diff']['after']:
            self.result['changed'] = True

    # TODO: This could be designed to update existing keys
    def update_qs(self, params):
        ''' Append key-value pairs to self.filter_string '''
        accepted_params = dict((k, v) for (k, v) in params.items() if v is not None)
        if accepted_params:
            if self.filter_string:
                self.filter_string += '&'
            else:
                self.filter_string = '?'
            self.filter_string += '&'.join(['%s=%s' % (k, v) for (k, v) in accepted_params.items()])

    # TODO: This could be designed to accept multiple obj_classes and keys
    def build_filter(self, obj_class, params):
        ''' Build an APIC filter based on obj_class and key-value pairs '''
        accepted_params = dict((k, v) for (k, v) in params.items() if v is not None)
        if len(accepted_params) == 1:
            return ','.join('eq({0}.{1},"{2}")'.format(obj_class, k, v) for (k, v) in accepted_params.items())
        elif len(accepted_params) > 1:
            return 'and(' + ','.join(['eq({0}.{1},"{2}")'.format(obj_class, k, v) for (k, v) in accepted_params.items()]) + ')'

    def _deep_url_path_builder(self, obj):
        target_class = obj['target_class']
        target_filter = obj['target_filter']
        subtree_class = obj['subtree_class']
        subtree_filter = obj['subtree_filter']
        object_rn = obj['object_rn']
        mo = obj['module_object']
        add_subtree_filter = obj['add_subtree_filter']
        add_target_filter = obj['add_target_filter']

        if self.module.params['state'] in ('absent', 'present') and mo is not None:
            self.path = 'api/mo/uni/{0}.json'.format(object_rn)
            self.update_qs({'rsp-prop-include': 'config-only'})

        else:
            # State is 'query'
            if object_rn is not None:
                # Query for a specific object in the module's class
                self.path = 'api/mo/uni/{0}.json'.format(object_rn)
            else:
                self.path = 'api/class/{0}.json'.format(target_class)

            if add_target_filter:
                self.update_qs(
                    {'query-target-filter': self.build_filter(target_class, target_filter)})

            if add_subtree_filter:
                self.update_qs(
                    {'rsp-subtree-filter': self.build_filter(subtree_class, subtree_filter)})

        if 'port' in self.params and self.params['port'] is not None:
            self.url = '{protocol}://{host}:{port}/{path}'.format(
                path=self.path, **self.module.params)

        else:
            self.url = '{protocol}://{host}/{path}'.format(
                path=self.path, **self.module.params)

        if self.child_classes:
            self.update_qs(
                {'rsp-subtree': 'full', 'rsp-subtree-class': ','.join(sorted(self.child_classes))})

    def _deep_url_parent_object(self, parent_objects, parent_class):

        for parent_object in parent_objects:
            if parent_object['aci_class'] is parent_class:
                return parent_object

        return None

    def construct_deep_url(self, target_object, parent_objects=None, child_classes=None):
        """
        This method is used to retrieve the appropriate URL path and filter_string to make the request to the APIC.

        :param target_object: The target class dictionary containing parent_class, aci_class, aci_rn, target_filter, and module_object keys.
        :param parent_objects: The parent class list of dictionaries containing parent_class, aci_class, aci_rn, target_filter, and module_object keys.
        :param child_classes: The list of child classes that the module supports along with the object.
        :type target_object: dict
        :type parent_objects: list[dict]
        :type child_classes: list[string]
        :return: The path and filter_string needed to build the full URL.
        """

        self.filter_string = ''
        rn_builder = None
        subtree_classes = None
        add_subtree_filter = False
        add_target_filter = False
        has_target_query = False
        has_target_query_compare = False
        has_target_query_difference = False
        has_target_query_called = False

        if child_classes is None:
            self.child_classes = set()
        else:
            self.child_classes = set(child_classes)

        target_parent_class = target_object['parent_class']
        target_class = target_object['aci_class']
        target_rn = target_object['aci_rn']
        target_filter = target_object['target_filter']
        target_module_object = target_object['module_object']

        url_path_object = dict(
            target_class=target_class,
            target_filter=target_filter,
            subtree_class=target_class,
            subtree_filter=target_filter,
            module_object=target_module_object
        )

        if target_module_object is not None:
            rn_builder = target_rn
        else:
            has_target_query = True
            has_target_query_compare = True

        if parent_objects is not None:
            current_parent_class = target_parent_class
            has_parent_query_compare = False
            has_parent_query_difference = False
            is_first_parent = True
            is_single_parent = None
            search_classes = set()

            while current_parent_class != 'uni':
                parent_object = self._deep_url_parent_object(
                    parent_objects=parent_objects, parent_class=current_parent_class)

                if parent_object is not None:
                    parent_parent_class = parent_object['parent_class']
                    parent_class = parent_object['aci_class']
                    parent_rn = parent_object['aci_rn']
                    parent_filter = parent_object['target_filter']
                    parent_module_object = parent_object['module_object']

                    if is_first_parent:
                        is_single_parent = True
                    else:
                        is_single_parent = False
                    is_first_parent = False

                    if parent_parent_class != 'uni':
                        search_classes.add(parent_class)

                    if parent_module_object is not None:
                        if rn_builder is not None:
                            rn_builder = '{0}/{1}'.format(parent_rn,
                                                          rn_builder)
                        else:
                            rn_builder = parent_rn

                        url_path_object['target_class'] = parent_class
                        url_path_object['target_filter'] = parent_filter

                        has_target_query = False
                    else:
                        rn_builder = None
                        subtree_classes = search_classes

                        has_target_query = True
                        if is_single_parent:
                            has_parent_query_compare = True

                    current_parent_class = parent_parent_class
                else:
                    raise ValueError("Reference error for parent_class '{0}'. Each parent_class must reference a valid object".format(current_parent_class))

                if not has_target_query_difference and not has_target_query_called:
                    if has_target_query is not has_target_query_compare:
                        has_target_query_difference = True
                else:
                    if not has_parent_query_difference and has_target_query is not has_parent_query_compare:
                        has_parent_query_difference = True
                has_target_query_called = True

            if not has_parent_query_difference and has_parent_query_compare and target_module_object is not None:
                add_target_filter = True

            elif has_parent_query_difference and target_module_object is not None:
                add_subtree_filter = True
                self.child_classes.add(target_class)

                if has_target_query:
                    add_target_filter = True

            elif has_parent_query_difference and not has_target_query and target_module_object is None:
                self.child_classes.add(target_class)
                self.child_classes.update(subtree_classes)

            elif not has_parent_query_difference and not has_target_query and target_module_object is None:
                self.child_classes.add(target_class)

            elif not has_target_query and is_single_parent and target_module_object is None:
                self.child_classes.add(target_class)

        url_path_object['object_rn'] = rn_builder
        url_path_object['add_subtree_filter'] = add_subtree_filter
        url_path_object['add_target_filter'] = add_target_filter

        self._deep_url_path_builder(url_path_object)

    def construct_url(self, root_class, subclass_1=None, subclass_2=None, subclass_3=None, child_classes=None):
        """
        This method is used to retrieve the appropriate URL path and filter_string to make the request to the APIC.

        :param root_class: The top-level class dictionary containing aci_class, aci_rn, target_filter, and module_object keys.
        :param sublass_1: The second-level class dictionary containing aci_class, aci_rn, target_filter, and module_object keys.
        :param sublass_2: The third-level class dictionary containing aci_class, aci_rn, target_filter, and module_object keys.
        :param sublass_3: The fourth-level class dictionary containing aci_class, aci_rn, target_filter, and module_object keys.
        :param child_classes: The list of child classes that the module supports along with the object.
        :type root_class: dict
        :type subclass_1: dict
        :type subclass_2: dict
        :type subclass_3: dict
        :type child_classes: list
        :return: The path and filter_string needed to build the full URL.
        """
        self.filter_string = ''

        if child_classes is None:
            self.child_classes = set()
        else:
            self.child_classes = set(child_classes)

        if subclass_3 is not None:
            self._construct_url_4(root_class, subclass_1, subclass_2, subclass_3)
        elif subclass_2 is not None:
            self._construct_url_3(root_class, subclass_1, subclass_2)
        elif subclass_1 is not None:
            self._construct_url_2(root_class, subclass_1)
        else:
            self._construct_url_1(root_class)

        if 'port' in self.params and self.params['port'] is not None:
            self.url = '{protocol}://{host}:{port}/{path}'.format(path=self.path, **self.module.params)
        else:
            self.url = '{protocol}://{host}/{path}'.format(path=self.path, **self.module.params)

        if self.child_classes:
            # Append child_classes to filter_string if filter string is empty
            self.update_qs({'rsp-subtree': 'full', 'rsp-subtree-class': ','.join(sorted(self.child_classes))})

    def _construct_url_1(self, obj):
        """
        This method is used by construct_url when the object is the top-level class.
        """
        obj_class = obj['aci_class']
        obj_rn = obj['aci_rn']
        obj_filter = obj['target_filter']
        mo = obj['module_object']

        if self.module.params['state'] in ('absent', 'present'):
            # State is absent or present
            self.path = 'api/mo/uni/{0}.json'.format(obj_rn)
            self.update_qs({'rsp-prop-include': 'config-only'})
        elif mo is None:
            # Query for all objects of the module's class (filter by properties)
            self.path = 'api/class/{0}.json'.format(obj_class)
            self.update_qs({'query-target-filter': self.build_filter(obj_class, obj_filter)})
        else:
            # Query for a specific object in the module's class
            self.path = 'api/mo/uni/{0}.json'.format(obj_rn)

    def _construct_url_2(self, parent, obj):
        """
        This method is used by construct_url when the object is the second-level class.
        """
        parent_class = parent['aci_class']
        parent_rn = parent['aci_rn']
        parent_filter = parent['target_filter']
        parent_obj = parent['module_object']
        obj_class = obj['aci_class']
        obj_rn = obj['aci_rn']
        obj_filter = obj['target_filter']
        mo = obj['module_object']

        if self.module.params['state'] in ('absent', 'present'):
            # State is absent or present
            self.path = 'api/mo/uni/{0}/{1}.json'.format(parent_rn, obj_rn)
            self.update_qs({'rsp-prop-include': 'config-only'})
        elif parent_obj is None and mo is None:
            # Query for all objects of the module's class
            self.path = 'api/class/{0}.json'.format(obj_class)
            self.update_qs({'query-target-filter': self.build_filter(obj_class, obj_filter)})
        elif parent_obj is None:  # mo is known
            # Query for all objects of the module's class that match the provided ID value
            self.path = 'api/class/{0}.json'.format(obj_class)
            self.update_qs({'query-target-filter': self.build_filter(obj_class, obj_filter)})
        elif mo is None:  # parent_obj is known
            # Query for all object's of the module's class that belong to a specific parent object
            self.child_classes.add(obj_class)
            self.path = 'api/mo/uni/{0}.json'.format(parent_rn)
        else:
            # Query for specific object in the module's class
            self.path = 'api/mo/uni/{0}/{1}.json'.format(parent_rn, obj_rn)

    def _construct_url_3(self, root, parent, obj):
        """
        This method is used by construct_url when the object is the third-level class.
        """
        root_class = root['aci_class']
        root_rn = root['aci_rn']
        root_filter = root['target_filter']
        root_obj = root['module_object']
        parent_class = parent['aci_class']
        parent_rn = parent['aci_rn']
        parent_filter = parent['target_filter']
        parent_obj = parent['module_object']
        obj_class = obj['aci_class']
        obj_rn = obj['aci_rn']
        obj_filter = obj['target_filter']
        mo = obj['module_object']

        if self.module.params['state'] in ('absent', 'present'):
            # State is absent or present
            self.path = 'api/mo/uni/{0}/{1}/{2}.json'.format(root_rn, parent_rn, obj_rn)
            self.update_qs({'rsp-prop-include': 'config-only'})
        elif root_obj is None and parent_obj is None and mo is None:
            # Query for all objects of the module's class
            self.path = 'api/class/{0}.json'.format(obj_class)
            self.update_qs({'query-target-filter': self.build_filter(obj_class, obj_filter)})
        elif root_obj is None and parent_obj is None:  # mo is known
            # Query for all objects of the module's class matching the provided ID value of the object
            self.path = 'api/class/{0}.json'.format(obj_class)
            self.update_qs({'query-target-filter': self.build_filter(obj_class, obj_filter)})
        elif root_obj is None and mo is None:  # parent_obj is known
            # Query for all objects of the module's class that belong to any parent class
            # matching the provided ID value for the parent object
            self.child_classes.add(obj_class)
            self.path = 'api/class/{0}.json'.format(parent_class)
            self.update_qs({'query-target-filter': self.build_filter(parent_class, parent_filter)})
        elif parent_obj is None and mo is None:  # root_obj is known
            # Query for all objects of the module's class that belong to a specific root object
            self.child_classes.update([parent_class, obj_class])
            self.path = 'api/mo/uni/{0}.json'.format(root_rn)
            # NOTE: No need to select by root_filter
            # self.update_qs({'query-target-filter': self.build_filter(root_class, root_filter)})
        elif root_obj is None:  # mo and parent_obj are known
            # Query for all objects of the module's class that belong to any parent class
            # matching the provided ID values for both object and parent object
            self.child_classes.add(obj_class)
            self.path = 'api/class/{0}.json'.format(parent_class)
            self.update_qs({'query-target-filter': self.build_filter(parent_class, parent_filter)})
            self.update_qs({'rsp-subtree-filter': self.build_filter(obj_class, obj_filter)})
        elif parent_obj is None:  # mo and root_obj are known
            # Query for all objects of the module's class that match the provided ID value and belong to a specific root object
            self.child_classes.add(obj_class)
            self.path = 'api/mo/uni/{0}.json'.format(root_rn)
            # NOTE: No need to select by root_filter
            # self.update_qs({'query-target-filter': self.build_filter(root_class, root_filter)})
            # TODO: Filter by parent_filter and obj_filter
            self.update_qs({'rsp-subtree-filter': self.build_filter(obj_class, obj_filter)})
        elif mo is None:  # root_obj and parent_obj are known
            # Query for all objects of the module's class that belong to a specific parent object
            self.child_classes.add(obj_class)
            self.path = 'api/mo/uni/{0}/{1}.json'.format(root_rn, parent_rn)
            # NOTE: No need to select by parent_filter
            # self.update_qs({'query-target-filter': self.build_filter(parent_class, parent_filter)})
        else:
            # Query for a specific object of the module's class
            self.path = 'api/mo/uni/{0}/{1}/{2}.json'.format(root_rn, parent_rn, obj_rn)

    def _construct_url_4(self, root, sec, parent, obj):
        """
        This method is used by construct_url when the object is the fourth-level class.
        """
        root_class = root['aci_class']
        root_rn = root['aci_rn']
        root_filter = root['target_filter']
        root_obj = root['module_object']
        sec_class = sec['aci_class']
        sec_rn = sec['aci_rn']
        sec_filter = sec['target_filter']
        sec_obj = sec['module_object']
        parent_class = parent['aci_class']
        parent_rn = parent['aci_rn']
        parent_filter = parent['target_filter']
        parent_obj = parent['module_object']
        obj_class = obj['aci_class']
        obj_rn = obj['aci_rn']
        obj_filter = obj['target_filter']
        mo = obj['module_object']

        if self.child_classes is None:
            self.child_classes = [obj_class]

        if self.module.params['state'] in ('absent', 'present'):
            # State is absent or present
            self.path = 'api/mo/uni/{0}/{1}/{2}/{3}.json'.format(root_rn, sec_rn, parent_rn, obj_rn)
            self.update_qs({'rsp-prop-include': 'config-only'})
        # TODO: Add all missing cases
        elif root_obj is None:
            self.child_classes.add(obj_class)
            self.path = 'api/class/{0}.json'.format(obj_class)
            self.update_qs({'query-target-filter': self.build_filter(obj_class, obj_filter)})
        elif sec_obj is None:
            self.child_classes.add(obj_class)
            self.path = 'api/mo/uni/{0}.json'.format(root_rn)
            # NOTE: No need to select by root_filter
            # self.update_qs({'query-target-filter': self.build_filter(root_class, root_filter)})
            # TODO: Filter by sec_filter, parent and obj_filter
            self.update_qs({'rsp-subtree-filter': self.build_filter(obj_class, obj_filter)})
        elif parent_obj is None:
            self.child_classes.add(obj_class)
            self.path = 'api/mo/uni/{0}/{1}.json'.format(root_rn, sec_rn)
            # NOTE: No need to select by sec_filter
            # self.update_qs({'query-target-filter': self.build_filter(sec_class, sec_filter)})
            # TODO: Filter by parent_filter and obj_filter
            self.update_qs({'rsp-subtree-filter': self.build_filter(obj_class, obj_filter)})
        elif mo is None:
            self.child_classes.add(obj_class)
            self.path = 'api/mo/uni/{0}/{1}/{2}.json'.format(root_rn, sec_rn, parent_rn)
            # NOTE: No need to select by parent_filter
            # self.update_qs({'query-target-filter': self.build_filter(parent_class, parent_filter)})
        else:
            # Query for a specific object of the module's class
            self.path = 'api/mo/uni/{0}/{1}/{2}/{3}.json'.format(root_rn, sec_rn, parent_rn, obj_rn)

    def delete_config(self):
        """
        This method is used to handle the logic when the modules state is equal to absent. The method only pushes a change if
        the object exists, and if check_mode is False. A successful change will mark the module as changed.
        """
        self.proposed = dict()

        if not self.existing:
            return

        elif not self.module.check_mode:
            # Sign and encode request as to APIC's wishes
            if self.params['private_key']:
                self.cert_auth(method='DELETE')

            resp, info = fetch_url(self.module, self.url,
                                   headers=self.headers,
                                   method='DELETE',
                                   timeout=self.params['timeout'],
                                   use_proxy=self.params['use_proxy'])

            self.response = info['msg']
            self.status = info['status']
            self.method = 'DELETE'

            # Handle APIC response
            if info['status'] == 200:
                self.result['changed'] = True
                self.response_json(resp.read())
            else:
                try:
                    # APIC error
                    self.response_json(info['body'])
                    self.fail_json(msg='APIC Error %(code)s: %(text)s' % self.error)
                except KeyError:
                    # Connection error
                    self.fail_json(msg='Connection failed for %(url)s. %(msg)s' % info)
        else:
            self.result['changed'] = True
            self.method = 'DELETE'

    def get_diff(self, aci_class):
        """
        This method is used to get the difference between the proposed and existing configurations. Each module
        should call the get_existing method before this method, and add the proposed config to the module results
        using the module's config parameters. The new config will added to the self.result dictionary.

        :param aci_class: Type str.
                          This is the root dictionary key for the MO's configuration body, or the ACI class of the MO.
        """
        proposed_config = self.proposed[aci_class]['attributes']
        if self.existing:
            existing_config = self.existing[0][aci_class]['attributes']
            config = {}

            # values are strings, so any diff between proposed and existing can be a straight replace
            for key, value in proposed_config.items():
                existing_field = existing_config.get(key)
                if value != existing_field:
                    config[key] = value

            # add name back to config only if the configs do not match
            if config:
                # TODO: If URLs are built with the object's name, then we should be able to leave off adding the name back
                # config["name"] = proposed_config["name"]
                config = {aci_class: {'attributes': config}}

            # check for updates to child configs and update new config dictionary
            children = self.get_diff_children(aci_class)
            if children and config:
                config[aci_class].update({'children': children})
            elif children:
                config = {aci_class: {'attributes': {}, 'children': children}}

        else:
            config = self.proposed

        self.config = config

    @staticmethod
    def get_diff_child(child_class, proposed_child, existing_child):
        """
        This method is used to get the difference between a proposed and existing child configs. The get_nested_config()
        method should be used to return the proposed and existing config portions of child.

        :param child_class: Type str.
                            The root class (dict key) for the child dictionary.
        :param proposed_child: Type dict.
                               The config portion of the proposed child dictionary.
        :param existing_child: Type dict.
                               The config portion of the existing child dictionary.
        :return: The child config with only values that are updated. If the proposed dictionary has no updates to make
                 to what exists on the APIC, then None is returned.
        """
        update_config = {child_class: {'attributes': {}}}
        for key, value in proposed_child.items():
            existing_field = existing_child.get(key)
            if value != existing_field:
                update_config[child_class]['attributes'][key] = value

        if not update_config[child_class]['attributes']:
            return None

        return update_config

    def get_diff_children(self, aci_class):
        """
        This method is used to retrieve the updated child configs by comparing the proposed children configs
        agains the objects existing children configs.

        :param aci_class: Type str.
                          This is the root dictionary key for the MO's configuration body, or the ACI class of the MO.
        :return: The list of updated child config dictionaries. None is returned if there are no changes to the child
                 configurations.
        """
        proposed_children = self.proposed[aci_class].get('children')
        if proposed_children:
            child_updates = []
            existing_children = self.existing[0][aci_class].get('children', [])

            # Loop through proposed child configs and compare against existing child configuration
            for child in proposed_children:
                child_class, proposed_child, existing_child = self.get_nested_config(child, existing_children)

                if existing_child is None:
                    child_update = child
                else:
                    child_update = self.get_diff_child(child_class, proposed_child, existing_child)

                # Update list of updated child configs only if the child config is different than what exists
                if child_update:
                    child_updates.append(child_update)
        else:
            return None

        return child_updates

    def get_existing(self):
        """
        This method is used to get the existing object(s) based on the path specified in the module. Each module should
        build the URL so that if the object's name is supplied, then it will retrieve the configuration for that particular
        object, but if no name is supplied, then it will retrieve all MOs for the class. Following this method will ensure
        that this method can be used to supply the existing configuration when using the get_diff method. The response, status,
        and existing configuration will be added to the self.result dictionary.
        """
        uri = self.url + self.filter_string

        # Sign and encode request as to APIC's wishes
        if self.params['private_key']:
            self.cert_auth(path=self.path + self.filter_string, method='GET')

        resp, info = fetch_url(self.module, uri,
                               headers=self.headers,
                               method='GET',
                               timeout=self.params['timeout'],
                               use_proxy=self.params['use_proxy'])
        self.response = info['msg']
        self.status = info['status']
        self.method = 'GET'

        # Handle APIC response
        if info['status'] == 200:
            self.existing = json.loads(resp.read())['imdata']
        else:
            try:
                # APIC error
                self.response_json(info['body'])
                self.fail_json(msg='APIC Error %(code)s: %(text)s' % self.error)
            except KeyError:
                # Connection error
                self.fail_json(msg='Connection failed for %(url)s. %(msg)s' % info)

    @staticmethod
    def get_nested_config(proposed_child, existing_children):
        """
        This method is used for stiping off the outer layers of the child dictionaries so only the configuration
        key, value pairs are returned.

        :param proposed_child: Type dict.
                               The dictionary that represents the child config.
        :param existing_children: Type list.
                                  The list of existing child config dictionaries.
        :return: The child's class as str (root config dict key), the child's proposed config dict, and the child's
                 existing configuration dict.
        """
        for key in proposed_child.keys():
            child_class = key
            proposed_config = proposed_child[key]['attributes']
            existing_config = None

            # FIXME: Design causes issues for repeated child_classes
            # get existing dictionary from the list of existing to use for comparison
            for child in existing_children:
                if child.get(child_class):
                    existing_config = child[key]['attributes']
                    # NOTE: This is an ugly fix
                    # Return the one that is a subset match
                    if set(proposed_config.items()).issubset(set(existing_config.items())):
                        break

        return child_class, proposed_config, existing_config

    def payload(self, aci_class, class_config, child_configs=None):
        """
        This method is used to dynamically build the proposed configuration dictionary from the config related parameters
        passed into the module. All values that were not passed values from the playbook task will be removed so as to not
        inadvertently change configurations.

        :param aci_class: Type str
                          This is the root dictionary key for the MO's configuration body, or the ACI class of the MO.
        :param class_config: Type dict
                             This is the configuration of the MO using the dictionary keys expected by the API
        :param child_configs: Type list
                              This is a list of child dictionaries associated with the MOs config. The list should only
                              include child objects that are used to associate two MOs together. Children that represent
                              MOs should have their own module.
        """
        proposed = dict((k, str(v)) for k, v in class_config.items() if v is not None)
        self.proposed = {aci_class: {'attributes': proposed}}

        # add child objects to proposed
        if child_configs:
            children = []
            for child in child_configs:
                child_copy = deepcopy(child)
                has_value = False
                for root_key in child_copy.keys():
                    for final_keys, values in child_copy[root_key]['attributes'].items():
                        if values is None:
                            child[root_key]['attributes'].pop(final_keys)
                        else:
                            child[root_key]['attributes'][final_keys] = str(values)
                            has_value = True
                if has_value:
                    children.append(child)

            if children:
                self.proposed[aci_class].update(dict(children=children))

    def post_config(self):
        """
        This method is used to handle the logic when the modules state is equal to present. The method only pushes a change if
        the object has differences than what exists on the APIC, and if check_mode is False. A successful change will mark the
        module as changed.
        """
        if not self.config:
            return
        elif not self.module.check_mode:
            # Sign and encode request as to APIC's wishes
            if self.params['private_key']:
                self.cert_auth(method='POST', payload=json.dumps(self.config))

            resp, info = fetch_url(self.module, self.url,
                                   data=json.dumps(self.config),
                                   headers=self.headers,
                                   method='POST',
                                   timeout=self.params['timeout'],
                                   use_proxy=self.params['use_proxy'])

            self.response = info['msg']
            self.status = info['status']
            self.method = 'POST'

            # Handle APIC response
            if info['status'] == 200:
                self.result['changed'] = True
                self.response_json(resp.read())
            else:
                try:
                    # APIC error
                    self.response_json(info['body'])
                    self.fail_json(msg='APIC Error %(code)s: %(text)s' % self.error)
                except KeyError:
                    # Connection error
                    self.fail_json(msg='Connection failed for %(url)s. %(msg)s' % info)
        else:
            self.result['changed'] = True
            self.method = 'POST'

    def exit_json(self, **kwargs):

        if 'state' in self.params:
            if self.params['state'] in ('absent', 'present'):
                if self.params['output_level'] in ('debug', 'info'):
                    self.result['previous'] = self.existing

        # Return the gory details when we need it
        if self.params['output_level'] == 'debug':
            if 'state' in self.params:
                self.result['filter_string'] = self.filter_string
            self.result['method'] = self.method
            # self.result['path'] = self.path  # Adding 'path' in result causes state: absent in output
            self.result['response'] = self.response
            self.result['status'] = self.status
            self.result['url'] = self.url

        if 'state' in self.params:
            self.original = self.existing
            if self.params['state'] in ('absent', 'present'):
                self.get_existing()

            # if self.module._diff and self.original != self.existing:
            #     self.result['diff'] = dict(
            #         before=json.dumps(self.original, sort_keys=True, indent=4),
            #         after=json.dumps(self.existing, sort_keys=True, indent=4),
            #     )
            self.result['current'] = self.existing

            if self.params['output_level'] in ('debug', 'info'):
                self.result['sent'] = self.config
                self.result['proposed'] = self.proposed

        self.result.update(**kwargs)
        self.module.exit_json(**self.result)

    def fail_json(self, msg, **kwargs):

        # Return error information, if we have it
        if self.error['code'] is not None and self.error['text'] is not None:
            self.result['error'] = self.error

        if 'state' in self.params:
            if self.params['state'] in ('absent', 'present'):
                if self.params['output_level'] in ('debug', 'info'):
                    self.result['previous'] = self.existing

            # Return the gory details when we need it
            if self.params['output_level'] == 'debug':
                if self.imdata is not None:
                    self.result['imdata'] = self.imdata
                    self.result['totalCount'] = self.totalCount

        if self.params['output_level'] == 'debug':
            if self.url is not None:
                if 'state' in self.params:
                    self.result['filter_string'] = self.filter_string
                self.result['method'] = self.method
                # self.result['path'] = self.path  # Adding 'path' in result causes state: absent in output
                self.result['response'] = self.response
                self.result['status'] = self.status
                self.result['url'] = self.url

        if 'state' in self.params:
            if self.params['output_level'] in ('debug', 'info'):
                self.result['sent'] = self.config
                self.result['proposed'] = self.proposed

        self.result.update(**kwargs)
        self.module.fail_json(msg=msg, **self.result)
