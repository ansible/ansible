import functools

from ansible.modules.cloud.amazon import route53_zone
from units.compat import unittest
from units.compat.mock import patch, call
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args


def parameterized(params_list):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for params_map in params_list:
                params_map.update(kwargs)
                func(*args, **params_map)
        return wrapper
    return decorator


# Inline and replace with subdict.items() <= superdict.items(), when Python 2.6 compat can be dropped
def is_subdict(subdict, superdict):
    return all(superdict[k] == v for k, v in subdict.items())


@patch('ansible.module_utils.aws.core.HAS_BOTO3', new=True)
@patch.object(route53_zone.AnsibleAWSModule, 'client')
@patch.object(route53_zone.time, 'time', return_value=1)
class TestRoute53Module(ModuleTestCase):
    def test_mutually_exclusive(self, *args):
        with self.assertRaises(AnsibleFailJson) as exec_info:
            set_module_args({
                'secret_key': 'SECRET_KEY',
                'access_key': 'ACCESS_KEY',
                'region': 'eu-central-1',
                'zone': 'example.com',
                'vpc_id': 'vpc-94ccc2ff',
                'vpc_region': 'eu-central-1',
                'comment': 'foobar',
                'delegation_set_id': 'A1BCDEF2GHIJKL',
                'state': 'present',
            })
            route53_zone.main()

        self.assertEqual(
            exec_info.exception.args[0]['msg'],
            'parameters are mutually exclusive: delegation_set_id|vpc_id, delegation_set_id|vpc_region',
        )

    @parameterized([
        {
            'check_mode': False,
            'response': {
                'private_zone': False,
                'vpc_id': None,
                'vpc_region': None,
                'comment': 'foobar',
                'name': 'example.com.',
                'delegation_set_id': '',
                'zone_id': 'ZONE_ID',
            },
        },
        {
            'check_mode': True,
            'response': {
                'private_zone': False,
                'vpc_id': None,
                'vpc_region': None,
                'comment': 'foobar',
                'name': 'example.com.',
                'delegation_set_id': None,
                'zone_id': None,
            },
        }
    ])
    @patch.object(route53_zone, 'find_zones', return_value=[])
    def test_create_public_zone(self, find_zones_mock, time_mock, client_mock, check_mode, response):
        client_mock.return_value.create_hosted_zone.return_value = {
            'HostedZone': {
                'Id': '/hostedzone/ZONE_ID',
                'Name': 'example.com.',
                'Config': {
                    'Comment': 'foobar',
                    'PrivateZone': False,
                },
            },
        }

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'secret_key': 'SECRET_KEY',
                'access_key': 'ACCESS_KEY',
                'region': 'eu-central-1',
                'zone': 'example.com',
                'comment': 'foobar',
                'state': 'present',
                '_ansible_check_mode': check_mode,
            })
            route53_zone.main()

        if check_mode:
            client_mock.return_value.create_hosted_zone.assert_not_called()
        else:
            client_mock.return_value.create_hosted_zone.assert_called_once_with(**{
                'HostedZoneConfig': {
                    'Comment': 'foobar',
                    'PrivateZone': False,
                },
                'Name': 'example.com.',
                'CallerReference': 'example.com.-1',
            })

        self.assertEqual(exec_info.exception.args[0]['changed'], True)
        self.assertTrue(is_subdict(response, exec_info.exception.args[0]))

    @parameterized([
        {
            'check_mode': False,
            'response': {
                'private_zone': True,
                'vpc_id': 'vpc-1',
                'vpc_region': 'eu-central-1',
                'comment': 'foobar',
                'name': 'example.com.',
                'delegation_set_id': None,
                'zone_id': 'ZONE_ID',
            },
        },
        {
            'check_mode': True,
            'response': {
                'private_zone': True,
                'vpc_id': 'vpc-1',
                'vpc_region': 'eu-central-1',
                'comment': 'foobar',
                'name': 'example.com.',
                'delegation_set_id': None,
                'zone_id': None,
            },
        }
    ])
    @patch.object(route53_zone, 'find_zones', return_value=[])
    def test_create_private_zone(self, find_zones_mock, time_mock, client_mock, check_mode, response):
        client_mock.return_value.create_hosted_zone.return_value = {
            'HostedZone': {
                'Id': '/hostedzone/ZONE_ID',
                'Name': 'example.com.',
                'Config': {
                    'Comment': 'foobar',
                    'PrivateZone': True
                },
            },
        }

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'secret_key': 'SECRET_KEY',
                'access_key': 'ACCESS_KEY',
                'region': 'eu-central-1',
                'zone': 'example.com',
                'comment': 'foobar',
                'vpc_id': 'vpc-1',
                'vpc_region': 'eu-central-1',
                'state': 'present',
                '_ansible_check_mode': check_mode,
            })
            route53_zone.main()

        if check_mode:
            client_mock.return_value.create_hosted_zone.assert_not_called()
        else:
            client_mock.return_value.create_hosted_zone.assert_called_once_with(**{
                'HostedZoneConfig': {
                    'Comment': 'foobar',
                    'PrivateZone': True,
                },
                'Name': 'example.com.',
                'CallerReference': 'example.com.-1',
                'VPC': {
                    'VPCRegion': 'eu-central-1',
                    'VPCId': 'vpc-1',
                },
            })

        self.assertEqual(exec_info.exception.args[0]['changed'], True)
        self.assertTrue(is_subdict(response, exec_info.exception.args[0]))

    @parameterized([
        {
            'check_mode': False,
            'response': {
                'private_zone': False,
                'vpc_id': None,
                'vpc_region': None,
                'comment': 'new',
                'name': 'example.com.',
                'delegation_set_id': '',
                'zone_id': 'ZONE_ID',
            },
        },
        {
            'check_mode': True,
            'response': {
                'private_zone': False,
                'vpc_id': None,
                'vpc_region': None,
                'comment': 'new',
                'name': 'example.com.',
                'delegation_set_id': None,
                'zone_id': 'ZONE_ID',
            },
        }
    ])
    @patch.object(route53_zone, 'find_zones', return_value=[{
        'Id': '/hostedzone/ZONE_ID',
        'Name': 'example.com.',
        'Config': {'Comment': '', 'PrivateZone': False},
    }])
    def test_update_comment_public_zone(self, find_zones_mock, time_mock, client_mock, check_mode, response):
        client_mock.return_value.get_hosted_zone.return_value = {
            'HostedZone': {
                'Id': '/hostedzone/ZONE_ID',
                'Name': 'example.com.',
                'Config': {'Comment': '', 'PrivateZone': False},
            },
        }

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'secret_key': 'SECRET_KEY',
                'access_key': 'ACCESS_KEY',
                'region': 'eu-central-1',
                'zone': 'example.com',
                'comment': 'new',
                'state': 'present',
                '_ansible_check_mode': check_mode,
            })
            route53_zone.main()

        if check_mode:
            client_mock.return_value.update_hosted_zone_comment.assert_not_called()
        else:
            client_mock.return_value.update_hosted_zone_comment.assert_called_once_with(**{
                'Id': '/hostedzone/ZONE_ID',
                'Comment': 'new',
            })

        self.assertEqual(exec_info.exception.args[0]['changed'], True)
        self.assertTrue(is_subdict(response, exec_info.exception.args[0]))

    @patch.object(route53_zone, 'find_zones', return_value=[{
        'Id': '/hostedzone/Z22OU4IUOVYM30',
        'Name': 'example.com.',
        'Config': {'Comment': '', 'PrivateZone': False},
    }])
    def test_update_public_zone_no_changes(self, find_zones_mock, time_mock, client_mock):
        client_mock.return_value.get_hosted_zone.return_value = {
            'HostedZone': {
                'Id': '/hostedzone/ZONE_ID',
                'Name': 'example.com.',
                'Config': {'Comment': '', 'PrivateZone': False},
            },
        }

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'secret_key': 'SECRET_KEY',
                'access_key': 'ACCESS_KEY',
                'region': 'eu-central-1',
                'zone': 'example.com',
                'comment': '',
                'state': 'present',
            })
            route53_zone.main()

        client_mock.return_value.update_hosted_zone_comment.assert_not_called()
        self.assertEqual(exec_info.exception.args[0]['changed'], False)

    @parameterized([
        {
            'check_mode': False,
            'response': {
                'private_zone': True,
                'vpc_id': 'vpc-1',
                'vpc_region': 'eu-central-1',
                'comment': 'new',
                'name': 'example.com.',
                'delegation_set_id': None,
                'zone_id': 'ZONE_ID',
            },
        },
        {
            'check_mode': True,
            'response': {
                'private_zone': True,
                'vpc_id': 'vpc-1',
                'vpc_region': 'eu-central-1',
                'comment': 'new',
                'name': 'example.com.',
                'delegation_set_id': None,
                'zone_id': 'ZONE_ID',
            },
        }
    ])
    @patch.object(route53_zone, 'find_zones', return_value=[{
        'Id': '/hostedzone/ZONE_ID',
        'Name': 'example.com.',
        'Config': {'Comment': 'foobar', 'PrivateZone': True},
    }])
    def test_update_comment_private_zone(self, find_zones_mock, time_mock, client_mock, check_mode, response):
        client_mock.return_value.get_hosted_zone.return_value = {
            'HostedZone': {
                'Id': '/hostedzone/ZONE_ID',
                'Name': 'example.com.',
                'Config': {'Comment': 'foobar', 'PrivateZone': True},
            },
            'VPCs': [{'VPCRegion': 'eu-central-1', 'VPCId': 'vpc-1'}],
        }

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'secret_key': 'SECRET_KEY',
                'access_key': 'ACCESS_KEY',
                'region': 'eu-central-1',
                'zone': 'example.com',
                'comment': 'new',
                'vpc_id': 'vpc-1',
                'vpc_region': 'eu-central-1',
                'state': 'present',
                '_ansible_check_mode': check_mode,
            })
            route53_zone.main()

        if check_mode:
            client_mock.return_value.update_hosted_zone_comment.assert_not_called()
        else:
            client_mock.return_value.update_hosted_zone_comment.assert_called_once_with(**{
                'Id': '/hostedzone/ZONE_ID',
                'Comment': 'new',
            })

        self.assertEqual(exec_info.exception.args[0]['changed'], True)
        self.assertTrue(is_subdict(response, exec_info.exception.args[0]))

    @parameterized([
        {
            'check_mode': False,
            'response': {
                'private_zone': True,
                'vpc_id': 'vpc-2',
                'vpc_region': 'us-east-2',
                'comment': 'foobar',
                'name': 'example.com.',
                'delegation_set_id': None,
                'zone_id': 'ZONE_ID_2',
            },
        },
        {
            'check_mode': True,
            'response': {
                'private_zone': True,
                'vpc_id': 'vpc-2',
                'vpc_region': 'us-east-2',
                'comment': 'foobar',
                'name': 'example.com.',
                'delegation_set_id': None,
                'zone_id': None,
            },
        }
    ])
    @patch.object(route53_zone, 'find_zones', return_value=[{
        'Id': '/hostedzone/ZONE_ID',
        'Name': 'example.com.',
        'Config': {'Comment': 'foobar', 'PrivateZone': True},
    }])
    def test_update_vpc_private_zone(self, find_zones_mock, time_mock, client_mock, check_mode, response):
        client_mock.return_value.get_hosted_zone.return_value = {
            'HostedZone': {
                'Id': '/hostedzone/ZONE_ID',
                'Name': 'example.com.',
                'Config': {'Comment': 'foobar', 'PrivateZone': True},
            },
            'VPCs': [{'VPCRegion': 'eu-central-1', 'VPCId': 'vpc-1'}],
        }
        client_mock.return_value.create_hosted_zone.return_value = {
            'HostedZone': {
                'Id': '/hostedzone/ZONE_ID_2',
                'Name': 'example.com.',
                'Config': {
                    'Comment': 'foobar',
                    'PrivateZone': True
                },
            },
        }

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'secret_key': 'SECRET_KEY',
                'access_key': 'ACCESS_KEY',
                'region': 'us-east-2',
                'zone': 'example.com',
                'comment': 'foobar',
                'vpc_id': 'vpc-2',
                'vpc_region': 'us-east-2',
                'state': 'present',
                '_ansible_check_mode': check_mode,
            })
            route53_zone.main()

        if check_mode:
            client_mock.return_value.create_hosted_zone.assert_not_called()
        else:
            client_mock.return_value.create_hosted_zone.assert_called_once_with(**{
                'HostedZoneConfig': {
                    'Comment': 'foobar',
                    'PrivateZone': True,
                },
                'Name': 'example.com.',
                'CallerReference': 'example.com.-1',
                'VPC': {
                    'VPCRegion': 'us-east-2',
                    'VPCId': 'vpc-2',
                },
            })

        self.assertEqual(exec_info.exception.args[0]['changed'], True)
        self.assertTrue(is_subdict(response, exec_info.exception.args[0]))

    @patch.object(route53_zone, 'find_zones', return_value=[{
        'Id': '/hostedzone/ZONE_ID',
        'Name': 'example.com.',
        'Config': {'Comment': 'foobar', 'PrivateZone': True},
    }])
    def test_update_private_zone_no_changes(self, find_zones_mock, time_mock, client_mock):
        client_mock.return_value.get_hosted_zone.return_value = {
            'HostedZone': {
                'Id': '/hostedzone/ZONE_ID',
                'Name': 'example.com.',
                'Config': {'Comment': 'foobar', 'PrivateZone': True},
            },
            'VPCs': [{'VPCRegion': 'eu-central-1', 'VPCId': 'vpc-1'}],
        }

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'secret_key': 'SECRET_KEY',
                'access_key': 'ACCESS_KEY',
                'region': 'eu-central-1',
                'zone': 'example.com',
                'comment': 'foobar',
                'vpc_id': 'vpc-1',
                'vpc_region': 'eu-central-1',
                'state': 'present',
            })
            route53_zone.main()

        client_mock.return_value.update_hosted_zone_comment.assert_not_called()
        self.assertEqual(exec_info.exception.args[0]['changed'], False)

        response = {
            'private_zone': True,
            'vpc_id': 'vpc-1',
            'vpc_region': 'eu-central-1',
            'comment': 'foobar',
            'name': 'example.com.',
            'delegation_set_id': None,
            'zone_id': 'ZONE_ID',
        }
        self.assertTrue(is_subdict(response, exec_info.exception.args[0]))

    @parameterized([
        {'check_mode': False},
        {'check_mode': True}
    ])
    @patch.object(route53_zone, 'find_zones', return_value=[{
        'Id': '/hostedzone/ZONE_ID',
        'Name': 'example.com.',
        'Config': {'Comment': '', 'PrivateZone': False},
    }])
    def test_delete_public_zone(self, find_zones_mock, time_mock, client_mock, check_mode):
        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'secret_key': 'SECRET_KEY',
                'access_key': 'ACCESS_KEY',
                'region': 'eu-central-1',
                'zone': 'example.com',
                'state': 'absent',
                '_ansible_check_mode': check_mode,
            })
            route53_zone.main()

        if check_mode:
            client_mock.return_value.delete_hosted_zone.assert_not_called()
        else:
            client_mock.return_value.delete_hosted_zone.assert_called_once_with(**{
                'Id': '/hostedzone/ZONE_ID',
            })

        self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @parameterized([
        {'check_mode': False},
        {'check_mode': True}
    ])
    @patch.object(route53_zone, 'find_zones', return_value=[{
        'Id': '/hostedzone/ZONE_ID',
        'Name': 'example.com.',
        'Config': {'Comment': 'foobar', 'PrivateZone': True},
    }])
    def test_delete_private_zone(self, find_zones_mock, time_mock, client_mock, check_mode):
        client_mock.return_value.get_hosted_zone.return_value = {
            'HostedZone': {
                'Id': '/hostedzone/ZONE_ID',
                'Name': 'example.com.',
                'Config': {'Comment': 'foobar', 'PrivateZone': True},
            },
            'VPCs': [{'VPCRegion': 'eu-central-1', 'VPCId': 'vpc-1'}],
        }

        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'secret_key': 'SECRET_KEY',
                'access_key': 'ACCESS_KEY',
                'region': 'eu-central-1',
                'zone': 'example.com',
                'vpc_id': 'vpc-1',
                'vpc_region': 'eu-central-1',
                'state': 'absent',
                '_ansible_check_mode': check_mode,
            })
            route53_zone.main()

        if check_mode:
            client_mock.return_value.delete_hosted_zone.assert_not_called()
        else:
            client_mock.return_value.delete_hosted_zone.assert_called_once_with(**{
                'Id': '/hostedzone/ZONE_ID',
            })

        self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @parameterized([
        {'check_mode': False},
        {'check_mode': True}
    ])
    @parameterized([
        {
            'hosted_zone_id': 'PRIVATE_ZONE_ID',
            'call_params': [call(**{
                'Id': 'PRIVATE_ZONE_ID',
            })],
        }, {
            'hosted_zone_id': 'all',
            'call_params': [call(**{
                'Id': '/hostedzone/PUBLIC_ZONE_ID',
            }), call(**{
                'Id': '/hostedzone/PRIVATE_ZONE_ID',
            })],
        }
    ])
    @patch.object(route53_zone, 'find_zones', return_value=[{
        'Id': '/hostedzone/PUBLIC_ZONE_ID',
        'Name': 'example.com.',
        'Config': {'Comment': '', 'PrivateZone': False},
    }, {
        'Id': '/hostedzone/PRIVATE_ZONE_ID',
        'Name': 'example.com.',
        'Config': {'Comment': 'foobar', 'PrivateZone': True},
    }])
    def test_delete_by_zone_id(self, find_zones_mock, time_mock, client_mock, hosted_zone_id, call_params, check_mode):
        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'secret_key': 'SECRET_KEY',
                'access_key': 'ACCESS_KEY',
                'region': 'eu-central-1',
                'zone': 'example.com',
                'hosted_zone_id': hosted_zone_id,
                'state': 'absent',
                '_ansible_check_mode': check_mode,
            })
            route53_zone.main()

        if check_mode:
            client_mock.return_value.delete_hosted_zone.assert_not_called()
        else:
            client_mock.return_value.delete_hosted_zone.assert_has_calls(call_params)

        self.assertEqual(exec_info.exception.args[0]['changed'], True)

    @patch.object(route53_zone, 'find_zones', return_value=[])
    def test_delete_absent_zone(self, find_zones_mock, time_mock, client_mock):
        with self.assertRaises(AnsibleExitJson) as exec_info:
            set_module_args({
                'secret_key': 'SECRET_KEY',
                'access_key': 'ACCESS_KEY',
                'region': 'eu-central-1',
                'zone': 'example.com',
                'state': 'absent',
            })
            route53_zone.main()

        client_mock.return_value.delete_hosted_zone.assert_not_called()
        self.assertEqual(exec_info.exception.args[0]['changed'], False)


if __name__ == '__main__':
    unittest.main()
