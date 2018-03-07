import json

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import Mock

from boto.dynamodb2.table import Table
from boto.dynamodb2.layer1 import DynamoDBConnection

from ansible.modules.cloud.amazon.dynamodb_table import dynamo_table_exists


class Response(object):

    def __init__(self, status, reason, result):
        self.status = status
        self.reason = reason
        self.result = result

    def read(self):
        response = json.dumps(self.result)
        return response.encode('utf-8')


class TestDynamoTable(unittest.TestCase):

    def setUp(self):
        self.conn = DynamoDBConnection(
            host='localhost',
            port=8000,
            aws_access_key_id='anything',
            aws_secret_access_key='anything',
            is_secure=False)

    def tearDown(self):
        pass

    def test_table_not_found_on_not_found_error(self):
        result = {
            '__type': 'com.amazonaws.dynamodb.v20120810#ResourceNotFoundException',
            'message': 'Requested resource not found: Table: test not found'
        }
        responose = Response(400, '400 Bad Request', result)
        self.conn._mexe = Mock(return_value=responose)
        table = Table('test', connection=self.conn)
        self.assertFalse(dynamo_table_exists(table))

    def test_table_not_found_on_non_existent_error(self):
        result = {
            '__type': 'com.amazonaws.dynamodb.v20120810#ResourceNotFoundException',
            'message': 'Cannot do operations on a non-existent table'
        }
        responose = Response(400, '400 Bad Request', result)
        self.conn._mexe = Mock(return_value=responose)
        table = Table('test', connection=self.conn)
        self.assertFalse(dynamo_table_exists(table))
