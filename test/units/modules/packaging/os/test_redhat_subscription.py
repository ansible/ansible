# Author: Jiri Hnidek (jhnidek@redhat.com)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from ansible.module_utils import basic
from ansible.modules.packaging.os import redhat_subscription

import pytest

TESTED_MODULE = redhat_subscription.__name__


@pytest.fixture
def patch_redhat_subscription(mocker):
    """
    Function used for mocking some parts of redhat_subscribtion module
    """
    mocker.patch('ansible.modules.packaging.os.redhat_subscription.RegistrationBase.REDHAT_REPO')
    mocker.patch('ansible.modules.packaging.os.redhat_subscription.isfile', return_value=False)
    mocker.patch('ansible.modules.packaging.os.redhat_subscription.unlink', return_value=True)
    mocker.patch('ansible.modules.packaging.os.redhat_subscription.AnsibleModule.get_bin_path',
                 return_value='/testbin/subscription-manager')


@pytest.mark.parametrize('patch_ansible_module', [{}], indirect=['patch_ansible_module'])
@pytest.mark.usefixtures('patch_ansible_module')
def test_without_required_parameters(capfd, patch_redhat_subscription):
    """
    Failure must occurs when all parameters are missing
    """
    with pytest.raises(SystemExit):
        redhat_subscription.main()
    out, err = capfd.readouterr()
    results = json.loads(out)
    assert results['failed']
    assert 'state is present but any of the following are missing' in results['msg']


