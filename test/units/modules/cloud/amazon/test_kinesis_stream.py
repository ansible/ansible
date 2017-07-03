import pytest
import unittest

boto3 = pytest.importorskip("boto3")
botocore = pytest.importorskip("botocore")

import ansible.modules.cloud.amazon.kinesis_stream as kinesis_stream

aws_region = 'us-west-2'


class AnsibleKinesisStreamFunctions(unittest.TestCase):

    def test_convert_to_lower(self):
        example = {
            'HasMoreShards': True,
            'RetentionPeriodHours': 24,
            'StreamName': 'test',
            'StreamARN': 'arn:aws:kinesis:east-side:123456789:stream/test',
            'StreamStatus': 'ACTIVE'
        }
        converted_example = kinesis_stream.convert_to_lower(example)
        keys = list(converted_example.keys())
        keys.sort()
        for i in range(len(keys)):
            if i == 0:
                self.assertEqual(keys[i], 'has_more_shards')
            if i == 1:
                self.assertEqual(keys[i], 'retention_period_hours')
            if i == 2:
                self.assertEqual(keys[i], 'stream_arn')
            if i == 3:
                self.assertEqual(keys[i], 'stream_name')
            if i == 4:
                self.assertEqual(keys[i], 'stream_status')

    def test_make_tags_in_aws_format(self):
        example = {
            'env': 'development'
        }
        should_return = [
            {
                'Key': 'env',
                'Value': 'development'
            }
        ]
        aws_tags = kinesis_stream.make_tags_in_aws_format(example)
        self.assertEqual(aws_tags, should_return)

    def test_make_tags_in_proper_format(self):
        example = [
            {
                'Key': 'env',
                'Value': 'development'
            },
            {
                'Key': 'service',
                'Value': 'web'
            }
        ]
        should_return = {
            'env': 'development',
            'service': 'web'
        }
        proper_tags = kinesis_stream.make_tags_in_proper_format(example)
        self.assertEqual(proper_tags, should_return)

    def test_recreate_tags_from_list(self):
        example = [('environment', 'development'), ('service', 'web')]
        should_return = [
            {
                'Key': 'environment',
                'Value': 'development'
            },
            {
                'Key': 'service',
                'Value': 'web'
            }
        ]
        aws_tags = kinesis_stream.recreate_tags_from_list(example)
        self.assertEqual(aws_tags, should_return)

    def test_get_tags(self):
        client = boto3.client('kinesis', region_name=aws_region)
        success, err_msg, tags = kinesis_stream.get_tags(client, 'test', check_mode=True)
        self.assertTrue(success)
        should_return = [
            {
                'Key': 'DryRunMode',
                'Value': 'true'
            }
        ]
        self.assertEqual(tags, should_return)

    def test_find_stream(self):
        client = boto3.client('kinesis', region_name=aws_region)
        success, err_msg, stream = (
            kinesis_stream.find_stream(client, 'test', check_mode=True)
        )
        should_return = {
            'HasMoreShards': True,
            'RetentionPeriodHours': 24,
            'StreamName': 'test',
            'StreamARN': 'arn:aws:kinesis:east-side:123456789:stream/test',
            'StreamStatus': 'ACTIVE'
        }
        self.assertTrue(success)
        self.assertEqual(stream, should_return)

    def test_wait_for_status(self):
        client = boto3.client('kinesis', region_name=aws_region)
        success, err_msg, stream = (
            kinesis_stream.wait_for_status(
                client, 'test', 'ACTIVE', check_mode=True
            )
        )
        should_return = {
            'HasMoreShards': True,
            'RetentionPeriodHours': 24,
            'StreamName': 'test',
            'StreamARN': 'arn:aws:kinesis:east-side:123456789:stream/test',
            'StreamStatus': 'ACTIVE'
        }
        self.assertTrue(success)
        self.assertEqual(stream, should_return)

    def test_tags_action_create(self):
        client = boto3.client('kinesis', region_name=aws_region)
        tags = {
            'env': 'development',
            'service': 'web'
        }
        success, err_msg = (
            kinesis_stream.tags_action(
                client, 'test', tags, 'create', check_mode=True
            )
        )
        self.assertTrue(success)

    def test_tags_action_delete(self):
        client = boto3.client('kinesis', region_name=aws_region)
        tags = {
            'env': 'development',
            'service': 'web'
        }
        success, err_msg = (
            kinesis_stream.tags_action(
                client, 'test', tags, 'delete', check_mode=True
            )
        )
        self.assertTrue(success)

    def test_tags_action_invalid(self):
        client = boto3.client('kinesis', region_name=aws_region)
        tags = {
            'env': 'development',
            'service': 'web'
        }
        success, err_msg = (
            kinesis_stream.tags_action(
                client, 'test', tags, 'append', check_mode=True
            )
        )
        self.assertFalse(success)

    def test_update_tags(self):
        client = boto3.client('kinesis', region_name=aws_region)
        tags = {
            'env': 'development',
            'service': 'web'
        }
        success, changed, err_msg = (
            kinesis_stream.update_tags(
                client, 'test', tags, check_mode=True
            )
        )
        self.assertTrue(success)

    def test_stream_action_create(self):
        client = boto3.client('kinesis', region_name=aws_region)
        success, err_msg = (
            kinesis_stream.stream_action(
                client, 'test', 10, 'create', check_mode=True
            )
        )
        self.assertTrue(success)

    def test_stream_action_delete(self):
        client = boto3.client('kinesis', region_name=aws_region)
        success, err_msg = (
            kinesis_stream.stream_action(
                client, 'test', 10, 'delete', check_mode=True
            )
        )
        self.assertTrue(success)

    def test_stream_action_invalid(self):
        client = boto3.client('kinesis', region_name=aws_region)
        success, err_msg = (
            kinesis_stream.stream_action(
                client, 'test', 10, 'append', check_mode=True
            )
        )
        self.assertFalse(success)

    def test_retention_action_increase(self):
        client = boto3.client('kinesis', region_name=aws_region)
        success, err_msg = (
            kinesis_stream.retention_action(
                client, 'test', 48, 'increase', check_mode=True
            )
        )
        self.assertTrue(success)

    def test_retention_action_decrease(self):
        client = boto3.client('kinesis', region_name=aws_region)
        success, err_msg = (
            kinesis_stream.retention_action(
                client, 'test', 24, 'decrease', check_mode=True
            )
        )
        self.assertTrue(success)

    def test_retention_action_invalid(self):
        client = boto3.client('kinesis', region_name=aws_region)
        success, err_msg = (
            kinesis_stream.retention_action(
                client, 'test', 24, 'create', check_mode=True
            )
        )
        self.assertFalse(success)

    def test_update(self):
        client = boto3.client('kinesis', region_name=aws_region)
        current_stream = {
            'HasMoreShards': True,
            'RetentionPeriodHours': 24,
            'StreamName': 'test',
            'StreamARN': 'arn:aws:kinesis:east-side:123456789:stream/test',
            'StreamStatus': 'ACTIVE'
        }
        tags = {
            'env': 'development',
            'service': 'web'
        }
        success, changed, err_msg = (
            kinesis_stream.update(
                client, current_stream, 'test', retention_period=48,
                tags=tags, check_mode=True
            )
        )
        self.assertTrue(success)
        self.assertTrue(changed)
        self.assertEqual(err_msg, 'Kinesis Stream test updated successfully.')

    def test_create_stream(self):
        client = boto3.client('kinesis', region_name=aws_region)
        tags = {
            'env': 'development',
            'service': 'web'
        }
        success, changed, err_msg, results = (
            kinesis_stream.create_stream(
                client, 'test', number_of_shards=10, retention_period=48,
                tags=tags, check_mode=True
            )
        )
        should_return = {
            'has_more_shards': True,
            'retention_period_hours': 24,
            'stream_name': 'test',
            'stream_arn': 'arn:aws:kinesis:east-side:123456789:stream/test',
            'stream_status': 'ACTIVE',
            'tags': tags,
        }
        self.assertTrue(success)
        self.assertTrue(changed)
        self.assertEqual(results, should_return)
        self.assertEqual(err_msg, 'Kinesis Stream test updated successfully.')
