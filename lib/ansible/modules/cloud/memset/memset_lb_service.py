#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Simon Weald <ansible@simonweald.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: memset_lb_service
author: "Simon Weald (@glitchcrab)"
version_added: "2.9"
short_description: Manage Memset loadbalancer services
notes:
  - A loadbalancer service is logically the Internet-facing 'frontend'. This must
    be backed by one or more servers using the C(memset_lb_server) module.
  - An API key generated via the Memset customer control panel is needed with the
    following minimum scope - I(loadbalancer.service.add), I(loadbalancer.service.info),
    I(loadbalancer.service.list), I(loadbalancer.service.remove),
    I(loadbalancer.service.update), I(server.info).
description:
    - Manage Memset loadbalancer services
options:
    state:
        default: present
        type: str
        description:
            - Indicates desired state of resource. Defaults to present.
            - When deleting a service there must be no servers currently attached to it as this will raise an error.
        choices: [ absent, present ]
    api_key:
        required: true
        type: str
        description:
            - The API key obtained from the Memset control panel.
    enabled:
        required: false
        default: true
        type: bool
        description:
            - Whether the service is enabled or not. Defaults to True.
    load_balancer:
        required: true
        type: str
        description:
            - The name of the load balancer - this is the product name e.g. C(lbtestyaa1).
    port:
        type: int
        description:
            - The port to be exposed to the Internet.
            - Must be in the range 1 > 65535 (inclusive).
    protocol:
        type: str
        description:
            - The protocol to be used by the load balacer.
        choices: [ tcp, http, https ]
    service_name:
        required: true
        type: str
        description:
            - Unique name to identify the service by (must be unique). Changing this will cause a new service to be created.
            - It can only consist of letters, numbers, underscores and hyphens and must be a maximum of 64 characters.
        aliases: [ 'name' ]
    virtual_ip:
        required: false
        type: str
        description:
            - The IP address to expose the service on (must be assigned to the loadbalancer product).
            - If not provided, it will default to the primary IP of the loadbalancer.
'''

EXAMPLES = '''
- name: create a loadbalanced service
  memset_lb_service:
    state: present
    api_key: 5eb86c9196ab03919abcf03857163741
    load_balancer: lbtestyaa1
    port: 443
    protocol: https
    service_name: my_https_service
    virtual_ip: 1.2.3.4
  delegate_to: localhost

- name: delete a loadbalanced service
  memset_lb_service:
    state: absent
    api_key: 5eb86c9196ab03919abcf03857163741
    load_balancer: lbtestyaa1
    service_name: my_https_service
  delegate_to: localhost
'''

RETURN = '''
---
memset_api:
  description: Info from the Memset API
  returned: when changed or state == present
  type: complex
  contains:
    enabled:
      description: Whether the service is enabled.
      returned: when state=present
      type: boolean
      sample: true
    load_balancer:
      description: The name of the loadbalancer product.
      returned: always
      type: string
      sample: lbtestyaa1
    port:
      description: The port the service is exposed on.
      returned: when state=present
    protocol:
      description: The protocol to be loadbalanced.
      returned: when state=present
      type: string
      sample: https
    servers:
      description: List of dictionaries of the servers attached to the service.
      returned: when state=present
      type: list
      sample: [
        {
          "name": "testyaa1",
          "ip_address": "10.0.0.10",
          "port": "443",
          "enabled": "true",
          "fallback": "false",
          "weight": "10"
        }
      ]
    service_name:
      description: The name of the service.
      returned: always
      type: string
      sample: my_https_service
    virtual_ip:
      description: The IP address the service is exposed on.
      returned: when state=present
      type: string
      sample: 1.2.3.4
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.memset import (memset_api_call, get_product_ips, get_primary_ip, MemsetServer)


def api_validation(args=None, loadbalancer=None):
    '''
    Perform some validation which will be enforced by Memset's API (see:
    https://www.memset.com/apidocs/methods_loadbalancer.service.html)
    '''
    re_match = r'^[a-z0-9-\_]{1,64}$'
    errors = dict()

    if not re.match(re_match, args['service_name'].lower()):
        errors['service_name'] = "Service name can only be contain alphanumeric chars, hyphens and underscores, and must be 64 chars or less."
    if not 1 <= args['port'] <= 65535:
        errors['port'] = "Port must be in the range 1 > 65535 (inclusive)."
    if len(loadbalancer.all_ips()) == 0:
        errors['misc'] = 'No IPs attached to loadbalancer'
    if args['virtual_ip'] and args['virtual_ip'] not in loadbalancer.all_ips():
        errors['virtual_ip'] = "{0} is not assigned to {1}" . format(args['virtual_ip'], args['load_balancer'])

    if len(errors) > 0:
        module.fail_json(failed=True, msg=errors)


