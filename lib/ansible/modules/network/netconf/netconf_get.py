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
extends_documentation_fragment: network_agnostic
options:
  source:
    description:
      - This argument specifies the datastore from which configuration data should be fetched.
        Valid values are I(running), I(candidate) and I(startup). If the C(source) value is not
        set both configuration and state information are returned in response from running datastore.
    choices: ['running', 'candidate', 'startup']
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
      - Encoding scheme to use when serializing output from the device. The option I(json) will
        serialize the output as JSON data. If the option value is I(json) it requires jxmlease
        to be installed on control node. The option I(pretty) is similar to received XML response
        but is using human readable format (spaces, new lines). The option value I(xml) is similar
        to received XML response but removes all XML namespaces.
    choices: ['json', 'pretty', 'xml']
  lock:
    description:
      - Instructs the module to explicitly lock the datastore specified as C(source). If no
        I(source) is defined, the I(running) datastore will be locked. By setting the option
        value I(always) is will explicitly lock the datastore mentioned in C(source) option.
        By setting the option value I(never) it will not lock the C(source) datastore. The
        value I(if-supported) allows better interworking with NETCONF servers, which do not
        support the (un)lock operation for all supported datastores.
    default: never
    choices: ['never', 'always', 'if-supported']
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

- name: Get system configuration data from running datastore state (junos)
  netconf_get:
    source: running
    filter: <configuration><system></system></configuration>

- name: Get configuration and state data in JSON format
  netconf_get:
    display: json

- name: get schema list using subtree w/ namespaces
  netconf_get:
    display: json
    filter: <netconf-state xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring"><schemas><schema/></schemas></netconf-state>
    lock: never

- name: get schema list using xpath
  netconf_get:
    display: xml
    filter: /netconf-state/schemas/schema

- name: get interface configuration with filter (iosxr)
  netconf_get:
    display: pretty
    filter: <interface-configurations xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"></interface-configurations>
    lock: if-supported

- name: Get system configuration data from running datastore state (junos)
  netconf_get:
    source: running
    filter: <configuration><system></system></configuration>
    lock: if-supported

- name: Get complete configuration data from running datastore (SROS)
  netconf_get:
    source: running
    filter: <configure xmlns="urn:nokia.com:sros:ns:yang:sr:conf"/>

- name: Get complete state data (SROS)
  netconf_get:
    filter: <state xmlns="urn:nokia.com:sros:ns:yang:sr:state"/>
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
            display format is xml or pretty pretty it is returned as a string apart from low-level
            errors (such as action plugin).
  type: complex
  contains:
    formatted_output:
      - Contains formatted response received from remote host as per the value in display format.
"""
import sys

try:
    from lxml.etree import tostring, fromstring, XMLSyntaxError
except ImportError:
    from xml.etree.ElementTree import tostring, fromstring
    if sys.version_info < (2, 7):
        from xml.parsers.expat import ExpatError as XMLSyntaxError
    else:
        from xml.etree.ElementTree import ParseError as XMLSyntaxError

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netconf.netconf import get_capabilities, get_config, get
from ansible.module_utils.network.common.netconf import remove_namespaces
from ansible.module_utils._text import to_text

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
        source=dict(choices=['running', 'candidate', 'startup']),
        filter=dict(),
        display=dict(choices=['json', 'pretty', 'xml']),
        lock=dict(default='never', choices=['never', 'always', 'if-supported'])
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

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
        module.fail_json(msg="filter value '%s' of type xpath is not supported on this device" % filter)

    # If source is None, NETCONF <get> operation is issued, reading config/state data
    # from the running datastore. The python expression "(source or 'running')" results
    # in the value of source (if not None) or the value 'running' (if source is None).

    if lock == 'never':
        execute_lock = False
    elif (source or 'running') in operations.get('lock_datastore', []):
        # lock is requested (always/if-support) and supported => lets do it
        execute_lock = True
    else:
        # lock is requested (always/if-supported) but not supported => issue warning
        module.warn("lock operation on '%s' source is not supported on this device" % (source or 'running'))
        execute_lock = (lock == 'always')

    if display == 'json' and not HAS_JXMLEASE:
        module.fail_json(msg='jxmlease is required to display response in json format'
                             'but does not appear to be installed. '
                             'It can be installed using `pip install jxmlease`')

    filter_spec = (filter_type, filter) if filter_type else None

    if source is not None:
        response = get_config(module, source, filter_spec, execute_lock)
    else:
        response = get(module, filter_spec, execute_lock)

    xml_resp = to_text(tostring(response))
    output = None

    if display == 'xml':
        output = remove_namespaces(xml_resp)
    elif display == 'json':
        try:
            output = jxmlease.parse(xml_resp)
        except Exception:
            raise ValueError(xml_resp)
    elif display == 'pretty':
        output = to_text(tostring(response, pretty_print=True))

    result = {
        'stdout': xml_resp,
        'output': output
    }

    module.exit_json(**result)


if __name__ == '__main__':
    main()
