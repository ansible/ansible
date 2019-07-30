#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: ec2_vpc_nacl
short_description: create and delete Network ACLs.
description:
  - Read the AWS documentation for Network ACLS
    U(https://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_ACLs.html)
version_added: "2.2"
options:
  name:
    description:
      - Tagged name identifying a network ACL.
      - One and only one of the I(name) or I(nacl_id) is required.
    required: false
  nacl_id:
    description:
      - NACL id identifying a network ACL.
      - One and only one of the I(name) or I(nacl_id) is required.
    required: false
    version_added: "2.4"
  vpc_id:
    description:
      - VPC id of the requesting VPC.
      - Required when state present.
    required: false
  subnets:
    description:
      - The list of subnets that should be associated with the network ACL.
      - Must be specified as a list
      - Each subnet can be specified as subnet ID, or its tagged name.
    required: false
  egress:
    description:
      - A list of rules for outgoing traffic. Each rule must be specified as a list.
        Each rule may contain the rule number (integer 1-32766), protocol (one of ['tcp', 'udp', 'icmp', '-1', 'all']),
        the rule action ('allow' or 'deny') the CIDR of the IPv4 network range to allow or deny,
        the ICMP type (-1 means all types), the ICMP code (-1 means all codes), the last port in the range for
        TCP or UDP protocols, and the first port in the range for TCP or UDP protocols.
        See examples.
    default: []
    required: false
  ingress:
    description:
      - List of rules for incoming traffic. Each rule must be specified as a list.
        Each rule may contain the rule number (integer 1-32766), protocol (one of ['tcp', 'udp', 'icmp', '-1', 'all']),
        the rule action ('allow' or 'deny') the CIDR of the IPv4 network range to allow or deny,
        the ICMP type (-1 means all types), the ICMP code (-1 means all codes), the last port in the range for
        TCP or UDP protocols, and the first port in the range for TCP or UDP protocols.
        See examples.
    default: []
    required: false
  tags:
    description:
      - Dictionary of tags to look for and apply when creating a network ACL.
    required: false
  state:
    description:
      - Creates or modifies an existing NACL
      - Deletes a NACL and reassociates subnets to the default NACL
    required: false
    choices: ['present', 'absent']
    default: present
author: Mike Mochan (@mmochan)
extends_documentation_fragment:
    - aws
    - ec2
requirements: [ botocore, boto3, json ]
'''

EXAMPLES = '''

# Complete example to create and delete a network ACL
# that allows SSH, HTTP and ICMP in, and all traffic out.
- name: "Create and associate production DMZ network ACL with DMZ subnets"
  ec2_vpc_nacl:
    vpc_id: vpc-12345678
    name: prod-dmz-nacl
    region: ap-southeast-2
    subnets: ['prod-dmz-1', 'prod-dmz-2']
    tags:
      CostCode: CC1234
      Project: phoenix
      Description: production DMZ
    ingress:
        # rule no, protocol, allow/deny, cidr, icmp_type, icmp_code,
        #                                             port from, port to
        - [100, 'tcp', 'allow', '0.0.0.0/0', null, null, 22, 22]
        - [200, 'tcp', 'allow', '0.0.0.0/0', null, null, 80, 80]
        - [300, 'icmp', 'allow', '0.0.0.0/0', 0, 8]
    egress:
        - [100, 'all', 'allow', '0.0.0.0/0', null, null, null, null]
    state: 'present'

- name: "Remove the ingress and egress rules - defaults to deny all"
  ec2_vpc_nacl:
    vpc_id: vpc-12345678
    name: prod-dmz-nacl
    region: ap-southeast-2
    subnets:
      - prod-dmz-1
      - prod-dmz-2
    tags:
      CostCode: CC1234
      Project: phoenix
      Description: production DMZ
    state: present

- name: "Remove the NACL subnet associations and tags"
  ec2_vpc_nacl:
    vpc_id: 'vpc-12345678'
    name: prod-dmz-nacl
    region: ap-southeast-2
    state: present

- name: "Delete nacl and subnet associations"
  ec2_vpc_nacl:
    vpc_id: vpc-12345678
    name: prod-dmz-nacl
    state: absent

- name: "Delete nacl by its id"
  ec2_vpc_nacl:
    nacl_id: acl-33b4ee5b
    state: absent
'''
RETURN = '''
task:
  description: The result of the create, or delete action.
  returned: success
  type: dict
'''

try:
    import botocore
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, get_aws_connection_info


# VPC-supported IANA protocol numbers
# http://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml
PROTOCOL_NUMBERS = {'all': -1, 'icmp': 1, 'tcp': 6, 'udp': 17, }


# Utility methods
def icmp_present(entry):
    if len(entry) == 6 and entry[1] == 'icmp' or entry[1] == 1:
        return True


def load_tags(module):
    tags = []
    if module.params.get('tags'):
        for name, value in module.params.get('tags').items():
            tags.append({'Key': name, 'Value': str(value)})
        tags.append({'Key': "Name", 'Value': module.params.get('name')})
    else:
        tags.append({'Key': "Name", 'Value': module.params.get('name')})
    return tags


def subnets_removed(nacl_id, subnets, client, module):
    results = find_acl_by_id(nacl_id, client, module)
    associations = results['NetworkAcls'][0]['Associations']
    subnet_ids = [assoc['SubnetId'] for assoc in associations]
    return [subnet for subnet in subnet_ids if subnet not in subnets]


def subnets_added(nacl_id, subnets, client, module):
    results = find_acl_by_id(nacl_id, client, module)
    associations = results['NetworkAcls'][0]['Associations']
    subnet_ids = [assoc['SubnetId'] for assoc in associations]
    return [subnet for subnet in subnets if subnet not in subnet_ids]


def subnets_changed(nacl, client, module):
    changed = False
    vpc_id = module.params.get('vpc_id')
    nacl_id = nacl['NetworkAcls'][0]['NetworkAclId']
    subnets = subnets_to_associate(nacl, client, module)
    if not subnets:
        default_nacl_id = find_default_vpc_nacl(vpc_id, client, module)[0]
        subnets = find_subnet_ids_by_nacl_id(nacl_id, client, module)
        if subnets:
            replace_network_acl_association(default_nacl_id, subnets, client, module)
            changed = True
            return changed
        changed = False
        return changed
    subs_added = subnets_added(nacl_id, subnets, client, module)
    if subs_added:
        replace_network_acl_association(nacl_id, subs_added, client, module)
        changed = True
    subs_removed = subnets_removed(nacl_id, subnets, client, module)
    if subs_removed:
        default_nacl_id = find_default_vpc_nacl(vpc_id, client, module)[0]
        replace_network_acl_association(default_nacl_id, subs_removed, client, module)
        changed = True
    return changed


def nacls_changed(nacl, client, module):
    changed = False
    params = dict()
    params['egress'] = module.params.get('egress')
    params['ingress'] = module.params.get('ingress')

    nacl_id = nacl['NetworkAcls'][0]['NetworkAclId']
    nacl = describe_network_acl(client, module)
    entries = nacl['NetworkAcls'][0]['Entries']
    egress = [rule for rule in entries if rule['Egress'] is True and rule['RuleNumber'] < 32767]
    ingress = [rule for rule in entries if rule['Egress'] is False and rule['RuleNumber'] < 32767]
    if rules_changed(egress, params['egress'], True, nacl_id, client, module):
        changed = True
    if rules_changed(ingress, params['ingress'], False, nacl_id, client, module):
        changed = True
    return changed


def tags_changed(nacl_id, client, module):
    changed = False
    tags = dict()
    if module.params.get('tags'):
        tags = module.params.get('tags')
    if module.params.get('name') and not tags.get('Name'):
        tags['Name'] = module.params['name']
    nacl = find_acl_by_id(nacl_id, client, module)
    if nacl['NetworkAcls']:
        nacl_values = [t.values() for t in nacl['NetworkAcls'][0]['Tags']]
        nacl_tags = [item for sublist in nacl_values for item in sublist]
        tag_values = [[key, str(value)] for key, value in tags.items()]
        tags = [item for sublist in tag_values for item in sublist]
        if sorted(nacl_tags) == sorted(tags):
            changed = False
            return changed
        else:
            delete_tags(nacl_id, client, module)
            create_tags(nacl_id, client, module)
            changed = True
            return changed
    return changed


def rules_changed(aws_rules, param_rules, Egress, nacl_id, client, module):
    changed = False
    rules = list()
    for entry in param_rules:
        rules.append(process_rule_entry(entry, Egress))
    if rules == aws_rules:
        return changed
    else:
        removed_rules = [x for x in aws_rules if x not in rules]
        if removed_rules:
            params = dict()
            for rule in removed_rules:
                params['NetworkAclId'] = nacl_id
                params['RuleNumber'] = rule['RuleNumber']
                params['Egress'] = Egress
                delete_network_acl_entry(params, client, module)
            changed = True
        added_rules = [x for x in rules if x not in aws_rules]
        if added_rules:
            for rule in added_rules:
                rule['NetworkAclId'] = nacl_id
                create_network_acl_entry(rule, client, module)
            changed = True
    return changed


def process_rule_entry(entry, Egress):
    params = dict()
    params['RuleNumber'] = entry[0]
    params['Protocol'] = str(PROTOCOL_NUMBERS[entry[1]])
    params['RuleAction'] = entry[2]
    params['Egress'] = Egress
    params['CidrBlock'] = entry[3]
    if icmp_present(entry):
        params['IcmpTypeCode'] = {"Type": int(entry[4]), "Code": int(entry[5])}
    else:
        if entry[6] or entry[7]:
            params['PortRange'] = {"From": entry[6], 'To': entry[7]}
    return params


def restore_default_associations(assoc_ids, default_nacl_id, client, module):
    if assoc_ids:
        params = dict()
        params['NetworkAclId'] = default_nacl_id[0]
        for assoc_id in assoc_ids:
            params['AssociationId'] = assoc_id
            restore_default_acl_association(params, client, module)
        return True


def construct_acl_entries(nacl, client, module):
    for entry in module.params.get('ingress'):
        params = process_rule_entry(entry, Egress=False)
        params['NetworkAclId'] = nacl['NetworkAcl']['NetworkAclId']
        create_network_acl_entry(params, client, module)
    for rule in module.params.get('egress'):
        params = process_rule_entry(rule, Egress=True)
        params['NetworkAclId'] = nacl['NetworkAcl']['NetworkAclId']
        create_network_acl_entry(params, client, module)


# Module invocations
def setup_network_acl(client, module):
    changed = False
    nacl = describe_network_acl(client, module)
    if not nacl['NetworkAcls']:
        nacl = create_network_acl(module.params.get('vpc_id'), client, module)
        nacl_id = nacl['NetworkAcl']['NetworkAclId']
        create_tags(nacl_id, client, module)
        subnets = subnets_to_associate(nacl, client, module)
        replace_network_acl_association(nacl_id, subnets, client, module)
        construct_acl_entries(nacl, client, module)
        changed = True
        return(changed, nacl['NetworkAcl']['NetworkAclId'])
    else:
        changed = False
        nacl_id = nacl['NetworkAcls'][0]['NetworkAclId']
        subnet_result = subnets_changed(nacl, client, module)
        nacl_result = nacls_changed(nacl, client, module)
        tag_result = tags_changed(nacl_id, client, module)
        if subnet_result is True or nacl_result is True or tag_result is True:
            changed = True
            return(changed, nacl_id)
        return (changed, nacl_id)


def remove_network_acl(client, module):
    changed = False
    result = dict()
    nacl = describe_network_acl(client, module)
    if nacl['NetworkAcls']:
        nacl_id = nacl['NetworkAcls'][0]['NetworkAclId']
        vpc_id = nacl['NetworkAcls'][0]['VpcId']
        associations = nacl['NetworkAcls'][0]['Associations']
        assoc_ids = [a['NetworkAclAssociationId'] for a in associations]
        default_nacl_id = find_default_vpc_nacl(vpc_id, client, module)
        if not default_nacl_id:
            result = {vpc_id: "Default NACL ID not found - Check the VPC ID"}
            return changed, result
        if restore_default_associations(assoc_ids, default_nacl_id, client, module):
            delete_network_acl(nacl_id, client, module)
            changed = True
            result[nacl_id] = "Successfully deleted"
            return changed, result
        if not assoc_ids:
            delete_network_acl(nacl_id, client, module)
            changed = True
            result[nacl_id] = "Successfully deleted"
            return changed, result
    return changed, result


# Boto3 client methods
def create_network_acl(vpc_id, client, module):
    try:
        if module.check_mode:
            nacl = dict(NetworkAcl=dict(NetworkAclId="nacl-00000000"))
        else:
            nacl = client.create_network_acl(VpcId=vpc_id)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))
    return nacl


def create_network_acl_entry(params, client, module):
    try:
        if not module.check_mode:
            client.create_network_acl_entry(**params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))


def create_tags(nacl_id, client, module):
    try:
        delete_tags(nacl_id, client, module)
        if not module.check_mode:
            client.create_tags(Resources=[nacl_id], Tags=load_tags(module))
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))


def delete_network_acl(nacl_id, client, module):
    try:
        if not module.check_mode:
            client.delete_network_acl(NetworkAclId=nacl_id)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))


def delete_network_acl_entry(params, client, module):
    try:
        if not module.check_mode:
            client.delete_network_acl_entry(**params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))


def delete_tags(nacl_id, client, module):
    try:
        if not module.check_mode:
            client.delete_tags(Resources=[nacl_id])
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))


def describe_acl_associations(subnets, client, module):
    if not subnets:
        return []
    try:
        results = client.describe_network_acls(Filters=[
            {'Name': 'association.subnet-id', 'Values': subnets}
        ])
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))
    associations = results['NetworkAcls'][0]['Associations']
    return [a['NetworkAclAssociationId'] for a in associations if a['SubnetId'] in subnets]


def describe_network_acl(client, module):
    try:
        if module.params.get('nacl_id'):
            nacl = client.describe_network_acls(Filters=[
                {'Name': 'network-acl-id', 'Values': [module.params.get('nacl_id')]}
            ])
        else:
            nacl = client.describe_network_acls(Filters=[
                {'Name': 'tag:Name', 'Values': [module.params.get('name')]}
            ])
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))
    return nacl


def find_acl_by_id(nacl_id, client, module):
    try:
        return client.describe_network_acls(NetworkAclIds=[nacl_id])
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))


def find_default_vpc_nacl(vpc_id, client, module):
    try:
        response = client.describe_network_acls(Filters=[
            {'Name': 'vpc-id', 'Values': [vpc_id]}])
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))
    nacls = response['NetworkAcls']
    return [n['NetworkAclId'] for n in nacls if n['IsDefault'] is True]


def find_subnet_ids_by_nacl_id(nacl_id, client, module):
    try:
        results = client.describe_network_acls(Filters=[
            {'Name': 'association.network-acl-id', 'Values': [nacl_id]}
        ])
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))
    if results['NetworkAcls']:
        associations = results['NetworkAcls'][0]['Associations']
        return [s['SubnetId'] for s in associations if s['SubnetId']]
    else:
        return []


def replace_network_acl_association(nacl_id, subnets, client, module):
    params = dict()
    params['NetworkAclId'] = nacl_id
    for association in describe_acl_associations(subnets, client, module):
        params['AssociationId'] = association
        try:
            if not module.check_mode:
                client.replace_network_acl_association(**params)
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=str(e))


def replace_network_acl_entry(entries, Egress, nacl_id, client, module):
    for entry in entries:
        params = entry
        params['NetworkAclId'] = nacl_id
        try:
            if not module.check_mode:
                client.replace_network_acl_entry(**params)
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=str(e))


def restore_default_acl_association(params, client, module):
    try:
        if not module.check_mode:
            client.replace_network_acl_association(**params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))


def subnets_to_associate(nacl, client, module):
    params = list(module.params.get('subnets'))
    if not params:
        return []
    all_found = []
    if any(x.startswith("subnet-") for x in params):
        try:
            subnets = client.describe_subnets(Filters=[
                {'Name': 'subnet-id', 'Values': params}])
            all_found.extend(subnets.get('Subnets', []))
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=str(e), exception=traceback.format_exc())
    if len(params) != len(all_found):
        try:
            subnets = client.describe_subnets(Filters=[
                {'Name': 'tag:Name', 'Values': params}])
            all_found.extend(subnets.get('Subnets', []))
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=str(e), exception=traceback.format_exc())
    return list(set(s['SubnetId'] for s in all_found if s.get('SubnetId')))


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        vpc_id=dict(),
        name=dict(),
        nacl_id=dict(),
        subnets=dict(required=False, type='list', default=list()),
        tags=dict(required=False, type='dict'),
        ingress=dict(required=False, type='list', default=list()),
        egress=dict(required=False, type='list', default=list()),
        state=dict(default='present', choices=['present', 'absent']),
    ),
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_one_of=[['name', 'nacl_id']],
                           required_if=[['state', 'present', ['vpc_id']]])

    if not HAS_BOTO3:
        module.fail_json(msg='json, botocore and boto3 are required.')
    state = module.params.get('state').lower()
    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        client = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg="Can't authorize connection - %s" % str(e))

    invocations = {
        "present": setup_network_acl,
        "absent": remove_network_acl
    }
    (changed, results) = invocations[state](client, module)
    module.exit_json(changed=changed, nacl_id=results)


if __name__ == '__main__':
    main()
