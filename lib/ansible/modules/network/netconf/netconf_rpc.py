#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: netconf_rpc
version_added: "2.6"
author:
    - "Ganesh Nalawade (@ganeshrn)"
    - "Sven Wisotzky (@wisotzky)"
short_description: Execute operations on NETCONF enabled network devices.
description:
    - NETCONF is a network management protocol developed and standardized by
      the IETF. It is documented in RFC 6241.
    - This module allows the user to execute NETCONF RPC requests as defined
      by IETF RFC standards as well as proprietary requests.
options:
  request:
    description:
      - This argument specifies the request content to be executed on the remote NETCONF
        enabled device. It needs to include the name of the operation including all
        attributes. If the value is a regular string, it is used as name of the operation
        without operation attributes. If the value is a dict, it is used as name of the
        operation with operation attributes. If the value is a string in XML format, it
        is directly used as RPC payload.
  xmlns:
    description:
      - NETCONF operations not defined in rfc6241 typically require the appropriate
        XML namespace to be set. In the case the I(request) option is not already
        provided in XML format, the namespace can be defined by the I(xmlns)
        option.
  display:
    description:
      - Encoding scheme to use when serializing output from the device. The option I(json) will
        serialize the output as JSON data. If the option value is I(json) it requires jxmlease
        to be installed on control node. The option I(pretty) is similar to received XML response
        but is using human readable format (spaces, new lines). The option value I(xml) is similar
        to received XML response but removes all XML namespaces.
    choices: ['json', 'pretty', 'xml']
requirements:
  - ncclient (>=v0.5.2)
  - jxmlease
  - dicttoxml

notes:
  - This module requires the NETCONF system service be enabled on the remote device
    being managed.
  - This module supports the use of connection=netconf
  - To execute C(get-config), C(get) or C(edit-config) requests it is recommended
    to use the Ansible I(netconf_get) and I(netconf_config) modules.
"""

EXAMPLES = """
- name: lock candidate
  netconf_rpc:
    request:
      lock:
        target:
          candidate:

- name: unlock candidate
  netconf_rpc:
    request: "{'unlock': {'target': {'candidate': None}}}"
    xmlns: "urn:ietf:params:xml:ns:netconf:base:1.0"

- name: discard changes
  netconf_rpc:
    request: discard-changes

- name: get-schema
  netconf_rpc:
    xmlns: urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring
    request:
      get-schema:
        identifier: ietf-netconf
        version: "2011-06-01"

- name: copy running to startup
  netconf_rpc:
    request:
      copy-config:
        source:
          running:
        target:
          startup:

- name: get schema list with JSON output
  netconf_rpc:
    request: |
      <get>
        <filter>
          <netconf-state xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring">
            <schemas/>
          </netconf-state>
        </filter>
      </get>
    display: json

- name: get schema using XML request
  netconf_rpc:
    request: |
      <get-schema xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring">
        <identifier>ietf-netconf-monitoring</identifier>
        <version>2010-10-04</version>
      </get-schema>
    display: json
"""

RETURN = """
stdout:
  description: The raw XML string containing configuration or state data
               received from the underlying ncclient library.
  returned: always apart from low-level errors (such as action plugin)
  type: string
  sample: '...'
stdout_lines:
  description: The value of stdout split into a list
  returned: always apart from low-level errors (such as action plugin)
  type: list
  sample: ['...', '...']
output:
  description: Based on the value of display option will return either the set of
               transformed XML to JSON format from the RPC response with type dict
               or pretty XML string response (human-readable) or response with
               namespace removed from XML string.
  returned: when the display format is selected as JSON it is returned as dict type, if the
            display format is xml or pretty pretty it is retured as a string apart from low-level
            errors (such as action plugin).
  type: complex
  contains:
    formatted_output:
      - Contains formatted response received from remote host as per the value in display format.
"""
import sys
import re

try:
    from lxml.etree import Element, SubElement, tostring, fromstring, XMLSyntaxError
except ImportError:
    from xml.etree.ElementTree import Element, SubElement, tostring, fromstring
    if sys.version_info < (2, 7):
        from xml.parsers.expat import ExpatError as XMLSyntaxError
    else:
        from xml.etree.ElementTree import ParseError as XMLSyntaxError

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netconf.netconf import dispatch
from ansible.module_utils.network.common.netconf import remove_namespaces

try:
    import jxmlease
    HAS_JXMLEASE = True
except ImportError:
    HAS_JXMLEASE = False

try:
    from dicttoxml import dicttoxml
    HAS_DICTTOXML = True
except ImportError:
    HAS_DICTTOXML = False


def get_xml_request(module, request, xmlns):
    if request is None:
        module.fail_json(msg='request is mandatory')

    if isinstance(request, str):
        if len(request) == 0:
            module.fail_json(msg='request cannot be empty string')

        try:
            # trying if request is already XML string
            fromstring(request)
            return request
        except XMLSyntaxError:
            pass

        try:
            # trying if request contains dict
            tmp = eval(request)
            if isinstance(tmp, dict):
                request = tmp
        except NameError:
            pass

    if isinstance(request, str):
        if xmlns is None:
            return '<%s/>' % request
        else:
            return '<%s xmlns="%s"/>' % (request, xmlns)

    if isinstance(request, dict):
        if not HAS_DICTTOXML:
            module.fail_json(msg='dicttoxml is required to render RPC operation payload'
                                 'but does not appear to be installed. '
                                 'It can be installed using `pip install dicttoxml`')
        xml = dicttoxml(request, root=False, attr_type=False)

        # Once the following PR is integrated, dicttoxml call needs to be updated:
        #   https://github.com/quandyfactory/dicttoxml/pull/64
        # Updated version of the dict>XML conversion:
        #   xml = dicttoxml(request, root=False, attr_type=False, fold_list=False)

        if xmlns is None:
            return xml
        else:
            return re.sub(r'(<[\w-]+)([^>]*>)', r'\1 xmlns="%s"\2' % xmlns, xml, count=1)

    module.fail_json(msg='unsupported request type `%s`' % type(request.__name__))


def main():
    """entry point for module execution
    """
    argument_spec = dict(
        request=dict(required=True),
        xmlns=dict(type="str"),
        display=dict(choices=['json', 'pretty', 'xml'])
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    request = module.params['request']
    display = module.params['display']
    xmlns = module.params['xmlns']

    if display == 'json' and not HAS_JXMLEASE:
        module.fail_json(msg='jxmlease is required to display response in json format'
                             'but does not appear to be installed. '
                             'It can be installed using `pip install jxmlease`')

    xml_req = get_xml_request(module, request, xmlns)
    response = dispatch(module, xml_req)

    xml_resp = tostring(response)
    output = None

    if display == 'xml':
        output = remove_namespaces(xml_resp)
    elif display == 'json':
        try:
            output = jxmlease.parse(xml_resp)
        except:
            raise ValueError(xml_resp)
    elif display == 'pretty':
        output = tostring(response, pretty_print=True)

    result = {
        'stdout': xml_resp,
        'output': output
    }

    module.exit_json(**result)

if __name__ == '__main__':
    main()
