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
        }
    }
}


def model_for(name):
    ec2_models = core_waiter.WaiterModel(waiter_config=ec2_data)
    return ec2_models.get_waiter(name)


waiters_by_name = {
    ('EC2', 'route_table_exists'): lambda ec2: core_waiter.Waiter(
        'route_table_exists',
        model_for('RouteTableExists'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_route_tables
        ))
}


def get_waiter(client, waiter_name):
    try:
        return waiters_by_name[(client.__class__.__name__, waiter_name)](client)
    except KeyError:
        raise NotImplementedError("Waiter {0} could not be found for client {1}. Available waiters: {2}".format(
            waiter_name, type(client), ', '.join(repr(k) for k in waiters_by_name.keys())))
