#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: hetzner_failover_ip
version_added: "2.9"
short_description: Manage Hetzner's failover IPs
author:
  - Felix Fontein (@felixfontein)
description:
  - Manage Hetzner's failover IPs.
  - See L(https://wiki.hetzner.de/index.php/Failover/en,Hetzner's documentation) for details
    on failover IPs.
options:
  hetzner_user:
    description: The username for the Robot webservice user.
    type: str
    required: yes
  hetzner_pass:
    description: The password for the Robot webservice user.
    type: str
    required: yes
  failover_ip:
    description: The failover IP address.
    type: str
    required: yes
  state:
    description:
      - Defines whether the IP will be routed or not.
      - If set to C(routed), I(value) must be specified.
    type: str
    choices:
      - routed
      - unrouted
    default: routed
  value:
    description:
      - The new value for the failover IP address.
      - Required when setting I(state) to C(routed).
    type: str
  timeout:
    description:
      - Timeout to use when routing or unrouting the failover IP.
      - Note that the API call returns when the failover IP has been
        successfully routed to the new address, respectively successfully
        unrouted.
    type: int
    default: 180
'''

EXAMPLES = r'''
- name: Set value of failover IP 1.2.3.4 to 5.6.7.8
  hetzner_failover_ip:
    hetzner_user: foo
    hetzner_pass: bar
    failover_ip: 1.2.3.4
    value: 5.6.7.8

- name: Set value of failover IP 1.2.3.4 to unrouted
  hetzner_failover_ip:
    hetzner_user: foo
    hetzner_pass: bar
    failover_ip: 1.2.3.4
    state: unrouted
'''

RETURN = r'''
value:
  description:
    - The value of the failover IP.
    - Will be C(none) if the IP is unrouted.
  returned: success
  type: str
state:
  description:
    - Will be C(routed) or C(unrouted).
  returned: success
  type: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.six.moves.urllib.parse import urlencode

# The API endpoint is fixed.
BASE_URL = "https://robot-ws.your-server.de"


def fetch_url_json(module, url, method='GET', timeout=10, data=None, headers=None, accept_errors=None):
    '''
    Make general request to Hetzner's JSON robot API.
    '''
    module.params['url_username'] = module.params['hetzner_user']
    module.params['url_password'] = module.params['hetzner_pass']
    resp, info = fetch_url(module, url, method=method, timeout=timeout, data=data, headers=headers)
    try:
        content = resp.read()
    except AttributeError:
        content = info.pop('body', None)

    if not content:
        module.fail_json(msg='Cannot retrieve content from {0}'.format(url))

    try:
        result = module.from_json(content.decode('utf8'))
        if 'error' in result:
            if accept_errors:
                if result['error']['code'] in accept_errors:
                    return result, result['error']['code']
            module.fail_json(msg='Request failed: {0} {1} ({2})'.format(
                result['error']['status'],
                result['error']['code'],
                result['error']['message']
            ))
        return result, None
    except ValueError:
        module.fail_json(msg='Cannot decode content retrieved from {0}'.format(url))


def get_failover(module, ip):
    '''
    Get current routing target of failover IP.

    The value ``None`` represents unrouted.

    See https://robot.your-server.de/doc/webservice/en.html#get-failover-failover-ip
    '''
    url = "{0}/failover/{1}".format(BASE_URL, ip)
    result, error = fetch_url_json(module, url)
    if 'failover' not in result:
        module.fail_json(msg='Cannot interpret result: {0}'.format(result))
    return result['failover']['active_server_ip']


def set_failover(module, ip, value, timeout=180):
    '''
    Set current routing target of failover IP.

    Return a pair ``(value, changed)``. The value ``None`` for ``value`` represents unrouted.

    See https://robot.your-server.de/doc/webservice/en.html#post-failover-failover-ip
    and https://robot.your-server.de/doc/webservice/en.html#delete-failover-failover-ip
    '''
    url = "{0}/failover/{1}".format(BASE_URL, ip)
    if value is None:
        result, error = fetch_url_json(
            module,
            url,
            method='DELETE',
            timeout=timeout,
            accept_errors=['FAILOVER_ALREADY_ROUTED']
        )
    else:
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        data = dict(
            active_server_ip=value,
        )
        result, error = fetch_url_json(
            module,
            url,
            method='POST',
            timeout=timeout,
            data=urlencode(data),
            headers=headers,
            accept_errors=['FAILOVER_ALREADY_ROUTED']
        )
    if error is not None:
        return value, False
    else:
        return result['failover']['active_server_ip'], True


def get_state(value):
    '''
    Create result dictionary for failover IP's value.

    The value ``None`` represents unrouted.
    '''
    return dict(
        value=value,
        state='routed' if value else 'unrouted'
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            hetzner_user=dict(type='str', required=True),
            hetzner_pass=dict(type='str', required=True, no_log=True),
            failover_ip=dict(type='str', required=True),
            state=dict(type='str', default='routed', choices=['routed', 'unrouted']),
            value=dict(type='str'),
            timeout=dict(type='int', default=180),
        ),
        supports_check_mode=True,
        required_if=(
            ('state', 'routed', ['value']),
        ),
    )

    failover_ip = module.params['failover_ip']
    value = get_failover(module, failover_ip)
    changed = False
    before = get_state(value)

    if module.params['state'] == 'routed':
        new_value = module.params['value']
    else:
        new_value = None

    if value != new_value:
        if module.check_mode:
            value = new_value
            changed = True
        else:
            value, changed = set_failover(module, failover_ip, new_value, timeout=module.params['timeout'])

    after = get_state(value)
    module.exit_json(
        changed=changed,
        diff=dict(
            before=before,
            after=after,
        ),
        **after
    )


if __name__ == '__main__':
    main()
