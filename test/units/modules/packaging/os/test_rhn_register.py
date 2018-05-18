import contextlib
import json
import os

from ansible.compat.tests.mock import mock_open
from ansible.module_utils import basic
from ansible.module_utils._text import to_native
import ansible.module_utils.six
from ansible.module_utils.six.moves import xmlrpc_client
from ansible.modules.packaging.os import rhn_register

import pytest


SYSTEMID = """<?xml version="1.0"?>
<params>
<param>
<value><struct>
<member>
<name>system_id</name>
<value><string>ID-123456789</string></value>
</member>
</struct></value>
</param>
</params>
"""


def skipWhenAllModulesMissing(modules):
    """Skip the decorated test unless one of modules is available."""
    for module in modules:
        try:
            __import__(module)
            return False
        except ImportError:
            continue

    return True


orig_import = __import__


@pytest.fixture
def import_libxml(mocker):
    def mock_import(name, *args, **kwargs):
        if name in ['libxml2', 'libxml']:
            raise ImportError()
        else:
            return orig_import(name, *args, **kwargs)

    if ansible.module_utils.six.PY3:
        mocker.patch('builtins.__import__', side_effect=mock_import)
    else:
        mocker.patch('__builtin__.__import__', side_effect=mock_import)


@pytest.fixture
def patch_rhn(mocker):
    load_config_return = {
        'serverURL': 'https://xmlrpc.rhn.redhat.com/XMLRPC',
        'systemIdPath': '/etc/sysconfig/rhn/systemid'
    }

    mocker.patch.object(rhn_register.Rhn, 'load_config', return_value=load_config_return)
    mocker.patch.object(rhn_register, 'HAS_UP2DATE_CLIENT', mocker.PropertyMock(return_value=True))


@pytest.mark.skipif(skipWhenAllModulesMissing(['libxml2', 'libxml']), reason='none are available: libxml2, libxml')
def test_systemid_with_requirements(capfd, mocker, patch_rhn):
    """Check 'msg' and 'changed' results"""

    mocker.patch.object(rhn_register.Rhn, 'enable')
    mock_isfile = mocker.patch('os.path.isfile', return_value=True)
    mocker.patch('ansible.modules.packaging.os.rhn_register.open', mock_open(read_data=SYSTEMID), create=True)
    rhn = rhn_register.Rhn()
    assert '123456789' == to_native(rhn.systemid)


@pytest.mark.parametrize('patch_ansible_module', [{}], indirect=['patch_ansible_module'])
@pytest.mark.usefixtures('patch_ansible_module')
def test_systemid_requirements_missing(capfd, mocker, patch_rhn, import_libxml):
    """Check that missing dependencies are detected"""

    mocker.patch('os.path.isfile', return_value=True)
    mocker.patch('ansible.modules.packaging.os.rhn_register.open', mock_open(read_data=SYSTEMID), create=True)

    with pytest.raises(SystemExit):
        rhn_register.main()

    out, err = capfd.readouterr()
    results = json.loads(out)
    assert results['failed']
    assert 'Missing arguments' in results['msg']


@pytest.mark.parametrize('patch_ansible_module', [{}], indirect=['patch_ansible_module'])
@pytest.mark.usefixtures('patch_ansible_module')
def test_without_required_parameters(capfd, patch_rhn):
    """Failure must occurs when all parameters are missing"""

    with pytest.raises(SystemExit):
        rhn_register.main()
    out, err = capfd.readouterr()
    results = json.loads(out)
    assert results['failed']
    assert 'Missing arguments' in results['msg']


