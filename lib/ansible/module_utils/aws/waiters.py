# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
try:
    import botocore.waiter as core_waiter
except ImportError:
    pass  # caught by HAS_BOTO3


ec2_data = {
    "version": 2,
    "waiters": {
        "RouteTableExists": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeRouteTables",
            "acceptors": [
                {
                    "matcher": "path",
                    "expected": True,
                    "argument": "length(RouteTables[]) > `0`",
                    "state": "success"
                },
                {
                    "matcher": "error",
                    "expected": "InvalidRouteTableID.NotFound",
                    "state": "retry"
                },
            ]
        },
        "SecurityGroupExists": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeSecurityGroups",
            "acceptors": [
                {
                    "matcher": "path",
                    "expected": True,
                    "argument": "length(SecurityGroups[]) > `0`",
                    "state": "success"
                },
                {
                    "matcher": "error",
                    "expected": "InvalidGroup.NotFound",
                    "state": "retry"
                },
            ]
        },
        "SubnetExists": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeSubnets",
            "acceptors": [
                {
                    "matcher": "path",
                    "expected": True,
                    "argument": "length(Subnets[]) > `0`",
                    "state": "success"
                },
                {
                    "matcher": "error",
                    "expected": "InvalidSubnetID.NotFound",
                    "state": "retry"
                },
            ]
        },
        "SubnetHasMapPublic": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeSubnets",
            "acceptors": [
                {
                    "matcher": "pathAll",
                    "expected": True,
                    "argument": "Subnets[].MapPublicIpOnLaunch",
                    "state": "success"
                },
            ]
        },
        "SubnetNoMapPublic": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeSubnets",
            "acceptors": [
                {
                    "matcher": "pathAll",
                    "expected": False,
                    "argument": "Subnets[].MapPublicIpOnLaunch",
                    "state": "success"
                },
            ]
        },
        "SubnetHasAssignIpv6": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeSubnets",
            "acceptors": [
                {
                    "matcher": "pathAll",
                    "expected": True,
                    "argument": "Subnets[].AssignIpv6AddressOnCreation",
                    "state": "success"
                },
            ]
        },
        "SubnetNoAssignIpv6": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeSubnets",
            "acceptors": [
                {
                    "matcher": "pathAll",
                    "expected": False,
                    "argument": "Subnets[].AssignIpv6AddressOnCreation",
                    "state": "success"
                },
            ]
        },
        "SubnetDeleted": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeSubnets",
            "acceptors": [
                {
                    "matcher": "path",
                    "expected": True,
                    "argument": "length(Subnets[]) > `0`",
                    "state": "retry"
                },
                {
                    "matcher": "error",
                    "expected": "InvalidSubnetID.NotFound",
                    "state": "success"
                },
            ]
        },
        "VpnGatewayExists": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeVpnGateways",
            "acceptors": [
                {
                    "matcher": "path",
                    "expected": True,
                    "argument": "length(VpnGateways[]) > `0`",
                    "state": "success"
                },
                {
                    "matcher": "error",
                    "expected": "InvalidVpnGatewayID.NotFound",
                    "state": "retry"
                },
            ]
        },
    }
}


waf_data = {
    "version": 2,
    "waiters": {
        "ChangeTokenInSync": {
            "delay": 20,
            "maxAttempts": 60,
            "operation": "GetChangeTokenStatus",
            "acceptors": [
                {
                    "matcher": "path",
                    "expected": True,
                    "argument": "ChangeTokenStatus == 'INSYNC'",
                    "state": "success"
                },
                {
                    "matcher": "error",
                    "expected": "WAFInternalErrorException",
                    "state": "retry"
                }
            ]
        }
    }
}


def ec2_model(name):
    ec2_models = core_waiter.WaiterModel(waiter_config=ec2_data)
    return ec2_models.get_waiter(name)


def waf_model(name):
    waf_models = core_waiter.WaiterModel(waiter_config=waf_data)
    return waf_models.get_waiter(name)


waiters_by_name = {
    ('EC2', 'route_table_exists'): lambda ec2: core_waiter.Waiter(
        'route_table_exists',
        ec2_model('RouteTableExists'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_route_tables
        )),
    ('EC2', 'security_group_exists'): lambda ec2: core_waiter.Waiter(
        'security_group_exists',
        ec2_model('SecurityGroupExists'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_security_groups
        )),
    ('EC2', 'subnet_exists'): lambda ec2: core_waiter.Waiter(
        'subnet_exists',
        ec2_model('SubnetExists'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_subnets
        )),
    ('EC2', 'subnet_has_map_public'): lambda ec2: core_waiter.Waiter(
        'subnet_has_map_public',
        ec2_model('SubnetHasMapPublic'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_subnets
        )),
    ('EC2', 'subnet_no_map_public'): lambda ec2: core_waiter.Waiter(
        'subnet_no_map_public',
        ec2_model('SubnetNoMapPublic'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_subnets
        )),
    ('EC2', 'subnet_has_assign_ipv6'): lambda ec2: core_waiter.Waiter(
        'subnet_has_assign_ipv6',
        ec2_model('SubnetHasAssignIpv6'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_subnets
        )),
    ('EC2', 'subnet_no_assign_ipv6'): lambda ec2: core_waiter.Waiter(
        'subnet_no_assign_ipv6',
        ec2_model('SubnetNoAssignIpv6'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_subnets
        )),
    ('EC2', 'subnet_deleted'): lambda ec2: core_waiter.Waiter(
        'subnet_deleted',
        ec2_model('SubnetDeleted'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_subnets
        )),
    ('EC2', 'vpn_gateway_exists'): lambda ec2: core_waiter.Waiter(
        'vpn_gateway_exists',
        ec2_model('VpnGatewayExists'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_vpn_gateways
        )),
    ('WAF', 'change_token_in_sync'): lambda waf: core_waiter.Waiter(
        'change_token_in_sync',
        waf_model('ChangeTokenInSync'),
        core_waiter.NormalizedOperationMethod(
            waf.get_change_token_status
        )),
}


def get_waiter(client, waiter_name):
    try:
        return waiters_by_name[(client.__class__.__name__, waiter_name)](client)
    except KeyError:
        raise NotImplementedError("Waiter {0} could not be found for client {1}. Available waiters: {2}".format(
            waiter_name, type(client), ', '.join(repr(k) for k in waiters_by_name.keys())))
