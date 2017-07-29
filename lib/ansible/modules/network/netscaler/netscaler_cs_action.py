#!/usr/bin/python
# -*- coding: utf-8 -*-

#  Copyright (c) 2017 Citrix Systems
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}


DOCUMENTATION = '''
---
module: netscaler_cs_action
short_description: Manage content switching actions
description:
    - Manage content switching actions
    - This module is intended to run either on the ansible  control node or a bastion (jumpserver) with access to the actual netscaler instance

version_added: "2.4.0"

author: George Nikolopoulos (@giorgos-nikolopoulos)

options:

    name:
        description:
            - >-
                Name for the content switching action. Must begin with an ASCII alphanumeric or underscore C(_)
                character, and must contain only ASCII alphanumeric, underscore C(_), hash C(#), period C(.), space C( ), colon
                C(:), at sign C(@), equal sign C(=), and hyphen C(-) characters. Can be changed after the content
                switching action is created.

    targetlbvserver:
        description:
            - "Name of the load balancing virtual server to which the content is switched."

    targetvserver:
        description:
            - "Name of the VPN virtual server to which the content is switched."

    targetvserverexpr:
        description:
            - "Information about this content switching action."

    comment:
        description:
            - "Comments associated with this cs action."

extends_documentation_fragment: netscaler
requirements:
    - nitro python sdk
'''

EXAMPLES = '''
# lb_vserver_1 must have been already created with the netscaler_lb_vserver module

- name: Configure netscaler content switching action
  delegate_to: localhost
  netscaler_cs_action:
      nsip: 172.18.0.2
      nitro_user: nsroot
      nitro_pass: nsroot
      validate_certs: no

      state: present

      name: action-1
      targetlbvserver: lb_vserver_1
'''

RETURN = '''
loglines:
    description: list of logged messages by the module
    returned: always
    type: list
    sample: "['message 1', 'message 2']"

msg:
    description: Message detailing the failure reason
    returned: failure
    type: string
    sample: "Action does not exist"

diff:
    description: List of differences between the actual configured object and the configuration specified in the module
    returned: failure
    type: dictionary
    sample: "{ 'targetlbvserver': 'difference. ours: (str) server1 other: (str) server2' }"
'''

import json

try:
    from nssrc.com.citrix.netscaler.nitro.resource.config.cs.csaction import csaction
    from nssrc.com.citrix.netscaler.nitro.exception.nitro_exception import nitro_exception
    PYTHON_SDK_IMPORTED = True
except ImportError as e:
    PYTHON_SDK_IMPORTED = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netscaler import (
    ConfigProxy,
    get_nitro_client,
    netscaler_common_arguments,
    log, loglines,
    ensure_feature_is_enabled,
    get_immutables_intersection
)


def action_exists(client, module):
    if csaction.count_filtered(client, 'name:%s' % module.params['name']) > 0:
        return True
    else:
        return False


def action_identical(client, module, csaction_proxy):
    if len(diff_list(client, module, csaction_proxy)) == 0:
        return True
    else:
        return False


def diff_list(client, module, csaction_proxy):
    action_list = csaction.get_filtered(client, 'name:%s' % module.params['name'])
    diff_list = csaction_proxy.diff_object(action_list[0])
    if False and 'targetvserverexpr' in diff_list:
        json_value = json.loads(action_list[0].targetvserverexpr)
        if json_value == module.params['targetvserverexpr']:
            del diff_list['targetvserverexpr']
    return diff_list


def main():

    module_specific_arguments = dict(

        name=dict(type='str'),
        targetlbvserver=dict(type='str'),
        targetvserverexpr=dict(type='str'),
        comment=dict(type='str'),
    )

    argument_spec = dict()

    argument_spec.update(netscaler_common_arguments)

    argument_spec.update(module_specific_arguments)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    module_result = dict(
        changed=False,
        failed=False,
        loglines=loglines
    )

    # Fail the module if imports failed
    if not PYTHON_SDK_IMPORTED:
        module.fail_json(msg='Could not load nitro python sdk')

    # Fallthrough to rest of execution
    client = get_nitro_client(module)

    try:
        client.login()
    except nitro_exception as e:
        msg = "nitro exception during login. errorcode=%s, message=%s" % (str(e.errorcode), e.message)
        module.fail_json(msg=msg)
    except Exception as e:
        if str(type(e)) == "<class 'requests.exceptions.ConnectionError'>":
            module.fail_json(msg='Connection error %s' % str(e))
        elif str(type(e)) == "<class 'requests.exceptions.SSLError'>":
            module.fail_json(msg='SSL Error %s' % str(e))
        else:
            module.fail_json(msg='Unexpected error during login %s' % str(e))

    readwrite_attrs = [
        'name',
        'targetlbvserver',
        'targetvserverexpr',
        'comment',
    ]
    readonly_attrs = [
        'hits',
        'referencecount',
        'undefhits',
        'builtin',
    ]

    immutable_attrs = [
        'name',
        'targetvserverexpr',
    ]

    transforms = {
    }

    json_encodes = ['targetvserverexpr']

    # Instantiate config proxy
    csaction_proxy = ConfigProxy(
        actual=csaction(),
        client=client,
        attribute_values_dict=module.params,
        readwrite_attrs=readwrite_attrs,
        readonly_attrs=readonly_attrs,
        immutable_attrs=immutable_attrs,
        transforms=transforms,
        json_encodes=json_encodes,
    )

    try:

        ensure_feature_is_enabled(client, 'CS')
        # Apply appropriate state
        if module.params['state'] == 'present':
            log('Applying actions for state present')
            if not action_exists(client, module):
                if not module.check_mode:
                    csaction_proxy.add()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            elif not action_identical(client, module, csaction_proxy):

                # Check if we try to change value of immutable attributes
                immutables_changed = get_immutables_intersection(csaction_proxy, diff_list(client, module, csaction_proxy).keys())
                if immutables_changed != []:
                    module.fail_json(
                        msg='Cannot update immutable attributes %s' % (immutables_changed,),
                        diff=diff_list(client, module, csaction_proxy),
                        **module_result
                    )

                if not module.check_mode:
                    csaction_proxy.update()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            else:
                module_result['changed'] = False

            # Sanity check for state
            log('Sanity checks for state present')
            if not module.check_mode:
                if not action_exists(client, module):
                    module.fail_json(msg='Content switching action does not exist', **module_result)
                if not action_identical(client, module, csaction_proxy):
                    module.fail_json(
                        msg='Content switching action differs from configured',
                        diff=diff_list(client, module, csaction_proxy),
                        **module_result
                    )

        elif module.params['state'] == 'absent':
            log('Applying actions for state absent')
            if action_exists(client, module):
                if not module.check_mode:
                    csaction_proxy.delete()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            else:
                module_result['changed'] = False

            # Sanity check for state
            if not module.check_mode:
                log('Sanity checks for state absent')
                if action_exists(client, module):
                    module.fail_json(msg='Content switching action still exists', **module_result)

    except nitro_exception as e:
        msg = "nitro exception errorcode=%s, message=%s" % (str(e.errorcode), e.message)
        module.fail_json(msg=msg, **module_result)

    client.logout()
    module.exit_json(**module_result)


if __name__ == "__main__":
    main()