TEST_CASES = [
    # Test the case, when the system is already registered
    [
        {
            'state': 'present',
            'server_hostname': 'subscription.rhsm.redhat.com',
            'username': 'admin',
            'password': 'admin',
            'org_id': 'admin'
        },
        {
            'id': 'test_already_registered_system',
            'run_command.calls': [
                (
                    # Calling of following command will be asserted
                    ['/testbin/subscription-manager', 'identity'],
                    # Was return code checked?
                    {'check_rc': False},
                    # Mock of returned code, stdout and stderr
                    (0, 'system identity: b26df632-25ed-4452-8f89-0308bfd167cb', '')
                )
            ],
            'changed': False,
            'msg': 'System already registered.'
        }
    ],
    # Test simple registration using username and password
    [
        {
            'state': 'present',
            'server_hostname': 'satellite.company.com',
            'username': 'admin',
            'password': 'admin',
        },
        {
            'id': 'test_registeration_username_password',
            'run_command.calls': [
                (
                    ['/testbin/subscription-manager', 'identity'],
                    {'check_rc': False},
                    (1, '', '')
                ),
                (
                    ['/testbin/subscription-manager', 'config', '--server.hostname=satellite.company.com'],
                    {'check_rc': True},
                    (0, '', '')
                ),
                (
                    ['/testbin/subscription-manager', 'register',
                        '--serverurl', 'satellite.company.com',
                        '--username', 'admin',
                        '--password', 'admin'],
                    {'check_rc': True, 'expand_user_and_vars': False},
                    (0, '', '')
                )
            ],
            'changed': True,
            'msg': "System successfully registered to 'satellite.company.com'."
        }
    ],
    # Test unregistration, when system is unregistered
    [
        {
            'state': 'absent',
            'server_hostname': 'subscription.rhsm.redhat.com',
            'username': 'admin',
            'password': 'admin',
        },
        {
            'id': 'test_unregisteration',
            'run_command.calls': [
                (
                    ['/testbin/subscription-manager', 'identity'],
                    {'check_rc': False},
                    (0, 'system identity: b26df632-25ed-4452-8f89-0308bfd167cb', '')
                ),
                (
                    ['/testbin/subscription-manager', 'unsubscribe', '--all'],
                    {'check_rc': True},
                    (0, '', '')
                ),
                (
                    ['/testbin/subscription-manager', 'unregister'],
                    {'check_rc': True},
                    (0, '', '')
                )
            ],
            'changed': True,
            'msg': "System successfully unregistered from subscription.rhsm.redhat.com."
        }
    ],
    # Test unregistration of already unregistered system
    [
        {
            'state': 'absent',
            'server_hostname': 'subscription.rhsm.redhat.com',
            'username': 'admin',
            'password': 'admin',
        },
        {
            'id': 'test_unregisteration_of_unregistered_system',
            'run_command.calls': [
                (
                    ['/testbin/subscription-manager', 'identity'],
                    {'check_rc': False},
                    (1, 'This system is not yet registered.', '')
                )
            ],
            'changed': False,
            'msg': "System already unregistered."
        }
    ],
    # Test registration using activation key
    [
        {
            'state': 'present',
            'server_hostname': 'satellite.company.com',
            'activationkey': 'some-activation-key',
            'org_id': 'admin'
        },
        {
            'id': 'test_registeration_activation_key',
            'run_command.calls': [
                (
                    ['/testbin/subscription-manager', 'identity'],
                    {'check_rc': False},
                    (1, 'This system is not yet registered.', '')
                ),
                (
                    ['/testbin/subscription-manager', 'config', '--server.hostname=satellite.company.com'],
                    {'check_rc': True},
                    (0, '', '')
                ),
                (
                    [
                        '/testbin/subscription-manager',
                        'register',
                        '--serverurl', 'satellite.company.com',
                        '--org', 'admin',
                        '--activationkey', 'some-activation-key'
                    ],
                    {'check_rc': True, 'expand_user_and_vars': False},
                    (0, '', '')
                )
            ],
            'changed': True,
            'msg': "System successfully registered to 'satellite.company.com'."
        }
    ],
    # Test of registration using username and password with auto-attach option
    [
        {
            'state': 'present',
            'username': 'admin',
            'password': 'admin',
            'org_id': 'admin',
            'auto_attach': 'true'
        },
        {
            'id': 'test_registeration_username_password_auto_attach',
            'run_command.calls': [
                (
                    ['/testbin/subscription-manager', 'identity'],
                    {'check_rc': False},
                    (1, 'This system is not yet registered.', '')
                ),
                (
                    [
                        '/testbin/subscription-manager',
                        'register',
                        '--org', 'admin',
                        '--auto-attach',
                        '--username', 'admin',
                        '--password', 'admin'
                    ],
                    {'check_rc': True, 'expand_user_and_vars': False},
                    (0, '', '')
                )
            ],
            'changed': True,
            'msg': "System successfully registered to 'None'."
        }
    ],
    # Test of force registration despite the system is already registered
    [
        {
            'state': 'present',
            'username': 'admin',
            'password': 'admin',
            'org_id': 'admin',
            'force_register': 'true'
        },
        {
            'id': 'test_force_registeration_username_password',
            'run_command.calls': [
                (
                    ['/testbin/subscription-manager', 'identity'],
                    {'check_rc': False},
                    (0, 'This system already registered.', '')
                ),
                (
                    [
                        '/testbin/subscription-manager',
                        'register',
                        '--force',
                        '--org', 'admin',
                        '--username', 'admin',
                        '--password', 'admin'
                    ],
                    {'check_rc': True, 'expand_user_and_vars': False},
                    (0, '', '')
                )
            ],
            'changed': True,
            'msg': "System successfully registered to 'None'."
        }
    ],
    # Test of registration using username, password and proxy options
    [
        {
            'state': 'present',
            'username': 'admin',
            'password': 'admin',
            'org_id': 'admin',
            'force_register': 'true',
            'server_proxy_hostname': 'proxy.company.com',
            'server_proxy_port': '12345',
            'server_proxy_user': 'proxy_user',
            'server_proxy_password': 'secret_proxy_password'
        },
        {
            'id': 'test_registeration_username_password_proxy_options',
            'run_command.calls': [
                (
                    ['/testbin/subscription-manager', 'identity'],
                    {'check_rc': False},
                    (0, 'This system already registered.', '')
                ),
                (
                    [
                        '/testbin/subscription-manager',
                        'config',
                        '--server.proxy_hostname=proxy.company.com',
                        '--server.proxy_password=secret_proxy_password',
                        '--server.proxy_port=12345',
                        '--server.proxy_user=proxy_user'
                    ],
                    {'check_rc': True},
                    (0, '', '')
                ),
                (
                    [
                        '/testbin/subscription-manager',
                        'register',
                        '--force',
                        '--org', 'admin',
                        '--proxy', 'proxy.company.com:12345',
                        '--proxyuser', 'proxy_user',
                        '--proxypassword', 'secret_proxy_password',
                        '--username', 'admin',
                        '--password', 'admin'
                    ],
                    {'check_rc': True, 'expand_user_and_vars': False},
                    (0, '', '')
                )
            ],
            'changed': True,
            'msg': "System successfully registered to 'None'."
        }
    ],
    # Test of registration using username and password and attach to pool
    [
        {
            'state': 'present',
            'username': 'admin',
            'password': 'admin',
            'org_id': 'admin',
            'pool': 'ff8080816b8e967f016b8e99632804a6'
        },
        {
            'id': 'test_registeration_username_password_pool',
            'run_command.calls': [
                (
                    ['/testbin/subscription-manager', 'identity'],
                    {'check_rc': False},
                    (1, 'This system is not yet registered.', '')
                ),
                (
                    [
                        '/testbin/subscription-manager',
                        'register',
                        '--org', 'admin',
                        '--username', 'admin',
                        '--password', 'admin'
                    ],
                    {'check_rc': True, 'expand_user_and_vars': False},
                    (0, '', '')
                ),
                (
                    [
                        'subscription-manager list --available',
                        {'check_rc': True, 'environ_update': {'LANG': 'C', 'LC_ALL': 'C', 'LC_MESSAGES': 'C'}},
                        (0,
                         '''
+-------------------------------------------+
    Available Subscriptions
+-------------------------------------------+
Subscription Name:   SP Server Premium (S: Premium, U: Production, R: SP Server)
Provides:            SP Server Bits
SKU:                 sp-server-prem-prod
Contract:            0
Pool ID:             ff8080816b8e967f016b8e99632804a6
Provides Management: Yes
Available:           5
Suggested:           1
Service Type:        L1-L3
Roles:               SP Server
Service Level:       Premium
Usage:               Production
Add-ons:
Subscription Type:   Standard
Starts:              06/25/19
Ends:                06/24/20
Entitlement Type:    Physical
''', ''),
                    ]
                ),
                (
                    'subscription-manager attach --pool ff8080816b8e967f016b8e99632804a6',
                    {'check_rc': True},
                    (0, '', '')
                )
            ],
            'changed': True,
            'msg': "System successfully registered to 'None'."
        }
    ],
    # Test of registration using username and password and attach to pool ID and quantities
    [
        {
            'state': 'present',
            'username': 'admin',
            'password': 'admin',
            'org_id': 'admin',
            'pool_ids': [{'ff8080816b8e967f016b8e99632804a6': 2}, {'ff8080816b8e967f016b8e99747107e9': 4}]
        },
        {
            'id': 'test_registeration_username_password_pool_ids_quantities',
            'run_command.calls': [
                (
                    ['/testbin/subscription-manager', 'identity'],
                    {'check_rc': False},
                    (1, 'This system is not yet registered.', '')
                ),
                (
                    [
                        '/testbin/subscription-manager',
                        'register',
                        '--org', 'admin',
                        '--username', 'admin',
                        '--password', 'admin'
                    ],
                    {'check_rc': True, 'expand_user_and_vars': False},
                    (0, '', '')
                ),
                (
                    [
                        'subscription-manager list --available',
                        {'check_rc': True, 'environ_update': {'LANG': 'C', 'LC_ALL': 'C', 'LC_MESSAGES': 'C'}},
                        (0,
                         '''
+-------------------------------------------+
    Available Subscriptions
+-------------------------------------------+
Subscription Name:   SP Smart Management (A: ADDON1)
Provides:            SP Addon 1 bits
SKU:                 sp-with-addon-1
Contract:            1
Pool ID:             ff8080816b8e967f016b8e99747107e9
Provides Management: Yes
Available:           10
Suggested:           1
Service Type:
Roles:
Service Level:
Usage:
Add-ons:             ADDON1
Subscription Type:   Standard
Starts:              25.6.2019
Ends:                24.6.2020
Entitlement Type:    Physical

Subscription Name:   SP Server Premium (S: Premium, U: Production, R: SP Server)
Provides:            SP Server Bits
SKU:                 sp-server-prem-prod
Contract:            0
Pool ID:             ff8080816b8e967f016b8e99632804a6
Provides Management: Yes
Available:           5
Suggested:           1
Service Type:        L1-L3
Roles:               SP Server
Service Level:       Premium
Usage:               Production
Add-ons:
Subscription Type:   Standard
Starts:              06/25/19
Ends:                06/24/20
Entitlement Type:    Physical
''', '')
                    ]
                ),
                (
                    [
                        '/testbin/subscription-manager',
                        'attach',
                        '--pool', 'ff8080816b8e967f016b8e99632804a6',
                        '--quantity', '2'
                    ],
                    {'check_rc': True},
                    (0, '', '')
                ),
                (
                    [
                        '/testbin/subscription-manager',
                        'attach',
                        '--pool', 'ff8080816b8e967f016b8e99747107e9',
                        '--quantity', '4'
                    ],
                    {'check_rc': True},
                    (0, '', '')
                )
            ],
            'changed': True,
            'msg': "System successfully registered to 'None'."
        }
    ],
    # Test of registration using username and password and attach to pool ID without quantities
    [
        {
            'state': 'present',
            'username': 'admin',
            'password': 'admin',
            'org_id': 'admin',
            'pool_ids': ['ff8080816b8e967f016b8e99632804a6', 'ff8080816b8e967f016b8e99747107e9']
        },
        {
            'id': 'test_registeration_username_password_pool_ids',
            'run_command.calls': [
                (
                    ['/testbin/subscription-manager', 'identity'],
                    {'check_rc': False},
                    (1, 'This system is not yet registered.', '')
                ),
                (
                    [
                        '/testbin/subscription-manager',
                        'register',
                        '--org', 'admin',
                        '--username', 'admin',
                        '--password', 'admin'
                    ],
                    {'check_rc': True, 'expand_user_and_vars': False},
                    (0, '', '')
                ),
                (
                    [
                        'subscription-manager list --available',
                        {'check_rc': True, 'environ_update': {'LANG': 'C', 'LC_ALL': 'C', 'LC_MESSAGES': 'C'}},
                        (0,
                         '''
+-------------------------------------------+
    Available Subscriptions
+-------------------------------------------+
Subscription Name:   SP Smart Management (A: ADDON1)
Provides:            SP Addon 1 bits
SKU:                 sp-with-addon-1
Contract:            1
Pool ID:             ff8080816b8e967f016b8e99747107e9
Provides Management: Yes
Available:           10
Suggested:           1
Service Type:
Roles:
Service Level:
Usage:
Add-ons:             ADDON1
Subscription Type:   Standard
Starts:              25.6.2019
Ends:                24.6.2020
Entitlement Type:    Physical

Subscription Name:   SP Server Premium (S: Premium, U: Production, R: SP Server)
Provides:            SP Server Bits
SKU:                 sp-server-prem-prod
Contract:            0
Pool ID:             ff8080816b8e967f016b8e99632804a6
Provides Management: Yes
Available:           5
Suggested:           1
Service Type:        L1-L3
Roles:               SP Server
Service Level:       Premium
Usage:               Production
Add-ons:
Subscription Type:   Standard
Starts:              06/25/19
Ends:                06/24/20
Entitlement Type:    Physical
''', '')
                    ]
                ),
                (
                    [
                        '/testbin/subscription-manager',
                        'attach',
                        '--pool', 'ff8080816b8e967f016b8e99632804a6'
                    ],
                    {'check_rc': True},
                    (0, '', '')
                ),
                (
                    [
                        '/testbin/subscription-manager',
                        'attach',
                        '--pool', 'ff8080816b8e967f016b8e99747107e9'
                    ],
                    {'check_rc': True},
                    (0, '', '')
                )
            ],
            'changed': True,
            'msg': "System successfully registered to 'None'."
        }
    ],
    # Test of registration using username and password and attach to pool ID (one pool)
    [
        {
            'state': 'present',
            'username': 'admin',
            'password': 'admin',
            'org_id': 'admin',
            'pool_ids': ['ff8080816b8e967f016b8e99632804a6']
        },
        {
            'id': 'test_registeration_username_password_one_pool_id',
            'run_command.calls': [
                (
                    ['/testbin/subscription-manager', 'identity'],
                    {'check_rc': False},
                    (1, 'This system is not yet registered.', '')
                ),
                (
                    [
                        '/testbin/subscription-manager',
                        'register',
                        '--org', 'admin',
                        '--username', 'admin',
                        '--password', 'admin'
                    ],
                    {'check_rc': True, 'expand_user_and_vars': False},
                    (0, '', '')
                ),
                (
                    [
                        'subscription-manager list --available',
                        {'check_rc': True, 'environ_update': {'LANG': 'C', 'LC_ALL': 'C', 'LC_MESSAGES': 'C'}},
                        (0,
                         '''
+-------------------------------------------+
    Available Subscriptions
+-------------------------------------------+
Subscription Name:   SP Smart Management (A: ADDON1)
Provides:            SP Addon 1 bits
SKU:                 sp-with-addon-1
Contract:            1
Pool ID:             ff8080816b8e967f016b8e99747107e9
Provides Management: Yes
Available:           10
Suggested:           1
Service Type:
Roles:
Service Level:
Usage:
Add-ons:             ADDON1
Subscription Type:   Standard
Starts:              25.6.2019
Ends:                24.6.2020
Entitlement Type:    Physical

Subscription Name:   SP Server Premium (S: Premium, U: Production, R: SP Server)
Provides:            SP Server Bits
SKU:                 sp-server-prem-prod
Contract:            0
Pool ID:             ff8080816b8e967f016b8e99632804a6
Provides Management: Yes
Available:           5
Suggested:           1
Service Type:        L1-L3
Roles:               SP Server
Service Level:       Premium
Usage:               Production
Add-ons:
Subscription Type:   Standard
Starts:              06/25/19
Ends:                06/24/20
Entitlement Type:    Physical
''', '')
                    ]
                ),
                (
                    [
                        '/testbin/subscription-manager',
                        'attach',
                        '--pool', 'ff8080816b8e967f016b8e99632804a6',
                    ],
                    {'check_rc': True},
                    (0, '', '')
                )
            ],
            'changed': True,
            'msg': "System successfully registered to 'None'."
        }
    ],
    # Test attaching different set of pool IDs
    [
        {
            'state': 'present',
            'username': 'admin',
            'password': 'admin',
            'org_id': 'admin',
            'pool_ids': [{'ff8080816b8e967f016b8e99632804a6': 2}, {'ff8080816b8e967f016b8e99747107e9': 4}]
        },
        {
            'id': 'test_attaching_different_pool_ids',
            'run_command.calls': [
                (
                    ['/testbin/subscription-manager', 'identity'],
                    {'check_rc': False},
                    (0, 'system identity: b26df632-25ed-4452-8f89-0308bfd167cb', ''),
                ),
                (
                    'subscription-manager list --consumed',
                    {'check_rc': True, 'environ_update': {'LANG': 'C', 'LC_ALL': 'C', 'LC_MESSAGES': 'C'}},
                    (0, '''
+-------------------------------------------+
   Consumed Subscriptions
+-------------------------------------------+
Subscription Name:   Multi-Attribute Stackable (4 cores, no content)
Provides:            Multi-Attribute Limited Product (no content)
SKU:                 cores4-multiattr
Contract:            1
Account:             12331131231
Serial:              7807912223970164816
Pool ID:             ff8080816b8e967f016b8e995f5103b5
Provides Management: No
Active:              True
Quantity Used:       1
Service Type:        Level 3
Roles:
Service Level:       Premium
Usage:
Add-ons:
Status Details:      Subscription is current
Subscription Type:   Stackable
Starts:              06/25/19
Ends:                06/24/20
Entitlement Type:    Physical
''', '')
                ),
                (
                    [
                        '/testbin/subscription-manager',
                        'unsubscribe',
                        '--serial=7807912223970164816',
                    ],
                    {'check_rc': True},
                    (0, '', '')
                ),
                (
                    [
                        'subscription-manager list --available',
                        {'check_rc': True, 'environ_update': {'LANG': 'C', 'LC_ALL': 'C', 'LC_MESSAGES': 'C'}},
                        (0,
                         '''
+-------------------------------------------+
    Available Subscriptions
+-------------------------------------------+
Subscription Name:   SP Smart Management (A: ADDON1)
Provides:            SP Addon 1 bits
SKU:                 sp-with-addon-1
Contract:            1
Pool ID:             ff8080816b8e967f016b8e99747107e9
Provides Management: Yes
Available:           10
Suggested:           1
Service Type:
Roles:
Service Level:
Usage:
Add-ons:             ADDON1
Subscription Type:   Standard
Starts:              25.6.2019
Ends:                24.6.2020
Entitlement Type:    Physical

Subscription Name:   SP Server Premium (S: Premium, U: Production, R: SP Server)
Provides:            SP Server Bits
SKU:                 sp-server-prem-prod
Contract:            0
Pool ID:             ff8080816b8e967f016b8e99632804a6
Provides Management: Yes
Available:           5
Suggested:           1
Service Type:        L1-L3
Roles:               SP Server
Service Level:       Premium
Usage:               Production
Add-ons:
Subscription Type:   Standard
Starts:              06/25/19
Ends:                06/24/20
Entitlement Type:    Physical

Subscription Name:   Multi-Attribute Stackable (4 cores, no content)
Provides:            Multi-Attribute Limited Product (no content)
SKU:                 cores4-multiattr
Contract:            1
Pool ID:             ff8080816b8e967f016b8e995f5103b5
Provides Management: No
Available:           10
Suggested:           1
Service Type:        Level 3
Roles:
Service Level:       Premium
Usage:
Add-ons:
Subscription Type:   Stackable
Starts:              11.7.2019
Ends:                10.7.2020
Entitlement Type:    Physical
''', '')
                    ]
                ),
                (
                    [
                        '/testbin/subscription-manager',
                        'attach',
                        '--pool', 'ff8080816b8e967f016b8e99632804a6',
                        '--quantity', '2'
                    ],
                    {'check_rc': True},
                    (0, '', '')
                ),
                (
                    [
                        '/testbin/subscription-manager',
                        'attach',
                        '--pool', 'ff8080816b8e967f016b8e99747107e9',
                        '--quantity', '4'
                    ],
                    {'check_rc': True},
                    (0, '', '')
                )
            ],
            'changed': True,
        }
    ]
]


