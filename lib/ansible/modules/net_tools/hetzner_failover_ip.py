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
  value:
    description:
      - The new value for the failover IP address.
      - Not setting this will unroute the failover IP.
    type: str
'''

EXAMPLES = r'''
- name: Set value of failover IP 1.2.3.4 to 5.6.7.8
  hetzner_failover_ip:
    hetzner_user: foo
    hetzner_pass: bar
    failover_ip: 1.2.3.4
    value: 5.6.7.8
'''

RETURN = r'''
value:
  description:
    - The value of the failover IP.
    - Will be C(none) if the IP is unrouted.
  returned: success
  type: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.six.moves.urllib.parse import urlencode

BASE_URL = "https://robot-ws.your-server.de"


def fetch_url_json(module, url, method='GET', timeout=10, data=None, headers=None, accept_errors=None):
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
    url = "{0}/failover/{1}".format(BASE_URL, ip)
    result, error = fetch_url_json(module, url)
    if 'failover' not in result:
        module.fail_json(msg='Cannot interpret result: {0}'.format(result))
    return result['failover']['active_server_ip']


def set_failover(module, ip, value):
    url = "{0}/failover/{1}".format(BASE_URL, ip)
    if value is None:
        result, error = fetch_url_json(
            module,
            url,
            method='DELETE',
            timeout=3 * 60,  # 3 minutes timeout should be enough
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
            timeout=3 * 60,  # 3 minutes timeout should be enough
            data=urlencode(data),
            headers=headers,
            accept_errors=['FAILOVER_ALREADY_ROUTED']
        )
    if error is not None:
        return value, False
    else:
        return result['failover']['active_server_ip'], True


def main():
    module = AnsibleModule(
        argument_spec=dict(
            hetzner_user=dict(type='str', required=True),
            hetzner_pass=dict(type='str', required=True, no_log=True),
            failover_ip=dict(type='str', required=True),
            value=dict(type='str'),
        ),
        supports_check_mode=True,
    )

    before = dict()
    after = dict()
    changed = False

    failover_ip = module.params['failover_ip']
    value = get_failover(module, failover_ip)
    before['value'] = value

    if value != module.params['value']:
        if module.check_mode:
            value = module.params['value']
            changed = True
        else:
            value, changed = set_failover(module, failover_ip, module.params['value'])

    after['value'] = value
    result = dict(
        changed=changed,
        value=value,
    )
    if module._diff:
        result['diff'] = dict(
            before=before,
            after=after,
        )
    module.exit_json(**result)


if __name__ == '__main__':
    main()
