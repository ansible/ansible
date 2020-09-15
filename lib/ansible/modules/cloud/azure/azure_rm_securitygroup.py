#!/usr/bin/python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_securitygroup
version_added: "2.1"
short_description: Manage Azure network security groups
description:
    - Create, update or delete a network security group.
    - A security group contains Access Control List (ACL) rules that allow or deny network traffic to subnets or individual network interfaces.
    - A security group is created with a set of default security rules and an empty set of security rules.
    - Shape traffic flow by adding rules to the empty set of security rules.

options:
    default_rules:
        description:
            - The set of default rules automatically added to a security group at creation.
            - In general default rules will not be modified. Modify rules to shape the flow of traffic to or from a subnet or NIC.
            - See rules below for the makeup of a rule dict.
    location:
        description:
            - Valid azure location. Defaults to location of the resource group.
    name:
        description:
            - Name of the security group to operate on.
    purge_default_rules:
        description:
            - Remove any existing rules not matching those defined in the default_rules parameter.
        type: bool
        default: 'no'
    purge_rules:
        description:
            - Remove any existing rules not matching those defined in the rules parameters.
        type: bool
        default: 'no'
    resource_group:
        description:
            - Name of the resource group the security group belongs to.
        required: true
    rules:
        description:
            - Set of rules shaping traffic flow to or from a subnet or NIC. Each rule is a dictionary.
        suboptions:
            name:
                description:
                    - Unique name for the rule.
                required: true
            description:
                description:
                    - Short description of the rule's purpose.
            protocol:
                description:
                    - Accepted traffic protocol.
                choices:
                    - Udp
                    - Tcp
                    - "*"
                default: "*"
            source_port_range:
                description:
                    - Port or range of ports from which traffic originates.
                    - It can accept string type or a list of string type.
                default: "*"
            destination_port_range:
                description:
                    - Port or range of ports to which traffic is headed.
                    - It can accept string type or a list of string type.
                default: "*"
            source_address_prefix:
                description:
                    - The CIDR or source IP range.
                    - Asterisk C(*) can also be used to match all source IPs.
                    - Default tags such as C(VirtualNetwork), C(AzureLoadBalancer) and C(Internet) can also be used.
                    - If this is an ingress rule, specifies where network traffic originates from.
                    - It can accept string type or a list of string type.
                default: "*"
            destination_address_prefix:
                description:
                    - The destination address prefix.
                    - CIDR or destination IP range.
                    - Asterisk C(*) can also be used to match all source IPs.
                    - Default tags such as C(VirtualNetwork), C(AzureLoadBalancer) and C(Internet) can also be used.
                    - It can accept string type or a list of string type.
                default: "*"
            source_application_security_groups:
                description:
                    - List of the source application security groups.
                    - It could be list of resource id.
                    - It could be list of names in same resource group.
                    - It could be list of dict containing resource_group and name.
                    - It is mutually exclusive with C(source_address_prefix) and C(source_address_prefixes).
                type: list
            destination_application_security_groups:
                description:
                    - List of the destination application security groups.
                    - It could be list of resource id.
                    - It could be list of names in same resource group.
                    - It could be list of dict containing I(resource_group) and I(name).
                    - It is mutually exclusive with C(destination_address_prefix) and C(destination_address_prefixes).
                type: list
            access:
                description:
                    - Whether or not to allow the traffic flow.
                choices:
                    - Allow
                    - Deny
                default: Allow
            priority:
                description:
                    - Order in which to apply the rule. Must a unique integer between 100 and 4096 inclusive.
                required: true
            direction:
                description:
                    - Indicates the direction of the traffic flow.
                choices:
                    - Inbound
                    - Outbound
                default: Inbound
    state:
        description:
            - Assert the state of the security group. Set to C(present) to create or update a security group. Set to C(absent) to remove a security group.
        default: present
        choices:
            - absent
            - present

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - Chris Houseknecht (@chouseknecht)
    - Matt Davis (@nitzmahone)

'''

EXAMPLES = '''