TEST_CASES_IDS = [item[1]['id'] for item in TEST_CASES]


@pytest.mark.parametrize('patch_ansible_module, testcase', TEST_CASES, ids=TEST_CASES_IDS, indirect=['patch_ansible_module'])
@pytest.mark.usefixtures('patch_ansible_module')
def test_redhat_subscribtion(mocker, capfd, patch_redhat_subscription, testcase):
    """
    Run unit tests for test cases listen in TEST_CASES
    """

    # Mock function used for running commands first
    call_results = [item[2] for item in testcase['run_command.calls']]
    mock_run_command = mocker.patch.object(
        basic.AnsibleModule,
        'run_command',
        side_effect=call_results)

    # Try to run test case
    with pytest.raises(SystemExit):
        redhat_subscription.main()

    out, err = capfd.readouterr()
    results = json.loads(out)

    assert 'changed' in results
    assert results['changed'] == testcase['changed']
    if 'msg' in results:
        assert results['msg'] == testcase['msg']

    assert basic.AnsibleModule.run_command.call_count == len(testcase['run_command.calls'])
    if basic.AnsibleModule.run_command.call_count:
        call_args_list = [(item[0][0], item[1]) for item in basic.AnsibleModule.run_command.call_args_list]
        expected_call_args_list = [(item[0], item[1]) for item in testcase['run_command.calls']]
        assert call_args_list == expected_call_args_list