def create_lb_service(args=None, service=None, loadbalancer=None):
    '''
    Creates or updates a service. Unique key is the service name
    so if this isn't matched a new service will be created.
    '''
    retvals, payload = dict(), dict()
    retvals['changed'], retvals['failed'] = False, False

    # if the user hasn't provided an IP, we use the primary IP of the loadbalancer
    if not args['virtual_ip']:
        args['virtual_ip'] = loadbalancer.primary_ip()

    for arg in ['enabled', 'port', 'protocol', 'service_name', 'virtual_ip']:
        payload[arg] = args[arg]

    if service is None:
        # add load_balancer to the payload late
        payload['load_balancer'] = args['load_balancer']
        # create the service
        if args['check_mode']:
            retvals['changed'] = True
            # return what would have been created to the user
            retvals['memset_api'] = payload
        else:
            api_method = 'loadbalancer.service.add'
            retvals['failed'], msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
            if not retvals['failed']:
                retvals['changed'] = True
                retvals['memset_api'] = payload
            else:
                retvals['msg'] = msg
    else:
        # perform various contortions in order to compare the existing service
        # to the payload we intend to POST.
        _service = service.copy()
        _service['service_name'] = service['name']
        del _service['name']
        try:
            # there may be servers attached to the service - remove those too.
            del _service['servers']
        except Exception:
            pass

        if _service == payload:
            # the payload and the service are the same, so we just exit unchanged
            retvals['memset_api'] = payload
        else:
            _diff = dict(set(payload.items()) ^ set(_service.items()))
            # add load_balancer to the payload after we've compared the dicts
            payload['load_balancer'] = args['load_balancer']
            # update service
            if args['check_mode']:
                retvals['changed'] = True
                retvals['diff'] = _diff
            else:
                api_method = 'loadbalancer.service.update'
                retvals['failed'], msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
                if not retvals['failed']:
                    retvals['changed'] = True
                    retvals['memset_api'] = payload

    return(retvals)


def delete_lb_service(args=None, service=None):
    '''
    Deletes a service if it exists. If there are still servers
    attached to the service then it will fail as these must be
    detached first.
    '''
    retvals, payload = dict(), dict()
    retvals['changed'], retvals['failed'] = False, False

    if service is not None:
        for arg in ['load_balancer', 'service_name']:
            payload[arg] = args[arg]
        if args['check_mode']:
            retvals['changed'] = True
        else:
            api_method = 'loadbalancer.service.remove'
            retvals['failed'], msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
            if not retvals['failed']:
                retvals['changed'] = True

    return(retvals)


def create_or_delete(args=None, loadbalancer=None):
    '''
    Performs initial auth validation and gets a list of
    existing services to provide to create/delete functions.
    '''
    retvals, payload = dict(), dict()
    retvals['changed'], retvals['failed'] = False, False

    # get the current services and check if the relevant service exists.
    payload['load_balancer'] = args['load_balancer']
    api_method = 'loadbalancer.service.list'
    has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)

    if has_failed:
        # this is the first time the API is called; incorrect credentials will
        # manifest themselves at this point so we need to ensure the user is
        # informed of the reason.
        retvals['failed'] = True
        retvals['msg'] = msg
        retvals['stderr'] = "API returned an error: {0}" . format(response.status_code)
        return(retvals)

    current_service = None
    for service in response.json():
        if service['name'] == args['service_name']:
            current_service = service

    if args['state'] == 'present':
        retvals = create_lb_service(args=args, service=current_service, loadbalancer=loadbalancer)

    if args['state'] == 'absent':
        retvals = delete_lb_service(args=args, service=current_service)

    return(retvals)


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            api_key=dict(required=True, type='str', no_log=True),
            enabled=dict(default="True", type='bool'),
            load_balancer=dict(required=True, type='str'),
            port=dict(required=False, type=int),
            protocol=dict(required=False, choices=['tcp', 'http', 'https'], type='str'),
            service_name=dict(required=True, type='str', aliases=['name']),
            virtual_ip=dict(required=False, type='str')
        ),
        supports_check_mode=True,
        required_if=[
            ["state", "present", ["protocol", "port"]]
        ]
    )

    # populate the dict with the user-provided vars.
    args = dict()
    for key, arg in module.params.items():
        args[key] = arg
    args['check_mode'] = module.check_mode

    # make an initial API call to get the loadbalancer's info.
    payload = dict()
    payload['name'] = args['load_balancer']
    api_method = 'server.info'
    has_failed, _msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)

    retvals = dict()
    if has_failed:
        # this is the first time the API is called; incorrect credentials will
        # manifest themselves at this point so we need to ensure the user is
        # informed of the reason.
        retvals['failed'] = has_failed
        retvals['msg'] = _msg
        retvals['stderr'] = "API returned an error: {0}" . format(response.status_code)
        module.fail_json(**retvals)

    # create an object to represent this loadbalancer.
    loadbalancer = MemsetServer(response.json())

    # validate some API-specific limitations.
    api_validation(args, loadbalancer)

    retvals = create_or_delete(args, loadbalancer)

    if retvals['failed']:
        module.fail_json(**retvals)
    else:
        module.exit_json(**retvals)


if __name__ == '__main__':
    main()
