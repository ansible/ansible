# (c) 2019 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import pytest

from ansible.module_utils.hetzner import BASE_URL
from ansible.modules.net_tools import hetzner_firewall_info
from .test_hetzner_firewall import FetchUrlCall, run_module_success, run_module_failed


# Tests for state (absent and present)


def test_absent(mocker):
    result = run_module_success(mocker, hetzner_firewall_info, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'disabled',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ])
    assert result['changed'] is False
    assert result['firewall']['status'] == 'disabled'
    assert result['firewall']['server_ip'] == '1.2.3.4'
    assert result['firewall']['server_number'] == 1


def test_present(mocker):
    result = run_module_success(mocker, hetzner_firewall_info, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ])
    assert result['changed'] is False
    assert result['firewall']['status'] == 'active'
    assert result['firewall']['server_ip'] == '1.2.3.4'
    assert result['firewall']['server_number'] == 1
    assert len(result['firewall']['rules']['input']) == 0


def test_present_w_rules(mocker):
    result = run_module_success(mocker, hetzner_firewall_info, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [
                        {
                            'name': 'Accept HTTPS traffic',
                            'ip_version': 'ipv4',
                            'dst_ip': None,
                            'dst_port': '443',
                            'src_ip': None,
                            'src_port': None,
                            'protocol': 'tcp',
                            'tcp_flags': None,
                            'action': 'accept',
                        },
                        {
                            'name': None,
                            'ip_version': 'ipv4',
                            'dst_ip': None,
                            'dst_port': None,
                            'src_ip': None,
                            'src_port': None,
                            'protocol': None,
                            'tcp_flags': None,
                            'action': 'discard',
                        }
                    ],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ])
    assert result['changed'] is False
    assert result['firewall']['status'] == 'active'
    assert result['firewall']['server_ip'] == '1.2.3.4'
    assert result['firewall']['server_number'] == 1
    assert len(result['firewall']['rules']['input']) == 2
    assert result['firewall']['rules']['input'][0]['name'] == 'Accept HTTPS traffic'
    assert result['firewall']['rules']['input'][0]['dst_port'] == '443'
    assert result['firewall']['rules']['input'][0]['action'] == 'accept'
    assert result['firewall']['rules']['input'][1]['dst_port'] is None
    assert result['firewall']['rules']['input'][1]['action'] == 'discard'


# Tests for wait_for_configured in getting status


def test_wait_get(mocker):
    result = run_module_success(mocker, hetzner_firewall_info, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'wait_for_configured': True,
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'in process',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ])
    assert result['changed'] is False
    assert result['firewall']['status'] == 'active'
    assert result['firewall']['server_ip'] == '1.2.3.4'
    assert result['firewall']['server_number'] == 1


def test_wait_get_timeout(mocker):
    result = run_module_failed(mocker, hetzner_firewall_info, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'wait_for_configured': True,
        'timeout': 0,
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'in process',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'in process',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ])
    assert result['msg'] == 'Timeout while waiting for firewall to be configured.'


def test_nowait_get(mocker):
    result = run_module_success(mocker, hetzner_firewall_info, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'wait_for_configured': False,
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'in process',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ])
    assert result['changed'] is False
    assert result['firewall']['status'] == 'in process'
    assert result['firewall']['server_ip'] == '1.2.3.4'
    assert result['firewall']['server_number'] == 1