SYSPURPOSE_TEST_CASES = [
    # Test setting syspurpose attributes (system is already registered)
    # and synchronization with candlepin server
    [
        {
            'state': 'present',
            'server_hostname': 'subscription.rhsm.redhat.com',
            'username': 'admin',
            'password': 'admin',
            'org_id': 'admin',
            'syspurpose': {
                'role': 'AwesomeOS',
                'usage': 'Production',
                'service_level_agreement': 'Premium',
                'addons': ['ADDON1', 'ADDON2'],
                'sync': True
            }
        },
        {
            'id': 'test_setting_syspurpose_attributes',
            'existing_syspurpose': {},
            'expected_syspurpose': {
                'role': 'AwesomeOS',
                'usage': 'Production',
                'service_level_agreement': 'Premium',
                'addons': ['ADDON1', 'ADDON2'],
            },
            'run_command.calls': [
                (
                    ['/testbin/subscription-manager', 'identity'],
                    {'check_rc': False},
                    (0, 'system identity: b26df632-25ed-4452-8f89-0308bfd167cb', '')
                ),
                (
                    ['/testbin/subscription-manager', 'status'],
                    {'check_rc': False},
                    (0, '''
+-------------------------------------------+
   System Status Details
+-------------------------------------------+
Overall Status: Current

System Purpose Status: Matched
''', '')
                )
            ],
            'changed': True,
            'msg': 'Syspurpose attributes changed.'
        }
    ],
    # Test setting unspupported attributes
    [
        {
            'state': 'present',
            'server_hostname': 'subscription.rhsm.redhat.com',
            'username': 'admin',
            'password': 'admin',
            'org_id': 'admin',
            'syspurpose': {
                'foo': 'Bar',
                'role': 'AwesomeOS',
                'usage': 'Production',
                'service_level_agreement': 'Premium',
                'addons': ['ADDON1', 'ADDON2'],
                'sync': True
            }
        },
        {
            'id': 'test_setting_syspurpose_wrong_attributes',
            'existing_syspurpose': {},
            'expected_syspurpose': {},
            'run_command.calls': [],
            'failed': True
        }
    ],
    # Test setting addons not a list
    [
        {
            'state': 'present',
            'server_hostname': 'subscription.rhsm.redhat.com',
            'username': 'admin',
            'password': 'admin',
            'org_id': 'admin',
            'syspurpose': {
                'role': 'AwesomeOS',
                'usage': 'Production',
                'service_level_agreement': 'Premium',
                'addons': 'ADDON1',
                'sync': True
            }
        },
        {
            'id': 'test_setting_syspurpose_addons_not_list',
            'existing_syspurpose': {},
            'expected_syspurpose': {
                'role': 'AwesomeOS',
                'usage': 'Production',
                'service_level_agreement': 'Premium',
                'addons': ['ADDON1']
            },
            'run_command.calls': [
                (
                    ['/testbin/subscription-manager', 'identity'],
                    {'check_rc': False},
                    (0, 'system identity: b26df632-25ed-4452-8f89-0308bfd167cb', '')
                ),
                (
                    ['/testbin/subscription-manager', 'status'],
                    {'check_rc': False},
                    (0, '''
+-------------------------------------------+
   System Status Details
+-------------------------------------------+
Overall Status: Current

System Purpose Status: Matched
''', '')
                )
            ],
            'changed': True,
            'msg': 'Syspurpose attributes changed.'
        }
    ],
    # Test setting syspurpose attributes (system is already registered)
    # without synchronization with candlepin server. Some syspurpose attributes were set
    # in the past
    [
        {
            'state': 'present',
            'server_hostname': 'subscription.rhsm.redhat.com',
            'username': 'admin',
            'password': 'admin',
            'org_id': 'admin',
            'syspurpose': {
                'role': 'AwesomeOS',
                'service_level_agreement': 'Premium',
                'addons': ['ADDON1', 'ADDON2'],
                'sync': False
            }
        },
        {
            'id': 'test_changing_syspurpose_attributes',
            'existing_syspurpose': {
                'role': 'CoolOS',
                'usage': 'Production',
                'service_level_agreement': 'Super',
                'addons': [],
                'foo': 'bar'
            },
            'expected_syspurpose': {
                'role': 'AwesomeOS',
                'service_level_agreement': 'Premium',
                'addons': ['ADDON1', 'ADDON2'],
                'foo': 'bar'
            },
            'run_command.calls': [
                (
                    ['/testbin/subscription-manager', 'identity'],
                    {'check_rc': False},
                    (0, 'system identity: b26df632-25ed-4452-8f89-0308bfd167cb', '')
                ),
            ],
            'changed': True,
            'msg': 'Syspurpose attributes changed.'
        }
    ],
    # Test trying to set syspurpose attributes (system is already registered)
    # without synchronization with candlepin server. Some syspurpose attributes were set
    # in the past. Syspurpose attributes are same as before
    [
        {
            'state': 'present',
            'server_hostname': 'subscription.rhsm.redhat.com',
            'username': 'admin',
            'password': 'admin',
            'org_id': 'admin',
            'syspurpose': {
                'role': 'AwesomeOS',
                'service_level_agreement': 'Premium',
                'addons': ['ADDON1', 'ADDON2'],
                'sync': False
            }
        },
        {
            'id': 'test_not_changing_syspurpose_attributes',
            'existing_syspurpose': {
                'role': 'AwesomeOS',
                'service_level_agreement': 'Premium',
                'addons': ['ADDON1', 'ADDON2'],
            },
            'expected_syspurpose': {
                'role': 'AwesomeOS',
                'service_level_agreement': 'Premium',
                'addons': ['ADDON1', 'ADDON2'],
            },
            'run_command.calls': [
                (
                    ['/testbin/subscription-manager', 'identity'],
                    {'check_rc': False},
                    (0, 'system identity: b26df632-25ed-4452-8f89-0308bfd167cb', '')
                ),
            ],
            'changed': False,
            'msg': 'System already registered.'
        }
    ],
    # Test of registration using username and password with auto-attach option, when
    # syspurpose attributes are set
    [
        {
            'state': 'present',
            'username': 'admin',
            'password': 'admin',
            'org_id': 'admin',
            'auto_attach': 'true',
            'syspurpose': {
                'role': 'AwesomeOS',
                'usage': 'Testing',
                'service_level_agreement': 'Super',
                'addons': ['ADDON1'],
                'sync': False
            },
        },
        {
            'id': 'test_registeration_username_password_auto_attach_syspurpose',
            'existing_syspurpose': None,
            'expected_syspurpose': {
                'role': 'AwesomeOS',
                'usage': 'Testing',
                'service_level_agreement': 'Super',
                'addons': ['ADDON1'],
            },
            'run_command.calls': [
                (
                    ['/testbin/subscription-manager', 'identity'],
                    {'check_rc': False},
                    (1, 'This system is not yet registered.', '')
                ),
                (
                    [
                        '/testbin/subscription-manager',
                        'register',
                        '--org', 'admin',
                        '--auto-attach',
                        '--username', 'admin',
                        '--password', 'admin'
                    ],
                    {'check_rc': True, 'expand_user_and_vars': False},
                    (0, '', '')
                )
            ],
            'changed': True,
            'msg': "System successfully registered to 'None'."
        }
    ],
    # Test of registration using username and password with auto-attach option, when
    # syspurpose attributes are set. Syspurpose attributes are also synchronized
    # in this case
    [
        {
            'state': 'present',
            'username': 'admin',
            'password': 'admin',
            'org_id': 'admin',
            'auto_attach': 'true',
            'syspurpose': {
                'role': 'AwesomeOS',
                'usage': 'Testing',
                'service_level_agreement': 'Super',
                'addons': ['ADDON1'],
                'sync': True
            },
        },
        {
            'id': 'test_registeration_username_password_auto_attach_syspurpose_sync',
            'existing_syspurpose': None,
            'expected_syspurpose': {
                'role': 'AwesomeOS',
                'usage': 'Testing',
                'service_level_agreement': 'Super',
                'addons': ['ADDON1'],
            },
            'run_command.calls': [
                (
                    ['/testbin/subscription-manager', 'identity'],
                    {'check_rc': False},
                    (1, 'This system is not yet registered.', '')
                ),
                (
                    [
                        '/testbin/subscription-manager',
                        'register',
                        '--org', 'admin',
                        '--auto-attach',
                        '--username', 'admin',
                        '--password', 'admin'
                    ],
                    {'check_rc': True, 'expand_user_and_vars': False},
                    (0, '', '')
                ),
                (
                    ['/testbin/subscription-manager', 'status'],
                    {'check_rc': False},
                    (0, '''
+-------------------------------------------+
   System Status Details
+-------------------------------------------+
Overall Status: Current

System Purpose Status: Matched
''', '')
                )
            ],
            'changed': True,
            'msg': "System successfully registered to 'None'."
        }
    ],
]


