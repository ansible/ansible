#!/usr/bin/python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'curated'}


DOCUMENTATION = '''
---
module: azure_rm_securitygroup
version_added: "2.1"
short_description: Manage Azure network security groups.
description:
    - Create, update or delete a network security group. A security group contains Access Control List (ACL) rules
      that allow or deny network traffic to subnets or individual network interfaces. A security group is created
      with a set of default security rules and an empty set of security rules. Shape traffic flow by adding
      rules to the empty set of security rules.

options:
    default_rules:
        description:
            - The set of default rules automatically added to a security group at creation. In general default
              rules will not be modified. Modify rules to shape the flow of traffic to or from a subnet or NIC. See
              rules below for the makeup of a rule dict.
        required: false
        default: null
    location:
        description:
            - Valid azure location. Defaults to location of the resource group.
        default: resource_group location
        required: false
    name:
        description:
            - Name of the security group to operate on.
        required: false
        default: null
    purge_default_rules:
        description:
            - Remove any existing rules not matching those defined in the default_rules parameter.
        default: false
        required: false
    purge_rules:
        description:
            - Remove any existing rules not matching those defined in the rules parameters.
        default: false
        required: false
    resource_group:
        description:
            - Name of the resource group the security group belongs to.
        required: true
    rules:
        description:
            - Set of rules shaping traffic flow to or from a subnet or NIC. Each rule is a dictionary.
        required: false
        default: null
        suboptions:
            name:
                description:
                  - Unique name for the rule.
                required: true
            description:
                description:
                  - Short description of the rule's purpose.
            protocol:
                description: Accepted traffic protocol.
                choices:
                  - Udp
                  - Tcp
                  - "*"
                default: "*"
            source_port_range:
                description:
                  - Port or range of ports from which traffic originates.
                default: "*"
            destination_port_range:
                description:
                  - Port or range of ports to which traffic is headed.
                default: "*"
            source_address_prefix:
                description:
                  - IP address or CIDR from which traffic originates.
                default: "*"
            destination_address_prefix:
                description:
                  - IP address or CIDR to which traffic is headed.
                default: "*"
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
            - Assert the state of the security group. Set to 'present' to create or update a security group. Set to
              'absent' to remove a security group.
        default: present
        required: false
        choices:
            - absent
            - present

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Chris Houseknecht (@chouseknecht)"
    - "Matt Davis (@nitzmahone)"

'''

EXAMPLES = '''

# Create a security group
- azure_rm_securitygroup:
      resource_group: mygroup
      name: mysecgroup
      purge_rules: yes
      rules:
          - name: DenySSH
            protocol: TCP
            destination_port_range: 22
            access: Deny
            priority: 100
            direction: Inbound
          - name: 'AllowSSH'
            protocol: TCP
            source_address_prefix: '174.109.158.0/24'
            destination_port_range: 22
            access: Allow
            priority: 101
            direction: Inbound

# Update rules on existing security group
- azure_rm_securitygroup:
      resource_group: mygroup
      name: mysecgroup
      rules:
          - name: DenySSH
            protocol: TCP
            destination_port_range: 22-23
            access: Deny
            priority: 100
            direction: Inbound
          - name: AllowSSHFromHome
            protocol: TCP
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
      resource_group: mygroup
      name: mysecgroup
      state: absent
'''

