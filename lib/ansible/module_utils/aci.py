# -*- coding: utf-8 -*-

# This code is part of Ansible, but is an independent component

# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.

# Copyright 2017 Dag Wieers <dag@wieers.com>
# Copyright 2017 Swetha Chunduri (@schunduri)
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

import json

from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_bytes

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


aci_argument_spec = dict(
    hostname=dict(type='str', required=True, aliases=['host']),
    username=dict(type='str', default='admin', aliases=['user']),
    password=dict(type='str', required=True, no_log=True),
    protocol=dict(type='str', removed_in_version='2.6'),  # Deprecated in v2.6
    timeout=dict(type='int', default=30),
    use_proxy=dict(type='bool', default=True),
    use_ssl=dict(type='bool', default=True),
    validate_certs=dict(type='bool', default=True),
)


def aci_response_error(result):
    ''' Set error information when found '''
    result['error_code'] = 0
    result['error_text'] = 'Success'
    # Handle possible APIC error information
    if result['totalCount'] != '0':
        try:
            result['error_code'] = result['imdata'][0]['error']['attributes']['code']
            result['error_text'] = result['imdata'][0]['error']['attributes']['text']
        except (KeyError, IndexError):
            pass


def aci_response_json(result, rawoutput):
    ''' Handle APIC JSON response output '''
    try:
        result.update(json.loads(rawoutput))
    except Exception as e:
        # Expose RAW output for troubleshooting
        result.update(raw=rawoutput, error_code=-1, error_text="Unable to parse output as JSON, see 'raw' output. %s" % e)
        return

    # Handle possible APIC error information
    aci_response_error(result)


def aci_response_xml(result, rawoutput):
    ''' Handle APIC XML response output '''

    # NOTE: The XML-to-JSON conversion is using the "Cobra" convention
    try:
        xml = lxml.etree.fromstring(to_bytes(rawoutput))
        xmldata = cobra.data(xml)
    except Exception as e:
        # Expose RAW output for troubleshooting
        result.update(raw=rawoutput, error_code=-1, error_text="Unable to parse output as XML, see 'raw' output. %s" % e)
        return

    # Reformat as ACI does for JSON API output
    try:
        result.update(imdata=xmldata['imdata']['children'])
    except KeyError:
        result['imdata'] = dict()
    result['totalCount'] = xmldata['imdata']['attributes']['totalCount']

    # Handle possible APIC error information
    aci_response_error(result)


class ACIModule(object):

    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.result = dict(changed=False)
        self.headers = None

        self.login()

    def define_protocol(self):
        ''' Set protocol based on use_ssl parameter '''

        # Set protocol for further use
        if self.params['protocol'] in ('http', 'https'):
            self.module.deprecate("Parameter 'protocol' is deprecated, please use 'use_ssl' instead.", '2.6')
        elif self.params['protocol'] is None:
            self.params['protocol'] = 'https' if self.params.get('use_ssl', True) else 'http'
        else:
            self.module.fail_json(msg="Parameter 'protocol' needs to be one of ( http, https )")

    def define_method(self):
        ''' Set method based on state parameter '''

        # Handle deprecated method/action parameter
        if self.params['method']:
            # Deprecate only if state was a valid option (not for aci_rest)
            if self.module.argument_spec('state', False):
                self.module.deprecate("Parameter 'method' or 'action' is deprecated, please use 'state' instead", '2.6')
            method_map = dict(delete='absent', get='query', post='present')
            self.params['state'] = method_map[self.params['method']]
        else:
            state_map = dict(absent='delete', present='post', query='get')
            self.params['method'] = state_map[self.params['state']]

    def login(self):
        ''' Log in to APIC '''

        # Ensure protocol is set (only do this once)
        self.define_protocol()

        # Perform login request
        url = '%(protocol)s://%(hostname)s/api/aaaLogin.json' % self.params
        payload = {'aaaUser': {'attributes': {'name': self.params['username'], 'pwd': self.params['password']}}}
        resp, auth = fetch_url(self.module, url,
                               data=json.dumps(payload),
                               method='POST',
                               timeout=self.params['timeout'],
                               use_proxy=self.params['use_proxy'])

        # Handle APIC response
        if auth['status'] != 200:
            self.result['response'] = auth['msg']
            self.result['status'] = auth['status']
            try:
                # APIC error
                aci_response_json(self.result, auth['body'])
                self.module.fail_json(msg='Authentication failed: %(error_code)s %(error_text)s' % self.result, **self.result)
            except KeyError:
                # Connection error
                self.module.fail_json(msg='Authentication failed for %(url)s. %(msg)s' % auth)

        # Retain cookie for later use
        self.headers = dict(Cookie=resp.headers['Set-Cookie'])

    def request(self, path, payload=None):
        ''' Perform a REST request '''

        # Ensure method is set (only do this once)
        self.define_method()

        # Perform request
        self.result['url'] = '%(protocol)s://%(hostname)s/' % self.params + path.lstrip('/')
        resp, info = fetch_url(self.module, self.result['url'],
                               data=payload,
                               headers=self.headers,
                               method=self.params['method'].upper(),
                               timeout=self.params['timeout'],
                               use_proxy=self.params['use_proxy'])

        self.result['response'] = info['msg']
        self.result['status'] = info['status']

        # Handle APIC response
        if info['status'] != 200:
            try:
                # APIC error
                aci_response_json(self.result, info['body'])
                self.module.fail_json(msg='Request failed: %(error_code)s %(error_text)s' % self.result, **self.result)
            except KeyError:
                # Connection error
                self.module.fail_json(msg='Request failed for %(url)s. %(msg)s' % info)

        aci_response_json(self.result, resp.read())

    def query(self, path):
        ''' Perform a query with no payload '''
        url = '%(protocol)s://%(hostname)s/' % self.params + path.lstrip('/')
        resp, query = fetch_url(self.module, url,
                                data=None,
                                headers=self.headers,
                                method='GET',
                                timeout=self.params['timeout'],
                                use_proxy=self.params['use_proxy'])

        # Handle APIC response
        if query['status'] != 200:
            self.result['response'] = query['msg']
            self.result['status'] = query['status']
            try:
                # APIC error
                aci_response_json(self.result, query['body'])
                self.module.fail_json(msg='Query failed: %(error_code)s %(error_text)s' % self.result, **self.result)
            except KeyError:
                # Connection error
                self.module.fail_json(msg='Query failed for %(url)s. %(msg)s' % query)

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
