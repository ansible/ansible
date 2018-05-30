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
module: netconf_set
version_added: "2.6"
author:
    - "Ganesh Nalawade (@ganeshrn)"
    - "Sven Wisotzky (@wisotzky)"
short_description: NETCONF module to modify device configuration
description:
    - NETCONF is a network management protocol developed and standardized by
      the IETF. It is documented in RFC 6241.
    - This module allows the user to change the configuration of NETCONF
      enabled network devices.
options:
  content:
    description:
      - This argument contains the configuration set to be pushed via I(edit-config)
        operation to the remote device. The I(content) value can either be provided
        as XML formatted string or as dictionary (JSON or YAML format).
  xmlns:
    description:
      - Defines the XML namespace to be used when rendering I(content) from JSON/YAML.
  operation:
    description:
      - Defined the I(default-operation) for the NETCONF I(edit-config) operation
    choices: ['merge', 'replace', 'none']
  lock:
    description:
      - Instructs the module to explicitly lock the target datastore while applying
        the configuration change to the remote device. If the value is I(never) the
        datastore is NOT locked. If the value is I(always) the target datastore will
        always be locked during the operation. If the value is I(if-supported) this
        module will only lock the datastore, if supported by the device - or issue
        a warning if not supported by the device.
    choices: ['never', 'always', 'if-supported']
    default: 'always'
  mode:
    description:
     - This option controls, what should happen with this configuraiton change. If
       the value is set to 'deploy' (default) it will change the target datastore
       and commit the changes.
       If the value is set to 'dryrun' it will push the config to the candidate
       datastore. The value of the candidate is compared before and after the
       edit-config. In conclusion dryrun can be used to see, if applying this change
       would result in changes or to audit, if the configuration is as expected.
    choices: ['deploy', 'validate', 'dryrun']
    default: 'deploy'
  backup:
    description:
     - If the configuration was changed and this option is set to I(True), this
       module will save a copy of the configuration with a unique filename
       in the backup directory of the playbook.
       This option will only be active in case of mode is I(deploy).
  display:
    description:
     - If this option is set, it will instruct this module to include the differences
       in the RETURN values. The option value I(xml) will include a complete copy
       of the target datastore before and after the change.
       The option value I(json) and I(json_string) will contain an RFC6902 compliant
       jsonpatch either as native list/dict or in string format.
    choices: ['json', 'json_string', 'xml']

requirements:
  - ncclient (>=v0.5.2)
  - jxmlease
  - jsonpatch

notes:
  - This module supports the use of connection=netconf.
  - This module requires the NETCONF system service be enabled on the remote device.
  - The module will execute the following actions
      Lock target datastore (depended on option I(lock))
      Discard changes, in case of target datastore is candidate
      get-config of target datastore (before the change)
      edit-config
      get-config of target datastore (after the change)
      Commit changes, in case of target datastore is candidate (not when dryrun)
      Unlock target datastore (depends on option I(lock))
  - To provide content in XML format is the more flexible variant increasing control
      Control the ordering of dict entries in the output
      Provide multiple XML namespaces (per XML note/attribute)
      Provide edit-config operations (e.g. to delete content)
  - Support for content in JSON/YAML format is to improve the playbook's readability
    (specific encoding rules apply for lists - check examples)
"""

EXAMPLES = """
- name: Add customer (Nokia SROS)
  netconf_set:
    content: |
        <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
          <configure xmlns="urn:nokia.com:sros:ns:yang:sr:conf">
            <service>
              <customer operation="merge">
                <customer-id>100</customer-id>
                <customer-name>acme-user</customer-name>
              </customer>
            </service>
          </configure>
        </config>
    backup: true

- name: Add 2 customers (Nokia SROS)
  netconf_set:
    content:
      configure:
        service:
          customer:
            - customer-name: "bravo"
              customer-id: 200
            - customer-name: "charlie"
              customer-id: 300
    xmlns: "urn:nokia.com:sros:ns:yang:sr:conf"
    operation: merge
    mode: dryrun
    lock: always
    display: json
  register: result
"""

RETURN = """
locked:
  description:
    - Returns I(true) if the target datastore was locked/unlocked during the operation.
  returned: always
  type: boolean
changed:
  description:
    - Returns I(true) if the target datastore was changed by that operation. Returns
      I(false) if the edit-config does not result in changes or dryrun is exectued.
  returned: always
  type: boolean
datastore:
  description:
    - The target datastore is automatically determined by presence of the :candidate and
      :writable-running capabilities. By default the module will use I(candidate) and fallback
      to I(running). The return value I(candidate) gives the caller an indication, which
      datastore has been automatically selected.
  returned: always
  type: string
diffs:
  description:
    - Contains the differences of the target datastore before and after the change.
      If option I(display) is not set, it will simply return I(true) or I(false).
  returned: always
  type: complex
