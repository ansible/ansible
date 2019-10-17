#!/usr/bin/python
# Copyright (c) 2017 Will Thames
# Copyright (c) 2015 Mike Mochan
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: aws_waf_condition
short_description: create and delete WAF Conditions
description:
  - Read the AWS documentation for WAF
    U(https://aws.amazon.com/documentation/waf/)
version_added: "2.5"

author:
  - Will Thames (@willthames)
  - Mike Mochan (@mmochan)
extends_documentation_fragment:
  - aws
  - ec2
options:
    name:
        description: Name of the Web Application Firewall condition to manage.
        required: yes
    type:
        description: the type of matching to perform.
        choices:
        - byte
        - geo
        - ip
        - regex
        - size
        - sql
        - xss
    filters:
        description:
        - A list of the filters against which to match.
        - For I(type)=C(byte), valid keys are C(field_to_match), C(position), C(header), C(transformation).
        - For I(type)=C(geo), the only valid key is C(country).
        - For I(type)=C(ip), the only valid key is C(ip_address).
        - For I(type)=C(regex), valid keys are C(field_to_match), C(transformation) and C(regex_pattern).
        - For I(type)=C(size), valid keys are C(field_to_match), C(transformation), C(comparison) and C(size).
        - For I(type)=C(sql), valid keys are C(field_to_match) and C(transformation).
        - For I(type)=C(xss), valid keys are C(field_to_match) and C(transformation).
        - I(field_to_match) can be one of C(uri), C(query_string), C(header) C(method) and C(body).
        - If I(field_to_match) is C(header), then C(header) must also be specified.
        - I(transformation) can be one of C(none), C(compress_white_space), C(html_entity_decode), C(lowercase), C(cmd_line), C(url_decode).
        - I(position), can be one of C(exactly), C(starts_with), C(ends_with), C(contains), C(contains_word).
        - I(comparison) can be one of C(EQ), C(NE), C(LE), C(LT), C(GE), C(GT).
        - I(target_string) is a maximum of 50 bytes.
        - I(regex_pattern) is a dict with a C(name) key and C(regex_strings) list of strings to match.
    purge_filters:
        description:
        - Whether to remove existing filters from a condition if not passed in I(filters).
        default: False
        type: bool
    waf_regional:
        description: Whether to use waf_regional module. Defaults to false.
        default: false
        required: no
        type: bool
        version_added: 2.9
    state:
        description: Whether the condition should be C(present) or C(absent).
        choices:
        - present
        - absent
        default: present

'''

EXAMPLES = '''
  - name: create WAF byte condition
    aws_waf_condition:
      name: my_byte_condition
      filters:
      - field_to_match: header
        position: STARTS_WITH
        target_string: Hello
        header: Content-type
      type: byte

  - name: create WAF geo condition
    aws_waf_condition:
      name: my_geo_condition
      filters:
        - country: US
        - country: AU
        - country: AT
      type: geo

  - name: create IP address condition
    aws_waf_condition:
      name: "{{ resource_prefix }}_ip_condition"
      filters:
        - ip_address: "10.0.0.0/8"
        - ip_address: "192.168.0.0/24"
      type: ip

  - name: create WAF regex condition
    aws_waf_condition:
      name: my_regex_condition
      filters:
        - field_to_match: query_string
          regex_pattern:
            name: greetings
            regex_strings:
              - '[hH]ello'
              - '^Hi there'
              - '.*Good Day to You'
      type: regex

  - name: create WAF size condition
    aws_waf_condition:
      name: my_size_condition
      filters:
        - field_to_match: query_string
          size: 300
          comparison: GT
      type: size

  - name: create WAF sql injection condition
    aws_waf_condition:
      name: my_sql_condition
      filters:
        - field_to_match: query_string
          transformation: url_decode
      type: sql

  - name: create WAF xss condition
    aws_waf_condition:
      name: my_xss_condition
      filters:
        - field_to_match: query_string
          transformation: url_decode
      type: xss

'''

RETURN = '''
condition:
  description: condition returned by operation
  returned: always
  type: complex
  contains:
    condition_id:
      description: type-agnostic ID for the condition
      returned: when state is present
      type: str
      sample: dd74b1ff-8c06-4a4f-897a-6b23605de413
    byte_match_set_id:
      description: ID for byte match set
      returned: always
      type: str
      sample: c4882c96-837b-44a2-a762-4ea87dbf812b
    byte_match_tuples:
      description: list of byte match tuples
      returned: always
      type: complex
      contains:
        field_to_match:
          description: Field to match
          returned: always
          type: complex
          contains:
            data:
              description: Which specific header (if type is header)
              type: str
              sample: content-type
            type:
              description: Type of field
              type: str
              sample: HEADER
        positional_constraint:
          description: Position in the field to match
          type: str
          sample: STARTS_WITH
        target_string:
          description: String to look for
          type: str
          sample: Hello
        text_transformation:
          description: Transformation to apply to the field before matching
          type: str
          sample: NONE
    geo_match_constraints:
      description: List of geographical constraints
      returned: when type is geo and state is present
      type: complex
      contains:
        type:
          description: Type of geo constraint
          type: str
          sample: Country
        value:
          description: Value of geo constraint (typically a country code)
          type: str
          sample: AT
    geo_match_set_id:
      description: ID of the geo match set
      returned: when type is geo and state is present
      type: str
      sample: dd74b1ff-8c06-4a4f-897a-6b23605de413
    ip_set_descriptors:
      description: list of IP address filters
      returned: when type is ip and state is present
      type: complex
      contains:
        type:
          description: Type of IP address (IPV4 or IPV6)
          returned: always
          type: str
          sample: IPV4
        value:
          description: IP address
          returned: always
          type: str
          sample: 10.0.0.0/8
    ip_set_id:
      description: ID of condition
      returned: when type is ip and state is present
      type: str
      sample: 78ad334a-3535-4036-85e6-8e11e745217b
    name:
      description: Name of condition
      returned: when state is present
      type: str
      sample: my_waf_condition
    regex_match_set_id:
      description: ID of the regex match set
      returned: when type is regex and state is present
      type: str
      sample: 5ea3f6a8-3cd3-488b-b637-17b79ce7089c
    regex_match_tuples:
      description: List of regex matches
      returned: when type is regex and state is present
      type: complex
      contains:
        field_to_match:
          description: Field on which the regex match is applied
          type: complex
          contains:
            type:
              description: The field name
              returned: when type is regex and state is present
              type: str
              sample: QUERY_STRING
        regex_pattern_set_id:
          description: ID of the regex pattern
          type: str
          sample: 6fdf7f2d-9091-445c-aef2-98f3c051ac9e
        text_transformation:
          description: transformation applied to the text before matching
          type: str
          sample: NONE
    size_constraint_set_id:
      description: ID of the size constraint set
      returned: when type is size and state is present
      type: str
      sample: de84b4b3-578b-447e-a9a0-0db35c995656
    size_constraints:
      description: List of size constraints to apply
      returned: when type is size and state is present
      type: complex
      contains:
        comparison_operator:
          description: Comparison operator to apply
          type: str
          sample: GT
        field_to_match:
          description: Field on which the size constraint is applied
          type: complex
          contains:
            type:
              description: Field name
              type: str
              sample: QUERY_STRING
        size:
          description: size to compare against the field
          type: int
          sample: 300
        text_transformation:
          description: transformation applied to the text before matching
          type: str
          sample: NONE
    sql_injection_match_set_id:
      description: ID of the SQL injection match set
      returned: when type is sql and state is present
      type: str
      sample: de84b4b3-578b-447e-a9a0-0db35c995656
    sql_injection_match_tuples:
      description: List of SQL injection match sets
      returned: when type is sql and state is present
      type: complex
      contains:
        field_to_match:
          description: Field on which the SQL injection match is applied
          type: complex
          contains:
            type:
              description: Field name
              type: str
              sample: QUERY_STRING
        text_transformation:
          description: transformation applied to the text before matching
          type: str
          sample: URL_DECODE
    xss_match_set_id:
      description: ID of the XSS match set
      returned: when type is xss and state is present
      type: str
      sample: de84b4b3-578b-447e-a9a0-0db35c995656
    xss_match_tuples:
      description: List of XSS match sets
      returned: when type is xss and state is present
      type: complex
      contains:
        field_to_match:
          description: Field on which the XSS match is applied
          type: complex
          contains:
            type:
              description: Field name
              type: str
              sample: QUERY_STRING
        text_transformation:
          description: transformation applied to the text before matching
          type: str
          sample: URL_DECODE
'''

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, ec2_argument_spec
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, AWSRetry, compare_policies
from ansible.module_utils.aws.waf import run_func_with_change_token_backoff, MATCH_LOOKUP
from ansible.module_utils.aws.waf import get_rule_with_backoff, list_rules_with_backoff, list_regional_rules_with_backoff


class Condition(object):

    def __init__(self, client, module):
        self.client = client
        self.module = module
        self.type = module.params['type']
        self.method_suffix = MATCH_LOOKUP[self.type]['method']
        self.conditionset = MATCH_LOOKUP[self.type]['conditionset']
        self.conditionsets = MATCH_LOOKUP[self.type]['conditionset'] + 's'
        self.conditionsetid = MATCH_LOOKUP[self.type]['conditionset'] + 'Id'
        self.conditiontuple = MATCH_LOOKUP[self.type]['conditiontuple']
        self.conditiontuples = MATCH_LOOKUP[self.type]['conditiontuple'] + 's'
        self.conditiontype = MATCH_LOOKUP[self.type]['type']

    def format_for_update(self, condition_set_id):
        # Prep kwargs
        kwargs = dict()
        kwargs['Updates'] = list()

        for filtr in self.module.params.get('filters'):
            # Only for ip_set
            if self.type == 'ip':
                # there might be a better way of detecting an IPv6 address
                if ':' in filtr.get('ip_address'):
                    ip_type = 'IPV6'
                else:
                    ip_type = 'IPV4'
                condition_insert = {'Type': ip_type, 'Value': filtr.get('ip_address')}

            # Specific for geo_match_set
            if self.type == 'geo':
                condition_insert = dict(Type='Country', Value=filtr.get('country'))

            # Common For everything but ip_set and geo_match_set
            if self.type not in ('ip', 'geo'):

                condition_insert = dict(FieldToMatch=dict(Type=filtr.get('field_to_match').upper()),
                                        TextTransformation=filtr.get('transformation', 'none').upper())

                if filtr.get('field_to_match').upper() == "HEADER":
                    if filtr.get('header'):
                        condition_insert['FieldToMatch']['Data'] = filtr.get('header').lower()
                    else:
                        self.module.fail_json(msg=str("DATA required when HEADER requested"))

            # Specific for byte_match_set
            if self.type == 'byte':
                condition_insert['TargetString'] = filtr.get('target_string')
                condition_insert['PositionalConstraint'] = filtr.get('position')

            # Specific for size_constraint_set
            if self.type == 'size':
                condition_insert['ComparisonOperator'] = filtr.get('comparison')
                condition_insert['Size'] = filtr.get('size')

            # Specific for regex_match_set
            if self.type == 'regex':
                condition_insert['RegexPatternSetId'] = self.ensure_regex_pattern_present(filtr.get('regex_pattern'))['RegexPatternSetId']

            kwargs['Updates'].append({'Action': 'INSERT', self.conditiontuple: condition_insert})

        kwargs[self.conditionsetid] = condition_set_id
        return kwargs

    def format_for_deletion(self, condition):
        return {'Updates': [{'Action': 'DELETE', self.conditiontuple: current_condition_tuple}
                            for current_condition_tuple in condition[self.conditiontuples]],
                self.conditionsetid: condition[self.conditionsetid]}

    @AWSRetry.exponential_backoff()
    def list_regex_patterns_with_backoff(self, **params):
        return self.client.list_regex_pattern_sets(**params)

    @AWSRetry.exponential_backoff()
    def get_regex_pattern_set_with_backoff(self, regex_pattern_set_id):
        return self.client.get_regex_pattern_set(RegexPatternSetId=regex_pattern_set_id)

    def list_regex_patterns(self):
        # at time of writing(2017-11-20) no regex pattern paginator exists
        regex_patterns = []
        params = {}
        while True:
            try:
                response = self.list_regex_patterns_with_backoff(**params)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self.module.fail_json_aws(e, msg='Could not list regex patterns')
            regex_patterns.extend(response['RegexPatternSets'])
            if 'NextMarker' in response:
                params['NextMarker'] = response['NextMarker']
            else:
                break
        return regex_patterns

    def get_regex_pattern_by_name(self, name):
        existing_regex_patterns = self.list_regex_patterns()
        regex_lookup = dict((item['Name'], item['RegexPatternSetId']) for item in existing_regex_patterns)
        if name in regex_lookup:
            return self.get_regex_pattern_set_with_backoff(regex_lookup[name])['RegexPatternSet']
        else:
            return None

    def ensure_regex_pattern_present(self, regex_pattern):
        name = regex_pattern['name']

        pattern_set = self.get_regex_pattern_by_name(name)
        if not pattern_set:
            pattern_set = run_func_with_change_token_backoff(self.client, self.module, {'Name': name},
                                                             self.client.create_regex_pattern_set)['RegexPatternSet']
        missing = set(regex_pattern['regex_strings']) - set(pattern_set['RegexPatternStrings'])
        extra = set(pattern_set['RegexPatternStrings']) - set(regex_pattern['regex_strings'])
        if not missing and not extra:
            return pattern_set
        updates = [{'Action': 'INSERT', 'RegexPatternString': pattern} for pattern in missing]
        updates.extend([{'Action': 'DELETE', 'RegexPatternString': pattern} for pattern in extra])
        run_func_with_change_token_backoff(self.client, self.module,
                                           {'RegexPatternSetId': pattern_set['RegexPatternSetId'], 'Updates': updates},
                                           self.client.update_regex_pattern_set, wait=True)
        return self.get_regex_pattern_set_with_backoff(pattern_set['RegexPatternSetId'])['RegexPatternSet']

    def delete_unused_regex_pattern(self, regex_pattern_set_id):
        try:
            regex_pattern_set = self.client.get_regex_pattern_set(RegexPatternSetId=regex_pattern_set_id)['RegexPatternSet']
            updates = list()
            for regex_pattern_string in regex_pattern_set['RegexPatternStrings']:
                updates.append({'Action': 'DELETE', 'RegexPatternString': regex_pattern_string})
            run_func_with_change_token_backoff(self.client, self.module,
                                               {'RegexPatternSetId': regex_pattern_set_id, 'Updates': updates},
                                               self.client.update_regex_pattern_set)

            run_func_with_change_token_backoff(self.client, self.module,
                                               {'RegexPatternSetId': regex_pattern_set_id},
                                               self.client.delete_regex_pattern_set, wait=True)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            if e.response['Error']['Code'] == 'WAFNonexistentItemException':
                return
            self.module.fail_json_aws(e, msg='Could not delete regex pattern')

    def get_condition_by_name(self, name):
        all_conditions = [d for d in self.list_conditions() if d['Name'] == name]
        if all_conditions:
            return all_conditions[0][self.conditionsetid]

    @AWSRetry.exponential_backoff()
    def get_condition_by_id_with_backoff(self, condition_set_id):
        params = dict()
        params[self.conditionsetid] = condition_set_id
        func = getattr(self.client, 'get_' + self.method_suffix)
        return func(**params)[self.conditionset]

    def get_condition_by_id(self, condition_set_id):
        try:
            return self.get_condition_by_id_with_backoff(condition_set_id)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg='Could not get condition')

    def list_conditions(self):
        method = 'list_' + self.method_suffix + 's'
        try:
            paginator = self.client.get_paginator(method)
            func = paginator.paginate().build_full_result
        except botocore.exceptions.OperationNotPageableError:
            # list_geo_match_sets and list_regex_match_sets do not have a paginator
            func = getattr(self.client, method)
        try:
            return func()[self.conditionsets]
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg='Could not list %s conditions' % self.type)

    def tidy_up_regex_patterns(self, regex_match_set):
        all_regex_match_sets = self.list_conditions()
        all_match_set_patterns = list()
        for rms in all_regex_match_sets:
            all_match_set_patterns.extend(conditiontuple['RegexPatternSetId']
                                          for conditiontuple in self.get_condition_by_id(rms[self.conditionsetid])[self.conditiontuples])
        for filtr in regex_match_set[self.conditiontuples]:
            if filtr['RegexPatternSetId'] not in all_match_set_patterns:
                self.delete_unused_regex_pattern(filtr['RegexPatternSetId'])

    def find_condition_in_rules(self, condition_set_id):
        rules_in_use = []
        try:
            if self.client.__class__.__name__ == 'WAF':
                all_rules = list_rules_with_backoff(self.client)
            elif self.client.__class__.__name__ == 'WAFRegional':
                all_rules = list_regional_rules_with_backoff(self.client)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg='Could not list rules')
        for rule in all_rules:
            try:
                rule_details = get_rule_with_backoff(self.client, rule['RuleId'])
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self.module.fail_json_aws(e, msg='Could not get rule details')
            if condition_set_id in [predicate['DataId'] for predicate in rule_details['Predicates']]:
                rules_in_use.append(rule_details['Name'])
        return rules_in_use

    def find_and_delete_condition(self, condition_set_id):
        current_condition = self.get_condition_by_id(condition_set_id)
        in_use_rules = self.find_condition_in_rules(condition_set_id)
        if in_use_rules:
            rulenames = ', '.join(in_use_rules)
            self.module.fail_json(msg="Condition %s is in use by %s" % (current_condition['Name'], rulenames))
        if current_condition[self.conditiontuples]:
            # Filters are deleted using update with the DELETE action
            func = getattr(self.client, 'update_' + self.method_suffix)
            params = self.format_for_deletion(current_condition)
            try:
                # We do not need to wait for the conditiontuple delete because we wait later for the delete_* call
                run_func_with_change_token_backoff(self.client, self.module, params, func)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self.module.fail_json_aws(e, msg='Could not delete filters from condition')
        func = getattr(self.client, 'delete_' + self.method_suffix)
        params = dict()
        params[self.conditionsetid] = condition_set_id
        try:
            run_func_with_change_token_backoff(self.client, self.module, params, func, wait=True)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg='Could not delete condition')
        # tidy up regex patterns
        if self.type == 'regex':
            self.tidy_up_regex_patterns(current_condition)
        return True, {}

    def find_missing(self, update, current_condition):
        missing = []
        for desired in update['Updates']:
            found = False
            desired_condition = desired[self.conditiontuple]
            current_conditions = current_condition[self.conditiontuples]
            for condition in current_conditions:
                if not compare_policies(condition, desired_condition):
                    found = True
            if not found:
                missing.append(desired)
        return missing

    def find_and_update_condition(self, condition_set_id):
        current_condition = self.get_condition_by_id(condition_set_id)
        update = self.format_for_update(condition_set_id)
        missing = self.find_missing(update, current_condition)
        if self.module.params.get('purge_filters'):
            extra = [{'Action': 'DELETE', self.conditiontuple: current_tuple}
                     for current_tuple in current_condition[self.conditiontuples]
                     if current_tuple not in [desired[self.conditiontuple] for desired in update['Updates']]]
        else:
            extra = []
        changed = bool(missing or extra)
        if changed:
            update['Updates'] = missing + extra
            func = getattr(self.client, 'update_' + self.method_suffix)
            try:
                result = run_func_with_change_token_backoff(self.client, self.module, update, func, wait=True)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self.module.fail_json_aws(e, msg='Could not update condition')
        return changed, self.get_condition_by_id(condition_set_id)

    def ensure_condition_present(self):
        name = self.module.params['name']
        condition_set_id = self.get_condition_by_name(name)
        if condition_set_id:
            return self.find_and_update_condition(condition_set_id)
        else:
            params = dict()
            params['Name'] = name
            func = getattr(self.client, 'create_' + self.method_suffix)
            try:
                condition = run_func_with_change_token_backoff(self.client, self.module, params, func)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self.module.fail_json_aws(e, msg='Could not create condition')
            return self.find_and_update_condition(condition[self.conditionset][self.conditionsetid])

    def ensure_condition_absent(self):
        condition_set_id = self.get_condition_by_name(self.module.params['name'])
        if condition_set_id:
            return self.find_and_delete_condition(condition_set_id)
        return False, {}


def main():
    filters_subspec = dict(
        country=dict(),
        field_to_match=dict(choices=['uri', 'query_string', 'header', 'method', 'body']),
        header=dict(),
        transformation=dict(choices=['none', 'compress_white_space',
                                     'html_entity_decode', 'lowercase',
                                     'cmd_line', 'url_decode']),
        position=dict(choices=['exactly', 'starts_with', 'ends_with',
                               'contains', 'contains_word']),
        comparison=dict(choices=['EQ', 'NE', 'LE', 'LT', 'GE', 'GT']),
        target_string=dict(),  # Bytes
        size=dict(type='int'),
        ip_address=dict(),
        regex_pattern=dict(),
    )
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True),
            type=dict(required=True, choices=['byte', 'geo', 'ip', 'regex', 'size', 'sql', 'xss']),
            filters=dict(type='list'),
            purge_filters=dict(type='bool', default=False),
            waf_regional=dict(type='bool', default=False),
            state=dict(default='present', choices=['present', 'absent']),
        ),
    )
    module = AnsibleAWSModule(argument_spec=argument_spec,
                              required_if=[['state', 'present', ['filters']]])
    state = module.params.get('state')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    resource = 'waf' if not module.params['waf_regional'] else 'waf-regional'
    client = boto3_conn(module, conn_type='client', resource=resource, region=region, endpoint=ec2_url, **aws_connect_kwargs)

    condition = Condition(client, module)

    if state == 'present':
        (changed, results) = condition.ensure_condition_present()
        # return a condition agnostic ID for use by aws_waf_rule
        results['ConditionId'] = results[condition.conditionsetid]
    else:
        (changed, results) = condition.ensure_condition_absent()

    module.exit_json(changed=changed, condition=camel_dict_to_snake_dict(results))


if __name__ == '__main__':
    main()