SYSPURPOSE_TEST_CASES_IDS = [item[1]['id'] for item in SYSPURPOSE_TEST_CASES]


@pytest.mark.parametrize('patch_ansible_module, testcase', SYSPURPOSE_TEST_CASES, ids=SYSPURPOSE_TEST_CASES_IDS, indirect=['patch_ansible_module'])
@pytest.mark.usefixtures('patch_ansible_module')
def test_redhat_subscribtion_syspurpose(mocker, capfd, patch_redhat_subscription, patch_ansible_module, testcase, tmpdir):
    """
    Run unit tests for test cases listen in SYSPURPOSE_TEST_CASES (syspurpose specific cases)
    """

    # Mock function used for running commands first
    call_results = [item[2] for item in testcase['run_command.calls']]
    mock_run_command = mocker.patch.object(
        basic.AnsibleModule,
        'run_command',
        side_effect=call_results)

    mock_syspurpose_file = tmpdir.mkdir("syspurpose").join("syspurpose.json")
    # When there there are some existing syspurpose attributes specified, then
    # write them to the file first
    if testcase['existing_syspurpose'] is not None:
        mock_syspurpose_file.write(json.dumps(testcase['existing_syspurpose']))
    else:
        mock_syspurpose_file.write("{}")

    redhat_subscription.SysPurpose.SYSPURPOSE_FILE_PATH = str(mock_syspurpose_file)

    # Try to run test case
    with pytest.raises(SystemExit):
        redhat_subscription.main()

    out, err = capfd.readouterr()
    results = json.loads(out)

    if 'failed' in testcase:
        assert results['failed'] == testcase['failed']
    else:
        assert 'changed' in results
        assert results['changed'] == testcase['changed']
        if 'msg' in results:
            assert results['msg'] == testcase['msg']

    mock_file_content = mock_syspurpose_file.read_text("utf-8")
    current_syspurpose = json.loads(mock_file_content)
    assert current_syspurpose == testcase['expected_syspurpose']

    assert basic.AnsibleModule.run_command.call_count == len(testcase['run_command.calls'])
    if basic.AnsibleModule.run_command.call_count:
        call_args_list = [(item[0][0], item[1]) for item in basic.AnsibleModule.run_command.call_args_list]
        expected_call_args_list = [(item[0], item[1]) for item in testcase['run_command.calls']]
        assert call_args_list == expected_call_args_list
