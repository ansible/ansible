from ansible.modules.cloud.amazon import dynamodb_table as dynamodb_table_module
import unittest
import json


class DynamodbTable_IndexTests(unittest.TestCase):
    def test_local_get_changed_indexes_create(self):
        param_local_index = [
            {
                "hash_key_name": "myhashkey",
                "name": "NamedIndex",
                "type": "all",
                "read_capacity": 10,
                "write_capacity": 10
            }
        ]
        indexes, global_indexes, attr_definitions = dynamodb_table_module.get_indexes(param_local_index)
        self.assertEqual(len(indexes), 1)
        self.assertEqual(indexes[0]['Projection']['ProjectionType'], 'ALL')

    def test_gsi_get_changed_indexes_create(self):
        table_gsi_indexs = []
        param_gsi_index = [
            {
                "hash_key_name": "myhashkey",
                "name": "NamedIndex",
                "type": "global_all",
                "read_capacity": 10,
                "write_capacity": 10
            }
        ]
        indexes, global_indexes, attr_definitions = dynamodb_table_module.get_indexes(param_gsi_index)
        actual = dynamodb_table_module.get_changed_global_indexes(table_gsi_indexs, global_indexes)
        expected = {"Create": {
            "IndexName": "NamedIndex",
            "KeySchema": [
                {
                    "AttributeName": "myhashkey",
                    "KeyType": "HASH"
                }
            ],
            "Projection": {
                "ProjectionType": "ALL"
            },
            "ProvisionedThroughput": {
                "ReadCapacityUnits": 10,
                "WriteCapacityUnits": 10
            }
        }
        }
        self.assertEqual(len(actual), 1)
        self.assertTrue('Create' in actual[0])
        self.assertTrue(actual[0].get('Create').get('IndexName') == 'NamedIndex')

    def test_gsi_get_changed_indexes_update_nochange(self):
        table_gsi_indexs = [{
            "IndexArn": "arn:aws:dynamodb:us-west-2:132601236262:table/ansible-table-/index/NamedIndex",
            "IndexName": "NamedIndex",
            "IndexSizeBytes": 0,
            "IndexStatus": "ACTIVE",
            "ItemCount": 0,
            "KeySchema": [
                {
                    "AttributeName": "myhashkey",
                    "KeyType": "HASH"
                }
            ],
            "Projection": {
                "ProjectionType": "ALL"
            },
            "ProvisionedThroughput": {
                "NumberOfDecreasesToday": 0,
                "ReadCapacityUnits": 10,
                "WriteCapacityUnits": 10
            }
        },
            {
            "IndexArn": "arn:aws:dynamodb:us-west-2:132601236262:table/ansible-table-/index/NamedIndexV2",
            "IndexName": "NamedIndexV2",
            "IndexSizeBytes": 0,
            "IndexStatus": "ACTIVE",
            "ItemCount": 0,
            "KeySchema": [
                {
                    "AttributeName": "myhashkey",
                    "KeyType": "HASH"
                },
                {
                    "AttributeName": "myrangekey",
                    "KeyType": "RANGE"
                }
            ],
            "Projection": {
                "ProjectionType": "ALL"
            },
            "ProvisionedThroughput": {
                "LastIncreaseDateTime": "2018-11-16T12:05:35.779000-05:00",
                "NumberOfDecreasesToday": 0,
                "ReadCapacityUnits": 10,
                "WriteCapacityUnits": 10
            }
        }
        ]
        param_gsi_index = [
            {
                "hash_key_name": "myhashkey",
                "name": "NamedIndex",
                "type": "global_all",
                "read_capacity": 10,
                "write_capacity": 10
            },
            {
                "hash_key_name": "myhashkey",
                "range_key_name": "myrangekey",
                "name": "NamedIndexV2",
                "type": "global_all",
                "read_capacity": 10,
                "write_capacity": 10
            }
        ]
        indexes, global_indexes, attr_definitions = dynamodb_table_module.get_indexes(param_gsi_index)
        actual = dynamodb_table_module.get_changed_global_indexes(table_gsi_indexs, global_indexes)
        expected = [{'Update': {'ProvisionedThroughput': {'WriteCapacityUnits': 100, 'ReadCapacityUnits': 100}, 'IndexName': 'NamedIndexV2'}},
                    {'Update': {'ProvisionedThroughput': {'WriteCapacityUnits': 100, 'ReadCapacityUnits': 100}, 'IndexName': 'NamedIndex'}}]
        self.assertEqual(len(actual), 0)

    def test_gsi_get_changed_indexes_update(self):
        table_gsi_indexs = [{
            "IndexArn": "arn:aws:dynamodb:us-west-2:132601236262:table/ansible-table-/index/NamedIndex",
            "IndexName": "NamedIndex",
            "IndexSizeBytes": 0,
            "IndexStatus": "ACTIVE",
            "ItemCount": 0,
            "KeySchema": [
                {
                    "AttributeName": "myhashkey",
                    "KeyType": "HASH"
                }
            ],
            "Projection": {
                "ProjectionType": "ALL"
            },
            "ProvisionedThroughput": {
                "NumberOfDecreasesToday": 0,
                "ReadCapacityUnits": 1,
                "WriteCapacityUnits": 1
            }
        },
            {
            "IndexArn": "arn:aws:dynamodb:us-west-2:132601236262:table/ansible-table-/index/NamedIndexV2",
            "IndexName": "NamedIndexV2",
            "IndexSizeBytes": 0,
            "IndexStatus": "ACTIVE",
            "ItemCount": 0,
            "KeySchema": [
                {
                    "AttributeName": "myhashkey",
                    "KeyType": "HASH"
                },
                {
                    "AttributeName": "myrangekey",
                    "KeyType": "RANGE"
                }
            ],
            "Projection": {
                "ProjectionType": "ALL"
            },
            "ProvisionedThroughput": {
                "LastIncreaseDateTime": "2018-11-16T12:05:35.779000-05:00",
                "NumberOfDecreasesToday": 0,
                "ReadCapacityUnits": 10,
                "WriteCapacityUnits": 10
            }
        }
        ]
        param_gsi_index = [
            {
                "hash_key_name": "myhashkey",
                "name": "NamedIndex",
                "type": "global_all",
                "read_capacity": 100,
                "write_capacity": 100
            },
            {
                "hash_key_name": "myhashkey",
                "range_key_name": "myrangekey",
                "name": "NamedIndexV2",
                "type": "global_all",
                "read_capacity": 150,
                "write_capacity": 150
            }
        ]
        indexes, global_indexes, attr_definitions = dynamodb_table_module.get_indexes(param_gsi_index)
        actual = dynamodb_table_module.get_changed_global_indexes(table_gsi_indexs, global_indexes)
        expected = [{'Update': {'ProvisionedThroughput': {'WriteCapacityUnits': 100, 'ReadCapacityUnits': 100}, 'IndexName': 'NamedIndexV2'}},
                    {'Update': {'ProvisionedThroughput': {'WriteCapacityUnits': 100, 'ReadCapacityUnits': 100}, 'IndexName': 'NamedIndex'}}]
        self.assertEqual(len(actual), 2)
