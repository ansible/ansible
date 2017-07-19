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
    protocol=dict(type='str'),  # Deprecated in v2.8
    timeout=dict(type='int', default=30),
    use_ssl=dict(type='bool', default=True),
    validate_certs=dict(type='bool', default=True),
)


def aci_response_error(result):

    # Handle possible APIC error information
    try:
        result['error_code'] = result['imdata'][0]['error']['attributes']['code']
        result['error_text'] = result['imdata'][0]['error']['attributes']['text']
    except KeyError:
        result['error_code'] = 0
        result['error_text'] = 'Success'

    return result


def aci_response_json(rawoutput):
    ''' Handle APIC JSON response output '''
    try:
        result = json.loads(rawoutput)
    except:
        e = get_exception()
        # Expose RAW output for troubleshooting
        return dict(raw=rawoutput, error_code=-1, error_text="Unable to parse output as JSON, see 'raw' output. %s" % e)

    # Handle possible APIC error information
    return aci_response_error(result)


def aci_response_xml(rawoutput):
    ''' Handle APIC XML response output '''

    # NOTE: The XML-to-JSON conversion is using the "Cobra" convention
    try:
        xml = lxml.etree.fromstring(to_bytes(rawoutput))
        xmldata = cobra.data(xml)
    except:
        e = get_exception()
        # Expose RAW output for troubleshooting
        return dict(raw=rawoutput, error_code=-1, error_text="Unable to parse output as XML, see 'raw' output. %s" % e)

    # Reformat as ACI does for JSON API output
    try:
        result = dict(imdata=xmldata['imdata']['children'])
    except KeyError:
        result = dict(imdata=dict())
    result['totalCount'] = xmldata['imdata']['attributes']['totalCount']

    # Handle possible APIC error information
    return aci_response_error(result)


def define_protocol(module):
    ''' Set protocol based on use_ssl parameter '''

    # Set protocol for further use
    if module.params['protocol'] in ('http', 'https'):
        module.deprecate("Parameter 'protocol' is deprecated, please use 'use_ssl' instead.", 2.8)
    elif module.params['protocol'] is None:
        module.params['protocol'] = 'https' if module.params.get('use_ssl', True) else 'http'
    else:
        module.fail_json(msg="Parameter 'protocol' needs to be one of ( http, https )")


def aci_login(module):
    ''' Log in to APIC '''

    # Ensure protocol is set (only do this once)
    define_protocol(module)

    # Perform login request
    url = '%(protocol)s://%(hostname)s/api/aaaLogin.json' % module.params
    payload = {'aaaUser': {'attributes': {'name': module.params['username'], 'pwd': module.params['password']}}}
    resp, auth = fetch_url(module, url, data=json.dumps(payload), method='POST', timeout=module.params['timeout'])

    # Handle APIC response
    if auth['status'] != 200:
        try:
            # APIC error
            result = aci_response_json(auth['body'])
            module.fail_json(response=auth['msg'], status=auth['status'], msg='Authentication failed: %(error_code)s %(error_text)s' % result, **result)
        except KeyError:
            # Connection error
            module.fail_json(msg='Authentication failed for %(url)s. %(msg)s' % auth)

    return resp


def aci_request(module, path, payload, method, headers):
    ''' Perform a REST request '''

    # Perform request
    url = '%(protocol)s://%(hostname)s/' % module.params + path.lstrip('/')
    resp, info = fetch_url(module, url, data=json.dumps(payload), method=method.upper(), timeout=module.params['timeout'], headers=headers)
    result['response'] = info['msg']
    result['status'] = info['status']

    # Handle APIC response
    if info['status'] != 200:
        try:
            # APIC error
            result = aci_response_json(info['body'])
            module.fail_json(msg='Request failed: %(error_code)s %(error_text)s' % result, **result)
        except KeyError:
            # Connection error
            module.fail_json(msg='Request failed for %(url)s. %(msg)s' % info)

    # Report success
    return aci_response_json(resp.read())


def aci_query(module, path, payload, headers, filters):

    # Do request
    # Filter JSON
    # Return filtered JSON
    return filtered_json
