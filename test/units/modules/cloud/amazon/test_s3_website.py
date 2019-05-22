import functools

from ansible.modules.cloud.amazon import s3_website
from units.compat import unittest
from units.compat.mock import patch, MagicMock
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args


def boto3_conn_wrapper(client_connection_mock, resource_connection_mock):
    def boto3_conn(module, conn_type=None, *args, **kwargs):
        if conn_type == 'resource':
            return resource_connection_mock
        else:
            return client_connection_mock

    return boto3_conn


def parameterized(params_list):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for params_map in params_list:
                params_map.update(kwargs)
                func(*args, **params_map)
        return wrapper
    return decorator


@patch.object(s3_website, 'HAS_BOTO3', new=True)
class TestS3WebsiteModule(ModuleTestCase):
    def test_mutually_exclusive(self, *args):
        with self.assertRaises(AnsibleFailJson) as exec_info:
            set_module_args({
                'secret_key': 'SECRET_KEY',
                'access_key': 'ACCESS_KEY',
                'region': 'eu-central-1',
                'name': 'bucket_name',
                'suffix': 'home.htm',
                'error_key': 'errors/404.htm',
                'redirect_all_requests': 'https://example.com',
                'state': 'present',
            })
            s3_website.main()

        self.assertEqual(
            exec_info.exception.args[0]['msg'],
            'parameters are mutually exclusive: redirect_all_requests|suffix, redirect_all_requests|error_key',
        )

    @parameterized([
        {
            'module_args': {},
            'bucket_website': {'IndexDocument': {'Suffix': 'index.html'}},
            'response': {'index_document': {'suffix': 'index.html'}},
        }, {
            'module_args': {'suffix': 'home.htm', 'error_key': 'errors/404.htm'},
            'bucket_website': {'IndexDocument': {'Suffix': 'home.htm'}, 'ErrorDocument': {'Key': 'errors/404.htm'}},
            'response': {'index_document': {'suffix': 'home.htm'}, 'error_document': {'key': 'errors/404.htm'}},
        }, {
            'module_args': {'redirect_all_requests': 'https://example.com'},
            'bucket_website': {'RedirectAllRequestsTo': {'Protocol': 'https', 'HostName': 'example.com'}},
            'response': {'redirect_all_requests_to': {'protocol': 'https', 'host_name': 'example.com'}},
        },
    ])
    @patch.object(s3_website, 'get_aws_connection_info', return_value=('eu-central-1', None, {}))
    def test_enable_website(self, *args, **kwargs):
        module_args, bucket_website, response = map(kwargs.get, ('module_args', 'bucket_website', 'response'))
        client_connection_mock = MagicMock(get_bucket_website=MagicMock(side_effect=[None, bucket_website]))

        bucket_website_mock = MagicMock()
        resource_connection_mock = MagicMock(
            BucketWebsite=MagicMock(return_value=bucket_website_mock)
        )

        with patch.object(s3_website, 'boto3_conn', side_effect=boto3_conn_wrapper(client_connection_mock, resource_connection_mock)):
            with self.assertRaises(AnsibleExitJson) as exec_info:
                module_args.update({
                    'secret_key': 'SECRET_KEY',
                    'access_key': 'ACCESS_KEY',
                    'region': 'eu-central-1',
                    'name': 'bucket_name',
                    'state': 'present',
                })
                set_module_args(module_args)
                s3_website.main()

            bucket_website_mock.put.assert_called_once_with(WebsiteConfiguration=bucket_website)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)
            # When Python 2.6 support can be dropped, simply assert response.items() <= exec_info.exception.args[0].items()
            self.assertTrue(all(exec_info.exception.args[0][k] == v for k, v in response.items()))

    @patch.object(s3_website, 'get_aws_connection_info', return_value=('eu-central-1', None, {}))
    def test_enable_website_check_mode(self, *args):
        client_connection_mock = MagicMock(get_bucket_website=MagicMock(return_value=None))

        bucket_website_mock = MagicMock()
        resource_connection_mock = MagicMock(
            BucketWebsite=MagicMock(return_value=bucket_website_mock)
        )

        with patch.object(s3_website, 'boto3_conn', side_effect=boto3_conn_wrapper(client_connection_mock, resource_connection_mock)):
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'secret_key': 'SECRET_KEY',
                    'access_key': 'ACCESS_KEY',
                    'region': 'eu-central-1',
                    'name': 'bucket_name',
                    'state': 'present',
                    '_ansible_check_mode': True,
                })
                s3_website.main()

            bucket_website_mock.put.assert_not_called()
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @parameterized([
        {
            'bucket_website': {'IndexDocument': {'Suffix': 'index.html'}},
            'module_args': {'suffix': 'home.htm'},
            'call_params': {'IndexDocument': {'Suffix': 'home.htm'}},
        }, {
            'bucket_website': {'IndexDocument': {'Suffix': 'index.html'}, 'ErrorDocument': {'Key': 'not_found.htm'}},
            'module_args': {'error_key': 'errors/404.htm'},
            'call_params': {'IndexDocument': {'Suffix': 'index.html'}, 'ErrorDocument': {'Key': 'errors/404.htm'}},
        }, {
            'bucket_website': {'RedirectAllRequestsTo': {'HostName': 'abc.com'}},
            'module_args': {'redirect_all_requests': 'https://example.com'},
            'call_params': {'RedirectAllRequestsTo': {'Protocol': 'https', 'HostName': 'example.com'}},
        },
    ])
    @patch.object(s3_website, 'get_aws_connection_info', return_value=('eu-central-1', None, {}))
    def test_update_website(self, *args, **kwargs):
        module_args, bucket_website, call_params = map(kwargs.get, ('module_args', 'bucket_website', 'call_params'))
        client_connection_mock = MagicMock(get_bucket_website=MagicMock(return_value=bucket_website))

        bucket_website_mock = MagicMock()
        resource_connection_mock = MagicMock(
            BucketWebsite=MagicMock(return_value=bucket_website_mock)
        )

        with patch.object(s3_website, 'boto3_conn', side_effect=boto3_conn_wrapper(client_connection_mock, resource_connection_mock)):
            with self.assertRaises(AnsibleExitJson) as exec_info:
                module_args.update({
                    'secret_key': 'SECRET_KEY',
                    'access_key': 'ACCESS_KEY',
                    'region': 'eu-central-1',
                    'name': 'bucket_name',
                    'state': 'present',
                })
                set_module_args(module_args)
                s3_website.main()

            bucket_website_mock.put.assert_called_once_with(WebsiteConfiguration=call_params)
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(s3_website, 'get_aws_connection_info', return_value=('eu-central-1', None, {}))
    def test_update_website_no_changes(self, *args):
        client_connection_mock = MagicMock(get_bucket_website=MagicMock(return_value={
            'IndexDocument': {
                'Suffix': 'index.html',
            },
            'ErrorDocument': {
                'Key': 'errors/404.htm',
            },
        }))

        bucket_website_mock = MagicMock()
        resource_connection_mock = MagicMock(
            BucketWebsite=MagicMock(return_value=bucket_website_mock)
        )

        with patch.object(s3_website, 'boto3_conn', side_effect=boto3_conn_wrapper(client_connection_mock, resource_connection_mock)):
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'secret_key': 'SECRET_KEY',
                    'access_key': 'ACCESS_KEY',
                    'region': 'eu-central-1',
                    'name': 'bucket_name',
                    'suffix': 'index.html',
                    'error_key': 'errors/404.htm',
                    'state': 'present',
                })
                s3_website.main()

            bucket_website_mock.put.assert_not_called()
            self.assertEqual(exec_info.exception.args[0]['changed'], False)

    @patch.object(s3_website, 'get_aws_connection_info', return_value=('eu-central-1', None, {}))
    def test_update_website_check_mode(self, *args):
        client_connection_mock = MagicMock(get_bucket_website=MagicMock(return_value={
            'IndexDocument': {
                'Suffix': 'index.html',
            }
        }))

        bucket_website_mock = MagicMock()
        resource_connection_mock = MagicMock(
            BucketWebsite=MagicMock(return_value=bucket_website_mock)
        )

        with patch.object(s3_website, 'boto3_conn', side_effect=boto3_conn_wrapper(client_connection_mock, resource_connection_mock)):
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'secret_key': 'SECRET_KEY',
                    'access_key': 'ACCESS_KEY',
                    'region': 'eu-central-1',
                    'name': 'bucket_name',
                    'suffix': 'home.htm',
                    'state': 'present',
                    '_ansible_check_mode': True,
                })
                s3_website.main()

            bucket_website_mock.put.assert_not_called()
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(s3_website, 'get_aws_connection_info', return_value=('eu-central-1', None, {}))
    def test_disable_website(self, *args):
        client_connection_mock = MagicMock()

        with patch.object(s3_website, 'boto3_conn', side_effect=boto3_conn_wrapper(client_connection_mock, None)):
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'secret_key': 'SECRET_KEY',
                    'access_key': 'ACCESS_KEY',
                    'region': 'eu-central-1',
                    'name': 'bucket_name',
                    'state': 'absent',
                })
                s3_website.main()

            client_connection_mock.delete_bucket_website.assert_called_once_with(Bucket='bucket_name')
            self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(s3_website, 'get_aws_connection_info', return_value=('eu-central-1', None, {}))
    def test_disable_website_check_mode(self, *args):
        client_connection_mock = MagicMock()

        with patch.object(s3_website, 'boto3_conn', side_effect=boto3_conn_wrapper(client_connection_mock, None)):
            with self.assertRaises(AnsibleExitJson) as exec_info:
                set_module_args({
                    'secret_key': 'SECRET_KEY',
                    'access_key': 'ACCESS_KEY',
                    'region': 'eu-central-1',
                    'name': 'bucket_name',
                    'state': 'absent',
                    '_ansible_check_mode': True,
                })
                s3_website.main()

            client_connection_mock.delete_bucket_website.assert_not_called()
            self.assertEqual(exec_info.exception.args[0]['changed'], True)


if __name__ == '__main__':
    unittest.main()
