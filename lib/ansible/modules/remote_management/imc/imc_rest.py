#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017, Dag Wieers <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: imc_rest
short_description: Manage Cisco IMC hardware through its REST API
description:
- Provides direct access to the Cisco IMC REST API.
- Perform any configuration changes and actions that the Cisco IMC supports.
- More information about the IMC REST API is available from
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
      of the http request being sent to the Cisco IMC REST API.
    - Parameter C(path) is mutual exclusive with parameter C(content).
    aliases: [ 'src', 'config_file' ]
  content:
    description:
    - When used instead of C(path), sets the content of the API requests directly.
    - This may be convenient to template simple requests, for anything complex use the M(template) module.
    - You can collate multiple IMC XML fragments and they will be processed sequentially in a single stream,
      the Cisco IMC output is subsequently merged.
    - Parameter C(content) is mutual exclusive with parameter C(path).
  protocol:
    description:
    - Connection protocol to use.
    default: https
    choices: [ http, https ]
  timeout:
    description:
    - The socket level timeout in seconds.
    - This is the time that every single connection (every fragment) can spend.
      If this C(timeout) is reached, the module will fail with a
      C(Connection failure) indicating that C(The read operation timed out).
    default: 60
  validate_certs:
    description:
    - If C(no), SSL certificates will not be validated.
    - This should only set to C(no) used on personally controlled sites using self-signed certificates.
    type: bool
    default: 'yes'
notes:
- The XML fragments don't need an authentication cookie, this is injected by the module automatically.
- The Cisco IMC XML output is being translated to JSON using the Cobra convention.
- Any configConfMo change requested has a return status of 'modified', even if there was no actual change
  from the previous configuration. As a result, this module will always report a change on subsequent runs.
  In case this behaviour is fixed in a future update to Cisco IMC, this module will automatically adapt.
- If you get a C(Connection failure) related to C(The read operation timed out) increase the C(timeout)
  parameter. Some XML fragments can take longer than the default timeout.
- More information about the IMC REST API is available from
  U(http://www.cisco.com/c/en/us/td/docs/unified_computing/ucs/c/sw/api/3_0/b_Cisco_IMC_api_301.html)
'''

EXAMPLES = r'''
- name: Power down server
  imc_rest:
    hostname: '{{ imc_hostname }}'
    username: '{{ imc_username }}'
    password: '{{ imc_password }}'
    validate_certs: no
    content: |
      <configConfMo><inConfig>
        <computeRackUnit dn="sys/rack-unit-1" adminPower="down"/>
      </inConfig></configConfMo>
  delegate_to: localhost

- name: Configure IMC using multiple XML fragments
  imc_rest:
    hostname: '{{ imc_hostname }}'
    username: '{{ imc_username }}'
    password: '{{ imc_password }}'
    validate_certs: no
    timeout: 120
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
  imc_rest:
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
  imc_rest:
    hostname: '{{ imc_host }}'
    username: '{{ imc_username }}'
    password: '{{ imc_password }}'
    validate_certs: no
    content: |
      <configConfMo><inConfig>
        <lsbootStorage dn="sys/rack-unit-1/boot-policy/storage-read-write" access="read-write" order="1" type="storage"/>
      </inConfig></configConfMo>
  delegate_to: localhost

- name: Add customer description to server
  imc_rest:
    hostname: '{{ imc_host }}'
    username: '{{ imc_username }}'
    password: '{{ imc_password }}'
    validate_certs: no
    content: |
        <configConfMo><inConfig>
          <computeRackUnit dn="sys/rack-unit-1" usrLbl="Customer Lab - POD{{ pod_id }} - {{ inventory_hostname_short }}"/>
        </inConfig></configConfMo>
    delegate_to: localhost

- name: Disable HTTP and increase session timeout to max value 10800 secs
  imc_rest:
    hostname: '{{ imc_host }}'
    username: '{{ imc_username }}'
    password: '{{ imc_password }}'
    validate_certs: no
    timeout: 120
    content: |
        <configConfMo><inConfig>
          <commHttp dn="sys/svc-ext/http-svc" adminState="disabled"/>
        </inConfig></configConfMo>

        <configConfMo><inConfig>
          <commHttps dn="sys/svc-ext/https-svc" adminState="enabled" sessionTimeout="10800"/>
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
  description: Cisco IMC XML output for any configConfMo XML fragments, translated to JSON using Cobra convention
  returned: success
  type: dict
  sample: |
elapsed:
  description: Elapsed time in seconds
  returned: always
  type: int
  sample: 31
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
import datetime
import itertools
import os

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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


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
            timeout=dict(type='int', default=60),
            validate_certs=dict(type='bool', default=True),
        ),
        supports_check_mode=True,
        mutually_exclusive=[['content', 'path']],
    )

    if not HAS_LXML_ETREE:
        module.fail_json(msg='module requires the lxml Python library installed on the managed host')

    if not HAS_XMLJSON_COBRA:
        module.fail_json(msg='module requires the xmljson (>= 0.1.8) Python library installed on the managed host')

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

    start = datetime.datetime.utcnow()

    # Perform login first
    url = '%s://%s/nuova' % (protocol, hostname)
    data = '<aaaLogin inName="%s" inPassword="%s"/>' % (username, password)
    resp, auth = fetch_url(module, url, data=data, method='POST', timeout=timeout)
    if resp is None or auth['status'] != 200:
        result['elapsed'] = (datetime.datetime.utcnow() - start).seconds
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
        if resp is None or info['status'] != 200:
            result['elapsed'] = (datetime.datetime.utcnow() - start).seconds
            module.fail_json(msg='Task failed with error %(status)s: %(msg)s' % info, **result)

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
    result['elapsed'] = (datetime.datetime.utcnow() - start).seconds
    module.exit_json(**result)

if __name__ == '__main__':
    main()
