#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

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
      - "Indicates the lifetime of the objects that are subject to the rule by the date they will expire. The value must be ISO-8601 format, the time must be midnight and a GMT timezone must be specified."
    required: false
    default: null
  expiration_days:
    description:
      - "Indicates the lifetime, in days, of the objects that are subject to the rule. The value must be a non-zero positive integer."
    required: false
    default: null
  prefix:
    description:
      - "Prefix identifying one or more objects to which the rule applies.  If no prefix is specified, the rule will apply to the whole bucket."
    required: false
    default: null
  region:
    description:
     - "AWS region to create the bucket in. If not set then the value of the AWS_REGION and EC2_REGION environment variables are checked, followed by the aws_region and ec2_region settings in the Boto config file.  If none of those are set the region defaults to the S3 Location: US Standard."
    required: false
    default: null
  rule_id:
    description:
      - "Unique identifier for the rule. The value cannot be longer than 255 characters. A unique value for the rule will be generated if no value is provided."
    required: false
    default: null
  state:
    description:
      - "Create or remove the lifecycle rule"
    required: false
    default: present
    choices: [ 'present', 'absent' ]
  status:
    description:
      - "If 'enabled', the rule is currently being applied. If 'disabled', the rule is not currently being applied."
    required: false
    default: enabled
    choices: [ 'enabled', 'disabled' ]
  storage_class:
    description:
      - "The storage class to transition to. Currently there is only one valid value - 'glacier'."
    required: false
    default: glacier
    choices: [ 'glacier' ]
  transition_date:
    description:
      - "Indicates the lifetime of the objects that are subject to the rule by the date they will transition to a different storage class. The value must be ISO-8601 format, the time must be midnight and a GMT timezone must be specified. If transition_days is not specified, this parameter is required."
    required: false
    default: null
  transition_days:
    description:
      - "Indicates when, in days, an object transitions to a different storage class. If transition_date is not specified, this parameter is required."
    required: false
    default: null

extends_documentation_fragment: aws
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
    
# Configure a lifecycle rule to transition all items with a prefix of /logs/ to glacier on 31 Dec 2020 and then delete on 31 Dec 2030. Note that midnight GMT must be specified.
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
    
