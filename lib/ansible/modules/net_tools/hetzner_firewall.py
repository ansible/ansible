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
module: hetzner_firewall
version_added: "2.10"
short_description: Manage Hetzner's dedicated server firewall
author:
  - Felix Fontein (@felixfontein)
description:
  - Manage Hetzner's dedicated server firewall.
  - Note that idempotency check for TCP flags simply compares strings and doesn't
    try to interpret the rules. This might change in the future.
seealso:
  - name: Firewall documentation
    description: Hetzner's documentation on the stateless firewall for dedicated servers
    link: https://wiki.hetzner.de/index.php/Robot_Firewall/en
  - module: hetzner_firewall_info
    description: Retrieve information on firewall configuration.
extends_documentation_fragment:
  - hetzner
options:
  server_ip:
    description: The server's main IP address.
    required: yes
    type: str
  port:
    description:
      - Switch port of firewall.
    type: str
    choices: [ main, kvm ]
    default: main
  state:
    description:
      - Status of the firewall.
      - Firewall is active if state is C(present), and disabled if state is C(absent).
    type: str
    default: present
    choices: [ present, absent ]
  whitelist_hos:
    description:
      - Whether Hetzner services have access.
    type: bool
  rules:
    description:
      - Firewall rules.
    type: dict
    suboptions:
      input:
        description:
          - Input firewall rules.
        type: list
        elements: dict
        suboptions:
          name:
            description:
              - Name of the firewall rule.
            type: str
          ip_version:
            description:
              - Internet protocol version.
              - Note that currently, only IPv4 is supported by Hetzner.
            required: yes
            type: str
            choices: [ ipv4, ipv6 ]
          dst_ip:
            description:
              - Destination IP address or subnet address.
              - CIDR notation.
            type: str
          dst_port:
            description:
              - Destination port or port range.
            type: str
          src_ip:
            description:
              - Source IP address or subnet address.
              - CIDR notation.
            type: str
          src_port:
            description:
              - Source port or port range.
            type: str
          protocol:
            description:
              - Protocol above IP layer
            type: str
          tcp_flags:
            description:
              - TCP flags or logical combination of flags.
              - Flags supported by Hetzner are C(syn), C(fin), C(rst), C(psh) and C(urg).
              - They can be combined with C(|) (logical or) and C(&) (logical and).
              - See L(the documentation,https://wiki.hetzner.de/index.php/Robot_Firewall/en#Parameter)
                for more information.
            type: str
          action:
            description:
              - Action if rule matches.
            required: yes
            type: str
            choices: [ accept, discard ]
  update_timeout:
    description:
      - Timeout to use when configuring the firewall.
      - Note that the API call returns before the firewall has been
        successfully set up.
    type: int
    default: 30
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
- name: Configure firewall for server with main IP 1.2.3.4
  hetzner_firewall:
    hetzner_user: foo
    hetzner_password: bar
    server_ip: 1.2.3.4
    status: active
    whitelist_hos: yes
    rules:
      input:
        - name: Allow everything to ports 20-23 from 4.3.2.1/24
          ip_version: ipv4
          src_ip: 4.3.2.1/24
          dst_port: '20-23'
          action: accept
        - name: Allow everything to port 443
          ip_version: ipv4
          dst_port: '443'
          action: accept
        - name: Drop everything else
          ip_version: ipv4
          action: discard
  register: result

- debug:
    msg: "{{ result }}"
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
from ansible.module_utils.compat import ipaddress as compat_ipaddress
from ansible.module_utils.hetzner import (
    HETZNER_DEFAULT_ARGUMENT_SPEC,
    BASE_URL,
    fetch_url_json,
    fetch_url_json_with_retries,
    CheckDoneTimeoutException,
)
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils._text import to_native, to_text


RULE_OPTION_NAMES = [
    'name', 'ip_version', 'dst_ip', 'dst_port', 'src_ip', 'src_port',
    'protocol', 'tcp_flags', 'action',
]

RULES = ['input']


def restrict_dict(dictionary, fields):
    result = dict()
    for k, v in dictionary.items():
        if k in fields:
            result[k] = v
    return result


def restrict_firewall_config(config):
    result = restrict_dict(config, ['port', 'status', 'whitelist_hos'])
    result['rules'] = dict()
    for ruleset in RULES:
        result['rules'][ruleset] = [
            restrict_dict(rule, RULE_OPTION_NAMES)
            for rule in config['rules'].get(ruleset) or []
        ]
    return result


def update(before, after, params, name):
    bv = before.get(name)
    after[name] = bv
    changed = False
    pv = params[name]
    if pv is not None:
        changed = pv != bv
        if changed:
            after[name] = pv
    return changed


def normalize_ip(ip, ip_version):
    if ip is None:
        return ip
    if '/' in ip:
        ip, range = ip.split('/')
    else:
        ip, range = ip, ''
    ip_addr = to_native(compat_ipaddress.ip_address(to_text(ip)).compressed)
    if range == '':
        range = '32' if ip_version.lower() == 'ipv4' else '128'
    return ip_addr + '/' + range


def update_rules(before, after, params, ruleset):
    before_rules = before['rules'][ruleset]
    after_rules = after['rules'][ruleset]
    params_rules = params['rules'][ruleset]
    changed = len(before_rules) != len(params_rules)
    for no, rule in enumerate(params_rules):
        rule['src_ip'] = normalize_ip(rule['src_ip'], rule['ip_version'])
        rule['dst_ip'] = normalize_ip(rule['dst_ip'], rule['ip_version'])
        if no < len(before_rules):
            before_rule = before_rules[no]
            before_rule['src_ip'] = normalize_ip(before_rule['src_ip'], before_rule['ip_version'])
            before_rule['dst_ip'] = normalize_ip(before_rule['dst_ip'], before_rule['ip_version'])
            if before_rule != rule:
                changed = True
        after_rules.append(rule)
    return changed


def encode_rule(output, rulename, input):
    for i, rule in enumerate(input['rules'][rulename]):
        for k, v in rule.items():
            if v is not None:
                output['rules[{0}][{1}][{2}]'.format(rulename, i, k)] = v


def create_default_rules_object():
    rules = dict()
    for ruleset in RULES:
        rules[ruleset] = []
    return rules


def firewall_configured(result, error):
    return result['firewall']['status'] != 'in process'


def main():
    argument_spec = dict(
        server_ip=dict(type='str', required=True),
        port=dict(type='str', default='main', choices=['main', 'kvm']),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        whitelist_hos=dict(type='bool'),
        rules=dict(type='dict', options=dict(
            input=dict(type='list', elements='dict', options=dict(
                name=dict(type='str'),
                ip_version=dict(type='str', required=True, choices=['ipv4', 'ipv6']),
                dst_ip=dict(type='str'),
                dst_port=dict(type='str'),
                src_ip=dict(type='str'),
                src_port=dict(type='str'),
                protocol=dict(type='str'),
                tcp_flags=dict(type='str'),
                action=dict(type='str', required=True, choices=['accept', 'discard']),
            )),
        )),
        update_timeout=dict(type='int', default=30),
        wait_for_configured=dict(type='bool', default=True),
        wait_delay=dict(type='int', default=10),
        timeout=dict(type='int', default=180),
    )
    argument_spec.update(HETZNER_DEFAULT_ARGUMENT_SPEC)
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    # Sanitize input
    module.params['status'] = 'active' if (module.params['state'] == 'present') else 'disabled'
    if module.params['rules'] is None:
        module.params['rules'] = {}
    if module.params['rules'].get('input') is None:
        module.params['rules']['input'] = []

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
        if not firewall_configured(result, error):
            module.fail_json(msg='Firewall configuration cannot be read as it is not configured.')

    full_before = result['firewall']
    if not full_before.get('rules'):
        full_before['rules'] = create_default_rules_object()
    before = restrict_firewall_config(full_before)

    # Build wanted (after) state and compare
    after = dict(before)
    changed = False
    changed |= update(before, after, module.params, 'port')
    changed |= update(before, after, module.params, 'status')
    changed |= update(before, after, module.params, 'whitelist_hos')
    after['rules'] = create_default_rules_object()
    if module.params['status'] == 'active':
        for ruleset in RULES:
            changed |= update_rules(before, after, module.params, ruleset)

    # Update if different
    construct_result = True
    construct_status = None
    if changed and not module.check_mode:
        # https://robot.your-server.de/doc/webservice/en.html#post-firewall-server-ip
        url = "{0}/firewall/{1}".format(BASE_URL, server_ip)
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        data = dict(after)
        data['whitelist_hos'] = str(data['whitelist_hos']).lower()
        del data['rules']
        for ruleset in RULES:
            encode_rule(data, ruleset, after)
        result, error = fetch_url_json(
            module,
            url,
            method='POST',
            timeout=module.params['update_timeout'],
            data=urlencode(data),
            headers=headers,
        )
        if module.params['wait_for_configured'] and not firewall_configured(result, error):
            try:
                result, error = fetch_url_json_with_retries(
                    module,
                    url,
                    check_done_callback=firewall_configured,
                    check_done_delay=module.params['wait_delay'],
                    check_done_timeout=module.params['timeout'],
                    skip_first=True,
                )
            except CheckDoneTimeoutException as e:
                result, error = e.result, e.error
                module.warn('Timeout while waiting for firewall to be configured.')

        full_after = result['firewall']
        if not full_after.get('rules'):
            full_after['rules'] = create_default_rules_object()
        construct_status = full_after['status']
        if construct_status != 'in process':
            # Only use result if configuration is done, so that diff will be ok
            after = restrict_firewall_config(full_after)
            construct_result = False

    if construct_result:
        # Construct result (used for check mode, and configuration still in process)
        full_after = dict(full_before)
        for k, v in after.items():
            if k != 'rules':
                full_after[k] = after[k]
        if construct_status is not None:
            # We want 'in process' here
            full_after['status'] = construct_status
        full_after['rules'] = dict()
        for ruleset in RULES:
            full_after['rules'][ruleset] = after['rules'][ruleset]

    module.exit_json(
        changed=changed,
        diff=dict(
            before=before,
            after=after,
        ),
        firewall=full_after,
    )


if __name__ == '__main__':
    main()
