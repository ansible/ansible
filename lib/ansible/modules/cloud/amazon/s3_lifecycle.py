#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
---
module: s3_lifecycle
short_description: Manage s3 bucket lifecycle rules in AWS
description:
    - Manage s3 bucket lifecycle rules in AWS
version_added: "2.0"
author: "Rob White (@wimnat)"
notes:
  - If specifying expiration time as days then transition time must also be specified in days
  - If specifying expiration time as a date then transition time must also be specified as a date
requirements:
  - python-dateutil
options:
  name:
    description:
      - "Name of the s3 bucket"
    required: true
  expiration_date:
    description:
      - >
        Indicates the lifetime of the objects that are subject to the rule by the date they will expire. The value must be ISO-8601 format, the time must
        be midnight and a GMT timezone must be specified.
  expiration_days:
    description:
      - "Indicates the lifetime, in days, of the objects that are subject to the rule. The value must be a non-zero positive integer."
  prefix:
    description:
      - "Prefix identifying one or more objects to which the rule applies.  If no prefix is specified, the rule will apply to the whole bucket."
  purge_transitions:
    description:
      - >
        "Whether to replace all the current transition(s) with the new transition(s). When false, the provided transition(s)
        will be added, replacing transitions with the same storage_class. When true, existing transitions will be removed and
        replaced with the new transition(s)
    default: true
    type: bool
    version_added: 2.6
  noncurrent_version_expiration_days:
    description:
      - 'Delete noncurrent versions this many days after they become noncurrent'
    required: false
    version_added: 2.6
  noncurrent_version_storage_class:
    description:
      - 'Transition noncurrent versions to this storage class'
    default: glacier
    choices: ['glacier', 'onezone_ia', 'standard_ia']
    required: false
    version_added: 2.6
  noncurrent_version_transition_days:
    description:
      - 'Transition noncurrent versions this many days after they become noncurrent'
    required: false
    version_added: 2.6
  noncurrent_version_transitions:
    description:
      - >
        A list of transition behaviors to be applied to noncurrent versions for the rule. Each storage class may be used only once. Each transition
        behavior contains these elements
          I(transition_days)
          I(storage_class)
    version_added: 2.6
  rule_id:
    description:
      - "Unique identifier for the rule. The value cannot be longer than 255 characters. A unique value for the rule will be generated if no value is provided."
  state:
    description:
      - "Create or remove the lifecycle rule"
    default: present
    choices: [ 'present', 'absent' ]
  status:
    description:
      - "If 'enabled', the rule is currently being applied. If 'disabled', the rule is not currently being applied."
    default: enabled
    choices: [ 'enabled', 'disabled' ]
  storage_class:
    description:
      - "The storage class to transition to. Currently there are two supported values - 'glacier',  'onezone_ia', or 'standard_ia'."
      - "The 'standard_ia' class is only being available from Ansible version 2.2."
    default: glacier
    choices: [ 'glacier', 'onezone_ia', 'standard_ia']
  transition_date:
    description:
      - >
        Indicates the lifetime of the objects that are subject to the rule by the date they will transition to a different storage class.
        The value must be ISO-8601 format, the time must be midnight and a GMT timezone must be specified. If transition_days is not specified,
        this parameter is required."
  transition_days:
    description:
      - "Indicates when, in days, an object transitions to a different storage class. If transition_date is not specified, this parameter is required."
  transitions:
    description:
      - A list of transition behaviors to be applied to the rule. Each storage class may be used only once. Each transition
        behavior may contain these elements
          I(transition_days)
          I(transition_date)
          I(storage_class)
    version_added: 2.6
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Configure a lifecycle rule on a bucket to expire (delete) items with a prefix of /logs/ after 30 days
- s3_lifecycle:
    name: mybucket
    expiration_days: 30
    prefix: /logs/
    status: enabled
    state: present

# Configure a lifecycle rule to transition all items with a prefix of /logs/ to glacier after 7 days and then delete after 90 days
- s3_lifecycle:
    name: mybucket
    transition_days: 7
    expiration_days: 90
    prefix: /logs/
    status: enabled
    state: present