'''

import xml.etree.ElementTree as ET
import copy
import datetime

try:
    import dateutil.parser
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False

try:
    import boto.ec2
    from boto.s3.connection import OrdinaryCallingFormat, Location
    from boto.s3.lifecycle import Lifecycle, Rule, Expiration, Transition
    from boto.exception import BotoServerError, S3CreateError, S3ResponseError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

def create_lifecycle_rule(connection, module):

    name = module.params.get("name")
    expiration_date = module.params.get("expiration_date")
    expiration_days = module.params.get("expiration_days")
    prefix = module.params.get("prefix")
    rule_id = module.params.get("rule_id")
    status = module.params.get("status")
    storage_class = module.params.get("storage_class")
    transition_date = module.params.get("transition_date")
    transition_days = module.params.get("transition_days")
    changed = False

    try:
        bucket = connection.get_bucket(name)
    except S3ResponseError, e:
        module.fail_json(msg=e.message)

    # Get the bucket's current lifecycle rules
    try:
        current_lifecycle_obj = bucket.get_lifecycle_config()
    except S3ResponseError, e:
        if e.error_code == "NoSuchLifecycleConfiguration":
            current_lifecycle_obj = Lifecycle()
        else:
            module.fail_json(msg=e.message)

    # Create expiration
    if expiration_days is not None:
        expiration_obj = Expiration(days=expiration_days)
    elif expiration_date is not None:
        expiration_obj = Expiration(date=expiration_date)
    else:
        expiration_obj = None
    
    # Create transition
    if transition_days is not None:
        transition_obj = Transition(days=transition_days, storage_class=storage_class.upper())
    elif transition_date is not None:
        transition_obj = Transition(date=transition_date, storage_class=storage_class.upper())
    else:
        transition_obj = None

    # Create rule
    rule = Rule(rule_id, prefix, status.title(), expiration_obj, transition_obj)

    # Create lifecycle
    lifecycle_obj = Lifecycle()

    appended = False
    # If current_lifecycle_obj is not None then we have rules to compare, otherwise just add the rule
    if current_lifecycle_obj:
        # If rule ID exists, use that for comparison otherwise compare based on prefix
        for existing_rule in current_lifecycle_obj:
            if rule.id == existing_rule.id:
                if compare_rule(rule, existing_rule):
                    lifecycle_obj.append(rule)
                    appended = True
                else:
                    lifecycle_obj.append(rule)
                    changed = True
                    appended = True
            elif rule.prefix == existing_rule.prefix:
                existing_rule.id = None
                if compare_rule(rule, existing_rule):
                    lifecycle_obj.append(rule)
                    appended = True
                else:
                    lifecycle_obj.append(rule)
                    changed = True
                    appended = True
        # If nothing appended then append now as the rule must not exist
        if not appended:
            lifecycle_obj.append(rule)
            changed = True
    else:
        lifecycle_obj.append(rule)
        changed = True

    # Write lifecycle to bucket
    try:
        bucket.configure_lifecycle(lifecycle_obj)
    except S3ResponseError, e:
        module.fail_json(msg=e.message)
        
    module.exit_json(changed=changed)

def compare_rule(rule_a, rule_b):

    # Copy objects
    rule1 = copy.deepcopy(rule_a)
    rule2 = copy.deepcopy(rule_b)

    # Delete Rule from Rule
    try:
        del rule1.Rule
    except AttributeError:
        pass

    try:
        del rule2.Rule
    except AttributeError:
        pass

    # Extract Expiration and Transition objects
    rule1_expiration = rule1.expiration
    rule1_transition = rule1.transition
    rule2_expiration = rule2.expiration
    rule2_transition = rule2.transition

    # Delete the Expiration and Transition objects from the Rule objects
    del rule1.expiration
    del rule1.transition
    del rule2.expiration
    del rule2.transition

    # Compare
    if rule1_transition is None:
        rule1_transition = Transition()
    if rule2_transition is None:
        rule2_transition = Transition()
    if rule1_expiration is None:
        rule1_expiration = Expiration()
    if rule2_expiration is None:
        rule2_expiration = Expiration()

    if (rule1.__dict__ == rule2.__dict__) and (rule1_expiration.__dict__ == rule2_expiration.__dict__) and (rule1_transition.__dict__ == rule2_transition.__dict__):
        return True
    else:
        return False


def destroy_lifecycle_rule(connection, module):

    name = module.params.get("name")
    prefix = module.params.get("prefix")
    rule_id = module.params.get("rule_id")
    changed = False

    if prefix is None:
        prefix = ""

    try:
        bucket = connection.get_bucket(name)
    except S3ResponseError, e:
        module.fail_json(msg=e.message)

    # Get the bucket's current lifecycle rules
    try:
        current_lifecycle_obj = bucket.get_lifecycle_config()
    except S3ResponseError, e:
        if e.error_code == "NoSuchLifecycleConfiguration":
            module.exit_json(changed=changed)
        else:
            module.fail_json(msg=e.message)

    # Create lifecycle
    lifecycle_obj = Lifecycle()
    
    # Check if rule exists
    # If an ID exists, use that otherwise compare based on prefix
    if rule_id is not None:
        for existing_rule in current_lifecycle_obj:
            if rule_id == existing_rule.id:
                # We're not keeping the rule (i.e. deleting) so mark as changed
                changed = True
            else:
                lifecycle_obj.append(existing_rule)
    else:
        for existing_rule in current_lifecycle_obj:
            if prefix == existing_rule.prefix:
                # We're not keeping the rule (i.e. deleting) so mark as changed
                changed = True
            else:
                lifecycle_obj.append(existing_rule)
                
    
    # Write lifecycle to bucket or, if there no rules left, delete lifecycle configuration
    try:
        if lifecycle_obj:
            bucket.configure_lifecycle(lifecycle_obj)
        else:
            bucket.delete_lifecycle_configuration()
    except BotoServerError, e:
        module.fail_json(msg=e.message)
        
    module.exit_json(changed=changed)
    

def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name = dict(required=True),
            expiration_days = dict(default=None, required=False, type='int'),
            expiration_date = dict(default=None, required=False, type='str'),
            prefix = dict(default=None, required=False),
            requester_pays = dict(default='no', type='bool'),
            rule_id = dict(required=False),
            state = dict(default='present', choices=['present', 'absent']),
            status = dict(default='enabled', choices=['enabled', 'disabled']),
            storage_class = dict(default='glacier', choices=['glacier']),
            transition_days = dict(default=None, required=False, type='int'),
            transition_date = dict(default=None, required=False, type='str')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive = [
                                                 [ 'expiration_days', 'expiration_date' ],
                                                 [ 'expiration_days', 'transition_date' ],
                                                 [ 'transition_days', 'transition_date' ],
                                                 [ 'transition_days', 'expiration_date' ]                 
                                                 ]
                           )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')
        
    if not HAS_DATEUTIL:
        module.fail_json(msg='dateutil required for this module')    

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)
    
    if region in ('us-east-1', '', None):
        # S3ism for the US Standard region
        location = Location.DEFAULT
    else:
        # Boto uses symbolic names for locations but region strings will
        # actually work fine for everything except us-east-1 (US Standard)
        location = region
    try:
        connection = boto.s3.connect_to_region(location, is_secure=True, calling_format=OrdinaryCallingFormat(), **aws_connect_params)
        # use this as fallback because connect_to_region seems to fail in boto + non 'classic' aws accounts in some cases
        if connection is None:
            connection = boto.connect_s3(**aws_connect_params)
    except (boto.exception.NoAuthHandlerFound, StandardError), e:
        module.fail_json(msg=str(e))

    expiration_date = module.params.get("expiration_date")
    transition_date = module.params.get("transition_date")
    state = module.params.get("state")

    # If expiration_date set, check string is valid
    if expiration_date is not None:
        try:
            datetime.datetime.strptime(expiration_date, "%Y-%m-%dT%H:%M:%S.000Z")
        except ValueError, e:
            module.fail_json(msg="expiration_date is not a valid ISO-8601 format. The time must be midnight and a timezone of GMT must be included")
    
    if transition_date is not None:
        try:
            datetime.datetime.strptime(transition_date, "%Y-%m-%dT%H:%M:%S.000Z")
        except ValueError, e:
            module.fail_json(msg="expiration_date is not a valid ISO-8601 format. The time must be midnight and a timezone of GMT must be included")
        
    if state == 'present':
        create_lifecycle_rule(connection, module)
    elif state == 'absent':
        destroy_lifecycle_rule(connection, module)

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
