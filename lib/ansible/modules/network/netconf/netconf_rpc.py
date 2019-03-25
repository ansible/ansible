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
extends_documentation_fragment: network_agnostic
options:
  rpc:
    description:
      - This argument specifies the request (name of the operation) to be executed on
        the remote NETCONF enabled device.
  xmlns:
    description:
      - NETCONF operations not defined in rfc6241 typically require the appropriate
        XML namespace to be set. In the case the I(request) option is not already
        provided in XML format, the namespace can be defined by the I(xmlns)
        option.
  content:
    description:
      - This argument specifies the optional request content (all RPC attributes).
        The I(content) value can either be provided as XML formatted string or as
        dictionary.
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
    rpc: lock
    content:
      target:
        candidate:

- name: unlock candidate
  netconf_rpc:
    rpc: unlock
    xmlns: "urn:ietf:params:xml:ns:netconf:base:1.0"
    content: "{'target': {'candidate': None}}"

- name: discard changes
  netconf_rpc:
    rpc: discard-changes

- name: get-schema
  netconf_rpc:
    rpc: get-schema
    xmlns: urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring
    content:
      identifier: ietf-netconf
      version: "2011-06-01"

- name: copy running to startup
  netconf_rpc:
    rpc: copy-config
    content:
      source:
        running:
      target:
        startup:

- name: get schema list with JSON output
  netconf_rpc:
    rpc: get
    content: |
      <filter>
        <netconf-state xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring">
          <schemas/>
        </netconf-state>
      </filter>
    display: json

- name: get schema using XML request
  netconf_rpc:
    rpc: "get-schema"
    xmlns: "urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring"
    content: |
      <identifier>ietf-netconf-monitoring</identifier>
      <version>2010-10-04</version>
    display: json
"""

RETURN = """
stdout:
  description: The raw XML string containing configuration or state data
               received from the underlying ncclient library.
  returned: always apart from low-level errors (such as action plugin)
  type: str
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

import ast

try:
    from lxml.etree import tostring
except ImportError:
    from xml.etree.ElementTree import tostring

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netconf.netconf import dispatch
from ansible.module_utils.network.common.netconf import remove_namespaces

try:
    import jxmlease
    HAS_JXMLEASE = True
except ImportError:
    HAS_JXMLEASE = False


def get_xml_request(module, request, xmlns, content):
    if content is None:
        if xmlns is None:
            return '<%s/>' % request
        else:
            return '<%s xmlns="%s"/>' % (request, xmlns)

    if isinstance(content, str):
        content = content.strip()

        if content.startswith('<') and content.endswith('>'):
            # assumption content contains already XML payload
            if xmlns is None:
                return '<%s>%s</%s>' % (request, content, request)
            else:
                return '<%s xmlns="%s">%s</%s>' % (request, xmlns, content, request)

        try:
            # trying if content contains dict
            content = ast.literal_eval(content)
        except Exception:
            module.fail_json(msg='unsupported content value `%s`' % content)

    if isinstance(content, dict):
        if not HAS_JXMLEASE:
            module.fail_json(msg='jxmlease is required to convert RPC content to XML '
                                 'but does not appear to be installed. '
                                 'It can be installed using `pip install jxmlease`')

        payload = jxmlease.XMLDictNode(content).emit_xml(pretty=False, full_document=False)
        if xmlns is None:
            return '<%s>%s</%s>' % (request, payload, request)
        else:
            return '<%s xmlns="%s">%s</%s>' % (request, xmlns, payload, request)

    module.fail_json(msg='unsupported content data-type `%s`' % type(content).__name__)


def main():
    """entry point for module execution
    """
    argument_spec = dict(
        rpc=dict(type="str", required=True),
        xmlns=dict(type="str"),
        content=dict(),
        display=dict(choices=['json', 'pretty', 'xml'])
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    rpc = module.params['rpc']
    xmlns = module.params['xmlns']
    content = module.params['content']
    display = module.params['display']

    if rpc is None:
        module.fail_json(msg='argument `rpc` must not be None')

    rpc = rpc.strip()
    if len(rpc) == 0:
        module.fail_json(msg='argument `rpc` must not be empty')

    if rpc in ['close-session']:
        # explicit close-session is not allowed, as this would make the next
        # NETCONF operation to the same host fail
        module.fail_json(msg='unsupported operation `%s`' % rpc)

    if display == 'json' and not HAS_JXMLEASE:
        module.fail_json(msg='jxmlease is required to display response in json format'
                             'but does not appear to be installed. '
                             'It can be installed using `pip install jxmlease`')

    xml_req = get_xml_request(module, rpc, xmlns, content)
    response = dispatch(module, xml_req)

    xml_resp = tostring(response)
    output = None

    if display == 'xml':
        output = remove_namespaces(xml_resp)
    elif display == 'json':
        try:
            output = jxmlease.parse(xml_resp)
        except Exception:
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
