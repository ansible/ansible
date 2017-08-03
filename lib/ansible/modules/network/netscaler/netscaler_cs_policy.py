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
module: netscaler_cs_policy
short_description: Manage content switching policy
description:
    - Manage content switching policy.
    - "This module is intended to run either on the ansible  control node or a bastion (jumpserver) with access to the actual netscaler instance."

version_added: "2.4"

author: George Nikolopoulos (@giorgos-nikolopoulos)

options:

    policyname:
        description:
            - >-
                Name for the content switching policy. Must begin with an ASCII alphanumeric or underscore C(_)
                character, and must contain only ASCII alphanumeric, underscore, hash C(#), period C(.), space C( ), colon
                C(:), at sign C(@), equal sign C(=), and hyphen C(-) characters. Cannot be changed after a policy is
                created.
            - "The following requirement applies only to the NetScaler CLI:"
            - >-
                If the name includes one or more spaces, enclose the name in double or single quotation marks (for
                example, my policy or my policy).
            - "Minimum length = 1"

    url:
        description:
            - >-
                URL string that is matched with the URL of a request. Can contain a wildcard character. Specify the
                string value in the following format: C([[prefix] [*]] [.suffix]).
            - "Minimum length = 1"
            - "Maximum length = 208"

    rule:
        description:
            - >-
                Expression, or name of a named expression, against which traffic is evaluated. Written in the classic
                or default syntax.
            - "Note:"
            - >-
                Maximum length of a string literal in the expression is 255 characters. A longer string can be split
                into smaller strings of up to 255 characters each, and the smaller strings concatenated with the +
                operator. For example, you can create a 500-character string as follows: '"<string of 255
                characters>" + "<string of 245 characters>"'

    domain:
        description:
            - "The domain name. The string value can range to 63 characters."
            - "Minimum length = 1"

    action:
        description:
            - >-
                Content switching action that names the target load balancing virtual server to which the traffic is
                switched.

extends_documentation_fragment: netscaler
requirements:
    - nitro python sdk
'''

EXAMPLES = '''
- name: Create url cs policy
  delegate_to: localhost
  netscaler_cs_policy:
    nsip: 172.18.0.2
    nitro_user: nsroot
    nitro_pass: nsroot
    validate_certs: no

    state: present

    policyname: policy_1
    url: /example/
'''

RETURN = '''
loglines:
    description: list of logged messages by the module
    returned: always
    type: list
    sample: ['message 1', 'message 2']

msg:
    description: Message detailing the failure reason
    returned: failure
    type: str
    sample: "Could not load nitro python sdk"

diff:
    description: List of differences between the actual configured object and the configuration specified in the module
    returned: failure
    type: dict
    sample: { 'url': 'difference. ours: (str) example1 other: (str) /example1' }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netscaler import ConfigProxy, get_nitro_client, netscaler_common_arguments, log, loglines, ensure_feature_is_enabled
try:
    from nssrc.com.citrix.netscaler.nitro.resource.config.cs.cspolicy import cspolicy
    from nssrc.com.citrix.netscaler.nitro.exception.nitro_exception import nitro_exception
    PYTHON_SDK_IMPORTED = True
except ImportError as e:
    PYTHON_SDK_IMPORTED = False


def policy_exists(client, module):
    log('Checking if policy exists')
    if cspolicy.count_filtered(client, 'policyname:%s' % module.params['policyname']) > 0:
        return True
    else:
        return False


def policy_identical(client, module, cspolicy_proxy):
    log('Checking if defined policy is identical to configured')
    if cspolicy.count_filtered(client, 'policyname:%s' % module.params['policyname']) == 0:
        return False
    policy_list = cspolicy.get_filtered(client, 'policyname:%s' % module.params['policyname'])
    diff_dict = cspolicy_proxy.diff_object(policy_list[0])
    if 'ip' in diff_dict:
        del diff_dict['ip']
    if len(diff_dict) == 0:
        return True
    else:
        return False


def diff_list(client, module, cspolicy_proxy):
    policy_list = cspolicy.get_filtered(client, 'policyname:%s' % module.params['policyname'])
    return cspolicy_proxy.diff_object(policy_list[0])


def main():

    module_specific_arguments = dict(
        policyname=dict(type='str'),
        url=dict(type='str'),
        rule=dict(type='str'),
        domain=dict(type='str'),
        action=dict(type='str'),
    )

    hand_inserted_arguments = dict(
    )

    argument_spec = dict()

    argument_spec.update(netscaler_common_arguments)
    argument_spec.update(module_specific_arguments)
    argument_spec.update(hand_inserted_arguments)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    module_result = dict(
        changed=False,
        failed=False,
        loglines=loglines,
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
        'policyname',
        'url',
        'rule',
        'domain',
        'action',
    ]
    readonly_attrs = [
        'vstype',
        'hits',
        'bindhits',
        'labelname',
        'labeltype',
        'priority',
        'activepolicy',
        'cspolicytype',
    ]

    transforms = {
    }

    # Instantiate config proxy
    cspolicy_proxy = ConfigProxy(
        actual=cspolicy(),
        client=client,
        attribute_values_dict=module.params,
        readwrite_attrs=readwrite_attrs,
        readonly_attrs=readonly_attrs,
        transforms=transforms,
    )

    try:
        ensure_feature_is_enabled(client, 'CS')

        # Apply appropriate state
        if module.params['state'] == 'present':
            log('Sanity checks for state present')
            if not policy_exists(client, module):
                if not module.check_mode:
                    cspolicy_proxy.add()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            elif not policy_identical(client, module, cspolicy_proxy):
                if not module.check_mode:
                    cspolicy_proxy.update()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            else:
                module_result['changed'] = False

            # Sanity check for state
            if not module.check_mode:
                log('Sanity checks for state present')
                if not policy_exists(client, module):
                    module.fail_json(msg='Policy does not exist', **module_result)
                if not policy_identical(client, module, cspolicy_proxy):
                    module.fail_json(msg='Policy differs from configured', diff=diff_list(client, module, cspolicy_proxy), **module_result)

        elif module.params['state'] == 'absent':
            log('Applying actions for state absent')
            if policy_exists(client, module):
                if not module.check_mode:
                    cspolicy_proxy.delete()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            else:
                module_result['changed'] = False

            # Sanity check for state
            if not module.check_mode:
                log('Sanity checks for state absent')
                if policy_exists(client, module):
                    module.fail_json(msg='Policy still exists', **module_result)

    except nitro_exception as e:
        msg = "nitro exception errorcode=%s, message=%s" % (str(e.errorcode), e.message)
        module.fail_json(msg=msg, **module_result)

    client.logout()
    module.exit_json(**module_result)


if __name__ == "__main__":
    main()
