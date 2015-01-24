#!/usr/bin/python
# -*- coding: utf-8 -*-


DOCUMENTATION = '''
---
module: ec2_group
version_added: "1.3"
short_description: maintain an ec2 VPC security group.
description:
    - maintains ec2 security groups. This module has a dependency on python-boto >= 2.5
options:
  name:
    description:
      - Name of the security group.
    required: true
  description:
    description:
      - Description of the security group.
    required: true
  vpc_id:
    description:
      - ID of the VPC to create the group in.
    required: false
  rules:
    description:
      - List of firewall inbound rules to enforce in this group (see example).
    required: false
  rules_egress:
    description:
      - List of firewall outbound rules to enforce in this group (see example).
    required: false
    version_added: "1.6"
  region:
    description:
      - the EC2 region to use
    required: false
    default: null
    aliases: []
  state:
    version_added: "1.4"
    description:
      - Create or delete a security group
    required: false
    default: 'present'
    choices: [ "present", "absent" ]
    aliases: []
  purge_rules:
    version_added: "1.8"
    description:
      - Purge existing rules on security group that are not found in rules
    required: false
    default: 'true'
    aliases: []
  purge_rules_egress:
    version_added: "1.8"
    description:
      - Purge existing rules_egress on security group that are not found in rules_egress
    required: false
    default: 'true'
    aliases: []

extends_documentation_fragment: aws

notes:
  - If a rule declares a group_name and that group doesn't exist, it will be
    automatically created. In that case, group_desc should be provided as well.
    The module will refuse to create a depended-on group without a description.
'''

EXAMPLES = '''
- name: example ec2 group
  ec2_group:
    name: example
    description: an example EC2 group
    vpc_id: 12345
    region: eu-west-1a
    aws_secret_key: SECRET
    aws_access_key: ACCESS
    rules:
      - proto: tcp
        from_port: 80
        to_port: 80
        cidr_ip: 0.0.0.0/0
      - proto: tcp
        from_port: 22
        to_port: 22
        cidr_ip: 10.0.0.0/8
      - proto: udp
        from_port: 10050
        to_port: 10050
        cidr_ip: 10.0.0.0/8
      - proto: udp
        from_port: 10051
        to_port: 10051
        group_id: sg-12345678
      - proto: all
        # the containing group name may be specified here
        group_name: example
    rules_egress:
      - proto: tcp
        from_port: 80
        to_port: 80
        cidr_ip: 0.0.0.0/0
        group_name: example-other
        # description to use if example-other needs to be created
        group_desc: other example EC2 group
'''

try:
    import boto.ec2
except ImportError:
    print "failed=True msg='boto required for this module'"
    sys.exit(1)


def make_rule_key(prefix, rule, group_id, cidr_ip):
    """Creates a unique key for an individual group rule"""
    if isinstance(rule, dict):
        proto, from_port, to_port = [rule.get(x, None) for x in ('proto', 'from_port', 'to_port')]
    else:  # isinstance boto.ec2.securitygroup.IPPermissions
        proto, from_port, to_port = [getattr(rule, x, None) for x in ('ip_protocol', 'from_port', 'to_port')]

    key = "%s-%s-%s-%s-%s-%s" % (prefix, proto, from_port, to_port, group_id, cidr_ip)
    return key.lower().replace('-none', '-None')


def addRulesToLookup(rules, prefix, dict):
    for rule in rules:
        for grant in rule.grants:
            dict[make_rule_key(prefix, rule, grant.group_id, grant.cidr_ip)] = (rule, grant)


