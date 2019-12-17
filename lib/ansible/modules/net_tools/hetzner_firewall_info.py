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
module: hetzner_firewall_info
version_added: "2.10"
short_description: Manage Hetzner's dedicated server firewall
author:
  - Felix Fontein (@felixfontein)
description:
  - Manage Hetzner's dedicated server firewall.
seealso:
  - name: Firewall documentation
    description: Hetzner's documentation on the stateless firewall for dedicated servers
    link: https://wiki.hetzner.de/index.php/Robot_Firewall/en
  - module: hetzner_firewall
    description: Configure firewall.
extends_documentation_fragment:
  - hetzner
options:
  server_ip:
    description: The server's main IP address.
    type: str
    required: yes
  wait_for_configured:
    description:
      - Whether to wait until the firewall has been successfully configured before
        determining what to do, and before returning from the module.
      - The API returns status C(in progress) when the firewall is currently
        being configured. If this happens, the module will try again until
        the status changes to C(active) or C(disabled).
      - Please note that there is a request limit. If you have to do multiple
        updates, it can be better to disable waiting, and regularly use
        M(hetzner_firewall_info) to query status.
    type: bool
    default: yes
  wait_delay:
    description:
      - Delay to wait (in seconds) before checking again whether the firewall has
        been configured.
    type: int
    default: 10
  timeout:
    description:
      - Timeout (in seconds) for waiting for firewall to be configured.
    type: int
    default: 180
'''

EXAMPLES = r'''
- name: Get firewall configuration for server with main IP 1.2.3.4
  hetzner_firewall_info:
    hetzner_user: foo
    hetzner_password: bar
    server_ip: 1.2.3.4
  register: result

- debug:
    msg: "{{ result.firewall }}"
'''

RETURN = r'''
firewall:
  description:
    - The firewall configuration.
  type: dict
  returned: success
  contains:
    port:
      description:
        - Switch port of firewall.
        - C(main) or C(kvm).
      type: str
      sample: main
    server_ip:
      description:
        - Server's main IP address.
      type: str
      sample: 1.2.3.4
    server_number:
      description:
        - Hetzner's internal server number.
      type: int
      sample: 12345
    status:
      description:
        - Status of the firewall.
        - C(active) or C(disabled).
        - Will be C(in process) if the firewall is currently updated, and
          I(wait_for_configured) is set to C(no) or I(timeout) to a too small value.
      type: str
      sample: active
    whitelist_hos:
      description:
        - Whether Hetzner services have access.
      type: bool
      sample: true
    rules:
      description:
        - Firewall rules.
      type: dict
      contains:
        input:
          description:
            - Input firewall rules.
          type: list
          elements: dict
          contains:
            name:
              description:
                - Name of the firewall rule.
              type: str
              sample: Allow HTTP access to server
            ip_version:
              description:
                - Internet protocol version.
              type: str
              sample: ipv4
            dst_ip:
              description:
                - Destination IP address or subnet address.
                - CIDR notation.
              type: str
              sample: 1.2.3.4/32
            dst_port:
              description:
                - Destination port or port range.
              type: str
              sample: "443"
            src_ip:
              description:
                - Source IP address or subnet address.
                - CIDR notation.
              type: str
              sample: null
            src_port:
              description:
                - Source port or port range.
              type: str
              sample: null
            protocol:
              description:
                - Protocol above IP layer
              type: str
              sample: tcp
            tcp_flags:
              description:
                - TCP flags or logical combination of flags.
              type: str
              sample: null
            action:
              description:
                - Action if rule matches.
                - C(accept) or C(discard).
              type: str
              sample: accept
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.hetzner import (
    HETZNER_DEFAULT_ARGUMENT_SPEC,
    BASE_URL,
    fetch_url_json,
    fetch_url_json_with_retries,
    CheckDoneTimeoutException,
)


def firewall_configured(result, error):
    return result['firewall']['status'] != 'in process'


def main():
    argument_spec = dict(
        server_ip=dict(type='str', required=True),
        wait_for_configured=dict(type='bool', default=True),
        wait_delay=dict(type='int', default=10),
        timeout=dict(type='int', default=180),
    )
    argument_spec.update(HETZNER_DEFAULT_ARGUMENT_SPEC)
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    server_ip = module.params['server_ip']

    # https://robot.your-server.de/doc/webservice/en.html#get-firewall-server-ip
    url = "{0}/firewall/{1}".format(BASE_URL, server_ip)
    if module.params['wait_for_configured']:
        try:
            result, error = fetch_url_json_with_retries(
                module,
                url,
                check_done_callback=firewall_configured,
                check_done_delay=module.params['wait_delay'],
                check_done_timeout=module.params['timeout'],
            )
        except CheckDoneTimeoutException as dummy:
            module.fail_json(msg='Timeout while waiting for firewall to be configured.')
    else:
        result, error = fetch_url_json(module, url)

    firewall = result['firewall']
    if not firewall.get('rules'):
        firewall['rules'] = dict()
        for ruleset in ['input']:
            firewall['rules'][ruleset] = []

    module.exit_json(
        changed=False,
        firewall=firewall,
    )


if __name__ == '__main__':
    main()
