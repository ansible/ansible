from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json


def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
