import pytest

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


def test_rule_to_permission():
    tests = [
        group_module.Rule((22, 22), 'udp', 'sg-1234567890', 'group', None),
        group_module.Rule((1, 65535), 'tcp', '0.0.0.0/0', 'ipv4', "All TCP from everywhere"),
        group_module.Rule((443, 443), 'tcp', 'ip-123456', 'ip_prefix', "Traffic to privatelink IPs"),
        group_module.Rule((443, 443), 'tcp', 'feed:dead:::beef/64', 'ipv6', None),
    ]
    for test in tests:
        perm = group_module.to_permission(test)
        assert perm['FromPort'], perm['ToPort'] == test.port_range
        assert perm['IpProtocol'] == test.protocol


def test_validate_ip():
    class Warner(object):
        def warn(self, msg):
            return
    ips = [
        ('1.1.1.1/24', '1.1.1.0/24'),
        ('192.168.56.101/16', '192.168.0.0/16'),
        # 64 bits make 8 octets, or 4 hextets
        ('1203:8fe0:fe80:b897:8990:8a7c:99bf:323d/64', '1203:8fe0:fe80:b897::/64'),
    ]

    for ip, net in ips:
        assert group_module.validate_ip(Warner(), ip) == net
