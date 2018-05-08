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
module: netconf_get
version_added: "2.6"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Fetch configuration/state data from Netconf enabled network devices.
description:
    - Netconf is a network management protocol developed and standardized by
      the IETF. It is documented in RFC 6241.

    - This module allows the user to fetch configuration and state data from Netconf
      enabled network devices.
options:
  source:
    description:
      - This argument specifies the datastore from which configuration data should be fetched.
        Valid values are I(running), I(candidate) and I(auto). If the value is I(auto) it fetches
        configuration data from I(candidate) datastore and if candidate datastore is not supported
        it fallback to I(running) datastore. If the C(source) value is not mentioned in that case
        both configuration and state information in returned in response from running datastore.
    choices: ['running', 'candidate', 'auto', 'startup']
  filter:
    description:
      - This argument specifies the XML string which acts as a filter to restrict the portions of
        the data to be are retrieved from remote device. If this option is not specified entire
        configuration or state data is returned in result depending on the value of C(source)
        option. The C(filter) value can be either xml string or xpath, if the filter is in
        xpath format the Netconf server running on remote host should support xpath capabiltiy
        else it will result in error.
  display:
    description:
      - Encoding scheme to use when serializing output from the device. Currently supported option
        value is I(json) only. If the option value is I(json) it requires jxmlease to be installed
        on control node.
    choices: ['json']
requirements:
  - ncclient (>=v0.5.2)
  - jxmlease

notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed.
  - This module supports the use of connection=netconf
"""

EXAMPLES = """
- name: Get confgiuration and state data
  netconf_get:

- name: Get configuration data from candidate datastore state
  netconf_get:
    source: candidate

- name: Get system configuration data from running datastore state
  netconf_get:
    source: running
    filter: <configuration><system></system></configuration>

- name: Get confgiuration and state data in json format
  netconf_get:
    display: json
"""

RETURN = """
stdout:
  description: The transformed xml string containing configuration or state data
               retrieved from remote host, namespace will be removed from this xml string.
  returned: always apart from low level errors (such as action plugin)
  type: string
  sample: '...'
stdout_lines:
  description: The value of stdout split into a list
  returned: always apart from low level errors (such as action plugin)
  type: list
  sample: ['...', '...']
output:
  description: The set of transformed xml to json format from the RPC responses
  returned: when display format is selected as json apart from low level
            errors (such as action plugin)
  type: dict
  sample: {'...'}
xml:
  description: The raw xml string received from the underlying ncclient library.
  returned: always apart from low level errors (such as action plugin)
  type: string
  sample: '...'
"""
import sys

try:
    from lxml.etree import Element, SubElement, tostring, fromstring, XMLSyntaxError
except ImportError:
    from xml.etree.ElementTree import Element, SubElement, tostring, fromstring
    if sys.version_info < (2, 7):
        from xml.parsers.expat import ExpatError as XMLSyntaxError
    else:
        from xml.etree.ElementTree import ParseError as XMLSyntaxError

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netconf.netconf import get_connection, get_capabilities, locked_config
from ansible.module_utils.network.common.netconf import remove_namespaces

try:
    import jxmlease
    HAS_JXMLEASE = True
except ImportError:
    HAS_JXMLEASE = False


def get_filter_type(filter):
    if not filter:
        return None
    else:
        try:
            fromstring(filter)
            return 'subtree'
        except XMLSyntaxError:
            return 'xpath'


def main():
    """entry point for module execution
    """
    argument_spec = dict(
        source=dict(choices=['running', 'candidate', 'startup', 'auto']),
        filter=dict(),
        display=dict(choices=['json'])
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    conn = get_connection(module)
    capabilities = get_capabilities(module)
    operations = capabilities['device_operations']

    source = module.params['source']
    filter = module.params['filter']
    filter_type = get_filter_type(filter)
    display = module.params['display']

    if source == 'candidate' and not operations.get('supports_commit', False):
        module.fail_json(msg='candidate source is not supported on this device')

    if source == 'startup' and not operations.get('supports_startup', False):
        module.fail_json(msg='startup source is not supported on this device')

    if filter_type == 'xpath' and not operations.get('supports_xpath', False):
        module.fail_json(msg='filter type xpath is not supported on this device')

    filter_spec = (filter_type, filter) if filter_type else None

    if source is not None:
        if source == 'auto':
            if operations.get('supports_commit', False):
                source = 'candidate'
            else:
                source = 'running'

        if source == 'candidate':
            with locked_config(module, target=source):
                response = conn.get_config(source=source, filter=filter_spec)
        else:
            response = conn.get_config(source=source, filter=filter_spec)

    else:
        response = conn.get(filter=filter_spec)

    response = tostring(response)
    transformed_resp = remove_namespaces(response)
    output = None
    if display == 'json':
        if not HAS_JXMLEASE:
            module.fail_json(msg='jxmlease is required to display response in json format'
                                 'but does not appear to be installed. '
                                 'It can be installed using `pip install jxmlease`')

        try:
            output = jxmlease.parse(transformed_resp)
        except:
            raise ValueError(response)

    result = {
        'stdout': transformed_resp,
        'xml': response,
        'output': output
    }

    module.exit_json(**result)

if __name__ == '__main__':
    main()
