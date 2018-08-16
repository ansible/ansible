#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_timer_policy
short_description: Manage timer policies on a BIG-IP
description:
  - Manage timer policies on a BIG-IP.
version_added: 2.6
options:
  name:
    description:
      - Specifies the name of the timer policy.
    required: True
  description:
    description:
      - Specifies descriptive text that identifies the timer policy.
  rules:
    description:
      - Rules that you want assigned to the timer policy
    suboptions:
      name:
        description:
          - The name of the rule.
        required: True
      protocol:
        description:
          - Specifies the IP protocol entry for which the timer policy rule is being
            configured. This could be a layer-4 protocol (such as C(tcp), C(udp) or
            C(sctp).
          - Only flows matching the configured protocol will make use of this rule.
          - When C(all-other) is specified, if there are no specific ip-protocol rules
            that match the flow, the flow matches all the other ip-protocol rules.
          - When specifying rules, if this parameter is not specified, the default of
            C(all-other) will be used.
        choices:
          - all-other
          - ah
          - bna
          - esp
          - etherip
          - gre
          - icmp
          - ipencap
          - ipv6
          - ipv6-auth
          - ipv6-crypt
          - ipv6-icmp
          - isp-ip
          - mux
          - ospf
          - sctp
          - tcp
          - udp
          - udplite
      destination_ports:
        description:
          - The list of destination ports to match the rule on.
          - Specify a port range by specifying start and end ports separated by a
            dash (-).
          - This field is only available if you have selected the C(sctp), C(tcp), or
            C(udp) protocol.
      idle_timeout:
        description:
          - Specifies an idle timeout, in seconds, for protocol and port pairs that
            match the timer policy rule.
          - When C(infinite), specifies that the protocol and port pairs that match
            the timer policy rule have no idle timeout.
          - When specifying rules, if this parameter is not specified, the default of
            C(unspecified) will be used.
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
  state:
    description:
      - When C(present), ensures that the resource exists.
      - When C(absent), ensures the resource is removed.
    default: present
    choices:
      - present
      - absent
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a timer policy
  bigip_timer_policy:
    name: timer1
    description: My timer policy
    rules:
      - name: rule1
        protocol: tcp
        idle_timeout: indefinite
        destination_ports:
          - 443
          - 80
      - name: rule2
        protocol: 200
      - name: rule3
        protocol: sctp
        idle_timeout: 200
        destination_ports:
          - 21
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Remove a timer policy and all its associated rules
  bigip_timer_policy:
    name: timer1
    description: My timer policy
    password: secret
    server: lb.mydomain.com
    state: absent
    user: admin
  delegate_to: localhost
'''

RETURN = r'''
description:
  description: The new description of the timer policy.
  returned: changed
  type: string
  sample: true
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import compare_dictionary
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False
except ImportError:
    from ansible.module_utils.network.f5.bigip import HAS_F5SDK
    from ansible.module_utils.network.f5.bigip import F5Client
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import cleanup_tokens
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import compare_dictionary
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    api_map = {

    }

    api_attributes = [
        'description',
        'rules'
    ]

    returnables = [
        'description',
        'rules'
    ]

    updatables = [
        'description',
        'rules'
    ]


class ApiParameters(Parameters):
    @property
    def rules(self):
        if self._values['rules'] is None:
            return None
        results = []
        for rule in self._values['rules']:
            result = dict()
            result['name'] = rule['name']
            if 'ipProtocol' in rule:
                result['protocol'] = str(rule['ipProtocol'])
            if 'timers' in rule:
                result['idle_timeout'] = str(rule['timers'][0]['value'])
            if 'destinationPorts' in rule:
                ports = list(set([str(x['name']) for x in rule['destinationPorts']]))
                ports.sort()
                result['destination_ports'] = ports
            results.append(result)
            results = sorted(results, key=lambda k: k['name'])
        return results


class ModuleParameters(Parameters):
    @property
    def rules(self):
        if self._values['rules'] is None:
            return None
        if len(self._values['rules']) == 1 and self._values['rules'][0] == '':
            return ''
        results = []
        for rule in self._values['rules']:
            result = dict()
            result['name'] = rule['name']
            if 'protocol' in rule:
                result['protocol'] = str(rule['protocol'])
            else:
                result['protocol'] = 'all-other'

            if 'idle_timeout' in rule:
                result['idle_timeout'] = str(rule['idle_timeout'])
            else:
                result['idle_timeout'] = 'unspecified'

            if 'destination_ports' in rule:
                ports = list(set([str(x) for x in rule['destination_ports']]))
                ports.sort()
                ports = [str(self._validate_port_entries(x)) for x in ports]
                result['destination_ports'] = ports
            results.append(result)
            results = sorted(results, key=lambda k: k['name'])
        return results

    def _validate_port_entries(self, port):
        if port == 'all-other':
            return 0
        if '-' in port:
            parts = port.split('-')
            if len(parts) != 2:
                raise F5ModuleError(
                    "The correct format for a port range is X-Y, where X is the start"
                    "port and Y is the end port."
                )
            try:
                start = int(parts[0])
                end = int(parts[1])
            except ValueError:
                raise F5ModuleError(
                    "The ports in a range must be numbers."
                    "You provided '{0}' and '{1}'.".format(parts[0], parts[1])
                )
            if start == end:
                return start
            if start > end:
                return '{0}-{1}'.format(end, start)
            else:
                return port
        else:
            try:
                return int(port)
            except ValueError:
                raise F5ModuleError(
                    "The specified destination port is not a number."
                )


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class UsableChanges(Changes):
    @property
    def rules(self):
        if self._values['rules'] is None:
            return None
        results = []
        for rule in self._values['rules']:
            result = dict()
            result['name'] = rule['name']
            if 'protocol' in rule:
                result['ipProtocol'] = rule['protocol']

            if 'destination_ports' in rule:
                if rule['protocol'] not in ['tcp', 'udp', 'sctp']:
                    raise F5ModuleError(
                        "Only the 'tcp', 'udp', and 'sctp' protocols support 'destination_ports'."
                    )
                ports = [dict(name=str(x)) for x in rule['destination_ports']]
                result['destinationPorts'] = ports
            else:
                result['destinationPorts'] = []

            if 'idle_timeout' in rule:
                if rule['idle_timeout'] in ['indefinite', 'immediate', 'unspecified']:
                    timeout = rule['idle_timeout']
                else:
                    try:
                        int(rule['idle_timeout'])
                        timeout = rule['idle_timeout']
                    except ValueError:
                        raise F5ModuleError(
                            "idle_timeout must be a number, or, one of 'indefinite', 'immediate', or 'unspecified'."
                        )
                result['timers'] = [
                    dict(name='flow-idle-timeout', value=timeout)
                ]
            results.append(result)
            results = sorted(results, key=lambda k: k['name'])
        return results


class ReportableChanges(Changes):
    pass


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            return self.__default(param)

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1

    @property
    def rules(self):
        if self.want.rules is None:
            return None
        if self.have.rules is None and self.want.rules == '':
            return None
        if self.have.rules is not None and self.want.rules == '':
            return []
        if self.have.rules is None:
            return self.want.rules

        want = [tuple(x.pop('destination_ports')) for x in self.want.rules if 'destination_ports' in x]
        have = [tuple(x.pop('destination_ports')) for x in self.have.rules if 'destination_ports' in x]
        if set(want) != set(have):
            return self.want.rules
        if compare_dictionary(self.want.rules, self.have.rules):
            return self.want.rules


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = UsableChanges(params=changed)

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = Parameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                if isinstance(change, dict):
                    changed.update(change)
                else:
                    changed[k] = change
        if changed:
            self.changes = UsableChanges(params=changed)
            return True
        return False

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        try:
            if state == "present":
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def exists(self):
        result = self.client.api.tm.net.timer_policys.timer_policy.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def create(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        self.client.api.tm.net.timer_policys.timer_policy.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def update_on_device(self):
        params = self.changes.api_params()
        resource = self.client.api.tm.net.timer_policys.timer_policy.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(**params)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        resource = self.client.api.tm.net.timer_policys.timer_policy.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if resource:
            resource.delete()

    def read_current_from_device(self):
        resource = self.client.api.tm.net.timer_policys.timer_policy.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return ApiParameters(params=result)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(required=True),
            description=dict(),
            rules=dict(
                type='list',
                suboptions=dict(
                    name=dict(required=True),
                    protocol=dict(
                        default='all-other',
                        choices=[
                            'all-other',
                            'ah',
                            'bna',
                            'esp',
                            'etherip',
                            'gre',
                            'icmp',
                            'ipencap',
                            'ipv6',
                            'ipv6-auth',
                            'ipv6-crypt',
                            'ipv6-icmp',
                            'isp-ip',
                            'mux',
                            'ospf',
                            'sctp',
                            'tcp',
                            'udp',
                            'udplite',
                        ]
                    ),
                    description=dict(),
                    idle_timeout=dict(default='unspecified'),
                    destination_ports=dict(
                        type='list'
                    )
                )
            ),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode
    )
    if not HAS_F5SDK:
        module.fail_json(msg="The python f5-sdk module is required")

    try:
        client = F5Client(**module.params)
        mm = ModuleManager(module=module, client=client)
        results = mm.exec_module()
        cleanup_tokens(client)
        module.exit_json(**results)
    except F5ModuleError as ex:
        cleanup_tokens(client)
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