"""

import ast
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
from ansible.module_utils.network.common.netconf import remove_namespaces

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import ConnectionError
import ansible.module_utils.network.netconf.netconf as netconf

try:
    import jxmlease
    HAS_JXMLEASE = True
except ImportError:
    HAS_JXMLEASE = False

try:
    import jsonpatch
    HAS_JSONPATCH = True
except ImportError:
    HAS_JSONPATCH = False


def get_xml_content(module, content, xmlns):
    if isinstance(content, str):
        if content.startswith('<') and content.endswith('>'):
            # assumption content contains already XML payload
            return content

        try:
            # trying if content contains dict
            content = ast.literal_eval(content)
        except:
            module.fail_json(msg='unsupported content value `%s`' % content)

    if isinstance(content, dict):
        if not HAS_JXMLEASE:
            module.fail_json(msg='jxmlease is required to convert RPC content to XML '
                                 'but does not appear to be installed. '
                                 'It can be installed using `pip install jxmlease`')

        payload = jxmlease.XMLDictNode(content).emit_xml(pretty=False, full_document=False)

        if xmlns is not None:
            payload = re.sub(r'(<[\w-]+)([^>]*>)', r'\1 xmlns="%s"\2' % xmlns, payload, count=1)

        return '<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">%s</config>' % payload

    module.fail_json(msg='unsupported content data-type `%s`' % type(content).__name__)
    return ""


def main():
    """entry point for module execution
    """
    argument_spec = dict(
        content=dict(required=True),
        xmlns=dict(type="str"),
        operation=dict(choices=['merge', 'replace', 'none']),
        lock=dict(default='always', choices=['never', 'always', 'if-supported']),
        backup=dict(type="bool", default=False),
        mode=dict(default='deploy', choices=['deploy', 'validate', 'dryrun']),
        display=dict(choices=['json', 'json_string', 'xml'])
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    content = module.params['content']
    xmlns = module.params['xmlns']
    operation = module.params['operation']
    lock = module.params['lock']
    backup = module.params['backup']
    mode = module.params['mode']
    display = module.params['display']

    capabilities = netconf.get_capabilities(module)
    operations = capabilities['device_operations']

    # check attributes
    if backup and mode != 'deploy':
        module.warn('will only create backups in case of mode=deploy')

    if display in ['json', 'json_string']:
        if not HAS_JXMLEASE:
            module.fail_json(msg='jxmlease is required to for display option `%s` '
                                 'but does not appear to be installed. '
                                 'It can be installed using `pip install jxmlease`' % display)
        if not HAS_JSONPATCH:
            module.fail_json(msg='jsonpatch is required to for display option `%s` '
                                 'but does not appear to be installed. '
                                 'It can be installed using `pip install jsonpatch`' % display)

    # determine: target datastore
    if operations.get('supports_commit', False):
        datastore = 'candidate'
    elif operations.get('supports_writable_running', False):
        if mode == 'deploy':
            datastore = 'running'
        else:
            module.fail_json(msg='mode `%s` requires :candidate supported' % mode)
    else:
        module.fail_json(msg='neither :candidate nor :writeable-running are supported')

    # evaluate: lock option
    if lock == 'never':
        execute_lock = False
    elif datastore in operations.get('lock_datastore', []):
        # lock is requested (always/if-support) and supported => lets do it
        execute_lock = True
    else:
        # lock is requested (always/if-supported) but not supported => issue warning
        module.warn('lock operation on `%s` source is not supported on this device' % datastore)
        execute_lock = lock is 'always'

    # content-builder
    if content is None:
        module.fail_json(msg='argument `content` must not be None')

    content = content.strip()
    if len(content) == 0:
        module.fail_json(msg='argument `content` must not be empty')

    content = get_xml_content(module, content, xmlns)

    # execute: netconf request(s)
    try:
        locked = False
        if execute_lock:
            netconf.lock_configuration(module, target=datastore)
            locked = True

        if datastore == 'candidate':
            netconf.discard_changes(module)

        response = netconf.get_config(module, source=datastore)
        before = tostring(response)

        netconf.edit_config(module, target=datastore, config=content, default_operation=operation)

        response = netconf.get_config(module, source=datastore)
        after = tostring(response)

        changed = False
        if before != after:
            if mode == 'validate':
                try:
                    netconf.validate(module, source=datastore)
                except ConnectionError as e:
                    module.fail_json(msg="validation failed with error")

            if mode == 'deploy':
                if (datastore == 'candidate'):
                    if operations.get('supports_confirmed_commit', False):
                        netconf.commit(module, confirmed=True)
                    netconf.commit(module)

                changed = True

                if operations.get('supports_startup', False):
                    netconf.copy_config(module, source="running", target="startup")

            if mode in ['validate', 'dryrun']:
                netconf.discard_changes(module)

    except ConnectionError as e:
        module.fail_json(msg=to_text(e, errors='surrogate_then_replace').strip())

    finally:
        if locked:
            netconf.unlock_configuration(module, target=datastore)

    result = {
        'changed': changed,
        'locked': locked,
        'datastore': datastore,
        'diffs': (before != after)
    }

    if backup and changed:
        result['__backup__'] = before

    if before != after:
        if display == 'xml':
            result['diffs'] = {'before': before, 'after': after}

        elif display == 'json':
            tmp1 = jxmlease.parse(before).prettyprint(currdepth=1)
            tmp2 = jxmlease.parse(after).prettyprint(currdepth=1)
            patch = jsonpatch.make_patch(tmp1, tmp2)
            result['diffs'] = patch.patch

        elif display == 'json_string':
            tmp1 = jxmlease.parse(before).prettyprint(currdepth=1)
            tmp2 = jxmlease.parse(after).prettyprint(currdepth=1)
            patch = jsonpatch.make_patch(tmp1, tmp2)
            result['diffs'] = patch.to_string()

        # warning:
        #   diff result might become unnecessary complex using jsonpatch:
        #   https://github.com/stefankoegl/python-json-patch/issues/78
        # todo:
        #   Check alternative implementation options to compare the datastore
        #   content before and after the change.

    module.exit_json(**result)

if __name__ == '__main__':
    main()
