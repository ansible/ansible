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
module: netscaler_gslb_service
short_description: Manage gslb service entities in Netscaler.
description:
    - Manage gslb service entities in Netscaler.

version_added: "2.4"

author: George Nikolopoulos (@giorgos-nikolopoulos)

options:

    servicename:
        description:
            - >-
                Name for the GSLB service. Must begin with an ASCII alphanumeric or underscore C(_) character, and
                must contain only ASCII alphanumeric, underscore C(_), hash C(#), period C(.), space, colon C(:), at C(@),
                equals C(=), and hyphen C(-) characters. Can be changed after the GSLB service is created.
            - >-
            - "Minimum length = 1"

    cnameentry:
        description:
            - "Canonical name of the GSLB service. Used in CNAME-based GSLB."
            - "Minimum length = 1"


    servername:
        description:
            - "Name of the server hosting the GSLB service."
            - "Minimum length = 1"

    servicetype:
        choices:
            - 'HTTP'
            - 'FTP'
            - 'TCP'
            - 'UDP'
            - 'SSL'
            - 'SSL_BRIDGE'
            - 'SSL_TCP'
            - 'NNTP'
            - 'ANY'
            - 'SIP_UDP'
            - 'SIP_TCP'
            - 'SIP_SSL'
            - 'RADIUS'
            - 'RDP'
            - 'RTSP'
            - 'MYSQL'
            - 'MSSQL'
            - 'ORACLE'
        description:
            - "Type of service to create."

    port:
        description:
            - "Port on which the load balancing entity represented by this GSLB service listens."
            - "Minimum value = 1"
            - "Range 1 - 65535"
            - "* in CLI is represented as 65535 in NITRO API"

    publicip:
        description:
            - >-
                The public IP address that a NAT device translates to the GSLB service's private IP address.
                Optional.

    publicport:
        description:
            - >-
                The public port associated with the GSLB service's public IP address. The port is mapped to the
                service's private port number. Applicable to the local GSLB service. Optional.

    maxclient:
        description:
            - >-
                The maximum number of open connections that the service can support at any given time. A GSLB service
                whose connection count reaches the maximum is not considered when a GSLB decision is made, until the
                connection count drops below the maximum.
            - "Minimum value = C(0)"
            - "Maximum value = C(4294967294)"

    healthmonitor:
        description:
            - "Monitor the health of the GSLB service."
        type: bool

    sitename:
        description:
            - "Name of the GSLB site to which the service belongs."
            - "Minimum length = 1"

    cip:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - >-
                In the request that is forwarded to the GSLB service, insert a header that stores the client's IP
                address. Client IP header insertion is used in connection-proxy based site persistence.

    cipheader:
        description:
            - >-
                Name for the HTTP header that stores the client's IP address. Used with the Client IP option. If
                client IP header insertion is enabled on the service and a name is not specified for the header, the
                NetScaler appliance uses the name specified by the cipHeader parameter in the set ns param command
                or, in the GUI, the Client IP Header parameter in the Configure HTTP Parameters dialog box.
            - "Minimum length = 1"

    sitepersistence:
        choices:
            - 'ConnectionProxy'
            - 'HTTPRedirect'
            - 'NONE'
        description:
            - "Use cookie-based site persistence. Applicable only to C(HTTP) and C(SSL) GSLB services."

    siteprefix:
        description:
            - >-
                The site's prefix string. When the service is bound to a GSLB virtual server, a GSLB site domain is
                generated internally for each bound service-domain pair by concatenating the site prefix of the
                service and the name of the domain. If the special string NONE is specified, the site-prefix string
                is unset. When implementing HTTP redirect site persistence, the NetScaler appliance redirects GSLB
                requests to GSLB services by using their site domains.

    clttimeout:
        description:
            - >-
                Idle time, in seconds, after which a client connection is terminated. Applicable if connection proxy
                based site persistence is used.
            - "Minimum value = 0"
            - "Maximum value = 31536000"

    maxbandwidth:
        description:
            - >-
                Integer specifying the maximum bandwidth allowed for the service. A GSLB service whose bandwidth
                reaches the maximum is not considered when a GSLB decision is made, until its bandwidth consumption
                drops below the maximum.

    downstateflush:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - >-
                Flush all active transactions associated with the GSLB service when its state transitions from UP to
                DOWN. Do not enable this option for services that must complete their transactions. Applicable if
                connection proxy based site persistence is used.

    maxaaausers:
        description:
            - >-
                Maximum number of SSL VPN users that can be logged on concurrently to the VPN virtual server that is
                represented by this GSLB service. A GSLB service whose user count reaches the maximum is not
                considered when a GSLB decision is made, until the count drops below the maximum.
            - "Minimum value = C(0)"
            - "Maximum value = C(65535)"

    monthreshold:
        description:
            - >-
                Monitoring threshold value for the GSLB service. If the sum of the weights of the monitors that are
                bound to this GSLB service and are in the UP state is not equal to or greater than this threshold
                value, the service is marked as DOWN.
            - "Minimum value = C(0)"
            - "Maximum value = C(65535)"

    hashid:
        description:
            - "Unique hash identifier for the GSLB service, used by hash based load balancing methods."
            - "Minimum value = C(1)"

    comment:
        description:
            - "Any comments that you might want to associate with the GSLB service."

    appflowlog:
        choices:
            - 'enabled'
            - 'disabled'
        description:
            - "Enable logging appflow flow information."

    ipaddress:
        description:
            - >-
                IP address for the GSLB service. Should represent a load balancing, content switching, or VPN virtual
                server on the NetScaler appliance, or the IP address of another load balancing device.

    monitor_bindings:
        description:
            - Bind monitors to this gslb service
        suboptions:

            weight:
                description:
                    - Weight to assign to the monitor-service binding.
                    - A larger number specifies a greater weight.
                    - Contributes to the monitoring threshold, which determines the state of the service.
                    - Minimum value = C(1)
                    - Maximum value = C(100)

            monitor_name:
                description:
                    - Monitor name.

extends_documentation_fragment: netscaler
requirements:
    - nitro python sdk
'''

EXAMPLES = '''
- name: Setup gslb service 2

  delegate_to: localhost
  register: result
  check_mode: "{{ check_mode }}"

  netscaler_gslb_service:
    operation: present

    servicename: gslb-service-2
    cnameentry: example.com
    sitename: gslb-site-1
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

import copy


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netscaler.netscaler import (
    ConfigProxy,
    get_nitro_client,
    netscaler_common_arguments,
    log,
    loglines,
    ensure_feature_is_enabled,
    monkey_patch_nitro_api,
    get_immutables_intersection,
)

try:
    monkey_patch_nitro_api()
    from nssrc.com.citrix.netscaler.nitro.resource.config.gslb.gslbservice import gslbservice
    from nssrc.com.citrix.netscaler.nitro.resource.config.gslb.gslbservice_lbmonitor_binding import gslbservice_lbmonitor_binding
    from nssrc.com.citrix.netscaler.nitro.exception.nitro_exception import nitro_exception
    PYTHON_SDK_IMPORTED = True
except ImportError as e:
    PYTHON_SDK_IMPORTED = False


def gslb_service_exists(client, module):
    if gslbservice.count_filtered(client, 'servicename:%s' % module.params['servicename']) > 0:
        return True
    else:
        return False


def gslb_service_identical(client, module, gslb_service_proxy):
    gslb_service_list = gslbservice.get_filtered(client, 'servicename:%s' % module.params['servicename'])
    diff_dict = gslb_service_proxy.diff_object(gslb_service_list[0])
    # Ignore ip attribute missing
    if 'ip' in diff_dict:
        del diff_dict['ip']
    if len(diff_dict) == 0:
        return True
    else:
        return False


def get_actual_monitor_bindings(client, module):
    log('get_actual_monitor_bindings')
    # Get actual monitor bindings and index them by monitor_name
    actual_monitor_bindings = {}
    if gslbservice_lbmonitor_binding.count(client, servicename=module.params['servicename']) != 0:
        # Get all monitor bindings associated with the named gslb vserver
        fetched_bindings = gslbservice_lbmonitor_binding.get(client, servicename=module.params['servicename'])
        # index by monitor name
        for binding in fetched_bindings:
            # complete_missing_attributes(binding, gslbservice_lbmonitor_binding_rw_attrs, fill_value=None)
            actual_monitor_bindings[binding.monitor_name] = binding
    return actual_monitor_bindings


def get_configured_monitor_bindings(client, module):
    log('get_configured_monitor_bindings')
    configured_monitor_proxys = {}
    gslbservice_lbmonitor_binding_rw_attrs = [
        'weight',
        'servicename',
        'monitor_name',
    ]
    # Get configured monitor bindings and index them by monitor_name
    if module.params['monitor_bindings'] is not None:
        for configured_monitor_bindings in module.params['monitor_bindings']:
            binding_values = copy.deepcopy(configured_monitor_bindings)
            binding_values['servicename'] = module.params['servicename']
            proxy = ConfigProxy(
                actual=gslbservice_lbmonitor_binding(),
                client=client,
                attribute_values_dict=binding_values,
                readwrite_attrs=gslbservice_lbmonitor_binding_rw_attrs,
                readonly_attrs=[],
            )
            configured_monitor_proxys[configured_monitor_bindings['monitor_name']] = proxy
    return configured_monitor_proxys


def monitor_bindings_identical(client, module):
    log('monitor_bindings_identical')
    actual_bindings = get_actual_monitor_bindings(client, module)
    configured_proxys = get_configured_monitor_bindings(client, module)

    actual_keyset = set(actual_bindings.keys())
    configured_keyset = set(configured_proxys.keys())

    symmetric_difference = actual_keyset ^ configured_keyset
    if len(symmetric_difference) != 0:
        log('Symmetric difference %s' % symmetric_difference)
        return False

    # Item for item equality test
    for key, proxy in configured_proxys.items():
        if not proxy.has_equal_attributes(actual_bindings[key]):
            log('monitor binding difference %s' % proxy.diff_object(actual_bindings[key]))
            return False

    # Fallthrough to True result
    return True


def sync_monitor_bindings(client, module):
    log('sync_monitor_bindings')

    actual_monitor_bindings = get_actual_monitor_bindings(client, module)
    configured_monitor_proxys = get_configured_monitor_bindings(client, module)

    # Delete actual bindings not in configured bindings
    for monitor_name, actual_binding in actual_monitor_bindings.items():
        if monitor_name not in configured_monitor_proxys.keys():
            log('Deleting absent binding for monitor %s' % monitor_name)
            log('dir is %s' % dir(actual_binding))
            gslbservice_lbmonitor_binding.delete(client, actual_binding)

    # Delete and re-add actual bindings that differ from configured
    for proxy_key, binding_proxy in configured_monitor_proxys.items():
        if proxy_key in actual_monitor_bindings:
            actual_binding = actual_monitor_bindings[proxy_key]
            if not binding_proxy.has_equal_attributes(actual_binding):
                log('Deleting differing binding for monitor %s' % actual_binding.monitor_name)
                log('dir %s' % dir(actual_binding))
                log('attribute monitor_name %s' % getattr(actual_binding, 'monitor_name'))
                log('attribute monitorname %s' % getattr(actual_binding, 'monitorname', None))
                gslbservice_lbmonitor_binding.delete(client, actual_binding)
                log('Adding anew binding for monitor %s' % binding_proxy.monitor_name)
                binding_proxy.add()

    # Add configured monitors that are missing from actual
    for proxy_key, binding_proxy in configured_monitor_proxys.items():
        if proxy_key not in actual_monitor_bindings.keys():
            log('Adding monitor binding for monitor %s' % binding_proxy.monitor_name)
            binding_proxy.add()


def diff_list(client, module, gslb_service_proxy):
    gslb_service_list = gslbservice.get_filtered(client, 'servicename:%s' % module.params['servicename'])
    diff_list = gslb_service_proxy.diff_object(gslb_service_list[0])
    if 'ip' in diff_list:
        del diff_list['ip']
    return diff_list


def all_identical(client, module, gslb_service_proxy):
    return gslb_service_identical(client, module, gslb_service_proxy) and monitor_bindings_identical(client, module)


def main():

    module_specific_arguments = dict(
        servicename=dict(type='str'),
        cnameentry=dict(type='str'),
        servername=dict(type='str'),
        servicetype=dict(
            type='str',
            choices=[
                'HTTP',
                'FTP',
                'TCP',
                'UDP',
                'SSL',
                'SSL_BRIDGE',
                'SSL_TCP',
                'NNTP',
                'ANY',
                'SIP_UDP',
                'SIP_TCP',
                'SIP_SSL',
                'RADIUS',
                'RDP',
                'RTSP',
                'MYSQL',
                'MSSQL',
                'ORACLE',
            ]
        ),
        port=dict(type='int'),
        publicip=dict(type='str'),
        publicport=dict(type='int'),
        maxclient=dict(type='float'),
        healthmonitor=dict(type='bool'),
        sitename=dict(type='str'),
        cip=dict(
            type='str',
            choices=[
                'enabled',
                'disabled',
            ]
        ),
        cipheader=dict(type='str'),
        sitepersistence=dict(
            type='str',
            choices=[
                'ConnectionProxy',
                'HTTPRedirect',
                'NONE',
            ]
        ),
        siteprefix=dict(type='str'),
        clttimeout=dict(type='float'),
        maxbandwidth=dict(type='float'),
        downstateflush=dict(
            type='str',
            choices=[
                'enabled',
                'disabled',
            ]
        ),
        maxaaausers=dict(type='float'),
        monthreshold=dict(type='float'),
        hashid=dict(type='float'),
        comment=dict(type='str'),
        appflowlog=dict(
            type='str',
            choices=[
                'enabled',
                'disabled',
            ]
        ),
        ipaddress=dict(type='str'),
    )

    hand_inserted_arguments = dict(
        monitor_bindings=dict(type='list'),
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
        'servicename',
        'cnameentry',
        'ip',
        'servername',
        'servicetype',
        'port',
        'publicip',
        'publicport',
        'maxclient',
        'healthmonitor',
        'sitename',
        'cip',
        'cipheader',
        'sitepersistence',
        'siteprefix',
        'clttimeout',
        'maxbandwidth',
        'downstateflush',
        'maxaaausers',
        'monthreshold',
        'hashid',
        'comment',
        'appflowlog',
        'ipaddress',
    ]

    readonly_attrs = [
        'gslb',
        'svrstate',
        'svreffgslbstate',
        'gslbthreshold',
        'gslbsvcstats',
        'monstate',
        'preferredlocation',
        'monitor_state',
        'statechangetimesec',
        'tickssincelaststatechange',
        'threshold',
        'clmonowner',
        'clmonview',
        '__count',
    ]

    immutable_attrs = [
        'servicename',
        'cnameentry',
        'ip',
        'servername',
        'servicetype',
        'port',
        'sitename',
        'state',
        'cipheader',
        'cookietimeout',
        'clttimeout',
        'svrtimeout',
        'viewip',
        'monitor_name_svc',
        'newname',
    ]

    transforms = {
        'healthmonitor': ['bool_yes_no'],
        'cip': [lambda v: v.upper()],
        'downstateflush': [lambda v: v.upper()],
        'appflowlog': [lambda v: v.upper()],
    }

    # params = copy.deepcopy(module.params)
    module.params['ip'] = module.params['ipaddress']

    # Instantiate config proxy
    gslb_service_proxy = ConfigProxy(
        actual=gslbservice(),
        client=client,
        attribute_values_dict=module.params,
        transforms=transforms,
        readwrite_attrs=readwrite_attrs,
        readonly_attrs=readonly_attrs,
        immutable_attrs=immutable_attrs,
    )

    try:
        ensure_feature_is_enabled(client, 'GSLB')
        # Apply appropriate state
        if module.params['state'] == 'present':
            if not gslb_service_exists(client, module):
                if not module.check_mode:
                    gslb_service_proxy.add()
                    sync_monitor_bindings(client, module)
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            elif not all_identical(client, module, gslb_service_proxy):

                # Check if we try to change value of immutable attributes
                immutables_changed = get_immutables_intersection(gslb_service_proxy, diff_list(client, module, gslb_service_proxy).keys())
                if immutables_changed != []:
                    module.fail_json(
                        msg='Cannot update immutable attributes %s' % (immutables_changed,),
                        diff=diff_list(client, module, gslb_service_proxy),
                        **module_result
                    )

                # Update main configuration object
                if not gslb_service_identical(client, module, gslb_service_proxy):
                    if not module.check_mode:
                        gslb_service_proxy.update()

                # Update monitor bindigns
                if not monitor_bindings_identical(client, module):
                    if not module.check_mode:
                        sync_monitor_bindings(client, module)

                # Fallthrough to save and change status update
                module_result['changed'] = True
                if module.params['save_config']:
                    client.save_config()
            else:
                module_result['changed'] = False

            # Sanity check for state
            if not module.check_mode:
                if not gslb_service_exists(client, module):
                    module.fail_json(msg='GSLB service does not exist', **module_result)
                if not gslb_service_identical(client, module, gslb_service_proxy):
                    module.fail_json(
                        msg='GSLB service differs from configured',
                        diff=diff_list(client, module, gslb_service_proxy),
                        **module_result
                    )
                if not monitor_bindings_identical(client, module):
                    module.fail_json(
                        msg='Monitor bindings differ from configured',
                        diff=diff_list(client, module, gslb_service_proxy),
                        **module_result
                    )

        elif module.params['state'] == 'absent':
            if gslb_service_exists(client, module):
                if not module.check_mode:
                    gslb_service_proxy.delete()
                    if module.params['save_config']:
                        client.save_config()
                module_result['changed'] = True
            else:
                module_result['changed'] = False

            # Sanity check for state
            if not module.check_mode:
                if gslb_service_exists(client, module):
                    module.fail_json(msg='GSLB service still exists', **module_result)

    except nitro_exception as e:
        msg = "nitro exception errorcode=%s, message=%s" % (str(e.errorcode), e.message)
        module.fail_json(msg=msg, **module_result)

    client.logout()
    module.exit_json(**module_result)


if __name__ == "__main__":
    main()
