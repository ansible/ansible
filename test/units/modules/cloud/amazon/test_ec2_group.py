import pytest

from .placebo_fixtures import placeboify, maybe_sleep
from ansible.modules.cloud.amazon import ec2_group as group_module

def test_from_permission():
    internal_http = {
        u'FromPort': 80,
        u'IpProtocol': 'tcp',
        u'IpRanges': [
            {
                u'CidrIp': '10.0.0.0/8',
                u'Description': 'Foo Bar Baz'
            },
        ],
        u'Ipv6Ranges': [
            {u'CidrIpv6': 'fe80::94cc:8aff:fef6:9cc/64'},
        ],
        u'PrefixListIds': [],
        u'ToPort': 80,
        u'UserIdGroupPairs': [],
    }
    perms = list(group_module.rule_from_group_permission(internal_http))
    assert len(perms) == 2
    assert perms[0].target == '10.0.0.0/8'
    assert perms[0].target_type == 'ipv4'
    assert perms[0].description == 'Foo Bar Baz'
    assert perms[1].target == 'fe80::94cc:8aff:fef6:9cc/64'


    global_egress = {
        'IpProtocol': '-1',
        'IpRanges': [{'CidrIp': '0.0.0.0/0'}],
        'Ipv6Ranges': [],
        'PrefixListIds': [],
        'UserIdGroupPairs': []
    }
    perms = list(group_module.rule_from_group_permission(global_egress))
    assert len(perms) == 1
    assert perms[0].target == '0.0.0.0/0'
    assert perms[0].port_range == (None, None)


    internal_prefix_http = {
        u'FromPort': 80,
        u'IpProtocol': 'tcp',
        u'PrefixListIds': [
            {'PrefixListId': 'p-1234'}
        ],
        u'ToPort': 80,
        u'UserIdGroupPairs': [],
    }
    perms = list(group_module.rule_from_group_permission(internal_prefix_http))
    assert len(perms) == 1
    assert perms[0].target == 'p-1234'

def test_from_rule_param():
    internal_http = {
        'cidr_ip': '10.0.0.0/8',
        'to_port': 80,
        'from_port': '80',
        'proto': 'tcp',
        'rule_desc': 'Foo Bar Baz',
    }
    perms = list(group_module.rule_from_rule_params([internal_http]))
    assert len(perms) == 1
    assert perms[0].target == '10.0.0.0/8'
    assert perms[0].port_range == (80, 80)
    internal_https = {
        'cidr_ip': '10.0.0.0/8',
        'to_port': 443,
        'from_port': '443',
    }
    perms = list(group_module.rule_from_rule_params([internal_https]))
    assert len(perms) == 1
    assert perms[0].target == '10.0.0.0/8'
    assert perms[0].port_range == (443, 443)
