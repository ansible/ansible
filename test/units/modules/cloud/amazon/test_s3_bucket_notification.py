import pytest

from units.compat.mock import MagicMock, patch
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

from ansible.modules.cloud.amazon.s3_bucket_notification import AmazonBucket, Config
from ansible.modules.cloud.amazon import s3_bucket_notification
try:
    from botocore.exceptions import ClientError
except ImportError:
    pass


class TestAmazonBucketOperations:
    def test_current_config(self):
        api_config = {
            'Id': 'test-id',
            'LambdaFunctionArn': 'test-arn',
            'Events': [],
            'Filter': {
                'Key': {
                    'FilterRules': [{
                        'Name': 'Prefix',
                        'Value': ''
                    }, {
                        'Name': 'Suffix',
                        'Value': ''
                    }]
                }
            }
        }
        client = MagicMock()
        client.get_bucket_notification_configuration.return_value = {
            'LambdaFunctionConfigurations': [api_config]
        }
        bucket = AmazonBucket(client, 'test-bucket')
        current = bucket.current_config('test-id')
        assert current.raw == api_config
        assert client.get_bucket_notification_configuration.call_count == 1

    def test_current_config_empty(self):
        client = MagicMock()
        client.get_bucket_notification_configuration.return_value = {
            'LambdaFunctionConfigurations': []
        }
        bucket = AmazonBucket(client, 'test-bucket')
        current = bucket.current_config('test-id')
        assert current is None
        assert client.get_bucket_notification_configuration.call_count == 1

    def test_apply_invalid_config(self):
        client = MagicMock()
        client.get_bucket_notification_configuration.return_value = {
            'LambdaFunctionConfigurations': []
        }
        client.put_bucket_notification_configuration.side_effect = ClientError({}, '')
        bucket = AmazonBucket(client, 'test-bucket')
        config = Config.from_params(**{
            'event_name': 'test_event',
            'lambda_function_arn': 'lambda_arn',
            'lambda_version': 1,
            'events': ['s3:ObjectRemoved:*', 's3:ObjectCreated:*'],
            'prefix': '',
            'suffix': ''
        })
        with pytest.raises(ClientError):
            bucket.apply_config(config)

    def test_apply_config(self):
        client = MagicMock()
        client.get_bucket_notification_configuration.return_value = {
            'LambdaFunctionConfigurations': []
        }

        bucket = AmazonBucket(client, 'test-bucket')
        config = Config.from_params(**{
            'event_name': 'test_event',
            'lambda_function_arn': 'lambda_arn',
            'lambda_version': 1,
            'events': ['s3:ObjectRemoved:*', 's3:ObjectCreated:*'],
            'prefix': '',
            'suffix': ''
        })
        bucket.apply_config(config)
        assert client.get_bucket_notification_configuration.call_count == 1
        assert client.put_bucket_notification_configuration.call_count == 1

    def test_apply_config_add_event(self):
        api_config = {
            'Id': 'test-id',
            'LambdaFunctionArn': 'test-arn',
            'Events': ['s3:ObjectRemoved:*'],
            'Filter': {
                'Key': {
                    'FilterRules': [{
                        'Name': 'Prefix',
                        'Value': ''
                    }, {
                        'Name': 'Suffix',
                        'Value': ''
                    }]
                }
            }
        }
        client = MagicMock()
        client.get_bucket_notification_configuration.return_value = {
            'LambdaFunctionConfigurations': [api_config]
        }

        bucket = AmazonBucket(client, 'test-bucket')
        config = Config.from_params(**{
            'event_name': 'test-id',
            'lambda_function_arn': 'test-arn',
            'lambda_version': 1,
            'events': ['s3:ObjectRemoved:*', 's3:ObjectCreated:*'],
            'prefix': '',
            'suffix': ''
        })
        bucket.apply_config(config)
        assert client.get_bucket_notification_configuration.call_count == 1
        assert client.put_bucket_notification_configuration.call_count == 1
        client.put_bucket_notification_configuration.assert_called_with(
            Bucket='test-bucket',
            NotificationConfiguration={
                'LambdaFunctionConfigurations': [{
                    'Id': 'test-id',
                    'LambdaFunctionArn': 'test-arn:1',
                    'Events': ['s3:ObjectCreated:*', 's3:ObjectRemoved:*'],
                    'Filter': {
                        'Key': {
                            'FilterRules': [{
                                'Name': 'Prefix',
                                'Value': ''
                            }, {
                                'Name': 'Suffix',
                                'Value': ''
                            }]
                        }
                    }
                }]
            }
        )

    def test_delete_config(self):
        api_config = {
            'Id': 'test-id',
            'LambdaFunctionArn': 'test-arn',
            'Events': [],
            'Filter': {
                'Key': {
                    'FilterRules': [{
                        'Name': 'Prefix',
                        'Value': ''
                    }, {
                        'Name': 'Suffix',
                        'Value': ''
                    }]
                }
            }
        }
        client = MagicMock()
        client.get_bucket_notification_configuration.return_value = {
            'LambdaFunctionConfigurations': [api_config]
        }
        bucket = AmazonBucket(client, 'test-bucket')
        config = Config.from_params(**{
            'event_name': 'test-id',
            'lambda_function_arn': 'lambda_arn',
            'lambda_version': 1,
            'events': [],
            'prefix': '',
            'suffix': ''
        })
        bucket.delete_config(config)
        assert client.get_bucket_notification_configuration.call_count == 1
        assert client.put_bucket_notification_configuration.call_count == 1
        client.put_bucket_notification_configuration.assert_called_with(
            Bucket='test-bucket',
            NotificationConfiguration={'LambdaFunctionConfigurations': []}
        )


