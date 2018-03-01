import botocore.waiter as core_waiter


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

ec2_models = core_waiter.WaiterModel(waiter_config=ec2_data)

waiters_by_name = {
    'route_table_exists': lambda ec2: core_waiter.Waiter(
        'route_table_exists',
        ec2_models.get_waiter('RouteTableExists'),
        ec2.describe_route_tables)
}
