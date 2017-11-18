# Copyright (c) 2017 Will Thames
#
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""
This module adds shared support for Web Application Firewall modules
"""

from ansible.module_utils.ec2 import camel_dict_to_snake_dict, AWSRetry

try:
    import botocore
except ImportError:
    pass  # caught by imported HAS_BOTO3


MATCH_LOOKUP = {
    'byte': {
        'method': 'byte_match_set',
        'conditionset': 'ByteMatchSet',
        'conditiontuple': 'ByteMatchTuple',
        'type': 'ByteMatch'
    },
    'geo': {
        'method': 'geo_match_set',
        'conditionset': 'GeoMatchSet',
        'conditiontuple': 'GeoMatchConstraint',
        'type': 'GeoMatch'
    },
    'ip': {
        'method': 'ip_set',
        'conditionset': 'IPSet',
        'conditiontuple': 'IPSetDescriptor',
        'type': 'IPMatch'
    },
    'regex': {
        'method': 'regex_match_set',
        'conditionset': 'RegexMatchSet',
        'conditiontuple': 'RegexMatchTuple',
        'type': 'RegexMatch'
    },
    'size': {
        'method': 'size_constraint_set',
        'conditionset': 'SizeConstraintSet',
        'conditiontuple': 'SizeConstraint',
        'type': 'SizeConstraint'
    },
    'sql': {
        'method': 'sql_injection_match_set',
        'conditionset': 'SqlInjectionMatchSet',
        'conditiontuple': 'SqlInjectionMatchTuple',
        'type': 'SqlInjectionMatch',
    },
    'xss': {
        'method': 'xss_match_set',
        'conditionset': 'XssMatchSet',
        'conditiontuple': 'XssMatchTuple',
        'type': 'XssMatch'
    },
}


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_rule_with_backoff(client, rule_id):
    return client.get_rule(RuleId=rule_id)['Rule']


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_byte_match_set_with_backoff(client, byte_match_set_id):
    return client.get_byte_match_set(ByteMatchSetId=byte_match_set_id)['ByteMatchSet']


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_ip_set_with_backoff(client, ip_set_id):
    return client.get_ip_set(IPSetId=ip_set_id)['IPSet']


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_size_constraint_set_with_backoff(client, size_constraint_set_id):
    return client.get_size_constraint_set(SizeConstraintSetId=size_constraint_set_id)['SizeConstraintSet']


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_sql_injection_match_set_with_backoff(client, sql_injection_match_set_id):
    return client.get_sql_injection_match_set(SqlInjectionMatchSetId=sql_injection_match_set_id)['SqlInjectionMatchSet']


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_xss_match_set_with_backoff(client, xss_match_set_id):
    return client.get_xss_match_set(XssMatchSetId=xss_match_set_id)['XssMatchSet']


def get_rule(client, module, rule_id):
    try:
        rule = get_rule_with_backoff(client, rule_id)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't obtain waf rule")

    match_sets = {
        'ByteMatch': get_byte_match_set_with_backoff,
        'IPMatch': get_ip_set_with_backoff,
        'SizeConstraint': get_size_constraint_set_with_backoff,
        'SqlInjectionMatch': get_sql_injection_match_set_with_backoff,
        'XssMatch': get_xss_match_set_with_backoff
    }
    if 'Predicates' in rule:
        for predicate in rule['Predicates']:
            if predicate['Type'] in match_sets:
                predicate.update(match_sets[predicate['Type']](client, predicate['DataId']))
                # replaced by Id from the relevant MatchSet
                del(predicate['DataId'])
    return rule


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_web_acl_with_backoff(client, web_acl_id):
    return client.get_web_acl(WebACLId=web_acl_id)['WebACL']


def get_web_acl(client, module, web_acl_id):
    try:
        web_acl = get_web_acl_with_backoff(client, web_acl_id)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't obtain web acl")

    if web_acl:
        try:
            for rule in web_acl['Rules']:
                rule.update(get_rule(client, module, rule['RuleId']))
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't obtain web acl rule")
    return camel_dict_to_snake_dict(web_acl)


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def list_rules_with_backoff(client):
    paginator = client.get_paginator('list_rules')
    return paginator.paginate().build_full_result()['Rules']


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def list_web_acls_with_backoff(client):
    paginator = client.get_paginator('list_web_acls')
    return paginator.paginate().build_full_result()['WebACLs']


def list_web_acls(client, module):
    try:
        return list_web_acls_with_backoff(client)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't obtain web acls")


def get_change_token(client, module):
    try:
        token = client.get_change_token()
        return token['ChangeToken']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't obtain change token")
