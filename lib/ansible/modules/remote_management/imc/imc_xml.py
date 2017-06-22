#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017, Dag Wieers <dag@wieers.com>

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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: imc_xml
short_description: Manage Cisco IMC hardware through its XML API
description:
- Provides direct access to the Cisco IMC XML API.
- Perform any configuration changes and actions that the Cisco IMC supports.
- More information about the IMC XML API is available from
  U(http://www.cisco.com/c/en/us/td/docs/unified_computing/ucs/c/sw/api/3_0/b_Cisco_IMC_api_301.html)
author:
- Dag Wieers (@dagwieers)
version_added: '2.4'
requirements:
- lxml
- xmljson >= 0.1.8
options:
  hostname:
    description:
    - IP Address or hostname of Cisco IMC, resolvable by Ansible control host.
    required: true
    aliases: [ host, ip ]
  username:
    description:
    - Username used to login to the switch.
    default: admin
    aliases: [ user ]
  password:
    description:
    - The password to use for authentication.
    default: password
  path:
    description:
    - Name of the absolute path of the filename that includes the body
      of the http request being sent to the Cisco IMC XML API.
    - Parameter C(path) is mutual exclusive with parameter C(content).
    aliases: [ src ]
  content:
    description:
    - When used instead of C(path), sets the content of the API requests directly.
    - This may be convenient to template simple requests, for anything complex use the M(template) module.
    - You can add multiple IMC XML documents and they will be processed sequentially,
      the Cisco IMC output is subsequently merged.
    - Parameter C(path) is mutual exclusive with parameter C(content).
  protocol:
    description:
    - Connection protocol to use.
    default: https
    choices: [ http, https ]
  timeout:
    description:
    - The socket level timeout in seconds.
    default: 30
  validate_certs:
    description:
    - If C(no), SSL certificates will not be validated.
    - This should only set to C(no) used on personally controlled sites using self-signed certificates.
    type: bool
    default: 'yes'
notes:
- The XML snippets don't need an authentication cookie, this is injected by the module automatically.
- The Cisco IMC XML output is being translated to JSON using the Cobra convention.
- Any configConfMo change requested has a return status of 'modified', even if there was no actual change
  from the previous configuration. As a result, this module will always report a change on subsequent runs.
  In case this behaviour is fixed in a future update to Cisco IMC, this module will automatically adapt.
- More information about the IMC XML API is available from
  U(http://www.cisco.com/c/en/us/td/docs/unified_computing/ucs/c/sw/api/3_0/b_Cisco_IMC_api_301.html)
'''

EXAMPLES = r'''
- name: Power down server
  imc_xml:
    hostname: '{{ imc_hostname }}'
    username: '{{ imc_username }}'
    password: '{{ imc_password }}'
    validate_certs: no
    content: |
      <configConfMo><inConfig>
        <computeRackUnit dn="sys/rack-unit-1" adminPower="down"/>
      </inConfig></configConfMo>
  delegate_to: localhost

- name: Configure IMC using multiple XML documents
  imc_xml:
    hostname: '{{ imc_hostname }}'
    username: '{{ imc_username }}'
    password: '{{ imc_password }}'
    validate_certs: no
    content: |
      <!-- Configure Serial-on-LAN -->
      <configConfMo><inConfig>
        <solIf dn="sys/rack-unit-1/sol-if" adminState="enable" speed=="115200" comport="com0"/>
      </inConfig></configConfMo>

      <!-- Configure Console Redirection -->
      <configConfMo><inConfig>
        <biosVfConsoleRedirection dn="sys/rack-unit-1/bios/bios-settings/Console-redirection"
          vpBaudRate="115200"
          vpConsoleRedirection="com-0"
          vpFlowControl="none"
          vpTerminalType="vt100"
          vpPuttyKeyPad="LINUX"
          vpRedirectionAfterPOST="Always Enable"/>
      </inConfig></configConfMo>
  delegate_to: localhost

- name: Enable PXE boot and power-cycle server
  imc_xml:
    hostname: '{{ imc_hostname }}'
    username: '{{ imc_username }}'
    password: '{{ imc_password }}'
    validate_certs: no
    content: |
      <!-- Configure PXE boot -->
      <configConfMo><inConfig>
        <lsbootLan dn="sys/rack-unit-1/boot-policy/lan-read-only" access="read-only" order="1" prot="pxe" type="lan"/>
      </inConfig></configConfMo>

      <!-- Power cycle server -->
      <configConfMo><inConfig>
        <computeRackUnit dn="sys/rack-unit-1" adminPower="cycle-immediate"/>
      </inConfig></configConfMo>
  delegate_to: localhost

- name: Reconfigure IMC to boot from storage
  imc_xml:
    hostname: '{{ imc_host }}'
    username: '{{ imc_username }}'
    password: '{{ imc_password }}'
    validate_certs: no
    content: |
      <configConfMo><inConfig>
        <lsbootStorage dn="sys/rack-unit-1/boot-policy/storage-read-write" access="read-write" order="1" type="storage"/>
      </inConfig></configConfMo>
  delegate_to: localhost
'''

RETURN = r'''
aaLogin:
  description: Cisco IMC XML output for the login, translated to JSON using Cobra convention
  returned: success
  type: dict
  sample: |
    "attributes": {
        "cookie": "",
        "outCookie": "1498902428/9de6dc36-417c-157c-106c-139efe2dc02a",
        "outPriv": "admin",
        "outRefreshPeriod": "600",
        "outSessionId": "114",
        "outVersion": "2.0(13e)",
        "response": "yes"
    }
configConfMo:
  description: Cisco IMC XML output for any configConfMo XML snipets, translated to JSON using Cobra convention
  returned: success
  type: dict
  sample: |
response:
  description: HTTP response message, including content length
  returned: always
  type: string
  sample: OK (729 bytes)
status:
  description: The HTTP response status code
  returned: always
  type: dict
  sample: 200
error:
  description: Cisco IMC XML error output for last request, translated to JSON using Cobra convention
  returned: failed
  type: dict
  sample: |
    "attributes": {
        "cookie": "",
        "errorCode": "ERR-xml-parse-error",
        "errorDescr": "XML PARSING ERROR: Element 'computeRackUnit', attribute 'admin_Power': The attribute 'admin_Power' is not allowed. ",
        "invocationResult": "594",
        "response": "yes"
    }
error_code:
  description: Cisco IMC error code
  returned: failed
  type: string
  sample: ERR-xml-parse-error
error_text:
  description: Cisco IMC error message
  returned: failed
  type: string
  sample: |
    XML PARSING ERROR: Element 'computeRackUnit', attribute 'admin_Power': The attribute 'admin_Power' is not allowed.
input:
  description: RAW XML input sent to the Cisco IMC, causing the error
  returned: failed
  type: string
  sample: |
    <configConfMo><inConfig><computeRackUnit dn="sys/rack-unit-1" admin_Power="down"/></inConfig></configConfMo>
output:
  description: RAW XML output eceived from the Cisco IMC, with error details
  returned: failed
  type: string
  sample: >
    <error cookie=""
      response="yes"
      errorCode="ERR-xml-parse-error"
      invocationResult="594"
      errorDescr="XML PARSING ERROR: Element 'computeRackUnit', attribute 'admin_Power': The attribute 'admin_Power' is not allowed.\n"/>
'''


import atexit
import itertools
import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.urls import fetch_url

try:
    import lxml.etree
    HAS_LXML_ETREE = True
except ImportError:
    HAS_LXML_ETREE = False

try:
    from xmljson import cobra
    HAS_XMLJSON_COBRA = True
except ImportError:
    HAS_XMLJSON_COBRA = False


def imc_response(module, rawoutput, rawinput=''):
    ''' Handle IMC returned data '''
    xmloutput = lxml.etree.fromstring(rawoutput)
    result = cobra.data(xmloutput)

    # Handle errors
    if xmloutput.get('errorCode') and xmloutput.get('errorDescr'):
        if rawinput:
            result['input'] = rawinput
        result['output'] = rawoutput
        result['error_code'] = xmloutput.get('errorCode')
        result['error_text'] = xmloutput.get('errorDescr')
        module.fail_json(msg='Request failed: %(error_text)s' % result, **result)

    return result


def logout(module, url, cookie, timeout):
    ''' Perform a logout, if needed '''
    data = '<aaaLogout cookie="%s" inCookie="%s"/>' % (cookie, cookie)
    resp, auth = fetch_url(module, url, data=data, method="POST", timeout=timeout)


def merge(one, two):
    ''' Merge two complex nested datastructures into one'''
    if isinstance(one, dict) and isinstance(two, dict):
        copy = dict(one)
        # copy.update({key: merge(one.get(key, None), two[key]) for key in two})
        copy.update(dict((key, merge(one.get(key, None), two[key])) for key in two))
        return copy

    elif isinstance(one, list) and isinstance(two, list):
        return [merge(alpha, beta) for (alpha, beta) in itertools.izip_longest(one, two)]

    return one if two is None else two


def main():

    module = AnsibleModule(
        argument_spec=dict(
            hostname=dict(type='str', required=True, aliases=['host', 'ip']),
            username=dict(type='str', default='admin', aliases=['user']),
            password=dict(type='str', default='password', no_log=True),
            content=dict(type='str'),
            path=dict(type='path', aliases=['config_file', 'src']),
            protocol=dict(type='str', default='https', choices=['http', 'https']),
            timeout=dict(type='int', default=30),
            validate_certs=dict(type='bool', default=True),
        ),
        supports_check_mode=True,
        mutually_exclusive=[['content', 'path']],
    )

    hostname = module.params['hostname']
    username = module.params['username']
    password = module.params['password']

    content = module.params['content']
    path = module.params['path']

    protocol = module.params['protocol']
    timeout = module.params['timeout']

    result = dict(
        failed=False,
        changed=False,
    )

    # Report missing file
    file_exists = False
    if path:
        if os.path.isfile(path):
            file_exists = True
        else:
            module.fail_json(msg='Cannot find/access path:\n%s' % path)

    # Perform login first
    url = '%s://%s/nuova' % (protocol, hostname)
    data = '<aaaLogin inName="%s" inPassword="%s"/>' % (username, password)
    resp, auth = fetch_url(module, url, data=data, method='POST', timeout=timeout)
    if resp is None or auth['status'] != 200:
        module.fail_json(msg='Task failed with error %(status)s: %(msg)s' % auth, **result)
    result.update(imc_response(module, resp.read()))

    # Store cookie for future requests
    try:
        cookie = result['aaaLogin']['attributes']['outCookie']
    except:
        module.fail_json(msg='Could not find cookie in output', **result)

    # If we would not log out properly, we run out of sessions quickly
    atexit.register(logout, module, url, cookie, timeout)

    # Prepare request data
    if content:
        rawdata = content
    elif file_exists:
        with open(path, 'r') as config_object:
            rawdata = config_object.read()

    # Wrap the XML documents in a <root> element
    xmldata = lxml.etree.fromstring('<root>%s</root>' % rawdata.replace('\n', ''))

    # Handle each XML document separately in the same session
    for xmldoc in list(xmldata):
        if xmldoc.tag is lxml.etree.Comment:
            continue
        # Add cookie to XML
        xmldoc.set('cookie', cookie)
        data = lxml.etree.tostring(xmldoc)

        # Perform actual request
        resp, info = fetch_url(module, url, data=data, method='POST', timeout=timeout)
        if resp is None or auth['status'] != 200:
            module.fail_json(msg='Task failed with error %(status)s: %(msg)s' % auth, **result)

        # Merge results with previous results
        rawoutput = resp.read()
        result = merge(result, imc_response(module, rawoutput, rawinput=data))
        result['response'] = info['msg']
        result['status'] = info['status']

        # Check for any changes
        # NOTE: Unfortunately IMC API always report status as 'modified'
        xmloutput = lxml.etree.fromstring(rawoutput)
        results = xmloutput.xpath('/configConfMo/outConfig/*/@status')
        result['changed'] = ('modified' in results)

    # Report success
    module.exit_json(**result)

if __name__ == '__main__':
    main()