RETURN = '''
state:
    description: Current state of the security group.
    returned: always
    type: dict
    sample: {
        "default_rules": [
            {
                "access": "Allow",
                "description": "Allow inbound traffic from all VMs in VNET",
                "destination_address_prefix": "VirtualNetwork",
                "destination_port_range": "*",
                "direction": "Inbound",
                "etag": 'W/"edf48d56-b315-40ca-a85d-dbcb47f2da7d"',
                "id": "/subscriptions/3f7e29ba-24e0-42f6-8d9c-5149a14bda37/resourceGroups/Testing/providers/Microsoft.Network/networkSecurityGroups/mysecgroup/defaultSecurityRules/AllowVnetInBound",
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
                "id": "/subscriptions/3f7e29ba-24e0-42f6-8d9c-5149a14bda37/resourceGroups/Testing/providers/Microsoft.Network/networkSecurityGroups/mysecgroup/defaultSecurityRules/AllowAzureLoadBalancerInBound",
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
                "id": "/subscriptions/3f7e29ba-24e0-42f6-8d9c-5149a14bda37/resourceGroups/Testing/providers/Microsoft.Network/networkSecurityGroups/mysecgroup/defaultSecurityRules/DenyAllInBound",
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
                "id": "/subscriptions/3f7e29ba-24e0-42f6-8d9c-5149a14bda37/resourceGroups/Testing/providers/Microsoft.Network/networkSecurityGroups/mysecgroup/defaultSecurityRules/AllowVnetOutBound",
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
                "id": "/subscriptions/3f7e29ba-24e0-42f6-8d9c-5149a14bda37/resourceGroups/Testing/providers/Microsoft.Network/networkSecurityGroups/mysecgroup/defaultSecurityRules/AllowInternetOutBound",
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
                "id": "/subscriptions/3f7e29ba-24e0-42f6-8d9c-5149a14bda37/resourceGroups/Testing/providers/Microsoft.Network/networkSecurityGroups/mysecgroup/defaultSecurityRules/DenyAllOutBound",
                "name": "DenyAllOutBound",
                "priority": 65500,
                "protocol": "*",
                "provisioning_state": "Succeeded",
                "source_address_prefix": "*",
                "source_port_range": "*"
            }
        ],
        "id": "/subscriptions/3f7e29ba-24e0-42f6-8d9c-5149a14bda37/resourceGroups/Testing/providers/Microsoft.Network/networkSecurityGroups/mysecgroup",
        "location": "westus",
        "name": "mysecgroup",
        "network_interfaces": [],
        "rules": [
            {
                "access": "Deny",
                "description": null,
                "destination_address_prefix": "*",
                "destination_port_range": "22",
                "direction": "Inbound",
                "etag": 'W/"edf48d56-b315-40ca-a85d-dbcb47f2da7d"',
                "id": "/subscriptions/3f7e29ba-24e0-42f6-8d9c-5149a14bda37/resourceGroups/Testing/providers/Microsoft.Network/networkSecurityGroups/mysecgroup/securityRules/DenySSH",
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
                "id": "/subscriptions/3f7e29ba-24e0-42f6-8d9c-5149a14bda37/resourceGroups/Testing/providers/Microsoft.Network/networkSecurityGroups/mysecgroup/securityRules/AllowSSH",
                "name": "AllowSSH",
                "priority": 101,
                "protocol": "Tcp",
                "provisioning_state": "Succeeded",
                "source_address_prefix": "174.109.158.0/24",
                "source_port_range": "*"
            }
        ],
        "subnets": [],
        "tags": {
            "delete": "on-exit",
            "foo": "bar",
            "testing": "testing"
        },
        "type": "Microsoft.Network/networkSecurityGroups"
    }
'''  # NOQA

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureHttpError
    from azure.mgmt.network.models import NetworkSecurityGroup, SecurityRule
    from azure.mgmt.network.models.network_management_client_enums import (SecurityRuleAccess,
                                                                           SecurityRuleDirection,
                                                                           SecurityRuleProtocol)
except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.six import integer_types


def validate_rule(rule, rule_type=None):
    '''
    Apply defaults to a rule dictionary and check that all values are valid.

    :param rule: rule dict
    :param rule_type: Set to 'default' if the rule is part of the default set of rules.
    :return: None
    '''

    if not rule.get('name'):
        raise Exception("Rule name value is required.")

    priority = rule.get('priority', None)
    if not priority:
        raise Exception("Rule priority is required.")
    if not isinstance(priority, integer_types):
        try:
            priority = int(priority)
            rule['priority'] = priority
        except:
            raise Exception("Rule priority attribute must be an integer.")
    if rule_type != 'default' and (priority < 100 or priority > 4096):
        raise Exception("Rule priority must be between 100 and 4096")

    if not rule.get('access'):
        rule['access'] = 'Allow'

    access_names = [member.value for member in SecurityRuleAccess]
    if rule['access'] not in access_names:
        raise Exception("Rule access must be one of [{0}]".format(', '.join(access_names)))

    if not rule.get('destination_address_prefix'):
        rule['destination_address_prefix'] = '*'

    if not rule.get('source_address_prefix'):
        rule['source_address_prefix'] = '*'

    if not rule.get('protocol'):
        rule['protocol'] = '*'

    protocol_names = [member.value for member in SecurityRuleProtocol]
    if rule['protocol'] not in protocol_names:
        raise Exception("Rule protocol must be one of [{0}]".format(', '.join(protocol_names)))

    if not rule.get('direction'):
        rule['direction'] = 'Inbound'

    direction_names = [member.value for member in SecurityRuleDirection]
    if rule['direction'] not in direction_names:
        raise Exception("Rule direction must be one of [{0}]".format(', '.join(direction_names)))

    if not rule.get('source_port_range'):
        rule['source_port_range'] = '*'

    if not rule.get('destination_port_range'):
        rule['destination_port_range'] = '*'