class TestConfig:
    def test_config_from_params(self):
        config = Config({
            'Id': 'test-id',
            'LambdaFunctionArn': 'test-arn:10',
            'Events': [],
            'Filter': {
                'Key': {
                    'FilterRules': [{
                        'Name': 'Prefix',
                        'Value': ''
                    }, {
                        'Name': 'Suffix',
                        'Value': ''
                    }]
                }
            }
        })
        config_from_params = Config.from_params(**{
            'event_name': 'test-id',
            'lambda_function_arn': 'test-arn',
            'lambda_version': 10,
            'events': [],
            'prefix': '',
            'suffix': ''
        })
        assert config.raw == config_from_params.raw
        assert config == config_from_params


class TestModule(ModuleTestCase):
    def test_module_fail_when_required_args_missing(self):
        with pytest.raises(AnsibleFailJson):
            set_module_args({})
            s3_bucket_notification.main()

    @patch('ansible.modules.cloud.amazon.s3_bucket_notification.AnsibleAWSModule.client')
    def test_add_s3_bucket_notification(self, aws_client):
        aws_client.return_value.get_bucket_notification_configuration.return_value = {
            'LambdaFunctionConfigurations': []
        }
        set_module_args({
            'region': 'us-east-2',
            'lambda_function_arn': 'test-lambda-arn',
            'bucket_name': 'test-lambda',
            'event_name': 'test-id',
            'events': ['s3:ObjectCreated:*', 's3:ObjectRemoved:*'],
            'state': 'present',
            'prefix': '/images',
            'suffix': '.jpg'
        })
        with pytest.raises(AnsibleExitJson) as context:
            s3_bucket_notification.main()
        result = context.value.args[0]
        assert result['changed'] is True
        assert aws_client.return_value.get_bucket_notification_configuration.call_count == 1
        aws_client.return_value.put_bucket_notification_configuration.assert_called_with(
            Bucket='test-lambda',
            NotificationConfiguration={
                'LambdaFunctionConfigurations': [{
                    'Id': 'test-id',
                    'LambdaFunctionArn': 'test-lambda-arn',
                    'Events': ['s3:ObjectCreated:*', 's3:ObjectRemoved:*'],
                    'Filter': {
                        'Key': {
                            'FilterRules': [{
                                'Name': 'Prefix',
                                'Value': '/images'
                            }, {
                                'Name': 'Suffix',
                                'Value': '.jpg'
                            }]
                        }
                    }
                }]
            })
