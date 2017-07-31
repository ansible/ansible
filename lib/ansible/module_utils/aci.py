# -*- coding: utf-8 -*-

# Copyright 2017 Dag Wieers <dag@wieers.com>
# Copyright 2017 Swetha Chunduri (@schunduri)

# This file is part of Ansible by Red Hat
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

import json

from ansible.module_utils.basic import get_exception
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
    except:
        e = get_exception()
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
    except:
        e = get_exception()
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
        resp, auth = fetch_url(self.module, url, data=json.dumps(payload), method='POST', timeout=self.params['timeout'])

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
        resp, info = fetch_url(self.module,
                               url=self.result['url'],
                               data=payload,
                               method=self.params['method'].upper(),
                               timeout=self.params['timeout'],
                               headers=self.headers)
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

    def request_diff(self, path, payload=None):
        ''' Perform a request, including a proper diff output '''
        self.result['diff'] = dict()
        self.result['diff']['before'] = self.query()
        self.request(path, payload=payload)
        # TODO: Check if we can use the request output for the 'after' diff
        self.result['diff']['after'] = self.query()

        if self.result['diff']['before'] != self.result['diff']['after']:
            self.result['changed'] = True

    def query(self, path):
        ''' Perform a query with no payload '''
        url = '%(protocol)s://%(hostname)s/' % self.params + path.lstrip('/')
        resp, query = fetch_url(self.module, url=url, data=None, method='GET',
                                timeout=self.params['timeout'],
                                headers=self.headers)

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
