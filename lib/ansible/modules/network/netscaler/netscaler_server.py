#!/usr/bin/python
# -*- coding: utf-8 -*-

#  Copyright (c) 2017 Citrix Systems
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: netscaler_server
short_description: Manage server configuration
description:
    - Manage server entities configuration.
    - This module is intended to run either on the ansible  control node or a bastion (jumpserver) with access to the actual netscaler instance.

version_added: "2.4.0"

author: George Nikolopoulos (@giorgos-nikolopoulos)

options:
    name:
        description:
            - "Name for the server."
            - >-
                Must begin with an ASCII alphabetic or underscore C(_) character, and must contain only ASCII
                alphanumeric, underscore C(_), hash C(#), period C(.), space C( ), colon C(:), at C(@), equals C(=), and hyphen C(-)
                characters.
            - "Can be changed after the name is created."
            - "Minimum length = 1"

    ipaddress:
        description:
            - >-
                IPv4 or IPv6 address of the server. If you create an IP address based server, you can specify the
                name of the server, instead of its IP address, when creating a service. Note: If you do not create a
                server entry, the server IP address that you enter when you create a service becomes the name of the
                server.

    domain:
        description:
            - "Domain name of the server. For a domain based configuration, you must create the server first."
            - "Minimum length = 1"

    translationip:
        description:
            - "IP address used to transform the server's DNS-resolved IP address."

    translationmask:
        description:
            - "The netmask of the translation ip."

    domainresolveretry:
        description:
            - >-
                Time, in seconds, for which the NetScaler appliance must wait, after DNS resolution fails, before
                sending the next DNS query to resolve the domain name.
            - "Minimum value = C(5)"
            - "Maximum value = C(20939)"
        default: 5

    ipv6address:
        description:
            - >-
                Support IPv6 addressing mode. If you configure a server with the IPv6 addressing mode, you cannot use
                the server in the IPv4 addressing mode.
        default: false
        type: bool

    comment:
        description:
            - "Any information about the server."

    td:
        description:
            - >-
                Integer value that uniquely identifies the traffic domain in which you want to configure the entity.
                If you do not specify an ID, the entity becomes part of the default traffic domain, which has an ID
                of 0.
            - "Minimum value = C(0)"
            - "Maximum value = C(4094)"

    graceful:
        description:
            - >-
                Shut down gracefully, without accepting any new connections, and disabling each service when all of
                its connections are closed.
            - This option is meaningful only when setting the I(disabled) option to C(true)
        type: bool
        version_added: "2.5"

    delay:
        description:
            - Time, in seconds, after which all the services configured on the server are disabled.
            - This option is meaningful only when setting the I(disabled) option to C(true)
        version_added: "2.5"

    disabled:
        description:
            - When set to C(true) the server state will be set to C(disabled).
            - When set to C(false) the server state will be set to C(enabled).
            - >-
                Note that due to limitations of the underlying NITRO API a C(disabled) state change alone
                does not cause the module result to report a changed status.
        type: bool
        default: false

extends_documentation_fragment: netscaler
requirements:
    - nitro python sdk
'''

EXAMPLES = '''
- name: Setup server
  delegate_to: localhost
  netscaler_server:
      nsip: 172.18.0.2
      nitro_user: nsroot
      nitro_pass: nsroot

      state: present

      name: server-1
      ipaddress: 192.168.1.1
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
    sample: "Action does not exist"

diff:
    description: List of differences between the actual configured object and the configuration specified in the module
    returned: failure
    type: dict
    sample: { 'targetlbvserver': 'difference. ours: (str) server1 other: (str) server2' }
'''

try:
    from nssrc.com.citrix.netscaler.nitro.resource.config.basic.server import server
    from nssrc.com.citrix.netscaler.nitro.exception.nitro_exception import nitro_exception
    PYTHON_SDK_IMPORTED = True
except ImportError as e:
    PYTHON_SDK_IMPORTED = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netscaler.netscaler import ConfigProxy, get_nitro_client, netscaler_common_arguments, log, loglines, \
    get_immutables_intersection


def server_exists(client, module):
    log('Checking if server exists')
    if server.count_filtered(client, 'name:%s' % module.params['name']) > 0:
        return True
    else:
        return False


def server_identical(client, module, server_proxy):
    log('Checking if configured server is identical')
    if server.count_filtered(client, 'name:%s' % module.params['name']) == 0:
        return False
    diff = diff_list(client, module, server_proxy)

    # Remove options that are not present in nitro server object
    # These are special options relevant to the disabled action
    for option in ['graceful', 'delay']:
        if option in diff:
            del diff[option]

    if diff == {}:
        return True
    else:
        return False


def diff_list(client, module, server_proxy):
    ret_val = server_proxy.diff_object(server.get_filtered(client, 'name:%s' % module.params['name'])[0]),
    return ret_val[0]


def do_state_change(client, module, server_proxy):
    if module.params['disabled']:
        log('Disabling server')
        result = server.disable(client, server_proxy.actual)
    else:
        log('Enabling server')
        result = server.enable(client, server_proxy.actual)
    return result


def main():

    module_specific_arguments = dict(
        name=dict(type='str'),
        ipaddress=dict(type='str'),
        domain=dict(type='str'),
        translationip=dict(type='str'),
        translationmask=dict(type='str'),
        domainresolveretry=dict(type='int'),
        ipv6address=dict(
            type='bool',
            default=False
        ),
        comment=dict(type='str'),
        td=dict(type='float'),
        graceful=dict(type='bool'),
        delay=dict(type='float')
    )

    hand_inserted_arguments = dict(
        disabled=dict(
            type='bool',
            default=False,
        ),
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

    # Instantiate Server Config object
    readwrite_attrs = [
        'name',
        'ipaddress',
        'domain',
        'translationip',
        'translationmask',
        'domainresolveretry',
        'ipv6address',
        'graceful',
        'delay',
        'comment',
        'td',
    ]

    readonly_attrs = [
        'statechangetimesec',
        'tickssincelaststatechange',
        'autoscale',
        'customserverid',
        'monthreshold',
        'maxclient',
        'maxreq',
        'maxbandwidth',
        'usip',
        'cka',
        'tcpb',
        'cmp',
        'clttimeout',
        'svrtimeout',
        'cipheader',
        'cip',
        'cacheable',
        'sc',
        'sp',
        'downstateflush',
        'appflowlog',
        'boundtd',
        '__count',
    ]

    immutable_attrs = [
        'name',
        'domain',
        'ipv6address',
        'td',
    ]

    transforms = {
        'graceful': ['bool_yes_no'],
        'ipv6address': ['bool_yes_no'],
    }

    server_proxy = ConfigProxy(
        actual=server(),
        client=client,
        attribute_values_dict=module.params,
        readwrite_attrs=readwrite_attrs,
        readonly_attrs=readonly_attrs,
        immutable_attrs=immutable_attrs,
        transforms=transforms,
    )

    try:

        # Apply appropriate state
        if module.params['state'] == 'present':
            log('Applying actions for state present')
            if not server_exists(client, module):
                if not module.check_mode:
                    server_proxy.add()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            elif not server_identical(client, module, server_proxy):

                # Check if we try to change value of immutable attributes
                immutables_changed = get_immutables_intersection(server_proxy, diff_list(client, module, server_proxy).keys())
                if immutables_changed != []:
                    msg = 'Cannot update immutable attributes %s' % (immutables_changed,)
                    module.fail_json(msg=msg, diff=diff_list(client, module, server_proxy), **module_result)
                if not module.check_mode:
                    server_proxy.update()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            else:
                module_result['changed'] = False

            if not module.check_mode:
                res = do_state_change(client, module, server_proxy)
                if res.errorcode != 0:
                    msg = 'Error when setting disabled state. errorcode: %s message: %s' % (res.errorcode, res.message)
                    module.fail_json(msg=msg, **module_result)

            # Sanity check for result
            log('Sanity checks for state present')
            if not module.check_mode:
                if not server_exists(client, module):
                    module.fail_json(msg='Server does not seem to exist', **module_result)
                if not server_identical(client, module, server_proxy):
                    module.fail_json(
                        msg='Server is not configured according to parameters given',
                        diff=diff_list(client, module, server_proxy),
                        **module_result
                    )

        elif module.params['state'] == 'absent':
            log('Applying actions for state absent')
            if server_exists(client, module):
                if not module.check_mode:
                    server_proxy.delete()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            else:
                module_result['changed'] = False

            # Sanity check for result
            log('Sanity checks for state absent')
            if not module.check_mode:
                if server_exists(client, module):
                    module.fail_json(msg='Server seems to be present', **module_result)

    except nitro_exception as e:
        msg = "nitro exception errorcode=%s, message=%s" % (str(e.errorcode), e.message)
        module.fail_json(msg=msg, **module_result)

    client.logout()
    module.exit_json(**module_result)


if __name__ == "__main__":
    main()