# Create a security group
- azure_rm_securitygroup:
      resource_group: myResourceGroup
      name: mysecgroup
      purge_rules: yes
      rules:
          - name: DenySSH
            protocol: Tcp
            destination_port_range: 22
            access: Deny
            priority: 100
            direction: Inbound
          - name: 'AllowSSH'
            protocol: Tcp
            source_address_prefix:
              - '174.109.158.0/24'
              - '174.109.159.0/24'
            destination_port_range: 22
            access: Allow
            priority: 101
            direction: Inbound
          - name: 'AllowMultiplePorts'
            protocol: Tcp
            source_address_prefix:
              - '174.109.158.0/24'
              - '174.109.159.0/24'
            destination_port_range:
              - 80
              - 443
            access: Allow
            priority: 102

# Update rules on existing security group
- azure_rm_securitygroup:
      resource_group: myResourceGroup
      name: mysecgroup
      rules:
          - name: DenySSH
            protocol: Tcp
            destination_port_range: 22-23
            access: Deny
            priority: 100
            direction: Inbound
          - name: AllowSSHFromHome
            protocol: Tcp
            source_address_prefix: '174.109.158.0/24'
            destination_port_range: 22-23
            access: Allow
            priority: 102
            direction: Inbound
      tags:
          testing: testing
          delete: on-exit

# Delete security group
- azure_rm_securitygroup:
      resource_group: myResourceGroup
      name: mysecgroup
      state: absent
'''

RETURN = '''
state:
    description:
        - Current state of the security group.
    returned: always
    type: complex
    contains:
        default_rules:
            description:
                - The default security rules of network security group.
            returned: always
            type: list
            sample: [
                    {
                        "access": "Allow",
                        "description": "Allow inbound traffic from all VMs in VNET",
                        "destination_address_prefix": "VirtualNetwork",
                        "destination_port_range": "*",
                        "direction": "Inbound",
                        "etag": 'W/"edf48d56-b315-40ca-a85d-dbcb47f2da7d"',
                        "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Network/networkSecurityGroups/mysecgroup/defaultSecurityRules/AllowVnetInBound",
                        "name": "AllowVnetInBound",
                        "priority": 65000,
                        "protocol": "*",
                        "provisioning_state": "Succeeded",
                        "source_address_prefix": "VirtualNetwork",
                        "source_port_range": "*"
                    },
                    {
                        "access": "Allow",
                        "description": "Allow inbound traffic from azure load balancer",
                        "destination_address_prefix": "*",
                        "destination_port_range": "*",
                        "direction": "Inbound",
                        "etag": 'W/"edf48d56-b315-40ca-a85d-dbcb47f2da7d"',
                        "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Network/networkSecurityGroups/mysecgroup/defaultSecurityRules/AllowAzureLoadBalancerInBound",
                        "name": "AllowAzureLoadBalancerInBound",
                        "priority": 65001,
                        "protocol": "*",
                        "provisioning_state": "Succeeded",
                        "source_address_prefix": "AzureLoadBalancer",
                        "source_port_range": "*"
                    },
                    {
                        "access": "Deny",
                        "description": "Deny all inbound traffic",
                        "destination_address_prefix": "*",
                        "destination_port_range": "*",
                        "direction": "Inbound",
                        "etag": 'W/"edf48d56-b315-40ca-a85d-dbcb47f2da7d"',
                        "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Network/networkSecurityGroups/mysecgroup/defaultSecurityRules/DenyAllInBound",
                        "name": "DenyAllInBound",
                        "priority": 65500,
                        "protocol": "*",
                        "provisioning_state": "Succeeded",
                        "source_address_prefix": "*",
                        "source_port_range": "*"
                    },
                    {
                        "access": "Allow",
                        "description": "Allow outbound traffic from all VMs to all VMs in VNET",
                        "destination_address_prefix": "VirtualNetwork",
                        "destination_port_range": "*",
                        "direction": "Outbound",
                        "etag": 'W/"edf48d56-b315-40ca-a85d-dbcb47f2da7d"',
                        "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Network/networkSecurityGroups/mysecgroup/defaultSecurityRules/AllowVnetOutBound",
                        "name": "AllowVnetOutBound",
                        "priority": 65000,
                        "protocol": "*",
                        "provisioning_state": "Succeeded",
                        "source_address_prefix": "VirtualNetwork",
                        "source_port_range": "*"
                    },
                    {
                        "access": "Allow",
                        "description": "Allow outbound traffic from all VMs to Internet",
                        "destination_address_prefix": "Internet",
                        "destination_port_range": "*",
                        "direction": "Outbound",
                        "etag": 'W/"edf48d56-b315-40ca-a85d-dbcb47f2da7d"',
                        "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Network/networkSecurityGroups/mysecgroup/defaultSecurityRules/AllowInternetOutBound",
                        "name": "AllowInternetOutBound",
                        "priority": 65001,
                        "protocol": "*",
                        "provisioning_state": "Succeeded",
                        "source_address_prefix": "*",
                        "source_port_range": "*"
                    },
                    {
                        "access": "Deny",
                        "description": "Deny all outbound traffic",
                        "destination_address_prefix": "*",
                        "destination_port_range": "*",
                        "direction": "Outbound",
                        "etag": 'W/"edf48d56-b315-40ca-a85d-dbcb47f2da7d"',
                        "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Network/networkSecurityGroups/mysecgroup/defaultSecurityRules/DenyAllOutBound",
                        "name": "DenyAllOutBound",
                        "priority": 65500,
                        "protocol": "*",
                        "provisioning_state": "Succeeded",
                        "source_address_prefix": "*",
                        "source_port_range": "*"
                    }
                ]
        id:
            description:
                - The resource ID.
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Network/networkSecurityGroups/mysecgroup"
        location:
            description:
                - The resource location.
            returned: always
            type: str
            sample: "westus"
        name:
            description:
                - Name of the security group.
            returned: always
            type: str
            sample: "mysecgroup"
        network_interfaces:
            description:
                - A collection of references to network interfaces.
            returned: always
            type: list
            sample: []
        rules:
            description:
                - A collection of security rules of the network security group.
            returned: always
            type: list
            sample: [
                {
                    "access": "Deny",
                    "description": null,
                    "destination_address_prefix": "*",
                    "destination_port_range": "22",
                    "direction": "Inbound",
                    "etag": 'W/"edf48d56-b315-40ca-a85d-dbcb47f2da7d"',
                    "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Network/networkSecurityGroups/mysecgroup/securityRules/DenySSH",
                    "name": "DenySSH",
                    "priority": 100,
                    "protocol": "Tcp",
                    "provisioning_state": "Succeeded",
                    "source_address_prefix": "*",
                    "source_port_range": "*"
                },
                {
                    "access": "Allow",
                    "description": null,
                    "destination_address_prefix": "*",
                    "destination_port_range": "22",
                    "direction": "Inbound",
                    "etag": 'W/"edf48d56-b315-40ca-a85d-dbcb47f2da7d"',
                    "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Network/networkSecurityGroups/mysecgroup/securityRules/AllowSSH",
                    "name": "AllowSSH",
                    "priority": 101,
                    "protocol": "Tcp",
                    "provisioning_state": "Succeeded",
                    "source_address_prefix": "174.109.158.0/24",
                    "source_port_range": "*"
                }
                ]
        subnets:
            description:
                - A collection of references to subnets.
            returned: always
            type: list
            sample: []
        tags:
            description:
                - Tags to assign to the security group.
            returned: always
            type: dict
            sample: {
                     "delete": "on-exit",
                     "foo": "bar",
                     "testing": "testing"
                    }
        type:
            description:
                - The resource type.
            returned: always
            type: str
            sample: "Microsoft.Network/networkSecurityGroups"