# Configure a lifecycle rule to transition all items with a prefix of /logs/ to glacier on 31 Dec 2020 and then delete on 31 Dec 2030.
# Note that midnight GMT must be specified.
# Be sure to quote your date strings
- s3_lifecycle:
    name: mybucket
    transition_date: "2020-12-30T00:00:00.000Z"
    expiration_date: "2030-12-30T00:00:00.000Z"
    prefix: /logs/
    status: enabled
    state: present

# Disable the rule created above
- s3_lifecycle:
    name: mybucket
    prefix: /logs/
    status: disabled
    state: present

# Delete the lifecycle rule created above
- s3_lifecycle:
    name: mybucket
    prefix: /logs/
    state: absent

# Configure a lifecycle rule to transition all backup files older than 31 days in /backups/ to standard infrequent access class.
- s3_lifecycle:
    name: mybucket
    prefix: /backups/
    storage_class: standard_ia
    transition_days: 31
    state: present
    status: enabled

# Configure a lifecycle rule to transition files to infrequent access after 30 days and glacier after 90
- s3_lifecycle:
    name: mybucket
    prefix: /logs/
    state: present
    status: enabled
    transitions:
      - transition_days: 30
        storage_class: standard_ia
      - transition_days: 90
        storage_class: glacier
'''

from copy import deepcopy
import datetime

try:
    import dateutil.parser
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAwsModule

from ansible.module_utils.aws.core import AnsibleAWSModule


def create_lifecycle_rule(client, module):

    name = module.params.get("name")
    expiration_date = module.params.get("expiration_date")
    expiration_days = module.params.get("expiration_days")
    noncurrent_version_expiration_days = module.params.get("noncurrent_version_expiration_days")
    noncurrent_version_transition_days = module.params.get("noncurrent_version_transition_days")
    noncurrent_version_transitions = module.params.get("noncurrent_version_transitions")
    noncurrent_version_storage_class = module.params.get("noncurrent_version_storage_class")
    prefix = module.params.get("prefix")
    rule_id = module.params.get("rule_id")
    status = module.params.get("status")
    storage_class = module.params.get("storage_class")
    transition_date = module.params.get("transition_date")
    transition_days = module.params.get("transition_days")
    transitions = module.params.get("transitions")
    purge_transitions = module.params.get("purge_transitions")
    changed = False

    # Get the bucket's current lifecycle rules
    try:
        current_lifecycle = client.get_bucket_lifecycle_configuration(Bucket=name)
        current_lifecycle_rules = current_lifecycle['Rules']
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':
            current_lifecycle_rules = []
        else:
            module.fail_json_aws(e)
    except BotoCoreError as e:
        module.fail_json_aws(e)

    rule = dict(Filter=dict(Prefix=prefix), Status=status.title())
    if rule_id is not None:
        rule['ID'] = rule_id
    # Create expiration
    if expiration_days is not None:
        rule['Expiration'] = dict(Days=expiration_days)
    elif expiration_date is not None:
        rule['Expiration'] = dict(Date=expiration_date)

    if noncurrent_version_expiration_days is not None:
        rule['NoncurrentVersionExpiration'] = dict(NoncurrentDays=noncurrent_version_expiration_days)

    if transition_days is not None:
        rule['Transitions'] = [dict(Days=transition_days, StorageClass=storage_class.upper()), ]

    elif transition_date is not None:
        rule['Transitions'] = [dict(Date=transition_date, StorageClass=storage_class.upper()), ]

    if transitions is not None:
        if not rule.get('Transitions'):
            rule['Transitions'] = []
        for transition in transitions:
            t_out = dict()
            if transition.get('transition_date'):
                t_out['Date'] = transition['transition_date']
            elif transition.get('transition_days'):
                t_out['Days'] = transition['transition_days']
            if transition.get('storage_class'):
                t_out['StorageClass'] = transition['storage_class'].upper()
                rule['Transitions'].append(t_out)

    if noncurrent_version_transition_days is not None:
        rule['NoncurrentVersionTransitions'] = [dict(NoncurrentDays=noncurrent_version_transition_days,
                                                     StorageClass=noncurrent_version_storage_class.upper()), ]

    if noncurrent_version_transitions is not None:
        if not rule.get('NoncurrentVersionTransitions'):
            rule['NoncurrentVersionTransitions'] = []
        for noncurrent_version_transition in noncurrent_version_transitions:
            t_out = dict()
            t_out['NoncurrentDays'] = noncurrent_version_transition['transition_days']
            if noncurrent_version_transition.get('storage_class'):
                t_out['StorageClass'] = noncurrent_version_transition['storage_class'].upper()
                rule['NoncurrentVersionTransitions'].append(t_out)

    lifecycle_configuration = dict(Rules=[])
    appended = False
    # If current_lifecycle_obj is not None then we have rules to compare, otherwise just add the rule
    if current_lifecycle_rules:
        # If rule ID exists, use that for comparison otherwise compare based on prefix
        for existing_rule in current_lifecycle_rules:
            if rule['Filter']['Prefix'] == existing_rule['Filter']['Prefix']:
                existing_rule.pop('ID')
            if rule.get('ID') == existing_rule.get('ID'):
                changed_, appended_ = update_or_append_rule(rule, existing_rule, purge_transitions, lifecycle_configuration)
                changed = changed_ or changed
                appended = appended_ or appended
            else:
                lifecycle_configuration['Rules'].append(existing_rule)

        # If nothing appended then append now as the rule must not exist
        if not appended:
            lifecycle_configuration['Rules'].append(rule)
            changed = True
    else:
        lifecycle_configuration['Rules'].append(rule)
        changed = True

    # Write lifecycle to bucket
    try:
        client.put_bucket_lifecycle_configuration(Bucket=name, LifecycleConfiguration=lifecycle_configuration)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)

    module.exit_json(changed=changed)


def update_or_append_rule(new_rule, existing_rule, purge_transitions, lifecycle_obj):
    changed = False
    if existing_rule['Status'] != new_rule['Status']:
        if not new_rule.get('Transitions') and existing_rule.get('Transitions'):
            new_rule['Transitions'] = existing_rule['Transitions']
        if not new_rule.get('Expiration') and existing_rule.get('Expiration'):
            new_rule['Expiration'] = existing_rule['Expiration']
        if not new_rule.get('NoncurrentVersionExpiration') and existing_rule.get('NoncurrentVersionExpiration'):
            new_rule['NoncurrentVersionExpiration'] = existing_rule['NoncurrentVersionExpiration']
        lifecycle_obj['Rules'].append(new_rule)
        changed = True
        appended = True
    else:
        if not purge_transitions:
            merge_transitions(new_rule, existing_rule)
        if compare_rule(new_rule, existing_rule, purge_transitions):
            lifecycle_obj['Rules'].append(new_rule)
            appended = True
        else:
            lifecycle_obj['Rules'].append(new_rule)
            changed = True
            appended = True
    return changed, appended


def compare_rule(rule_a, rule_b, purge_transitions):

    # Copy objects
    rule1 = deepcopy(rule_a)
    rule2 = deepcopy(rule_b)

    if purge_transitions:
        return rule1 == rule2
    else:
        transitions1 = rule1.pop('Transitions', [])
        transitions2 = rule2.pop('Transitions', [])
        noncurrent_transtions1 = rule1.pop('NoncurrentVersionTransitions', [])
        noncurrent_transtions2 = rule2.pop('NoncurrentVersionTransitions', [])
        if rule1 != rule2:
            return False
        for transition in transitions1:
            if transition not in transitions2:
                return False
        for transition in noncurrent_transtions1:
            if transition not in noncurrent_transtions2:
                return False
        return True


def merge_transitions(updated_rule, updating_rule):
    # because of the legal s3 transitions, we know only one can exist for each storage class.
    # So, our strategy is build some dicts, keyed on storage class and add the storage class transitions that are only
    # in updating_rule to updated_rule
    updated_transitions = {}
    updating_transitions = {}
    for transition in updated_rule['Transitions']:
        updated_transitions[transition['StorageClass']] = transition
    for transition in updating_rule['Transitions']:
        updating_transitions[transition['StorageClass']] = transition
    for storage_class, transition in updating_transitions.items():
        if updated_transitions.get(storage_class) is None:
            updated_rule['Transitions'].append(transition)


def destroy_lifecycle_rule(client, module):

    name = module.params.get("name")
    prefix = module.params.get("prefix")
    rule_id = module.params.get("rule_id")
    changed = False

    if prefix is None:
        prefix = ""

    # Get the bucket's current lifecycle rules
    try:
        current_lifecycle_rules = client.get_bucket_lifecycle_configuration(Bucket=name)['Rules']
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':
            current_lifecycle_rules = []
        else:
            module.fail_json_aws(e)
    except BotoCoreError as e:
        module.fail_json_aws(e)

    # Create lifecycle
    lifecycle_obj = dict(Rules=[])

    # Check if rule exists
    # If an ID exists, use that otherwise compare based on prefix
    if rule_id is not None:
        for existing_rule in current_lifecycle_rules:
            if rule_id == existing_rule['ID']:
                # We're not keeping the rule (i.e. deleting) so mark as changed
                changed = True
            else:
                lifecycle_obj['Rules'].append(existing_rule)
    else:
        for existing_rule in current_lifecycle_rules:
            if prefix == existing_rule['Filter']['Prefix']:
                # We're not keeping the rule (i.e. deleting) so mark as changed
                changed = True
            else:
                lifecycle_obj['Rules'].append(existing_rule)

    # Write lifecycle to bucket or, if there no rules left, delete lifecycle configuration
    try:
        if lifecycle_obj['Rules']:
            client.put_bucket_lifecycle_configuration(Bucket=name, LifecycleConfiguration=lifecycle_obj)
        elif current_lifecycle_rules:
            changed = True
            client.delete_bucket_lifecycle(Bucket=name)
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e)
    module.exit_json(changed=changed)


def main():
    argument_spec = dict(
        name=dict(required=True, type='str'),
        expiration_days=dict(type='int'),
        expiration_date=dict(),
        noncurrent_version_expiration_days=dict(type='int'),
        noncurrent_version_storage_class=dict(default='glacier', type='str', choices=['glacier', 'onezone_ia', 'standard_ia']),
        noncurrent_version_transition_days=dict(type='int'),
        noncurrent_version_transitions=dict(type='list'),
        prefix=dict(),
        requester_pays=dict(default='no', type='bool'),
        rule_id=dict(),
        state=dict(default='present', choices=['present', 'absent']),
        status=dict(default='enabled', choices=['enabled', 'disabled']),
        storage_class=dict(default='glacier', type='str', choices=['glacier', 'onezone_ia', 'standard_ia']),
        transition_days=dict(type='int'),
        transition_date=dict(),
        transitions=dict(type='list'),
        purge_transitions=dict(default='yes', type='bool')
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              mutually_exclusive=[
                                  ['expiration_days', 'expiration_date'],
                                  ['expiration_days', 'transition_date'],
                                  ['transition_days', 'transition_date'],
                                  ['transition_days', 'expiration_date'],
                                  ['transition_days', 'transitions'],
                                  ['transition_date', 'transitions'],
                                  ['noncurrent_version_transition_days', 'noncurrent_version_transitions'],
                              ],)

    if not HAS_DATEUTIL:
        module.fail_json(msg='dateutil required for this module')

    client = module.client('s3')

    expiration_date = module.params.get("expiration_date")
    transition_date = module.params.get("transition_date")
    state = module.params.get("state")

    if state == 'present' and module.params["status"] == "enabled":  # allow deleting/disabling a rule by id/prefix

        required_when_present = ('expiration_date', 'expiration_days', 'transition_date',
                                 'transition_days', 'transitions', 'noncurrent_version_expiration_days',
                                 'noncurrent_version_transition_days',
                                 'noncurrent_version_transitions')
        for param in required_when_present:
            if module.params.get(param):
                break
        else:
            msg = "one of the following is required when 'state' is 'present': %s" % ', '.join(required_when_present)
            module.fail_json(msg=msg)
    # If expiration_date set, check string is valid
    if expiration_date is not None:
        try:
            datetime.datetime.strptime(expiration_date, "%Y-%m-%dT%H:%M:%S.000Z")
        except ValueError as e:
            module.fail_json(msg="expiration_date is not a valid ISO-8601 format. The time must be midnight and a timezone of GMT must be included")

    if transition_date is not None:
        try:
            datetime.datetime.strptime(transition_date, "%Y-%m-%dT%H:%M:%S.000Z")
        except ValueError as e:
            module.fail_json(msg="expiration_date is not a valid ISO-8601 format. The time must be midnight and a timezone of GMT must be included")

    if state == 'present':
        create_lifecycle_rule(client, module)
    elif state == 'absent':
        destroy_lifecycle_rule(client, module)


if __name__ == '__main__':
    main()