TESTED_MODULE = rhn_register.__name__
TEST_CASES = [
    [
        # Registering an unregistered host
        {
            'activationkey': 'key',
            'username': 'user',
            'password': 'pass',
        },
        {
            'calls': [
                ('auth.login', ['X' * 43]),
                ('channel.software.listSystemChannels',
                    [[{'channel_name': 'Red Hat Enterprise Linux Server (v. 6 for 64-bit x86_64)', 'channel_label': 'rhel-x86_64-server-6'}]]),
                ('channel.software.setSystemChannels', [1]),
                ('auth.logout', [1]),
            ],
            'is_registered': False,
            'is_registered.call_count': 1,
            'enable.call_count': 1,
            'systemid.call_count': 2,
            'changed': True,
            'msg': "System successfully registered to 'rhn.redhat.com'.",
            'run_command.call_count': 1,
            'run_command.call_args': '/usr/sbin/rhnreg_ks',
            'request_called': True,
            'unlink.call_count': 0,
        }
    ],
    [
        # Register an host already registered, check that result is unchanged
        {
            'activationkey': 'key',
            'username': 'user',
            'password': 'pass',
        },
        {
            'calls': [
            ],
            'is_registered': True,
            'is_registered.call_count': 1,
            'enable.call_count': 0,
            'systemid.call_count': 0,
            'changed': False,
            'msg': 'System already registered.',
            'run_command.call_count': 0,
            'request_called': False,
            'unlink.call_count': 0,
        },
    ],
    [
        # Unregister an host, check that result is changed
        {
            'activationkey': 'key',
            'username': 'user',
            'password': 'pass',
            'state': 'absent',
        },
        {
            'calls': [
                ('auth.login', ['X' * 43]),
                ('system.deleteSystems', [1]),
                ('auth.logout', [1]),
            ],
            'is_registered': True,
            'is_registered.call_count': 1,
            'enable.call_count': 0,
            'systemid.call_count': 1,
            'changed': True,
            'msg': 'System successfully unregistered from rhn.redhat.com.',
            'run_command.call_count': 0,
            'request_called': True,
            'unlink.call_count': 1,
        }
    ],
    [
        # Unregister a unregistered host (systemid missing) locally, check that result is unchanged
        {
            'activationkey': 'key',
            'username': 'user',
            'password': 'pass',
            'state': 'absent',
        },
        {
            'calls': [],
            'is_registered': False,
            'is_registered.call_count': 1,
            'enable.call_count': 0,
            'systemid.call_count': 0,
            'changed': False,
            'msg': 'System already unregistered.',
            'run_command.call_count': 0,
            'request_called': False,
            'unlink.call_count': 0,
        }

    ],
    [
        # Unregister an unknown host (an host with a systemid available locally, check that result contains failed
        {
            'activationkey': 'key',
            'username': 'user',
            'password': 'pass',
            'state': 'absent',
        },
        {
            'calls': [
                ('auth.login', ['X' * 43]),
                ('system.deleteSystems', xmlrpc_client.Fault(1003, 'The following systems were NOT deleted: 123456789')),
                ('auth.logout', [1]),
            ],
            'is_registered': True,
            'is_registered.call_count': 1,
            'enable.call_count': 0,
            'systemid.call_count': 1,
            'failed': True,
            'msg': "Failed to unregister: <Fault 1003: 'The following systems were NOT deleted: 123456789'>",
            'run_command.call_count': 0,
            'request_called': True,
            'unlink.call_count': 0,
        }
    ],
]


@pytest.mark.parametrize('patch_ansible_module, testcase', TEST_CASES, indirect=['patch_ansible_module'])
@pytest.mark.usefixtures('patch_ansible_module')
def test_register_parameters(mocker, capfd, mock_request, patch_rhn, testcase):
    # successful execution, no output
    mocker.patch.object(basic.AnsibleModule, 'run_command', return_value=(0, '', ''))
    mock_is_registered = mocker.patch.object(rhn_register.Rhn, 'is_registered', mocker.PropertyMock(return_value=testcase['is_registered']))
    mocker.patch.object(rhn_register.Rhn, 'enable')
    mock_systemid = mocker.patch.object(rhn_register.Rhn, 'systemid', mocker.PropertyMock(return_value=12345))
    mocker.patch('os.unlink', return_value=True)

    with pytest.raises(SystemExit):
        rhn_register.main()

    assert basic.AnsibleModule.run_command.call_count == testcase['run_command.call_count']
    if basic.AnsibleModule.run_command.call_count:
        assert basic.AnsibleModule.run_command.call_args[0][0][0] == testcase['run_command.call_args']

    assert mock_is_registered.call_count == testcase['is_registered.call_count']
    assert rhn_register.Rhn.enable.call_count == testcase['enable.call_count']
    assert mock_systemid.call_count == testcase['systemid.call_count']
    assert xmlrpc_client.Transport.request.called == testcase['request_called']
    assert os.unlink.call_count == testcase['unlink.call_count']

    out, err = capfd.readouterr()
    results = json.loads(out)
    assert results.get('changed') == testcase.get('changed')
    assert results.get('failed') == testcase.get('failed')
    assert results['msg'] == testcase['msg']
    assert not testcase['calls']  # all calls should have been consumed
