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
author:
    - "Ganesh Nalawade (@ganeshrn)"
    - "Sven Wisotzky (@wisotzky)"
short_description: Fetch configuration/state data from NETCONF enabled network devices.
description:
    - NETCONF is a network management protocol developed and standardized by
      the IETF. It is documented in RFC 6241.
    - This module allows the user to fetch configuration and state data from NETCONF
      enabled network devices.
options:
  source:
    description:
      - This argument specifies the datastore from which configuration data should be fetched.
        Valid values are I(running), I(candidate) and I(auto). If the value is I(auto) it fetches
        configuration data from I(candidate) datastore and if candidate datastore is not supported
        it fallback to I(running) datastore. If the C(source) value is not mentioned in that case
        both configuration and state information is returned in the response from running datastore.
    choices: ['running', 'candidate', 'startup']
    default: 'running'
  filter:
    description:
      - This argument specifies the XML string which acts as a filter to restrict the portions of
        the data to be are retrieved from the remote device. If this option is not specified entire
        configuration or state data is returned in result depending on the value of C(source)
        option. The C(filter) value can be either XML string or XPath, if the filter is in
        XPath format the NETCONF server running on remote host should support xpath capability
        else it will result in an error.
  display:
    description:
      - Encoding scheme to use when serializing output from the device. Currently supported option
        value is I(json) and I(pretty).  The option I(pretty) is similar to I(xml) but is using human
        readable format (spaces, new lines). The option I(json) will serialize the output as JSON data.
        If the option value is I(json) it requires jxmlease to be installed on control node.
    choices: ['json', 'pretty']
  lock:
    description:
      - Instructs the module to explicitly lock the datastore specified as C(source). If no
        I(source) is defined, the I(running) datastore will be locked. By setting the option
        value I(True) is will always lock the datastore mentioned in C(source) option provided
        the platform supports it else module will report error By setting the option value I(False)
        it will never lock the C(source) datastore.
    default: False
    type: bool
requirements:
  - ncclient (>=v0.5.2)
  - jxmlease

notes:
  - This module requires the NETCONF system service be enabled on
    the remote device being managed.
  - This module supports the use of connection=netconf
"""

EXAMPLES = """
- name: Get running configuration and state data
  netconf_get:

- name: Get configuration and state data from startup datastore
  netconf_get:
    source: startup

- name: Get system configuration data from running datastore state
  netconf_get:
    source: running
    filter: <configuration><system></system></configuration>

- name: Get configuration and state data in JSON format
  netconf_get:
    display: json

- name: get schema list using subtree w/ namespaces
  netconf_get:
    format: json
    filter: <netconf-state xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring"><schemas><schema/></schemas></netconf-state>
    lock: False

- name: get schema list using xpath
  netconf_get:
    format: json
    filter: /netconf-state/schemas/schema
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
  description: The set of transformed XML to JSON format from the RPC responses
               or pretty XML based on the value of C(display) option.
  returned: when the display format is selected as JSON os pretty apart from low-level
            errors (such as action plugin)
  type: dict
  sample: {'...'}
xml:
  description: The transformed XML string after removing namespace.
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
        source=dict(default='running', choices=['running', 'candidate', 'startup']),
        filter=dict(),
        display=dict(choices=['json', 'pretty']),
        lock=dict(default=False, type=bool)
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    conn = get_connection(module)
    capabilities = get_capabilities(module)
    operations = capabilities['device_operations']

    source = module.params['source']
    filter = module.params['filter']
    filter_type = get_filter_type(filter)
    lock = module.params['lock']
    display = module.params['display']

    if source == 'candidate' and not operations.get('supports_commit', False):
        module.fail_json(msg='candidate source is not supported on this device')

    if source == 'startup' and not operations.get('supports_startup', False):
        module.fail_json(msg='startup source is not supported on this device')

    if filter_type == 'xpath' and not operations.get('supports_xpath', False):
        module.fail_json(msg='filter type xpath is not supported on this device')

    if lock and not operations.get('supports_lock', False):
        module.fail_json(msg='lock operation is not supported on this device')

    if lock and source not in operations.get('lock_datastore', []):
        module.fail_json(msg='lock operation on source %s is not supported on this device' % source)

    filter_spec = (filter_type, filter) if filter_type else None

    if source is not None:
        if lock:
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
    elif display == 'pretty':
        output = tostring(response, pretty_print=True)

    result = {
        'stdout': response,
        'xml': transformed_resp,
        'output': output
    }

    module.exit_json(**result)

if __name__ == '__main__':
    main()