def compare_rules(r, rule):
    matched = False
    changed = False
    if r['name'] == rule['name']:
        matched = True
        if rule.get('description', None) != r['description']:
            changed = True
            r['description'] = rule['description']
        if rule['protocol'] != r['protocol']:
            changed = True
            r['protocol'] = rule['protocol']
        if str(rule['source_port_range']) != str(r['source_port_range']):
            changed = True
            r['source_port_range'] = str(rule['source_port_range'])
        if str(rule['destination_port_range']) != str(r['destination_port_range']):
            changed = True
            r['destination_port_range'] = str(rule['destination_port_range'])
        if rule['access'] != r['access']:
            changed = True
            r['access'] = rule['access']
        if rule['priority'] != r['priority']:
            changed = True
            r['priority'] = rule['priority']
        if rule['direction'] != r['direction']:
            changed = True
            r['direction'] = rule['direction']
    return matched, changed


def create_rule_instance(rule):
    '''
    Create an instance of SecurityRule from a dict.

    :param rule: dict
    :return: SecurityRule
    '''
    return SecurityRule(
        rule['protocol'],
        rule['source_address_prefix'],
        rule['destination_address_prefix'],
        rule['access'],
        rule['direction'],
        id=rule.get('id', None),
        description=rule.get('description', None),
        source_port_range=rule.get('source_port_range', None),
        destination_port_range=rule.get('destination_port_range', None),
        priority=rule.get('priority', None),
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


class AzureRMSecurityGroup(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            default_rules=dict(type='list'),
            location=dict(type='str'),
            name=dict(type='str', required=True),
            purge_default_rules=dict(type='bool', default=False),
            purge_rules=dict(type='bool', default=False),
            resource_group=dict(required=True, type='str'),
            rules=dict(type='list'),
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

        self.results = dict(
            changed=False,
            state=dict()
        )

        super(AzureRMSecurityGroup, self).__init__(self.module_arg_spec,
                                                   supports_check_mode=True)

    def exec_module(self, **kwargs):

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
                    validate_rule(rule)
                except Exception as exc:
                    self.fail("Error validating rule {0} - {1}".format(rule, str(exc)))

        if self.default_rules:
            for rule in self.default_rules:
                try:
                    validate_rule(rule, 'default')
                except Exception as exc:
                    self.fail("Error validating default rule {0} - {1}".format(rule, str(exc)))

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
        except CloudError:
            if self.state == 'present':
                self.log("CHANGED: security group not found and state is 'present'")
                changed = True

        if self.state == 'present' and not changed:
            # update the security group
            self.log("Update security group {0}".format(self.name))

            if self.rules:
                for rule in self.rules:
                    rule_matched = False
                    for r in results['rules']:
                        match, changed = compare_rules(r, rule)
                        if changed:
                            changed = True
                        if match:
                            rule_matched = True

                    if not rule_matched:
                        changed = True
                        results['rules'].append(rule)

            if self.purge_rules:
                new_rules = []
                for rule in results['rules']:
                    for r in self.rules:
                        if rule['name'] == r['name']:
                            new_rules.append(rule)
                results['rules'] = new_rules

            if self.default_rules:
                for rule in self.default_rules:
                    rule_matched = False
                    for r in results['default_rules']:
                        match, changed = compare_rules(r, rule)
                        if changed:
                            changed = True
                        if match:
                            rule_matched = True
                    if not rule_matched:
                        changed = True
                        results['default_rules'].append(rule)

            if self.purge_default_rules:
                new_default_rules = []
                for rule in results['default_rules']:
                    for r in self.default_rules:
                        if rule['name'] == r['name']:
                            new_default_rules.append(rule)
                results['default_rules'] = new_default_rules

            update_tags, results['tags'] = self.update_tags(results['tags'])
            if update_tags:
                changed = True

            self.results['changed'] = changed
            self.results['state'] = results
            if not self.check_mode:
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
        parameters = NetworkSecurityGroup()
        if results.get('rules'):
            parameters.security_rules = []
            for rule in results.get('rules'):
                parameters.security_rules.append(create_rule_instance(rule))
        if results.get('default_rules'):
            parameters.default_security_rules = []
            for rule in results.get('default_rules'):
                parameters.default_security_rules.append(create_rule_instance(rule))
        parameters.tags = results.get('tags')
        parameters.location = results.get('location')

        try:
            poller = self.network_client.network_security_groups.create_or_update(self.resource_group,
                                                                                  self.name,
                                                                                  parameters)
            result = self.get_poller_result(poller)
        except AzureHttpError as exc:
            self.fail("Error creating/updating security group {0} - {1}".format(self.name, str(exc)))
        return create_network_security_group_dict(result)

    def delete(self):
        try:
            poller = self.network_client.network_security_groups.delete(self.resource_group, self.name)
            result = self.get_poller_result(poller)
        except AzureHttpError as exc:
            raise Exception("Error deleting security group {0} - {1}".format(self.name, str(exc)))
        return result


def main():
    AzureRMSecurityGroup()


if __name__ == '__main__':
    main()