def get_target_from_rule(module, ec2, rule, name, group, groups, vpc_id):
    """
    Returns tuple of (group_id, ip) after validating rule params.

    rule: Dict describing a rule.
    name: Name of the security group being managed.
    groups: Dict of all available security groups.

    AWS accepts an ip range or a security group as target of a rule. This
    function validate the rule specification and return either a non-None
    group_id or a non-None ip range.
    """

    group_id = None
    group_name = None
    ip = None
    target_group_created = False
    if 'group_id' in rule and 'cidr_ip' in rule:
        module.fail_json(msg="Specify group_id OR cidr_ip, not both")
    elif 'group_name' in rule and 'cidr_ip' in rule:
        module.fail_json(msg="Specify group_name OR cidr_ip, not both")
    elif 'group_id' in rule and 'group_name' in rule:
        module.fail_json(msg="Specify group_id OR group_name, not both")
    elif 'group_id' in rule:
        group_id = rule['group_id']
    elif 'group_name' in rule:
        group_name = rule['group_name']
        if group_name in groups:
            group_id = groups[group_name].id
        elif group_name == name:
            group_id = group.id
            groups[group_id] = group
            groups[group_name] = group
        else:
            if not rule.get('group_desc', '').strip():
                module.fail_json(msg="group %s will be automatically created by rule %s and no description was provided" % (group_name, rule))
            if not module.check_mode:
                auto_group = ec2.create_security_group(group_name, rule['group_desc'], vpc_id=vpc_id)
                group_id = auto_group.id
                groups[group_id] = auto_group
                groups[group_name] = auto_group
            target_group_created = True
    elif 'cidr_ip' in rule:
        ip = rule['cidr_ip']

    return group_id, ip, target_group_created


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            name=dict(required=True),
            description=dict(required=True),
            vpc_id=dict(),
            rules=dict(),
            rules_egress=dict(),
            state = dict(default='present', choices=['present', 'absent']),
            purge_rules=dict(default=True, required=False, type='bool'),
            purge_rules_egress=dict(default=True, required=False, type='bool'),

        )
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    name = module.params['name']
    description = module.params['description']
    vpc_id = module.params['vpc_id']
    rules = module.params['rules']
    rules_egress = module.params['rules_egress']
    state = module.params.get('state')
    purge_rules = module.params['purge_rules']
    purge_rules_egress = module.params['purge_rules_egress']

    changed = False

    ec2 = ec2_connect(module)

    # find the group if present
    group = None
    groups = {}
    for curGroup in ec2.get_all_security_groups():
        groups[curGroup.id] = curGroup
        groups[curGroup.name] = curGroup

        if curGroup.name == name and (vpc_id is None or curGroup.vpc_id == vpc_id):
            group = curGroup

    # Ensure requested group is absent
    if state == 'absent':
        if group:
            '''found a match, delete it'''
            try:
                group.delete()
            except Exception, e:
                module.fail_json(msg="Unable to delete security group '%s' - %s" % (group, e))
            else:
                group = None
                changed = True
        else:
            '''no match found, no changes required'''

    # Ensure requested group is present
    elif state == 'present':
        if group:
            '''existing group found'''
            # check the group parameters are correct
            group_in_use = False
            rs = ec2.get_all_instances()
            for r in rs:
                for i in r.instances:
                    group_in_use |= reduce(lambda x, y: x | (y.name == 'public-ssh'), i.groups, False)

            if group.description != description:
                if group_in_use:
                    module.fail_json(msg="Group description does not match, but it is in use so cannot be changed.")

        # if the group doesn't exist, create it now
        else:
            '''no match found, create it'''
            if not module.check_mode:
                group = ec2.create_security_group(name, description, vpc_id=vpc_id)

                # When a group is created, an egress_rule ALLOW ALL
                # to 0.0.0.0/0 is added automatically but it's not
                # reflected in the object returned by the AWS API
                # call. We re-read the group for getting an updated object
                # amazon sometimes takes a couple seconds to update the security group so wait till it exists
                while len(ec2.get_all_security_groups(filters={ 'group_id': group.id, })) == 0:
                    time.sleep(0.1)

                group = ec2.get_all_security_groups(group_ids=(group.id,))[0]
            changed = True
    else:
        module.fail_json(msg="Unsupported state requested: %s" % state)

    # create a lookup for all existing rules on the group
    if group:

        # Manage ingress rules
        groupRules = {}
        addRulesToLookup(group.rules, 'in', groupRules)

        # Now, go through all provided rules and ensure they are there.
        if rules:
            for rule in rules:
                group_id, ip, target_group_created = get_target_from_rule(module, ec2, rule, name, group, groups, vpc_id)
                if target_group_created:
                    changed = True

                if rule['proto'] in ('all', '-1', -1):
                    rule['proto'] = -1
                    rule['from_port'] = None
                    rule['to_port'] = None

                # If rule already exists, don't later delete it
                ruleId = make_rule_key('in', rule, group_id, ip)
                if ruleId in groupRules:
                    del groupRules[ruleId]
                # Otherwise, add new rule
                else:
                    grantGroup = None
                    if group_id:
                        grantGroup = groups[group_id]

                    if not module.check_mode:
                        group.authorize(rule['proto'], rule['from_port'], rule['to_port'], ip, grantGroup)
                    changed = True

        # Finally, remove anything left in the groupRules -- these will be defunct rules
        if purge_rules:
            for (rule, grant) in groupRules.itervalues() :
                grantGroup = None
                if grant.group_id:
                    grantGroup = groups[grant.group_id]
                if not module.check_mode:
                    group.revoke(rule.ip_protocol, rule.from_port, rule.to_port, grant.cidr_ip, grantGroup)
                changed = True

        # Manage egress rules
        groupRules = {}
        addRulesToLookup(group.rules_egress, 'out', groupRules)

        # Now, go through all provided rules and ensure they are there.
        if rules_egress:
            for rule in rules_egress:
                group_id, ip, target_group_created = get_target_from_rule(module, ec2, rule, name, group, groups, vpc_id)
                if target_group_created:
                    changed = True

                if rule['proto'] in ('all', '-1', -1):
                    rule['proto'] = -1
                    rule['from_port'] = None
                    rule['to_port'] = None

                # If rule already exists, don't later delete it
                ruleId = make_rule_key('out', rule, group_id, ip)
                if ruleId in groupRules:
                    del groupRules[ruleId]
                # Otherwise, add new rule
                else:
                    grantGroup = None
                    if group_id:
                        grantGroup = groups[group_id].id

                    if not module.check_mode:
                        ec2.authorize_security_group_egress(
                                group_id=group.id,
                                ip_protocol=rule['proto'],
                                from_port=rule['from_port'],
                                to_port=rule['to_port'],
                                src_group_id=grantGroup,
                                cidr_ip=ip)
                    changed = True
        elif vpc_id and not module.check_mode:
            # when using a vpc, but no egress rules are specified,
            # we add in a default allow all out rule, which was the
            # default behavior before egress rules were added
            default_egress_rule = 'out--1-None-None-None-0.0.0.0/0'
            if default_egress_rule not in groupRules:
                ec2.authorize_security_group_egress(
                    group_id=group.id,
                    ip_protocol=-1,
                    from_port=None,
                    to_port=None,
                    src_group_id=None,
                    cidr_ip='0.0.0.0/0'
                )
                changed = True
            else:
                # make sure the default egress rule is not removed
                del groupRules[default_egress_rule]

        # Finally, remove anything left in the groupRules -- these will be defunct rules
        if purge_rules_egress:
            for (rule, grant) in groupRules.itervalues():
                grantGroup = None
                if grant.group_id:
                    grantGroup = groups[grant.group_id].id
                if not module.check_mode:
                    ec2.revoke_security_group_egress(
                            group_id=group.id,
                            ip_protocol=rule.ip_protocol,
                            from_port=rule.from_port,
                            to_port=rule.to_port,
                            src_group_id=grantGroup,
                            cidr_ip=grant.cidr_ip)
                changed = True

    if group:
        module.exit_json(changed=changed, group_id=group.id)
    else:
        module.exit_json(changed=changed, group_id=None)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
