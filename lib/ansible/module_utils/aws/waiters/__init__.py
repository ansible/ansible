# extra waiters for AWS utils
import botocore.waiter as core_waiter

vpc_config = {
  "version": 2,
  "waiters": {
    "": {
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
}}

vpc_models = core_waiter.WaiterModel(waiter_config=vpc_config)

def get_waiter(ec2, waiter_name):
    return core_waiter.Waiter('route_table_exists', vpc_models.get_waiter('RouteTableExists'), ec2.describe_route_tables)