'''  # NOQA

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.tools import is_valid_resource_id
    from azure.mgmt.network import NetworkManagementClient
except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.six import integer_types
from ansible.module_utils._text import to_native


def validate_rule(self, rule, rule_type=None):
    '''
    Apply defaults to a rule dictionary and check that all values are valid.

    :param rule: rule dict
    :param rule_type: Set to 'default' if the rule is part of the default set of rules.
    :return: None
    '''
    priority = rule.get('priority', 0)
    if rule_type != 'default' and (priority < 100 or priority > 4096):
        raise Exception("Rule priority must be between 100 and 4096")

    def check_plural(src, dest):
        if isinstance(rule.get(src), list):
            rule[dest] = rule[src]
            rule[src] = None

    check_plural('destination_address_prefix', 'destination_address_prefixes')
    check_plural('source_address_prefix', 'source_address_prefixes')
    check_plural('source_port_range', 'source_port_ranges')
    check_plural('destination_port_range', 'destination_port_ranges')

    # when source(destination)_application_security_groups set, remove the default value * of source(destination)_address_prefix
    if rule.get('source_application_security_groups') and rule.get('source_address_prefix') == '*':
        rule['source_address_prefix'] = None
    if rule.get('destination_application_security_groups') and rule.get('destination_address_prefix') == '*':
        rule['destination_address_prefix'] = None


def compare_rules_change(old_list, new_list, purge_list):
    old_list = old_list or []
    new_list = new_list or []
    changed = False

    for old_rule in old_list:
        matched = next((x for x in new_list if x['name'] == old_rule['name']), [])
        if matched:  # if the new one is in the old list, check whether it is updated
            changed = changed or compare_rules(old_rule, matched)
        elif not purge_list:  # keep this rule
            new_list.append(old_rule)
        else:  # one rule is removed
            changed = True
    # Compare new list and old list is the same? here only compare names
    if not changed:
        new_names = [to_native(x['name']) for x in new_list]
        old_names = [to_native(x['name']) for x in old_list]
        changed = (set(new_names) != set(old_names))
    return changed, new_list


def compare_rules(old_rule, rule):
    changed = False
    if old_rule['name'] != rule['name']:
        changed = True
    if rule.get('description', None) != old_rule['description']:
        changed = True
    if rule['protocol'] != old_rule['protocol']:
        changed = True
    if str(rule['source_port_range']) != str(old_rule['source_port_range']):
        changed = True
    if str(rule['destination_port_range']) != str(old_rule['destination_port_range']):
        changed = True
    if rule['access'] != old_rule['access']:
        changed = True
    if rule['priority'] != old_rule['priority']:
        changed = True
    if rule['direction'] != old_rule['direction']:
        changed = True
    if str(rule['source_address_prefix']) != str(old_rule['source_address_prefix']):
        changed = True
    if str(rule['destination_address_prefix']) != str(old_rule['destination_address_prefix']):
        changed = True
    if set(rule.get('source_address_prefixes') or []) != set(old_rule.get('source_address_prefixes') or []):
        changed = True
    if set(rule.get('destination_address_prefixes') or []) != set(old_rule.get('destination_address_prefixes') or []):
        changed = True
    if set(rule.get('source_port_ranges') or []) != set(old_rule.get('source_port_ranges') or []):
        changed = True
    if set(rule.get('destination_port_ranges') or []) != set(old_rule.get('destination_port_ranges') or []):
        changed = True
    if set(rule.get('source_application_security_groups') or []) != set(old_rule.get('source_application_security_groups') or []):
        changed = True
    if set(rule.get('destination_application_security_groups') or []) != set(old_rule.get('destination_application_security_groups') or []):
        changed = True
    return changed


def create_rule_instance(self, rule):
    '''
    Create an instance of SecurityRule from a dict.

    :param rule: dict
    :return: SecurityRule
    '''
    return self.nsg_models.SecurityRule(
        description=rule.get('description', None),
        protocol=rule.get('protocol', None),
        source_port_range=rule.get('source_port_range', None),
        destination_port_range=rule.get('destination_port_range', None),
        source_address_prefix=rule.get('source_address_prefix', None),
        source_address_prefixes=rule.get('source_address_prefixes', None),
        destination_address_prefix=rule.get('destination_address_prefix', None),
        destination_address_prefixes=rule.get('destination_address_prefixes', None),
        source_port_ranges=rule.get('source_port_ranges', None),
        destination_port_ranges=rule.get('destination_port_ranges', None),
        source_application_security_groups=[
            self.nsg_models.ApplicationSecurityGroup(id=p)
            for p in rule.get('source_application_security_groups')] if rule.get('source_application_security_groups') else None,
        destination_application_security_groups=[
            self.nsg_models.ApplicationSecurityGroup(id=p)
            for p in rule.get('destination_application_security_groups')] if rule.get('destination_application_security_groups') else None,
        access=rule.get('access', None),
        priority=rule.get('priority', None),
        direction=rule.get('direction', None),
        provisioning_state=rule.get('provisioning_state', None),
        name=rule.get('name', None),
        etag=rule.get('etag', None)
    )


def create_rule_dict_from_obj(rule):
    '''
    Create a dict from an instance of a SecurityRule.

    :param rule: SecurityRule
    :return: dict
    '''
    return dict(
        id=rule.id,
        name=rule.name,
        description=rule.description,
        protocol=rule.protocol,
        source_port_range=rule.source_port_range,
        destination_port_range=rule.destination_port_range,
        source_address_prefix=rule.source_address_prefix,
        destination_address_prefix=rule.destination_address_prefix,
        source_port_ranges=rule.source_port_ranges,
        destination_port_ranges=rule.destination_port_ranges,
        source_address_prefixes=rule.source_address_prefixes,
        destination_address_prefixes=rule.destination_address_prefixes,
        source_application_security_groups=[p.id for p in rule.source_application_security_groups] if rule.source_application_security_groups else None,
        destination_application_security_groups=[
            p.id for p in rule.destination_application_security_groups] if rule.destination_application_security_groups else None,
        access=rule.access,
        priority=rule.priority,
        direction=rule.direction,
        provisioning_state=rule.provisioning_state,
        etag=rule.etag
    )


def create_network_security_group_dict(nsg):
    results = dict(
        id=nsg.id,
        name=nsg.name,
        type=nsg.type,
        location=nsg.location,
        tags=nsg.tags,
    )
    results['rules'] = []
    if nsg.security_rules:
        for rule in nsg.security_rules:
            results['rules'].append(create_rule_dict_from_obj(rule))

    results['default_rules'] = []
    if nsg.default_security_rules:
        for rule in nsg.default_security_rules:
            results['default_rules'].append(create_rule_dict_from_obj(rule))

    results['network_interfaces'] = []
    if nsg.network_interfaces:
        for interface in nsg.network_interfaces:
            results['network_interfaces'].append(interface.id)

    results['subnets'] = []
    if nsg.subnets:
        for subnet in nsg.subnets:
            results['subnets'].append(subnet.id)

    return results


rule_spec = dict(
    name=dict(type='str', required=True),
    description=dict(type='str'),
    protocol=dict(type='str', choices=['Udp', 'Tcp', '*'], default='*'),
    source_port_range=dict(type='raw', default='*'),
    destination_port_range=dict(type='raw', default='*'),
    source_address_prefix=dict(type='raw', default='*'),
    destination_address_prefix=dict(type='raw', default='*'),
    source_application_security_groups=dict(type='list', elements='raw'),
    destination_application_security_groups=dict(type='list', elements='raw'),
    access=dict(type='str', choices=['Allow', 'Deny'], default='Allow'),
    priority=dict(type='int', required=True),
    direction=dict(type='str', choices=['Inbound', 'Outbound'], default='Inbound')
)


class AzureRMSecurityGroup(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            default_rules=dict(type='list', elements='dict', options=rule_spec),
            location=dict(type='str'),
            name=dict(type='str', required=True),
            purge_default_rules=dict(type='bool', default=False),
            purge_rules=dict(type='bool', default=False),
            resource_group=dict(required=True, type='str'),
            rules=dict(type='list', elements='dict', options=rule_spec),
            state=dict(type='str', default='present', choices=['present', 'absent']),
        )

        self.default_rules = None
        self.location = None
        self.name = None
        self.purge_default_rules = None
        self.purge_rules = None
        self.resource_group = None
        self.rules = None
        self.state = None
        self.tags = None
        self.nsg_models = None  # type: azure.mgmt.network.models

        self.results = dict(
            changed=False,
            state=dict()
        )

        mutually_exclusive = [["source_application_security_group", "source_address_prefix"],
                              ["source_application_security_group", "source_address_prefixes"],
                              ["destination_application_security_group", "destination_address_prefix"],
                              ["destination_application_security_group", "destination_address_prefixes"]]

        super(AzureRMSecurityGroup, self).__init__(self.module_arg_spec,
                                                   supports_check_mode=True,
                                                   mutually_exclusive=mutually_exclusive)

    def exec_module(self, **kwargs):
        # tighten up poll interval for security groups; default 30s is an eternity
        # this value is still overridden by the response Retry-After header (which is set on the initial operation response to 10s)
        self.network_client.config.long_running_operation_timeout = 3
        self.nsg_models = self.network_client.network_security_groups.models

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        changed = False
        results = dict()

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            # Set default location
            self.location = resource_group.location

        if self.rules:
            for rule in self.rules:
                try:
                    validate_rule(self, rule)
                except Exception as exc:
                    self.fail("Error validating rule {0} - {1}".format(rule, str(exc)))
                self.convert_asg_to_id(rule)

        if self.default_rules:
            for rule in self.default_rules:
                try:
                    validate_rule(self, rule, 'default')
                except Exception as exc:
                    self.fail("Error validating default rule {0} - {1}".format(rule, str(exc)))
                self.convert_asg_to_id(rule)

        try:
            nsg = self.network_client.network_security_groups.get(self.resource_group, self.name)
            results = create_network_security_group_dict(nsg)
            self.log("Found security group:")
            self.log(results, pretty_print=True)
            self.check_provisioning_state(nsg, self.state)
            if self.state == 'present':
                pass
            elif self.state == 'absent':
                self.log("CHANGED: security group found but state is 'absent'")
                changed = True
        except CloudError:  # TODO: actually check for ResourceMissingError
            if self.state == 'present':
                self.log("CHANGED: security group not found and state is 'present'")
                changed = True

        if self.state == 'present' and not changed:
            # update the security group
            self.log("Update security group {0}".format(self.name))

            update_tags, results['tags'] = self.update_tags(results['tags'])
            if update_tags:
                changed = True

            rule_changed, new_rule = compare_rules_change(results['rules'], self.rules, self.purge_rules)
            if rule_changed:
                changed = True
                results['rules'] = new_rule
            rule_changed, new_rule = compare_rules_change(results['default_rules'], self.default_rules, self.purge_default_rules)
            if rule_changed:
                changed = True
                results['default_rules'] = new_rule

            self.results['changed'] = changed
            self.results['state'] = results
            if not self.check_mode and changed:
                self.results['state'] = self.create_or_update(results)

        elif self.state == 'present' and changed:
            # create the security group
            self.log("Create security group {0}".format(self.name))

            if not self.location:
                self.fail("Parameter error: location required when creating a security group.")

            results['name'] = self.name
            results['location'] = self.location
            results['rules'] = []
            results['default_rules'] = []
            results['tags'] = {}

            if self.rules:
                results['rules'] = self.rules
            if self.default_rules:
                results['default_rules'] = self.default_rules
            if self.tags:
                results['tags'] = self.tags

            self.results['changed'] = changed
            self.results['state'] = results
            if not self.check_mode:
                self.results['state'] = self.create_or_update(results)

        elif self.state == 'absent' and changed:
            self.log("Delete security group {0}".format(self.name))
            self.results['changed'] = changed
            self.results['state'] = dict()
            if not self.check_mode:
                self.delete()
                # the delete does not actually return anything. if no exception, then we'll assume
                # it worked.
                self.results['state']['status'] = 'Deleted'

        return self.results

    def create_or_update(self, results):
        parameters = self.nsg_models.NetworkSecurityGroup()
        if results.get('rules'):
            parameters.security_rules = []
            for rule in results.get('rules'):
                parameters.security_rules.append(create_rule_instance(self, rule))
        if results.get('default_rules'):
            parameters.default_security_rules = []
            for rule in results.get('default_rules'):
                parameters.default_security_rules.append(create_rule_instance(self, rule))
        parameters.tags = results.get('tags')
        parameters.location = results.get('location')

        try:
            poller = self.network_client.network_security_groups.create_or_update(resource_group_name=self.resource_group,
                                                                                  network_security_group_name=self.name,
                                                                                  parameters=parameters)
            result = self.get_poller_result(poller)
        except CloudError as exc:
            self.fail("Error creating/updating security group {0} - {1}".format(self.name, str(exc)))
        return create_network_security_group_dict(result)

    def delete(self):
        try:
            poller = self.network_client.network_security_groups.delete(resource_group_name=self.resource_group, network_security_group_name=self.name)
            result = self.get_poller_result(poller)
        except CloudError as exc:
            self.fail("Error deleting security group {0} - {1}".format(self.name, str(exc)))

        return result

    def convert_asg_to_id(self, rule):
        def convert_to_id(rule, key):
            if rule.get(key):
                ids = []
                for p in rule.get(key):
                    if isinstance(p, dict):
                        ids.append("/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/applicationSecurityGroups/{2}".format(
                            self.subscription_id, p.get('resource_group'), p.get('name')))
                    elif isinstance(p, str):
                        if is_valid_resource_id(p):
                            ids.append(p)
                        else:
                            ids.append("/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/applicationSecurityGroups/{2}".format(
                                self.subscription_id, self.resource_group, p))
                rule[key] = ids
        convert_to_id(rule, 'source_application_security_groups')
        convert_to_id(rule, 'destination_application_security_groups')


def main():
    AzureRMSecurityGroup()


if __name__ == '__main__':
    main()
