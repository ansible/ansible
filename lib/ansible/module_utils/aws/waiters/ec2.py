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
                }
            ]
        }
    }
}


def model_for(name):
    ec2_models = core_waiter.WaiterModel(waiter_config=ec2_data)
    return ec2_models.get_waiter(name)


waiters_by_name = {
    'route_table_exists': lambda ec2: core_waiter.Waiter(
        'route_table_exists',
        model_for('RouteTableExists'),
        ec2.describe_route_tables)
}
