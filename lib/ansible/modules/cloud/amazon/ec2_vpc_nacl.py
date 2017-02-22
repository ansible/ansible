#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'status': ['stableinterface'],
                    'supported_by': 'committer',
                    'version': '1.0'}

DOCUMENTATION = '''
module: ec2_vpc_nacl
short_description: create and delete Network ACLs.
description:
  - Read the AWS documentation for Network ACLS
    U(http://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_ACLs.html)
version_added: "2.2"
options:
  name:
    description:
      - Tagged name identifying a network ACL. At least one of C(name) or C(nacl_id)
        must be set when updating or removing a Network ACL
    required: false
  nacl_id:
    description:
      - Network ACL resource identifier. At least one of C(name) or C(nacl_id)
        must be set when updating or removing a Network ACL
    required: false
    version_added: "2.3"
  vpc_id:
    description:
      - VPC id of the requesting VPC.
    required: true
  subnets:
    description:
      - The list of subnets that should be associated with the network ACL.
      - Must be specified as a list
      - Each subnet can be specified as subnet ID, or its tagged name.
    required: false
  egress:
    description:
      - A list of rules for outgoing traffic.
      - Each rule must be specified as a list.
    required: false
  ingress:
    description:
      - List of rules for incoming traffic.
      - Each rule must be specified as a list.
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
author: Mike Mochan(@mmochan)
extends_documentation_fragment: aws
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
    ingress: [
        # rule no, protocol, allow/deny, cidr, icmp_code, icmp_type,
        #                                             port from, port to
        [100, 'tcp', 'allow', '0.0.0.0/0', null, null, 22, 22],
        [200, 'tcp', 'allow', '0.0.0.0/0', null, null, 80, 80],
        [300, 'icmp', 'allow', '0.0.0.0/0', 0, 8],
    ]
    egress: [
        [100, 'all', 'allow', '0.0.0.0/0', null, null, null, null]
    ]
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
'''
RETURN = '''
task:
  description: The result of the create, or delete action.
  returned: success
  type: dictionary
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, get_aws_connection_info
from ansible.module_utils.ec2 import boto3_tag_list_to_ansible_dict, HAS_BOTO3, update_aws_tags

try:
    import botocore
except ImportError:
    pass  # caught by imported HAS_BOTO3


# Common fields for the default rule that is contained within every VPC NACL.
DEFAULT_RULE_FIELDS = {
    'RuleNumber': 32767,
    'RuleAction': 'deny',
    'CidrBlock':  '0.0.0.0/0',
    'Protocol': '-1'
}

DEFAULT_INGRESS = dict(DEFAULT_RULE_FIELDS.items() + [('Egress', False)])
DEFAULT_EGRESS = dict(DEFAULT_RULE_FIELDS.items() + [('Egress', True)])

# VPC-supported IANA protocol numbers
# http://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml
PROTOCOL_NUMBERS = {'all': -1, 'icmp': 1, 'tcp': 6, 'udp': 17, }


# Utility methods
def icmp_present(entry):
    if len(entry) == 6 and entry[1] == 'icmp' or entry[1] == 1:
        return True


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


def subnets_changed(nacl_id, client, module):
    changed = False
    vpc_id = module.params.get('vpc_id')
    subnets = subnets_to_associate(client, module)
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


def nacls_changed(nacl_id, client, module):
    changed = False
    params = dict()
    params['egress'] = module.params.get('egress')
    params['ingress'] = module.params.get('ingress')

    nacl = describe_network_acl(client, module)
    entries = nacl['NetworkAcls'][0]['Entries']
    tmp_egress = [entry for entry in entries if entry['Egress'] is True and DEFAULT_EGRESS !=entry]
    tmp_ingress = [entry for entry in entries if entry['Egress'] is False]
    egress = [rule for rule in tmp_egress if DEFAULT_EGRESS != rule]
    ingress = [rule for rule in tmp_ingress if DEFAULT_INGRESS != rule]
    if rules_changed(egress, params['egress'], True, nacl_id, client, module):
        changed = True
    if rules_changed(ingress, params['ingress'], False, nacl_id, client, module):
        changed = True
    return changed


def tags_changed(nacl, client, module):
    changed = False
    tags = dict()
    if module.params.get('tags'):
        tags = module.params.get('tags')
    if module.params.get('name'):
        tags['Name'] = module.params.get('name')
    if nacl:
        nacl_tags = boto3_tag_list_to_ansible_dict(nacl['Tags'])
        nacl_id = nacl['NetworkAclId']
        changed = update_aws_tags(client, nacl_id, nacl_tags, tags)
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


def construct_acl_entries(nacl_id, client, module):
    for entry in module.params.get('ingress'):
        params = process_rule_entry(entry, Egress=False)
        params['NetworkAclId'] = nacl_id
        create_network_acl_entry(params, client, module)
    for rule in module.params.get('egress'):
        params = process_rule_entry(rule, Egress=True)
        params['NetworkAclId'] = nacl_id
        create_network_acl_entry(params, client, module)


# Module invocations
def setup_network_acl(client, module):
    changed = False
    nacls = describe_network_acl(client, module)
    if not nacls['NetworkAcls']:
        nacl = create_network_acl(module.params.get('vpc_id'), client, module)['NetworkAcl']
        nacl_id = nacl['NetworkAclId']
        tags_changed(nacl, client, module)
        subnets = subnets_to_associate(client, module)
        replace_network_acl_association(nacl_id, subnets, client, module)
        construct_acl_entries(nacl_id, client, module)
        changed = True
        return(changed, nacl_id)
    else:
        changed = False
        nacl = nacls['NetworkAcls'][0]
        nacl_id = nacl['NetworkAclId']
        subnet_result = subnets_changed(nacl_id, client, module)
        nacl_result = nacls_changed(nacl_id, client, module)
        tag_result = tags_changed(nacl, client, module)
        if subnet_result is True or nacl_result is True or tag_result is True:
            changed = True
            return(changed, nacl_id)
        return (changed, nacl_id)


def remove_network_acl(client, module):
    changed = False
    result = dict()
    vpc_id = module.params.get('vpc_id')
    nacl = describe_network_acl(client, module)
    if nacl['NetworkAcls']:
        nacl_id = nacl['NetworkAcls'][0]['NetworkAclId']
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
        nacl = client.create_network_acl(VpcId=vpc_id)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))
    return nacl


def create_network_acl_entry(params, client, module):
    try:
        result = client.create_network_acl_entry(**params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))
    return result


def delete_network_acl(nacl_id, client, module):
    try:
        client.delete_network_acl(NetworkAclId=nacl_id)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))


def delete_network_acl_entry(params, client, module):
    try:
        client.delete_network_acl_entry(**params)
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
        filters = []
        if module.params.get('name'):
            filters.append({'Name': 'tag:Name', 'Values': [module.params.get('name')]})
        elif module.params.get('nacl_id'):
            filters.append({'Name': 'network-acl-id', 'Values': [module.params.get('nacl_id')]})
        if not filters:
            module.fail_json(msg="At least one of name or nacl_id must be set")
        nacl = client.describe_network_acls(Filters=filters)
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
    return [n['NetworkAclId'] for n in nacls if n['IsDefault']]


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
            client.replace_network_acl_association(**params)
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=str(e))


def replace_network_acl_entry(entries, Egress, nacl_id, client, module):
    params = dict()
    for entry in entries:
        params = entry
        params['NetworkAclId'] = nacl_id
        try:
            client.replace_network_acl_entry(**params)
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=str(e))


def restore_default_acl_association(params, client, module):
    try:
        client.replace_network_acl_association(**params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))


def subnets_to_associate(client, module):
    params = list(module.params.get('subnets'))
    if not params:
        return []
    if params[0].startswith("subnet-"):
        try:
            subnets = client.describe_subnets(Filters=[
                {'Name': 'subnet-id', 'Values': params}])
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=str(e))
    else:
        try:
            subnets = client.describe_subnets(Filters=[
                {'Name': 'tag:Name', 'Values': params}])
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=str(e))
    return [s['SubnetId'] for s in subnets['Subnets'] if s['SubnetId']]


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            vpc_id=dict(required=True),
            name=dict(),
            nacl_id=dict(),
            subnets=dict(type='list', default=list()),
            tags=dict(type='dict'),
            ingress=dict(type='list', default=list()),
            egress=dict(type='list', default=list(),),
            state=dict(default='present', choices=['present', 'absent']),
        ),
    )
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='botocore and boto3 are required.')
    state = module.params.get('state')
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
