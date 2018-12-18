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
module: netscaler_gslb_site
short_description: Manage gslb site entities in Netscaler.
description:
    - Manage gslb site entities in Netscaler.

version_added: "2.4.0"

author: George Nikolopoulos (@giorgos-nikolopoulos)

options:

    sitename:
        description:
            - >-
                Name for the GSLB site. Must begin with an ASCII alphanumeric or underscore C(_) character, and must
                contain only ASCII alphanumeric, underscore C(_), hash C(#), period C(.), space C( ), colon C(:), at C(@), equals
                C(=), and hyphen C(-) characters. Cannot be changed after the virtual server is created.
            - "Minimum length = 1"

    sitetype:
        choices:
            - 'REMOTE'
            - 'LOCAL'
        description:
            - >-
                Type of site to create. If the type is not specified, the appliance automatically detects and sets
                the type on the basis of the IP address being assigned to the site. If the specified site IP address
                is owned by the appliance (for example, a MIP address or SNIP address), the site is a local site.
                Otherwise, it is a remote site.

    siteipaddress:
        description:
            - >-
                IP address for the GSLB site. The GSLB site uses this IP address to communicate with other GSLB
                sites. For a local site, use any IP address that is owned by the appliance (for example, a SNIP or
                MIP address, or the IP address of the ADNS service).
            - "Minimum length = 1"

    publicip:
        description:
            - >-
                Public IP address for the local site. Required only if the appliance is deployed in a private address
                space and the site has a public IP address hosted on an external firewall or a NAT device.
            - "Minimum length = 1"

    metricexchange:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - >-
                Exchange metrics with other sites. Metrics are exchanged by using Metric Exchange Protocol (MEP). The
                appliances in the GSLB setup exchange health information once every second.
            - >-
                If you disable metrics exchange, you can use only static load balancing methods (such as round robin,
                static proximity, or the hash-based methods), and if you disable metrics exchange when a dynamic load
                balancing method (such as least connection) is in operation, the appliance falls back to round robin.
                Also, if you disable metrics exchange, you must use a monitor to determine the state of GSLB
                services. Otherwise, the service is marked as DOWN.

    nwmetricexchange:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - >-
                Exchange, with other GSLB sites, network metrics such as round-trip time (RTT), learned from
                communications with various local DNS (LDNS) servers used by clients. RTT information is used in the
                dynamic RTT load balancing method, and is exchanged every 5 seconds.

    sessionexchange:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - "Exchange persistent session entries with other GSLB sites every five seconds."

    triggermonitor:
        choices:
            - 'ALWAYS'
            - 'MEPDOWN'
            - 'MEPDOWN_SVCDOWN'
        description:
            - >-
                Specify the conditions under which the GSLB service must be monitored by a monitor, if one is bound.
                Available settings function as follows:
            - "* C(ALWAYS) - Monitor the GSLB service at all times."
            - >-
                * C(MEPDOWN) - Monitor the GSLB service only when the exchange of metrics through the Metrics Exchange
                Protocol (MEP) is disabled.
            - "C(MEPDOWN_SVCDOWN) - Monitor the service in either of the following situations:"
            - "* The exchange of metrics through MEP is disabled."
            - >-
                * The exchange of metrics through MEP is enabled but the status of the service, learned through
                metrics exchange, is DOWN.

    parentsite:
        description:
            - "Parent site of the GSLB site, in a parent-child topology."

    clip:
        description:
            - >-
                Cluster IP address. Specify this parameter to connect to the remote cluster site for GSLB auto-sync.
                Note: The cluster IP address is defined when creating the cluster.

    publicclip:
        description:
            - >-
                IP address to be used to globally access the remote cluster when it is deployed behind a NAT. It can
                be same as the normal cluster IP address.

    naptrreplacementsuffix:
        description:
            - >-
                The naptr replacement suffix configured here will be used to construct the naptr replacement field in
                NAPTR record.
            - "Minimum length = 1"


extends_documentation_fragment: netscaler
requirements:
    - nitro python sdk
'''

EXAMPLES = '''
- name: Setup gslb site
  delegate_to: localhost
  netscaler_gslb_site:
    nsip: 172.18.0.2
    nitro_user: nsroot
    nitro_pass: nsroot

    sitename: gslb-site-1
    siteipaddress: 192.168.1.1
    sitetype: LOCAL
    publicip: 192.168.1.1
    metricexchange: enabled
    nwmetricexchange: enabled
    sessionexchange: enabled
    triggermonitor: ALWAYS

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
    type: str
    sample: "Action does not exist"

diff:
    description: List of differences between the actual configured object and the configuration specified in the module
    returned: failure
    type: dict
    sample: "{ 'targetlbvserver': 'difference. ours: (str) server1 other: (str) server2' }"
'''

try:
    from nssrc.com.citrix.netscaler.nitro.resource.config.gslb.gslbsite import gslbsite
    from nssrc.com.citrix.netscaler.nitro.exception.nitro_exception import nitro_exception
    PYTHON_SDK_IMPORTED = True
except ImportError as e:
    PYTHON_SDK_IMPORTED = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netscaler.netscaler import (
    ConfigProxy,
    get_nitro_client,
    netscaler_common_arguments,
    log,
    loglines,
    ensure_feature_is_enabled,
    get_immutables_intersection,
)


def gslb_site_exists(client, module):
    if gslbsite.count_filtered(client, 'sitename:%s' % module.params['sitename']) > 0:
        return True
    else:
        return False


def gslb_site_identical(client, module, gslb_site_proxy):
    gslb_site_list = gslbsite.get_filtered(client, 'sitename:%s' % module.params['sitename'])
    diff_dict = gslb_site_proxy.diff_object(gslb_site_list[0])
    if len(diff_dict) == 0:
        return True
    else:
        return False


def diff_list(client, module, gslb_site_proxy):
    gslb_site_list = gslbsite.get_filtered(client, 'sitename:%s' % module.params['sitename'])
    return gslb_site_proxy.diff_object(gslb_site_list[0])


def main():

    module_specific_arguments = dict(
        sitename=dict(type='str'),
        sitetype=dict(
            type='str',
            choices=[
                'REMOTE',
                'LOCAL',
            ]
        ),
        siteipaddress=dict(type='str'),
        publicip=dict(type='str'),
        metricexchange=dict(
            type='str',
            choices=[
                'enabled',
                'disabled',
            ]
        ),
        nwmetricexchange=dict(
            type='str',
            choices=[
                'enabled',
                'disabled',
            ]
        ),
        sessionexchange=dict(
            type='str',
            choices=[
                'enabled',
                'disabled',
            ]
        ),
        triggermonitor=dict(
            type='str',
            choices=[
                'ALWAYS',
                'MEPDOWN',
                'MEPDOWN_SVCDOWN',
            ]
        ),
        parentsite=dict(type='str'),
        clip=dict(type='str'),
        publicclip=dict(type='str'),
        naptrreplacementsuffix=dict(type='str'),
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
        'sitename',
        'sitetype',
        'siteipaddress',
        'publicip',
        'metricexchange',
        'nwmetricexchange',
        'sessionexchange',
        'triggermonitor',
        'parentsite',
        'clip',
        'publicclip',
        'naptrreplacementsuffix',
    ]

    readonly_attrs = [
        'status',
        'persistencemepstatus',
        'version',
        '__count',
    ]

    immutable_attrs = [
        'sitename',
        'sitetype',
        'siteipaddress',
        'publicip',
        'parentsite',
        'clip',
        'publicclip',
    ]

    transforms = {
        'metricexchange': [lambda v: v.upper()],
        'nwmetricexchange': [lambda v: v.upper()],
        'sessionexchange': [lambda v: v.upper()],
    }

    # Instantiate config proxy
    gslb_site_proxy = ConfigProxy(
        actual=gslbsite(),
        client=client,
        attribute_values_dict=module.params,
        readwrite_attrs=readwrite_attrs,
        readonly_attrs=readonly_attrs,
        immutable_attrs=immutable_attrs,
        transforms=transforms,
    )

    try:
        ensure_feature_is_enabled(client, 'GSLB')

        # Apply appropriate state
        if module.params['state'] == 'present':
            log('Applying actions for state present')
            if not gslb_site_exists(client, module):
                if not module.check_mode:
                    gslb_site_proxy.add()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            elif not gslb_site_identical(client, module, gslb_site_proxy):

                # Check if we try to change value of immutable attributes
                immutables_changed = get_immutables_intersection(gslb_site_proxy, diff_list(client, module, gslb_site_proxy).keys())
                if immutables_changed != []:
                    module.fail_json(
                        msg='Cannot update immutable attributes %s' % (immutables_changed,),
                        diff=diff_list(client, module, gslb_site_proxy),
                        **module_result
                    )

                if not module.check_mode:
                    gslb_site_proxy.update()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            else:
                module_result['changed'] = False

            # Sanity check for state
            if not module.check_mode:
                log('Sanity checks for state present')
                if not gslb_site_exists(client, module):
                    module.fail_json(msg='GSLB site does not exist', **module_result)
                if not gslb_site_identical(client, module, gslb_site_proxy):
                    module.fail_json(msg='GSLB site differs from configured', diff=diff_list(client, module, gslb_site_proxy), **module_result)

        elif module.params['state'] == 'absent':
            log('Applying actions for state absent')
            if gslb_site_exists(client, module):
                if not module.check_mode:
                    gslb_site_proxy.delete()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            else:
                module_result['changed'] = False

            # Sanity check for state
            if not module.check_mode:
                log('Sanity checks for state absent')
                if gslb_site_exists(client, module):
                    module.fail_json(msg='GSLB site still exists', **module_result)

    except nitro_exception as e:
        msg = "nitro exception errorcode=%s, message=%s" % (str(e.errorcode), e.message)
        module.fail_json(msg=msg, **module_result)

    client.logout()
    module.exit_json(**module_result)


if __name__ == "__main__":
    main()
