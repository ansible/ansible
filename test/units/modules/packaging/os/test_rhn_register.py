import json

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import PropertyMock, patch, mock_open
from ansible.module_utils import basic
from ansible.module_utils.six.moves import xmlrpc_client
from ansible.module_utils._text import to_bytes
from ansible.modules.packaging.os import rhn_register


def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class AnsibleExitJson(Exception):
    pass


class AnsibleFailJson(Exception):
    pass


def exit_json(*args, **kwargs):
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


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
            return lambda func: func
        except ImportError:
            continue

    return unittest.skip("{0}: none are available".format(', '.join(modules)))


class TestRhnRegister(unittest.TestCase):

    def setUp(self):
        self.module = rhn_register
        self.module.HAS_UP2DATE_CLIENT = True

        load_config_return = {
            'serverURL': 'https://xmlrpc.rhn.redhat.com/XMLRPC',
            'systemIdPath': '/etc/sysconfig/rhn/systemid'
        }
        self.mock_load_config = patch.object(rhn_register.Rhn, 'load_config', return_value=load_config_return)
        self.mock_load_config.start()
        self.addCleanup(self.mock_load_config.stop)

        self.mock_exit_fail = patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)
        self.mock_exit_fail.start()
        self.addCleanup(self.mock_exit_fail.stop)

    def tearDown(self):
        pass

#    This one fails, module needs to be fixed.
#    @patch('os.path.isfile')
#    def test_systemid_requirements_missing(self, mock_isfile):
#        """Check that missing dependencies are detected"""
#
#        def mock_import(name, *args):
#            if name in ['libxml2', 'libxml']:
#                raise ImportError()
#            else:
#                return orig_import(name, *args)
#
#        mock_isfile.return_value = True
#        with patch('ansible.modules.packaging.os.rhn_register.open', mock_open(read_data=SYSTEMID), create=True):
#            orig_import = __import__
#            with patch('__builtin__.__import__', side_effect=mock_import):
#                rhn = self.module.Rhn()
#                with self.assertRaises(AnsibleFailJson):
#                    rhn.systemid

    @skipWhenAllModulesMissing(['libxml2', 'libxml'])
    @patch('os.path.isfile')
    def test_systemid_with_requirements(self, mock_isfile):
        """Check systemid property"""

        def mock_import(name, *args):
            if name in ['libxml2', 'libxml']:
                raise ImportError()
            else:
                return orig_import(name, *args)

        mock_isfile.return_value = True
        with patch('ansible.modules.packaging.os.rhn_register.open', mock_open(read_data=SYSTEMID), create=True):
            orig_import = __import__
            with patch('__builtin__.__import__', side_effect=mock_import):
                rhn = self.module.Rhn()
                self.assertEqual('123456789', rhn.systemid)

    def test_without_required_parameters(self):
        """Failure must occurs when all parameters are missing"""
        with self.assertRaises(AnsibleFailJson):
            set_module_args({})
            self.module.main()

    def test_register_parameters(self):
        """Registering an unregistered host"""
        set_module_args({
            'activationkey': 'key',
            'username': 'user',
            'password': 'pass',
        })

        def transport_request(host, handler, request_body, verbose=0):
            """Fake request"""
            if '<methodName>auth.login</methodName>' in request_body:
                return ['X' * 43]
            elif '<methodName>channel.software.listSystemChannels</methodName>' in request_body:
                return [[{'channel_name': 'Red Hat Enterprise Linux Server (v. 6 for 64-bit x86_64)', 'channel_label': 'rhel-x86_64-server-6'}]]
            elif '<methodName>channel.software.setSystemChannels</methodName>' in request_body:
                return [1]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.return_value = 0, '', ''  # successful execution, no output
            with patch.object(rhn_register.Rhn, 'systemid', PropertyMock(return_value=12345)):
                with patch('ansible.modules.packaging.os.rhn_register.xmlrpc_client.Transport.request', side_effect=transport_request) as req:
                    with self.assertRaises(AnsibleExitJson) as result:
                        self.module.main()
                    self.assertTrue(result.exception.args[0]['changed'])
                self.assertEqual(req.call_count, 3)

        self.assertEqual(run_command.call_count, 1)
        self.assertEqual(run_command.call_args[0][0][0], '/usr/sbin/rhnreg_ks')

    def test_register_add_channel(self):
        """Register an unregistered host and add another channel"""
        set_module_args({
            'activationkey': 'key',
            'username': 'user',
            'password': 'pass',
            'channels': 'rhel-x86_64-server-6-debuginfo'
        })

        def transport_request(host, handler, request_body, verbose=0):
            """Fake request"""
            if '<methodName>auth.login</methodName>' in request_body:
                return ['X' * 43]
            elif '<methodName>channel.software.listSystemChannels</methodName>' in request_body:
                return [[{'channel_name': 'Red Hat Enterprise Linux Server (v. 6 for 64-bit x86_64)', 'channel_label': 'rhel-x86_64-server-6'}]]
            elif '<methodName>channel.software.setSystemChannels</methodName>' in request_body:
                return [1]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.return_value = 0, '', ''  # successful execution, no output
            with patch.object(rhn_register.Rhn, 'systemid', PropertyMock(return_value=12345)):
                with patch('ansible.modules.packaging.os.rhn_register.xmlrpc_client.Transport.request', side_effect=transport_request) as req:
                    with self.assertRaises(AnsibleExitJson) as result:
                        self.module.main()
                    self.assertTrue(result.exception.args[0]['changed'])
                self.assertEqual(req.call_count, 3)

        self.assertEqual(run_command.call_count, 1)
        self.assertEqual(run_command.call_args[0][0][0], '/usr/sbin/rhnreg_ks')

    def test_already_registered(self):
        """Register an host already registered, check that result is
        unchanged"""
        set_module_args({
            'activationkey': 'key',
            'username': 'user',
            'password': 'pass',
        })

        def transport_request(host, handler, request_body, verbose=0):
            """Fake request"""
            if '<methodName>auth.login</methodName>' in request_body:
                return ['X' * 43]
            elif '<methodName>channel.software.listSystemChannels</methodName>' in request_body:
                return [[{'channel_name': 'Red Hat Enterprise Linux Server (v. 6 for 64-bit x86_64)', 'channel_label': 'rhel-x86_64-server-6'}]]
            elif '<methodName>channel.software.setSystemChannels</methodName>' in request_body:
                return [1]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            with patch.object(rhn_register.Rhn, 'is_registered', PropertyMock(return_value=True)) as mock_systemid:
                with patch('ansible.modules.packaging.os.rhn_register.xmlrpc_client.Transport.request', side_effect=transport_request) as req:
                    with self.assertRaises(AnsibleExitJson) as result:
                        self.module.main()
                    self.assertFalse(result.exception.args[0]['changed'])
                self.assertFalse(req.called)
            self.assertEqual(mock_systemid.call_count, 1)

        self.assertFalse(run_command.called)

    @patch('os.unlink')
    def test_unregister(self, mock_unlink):
        """Unregister an host, check that result is changed"""

        mock_unlink.return_value = True

        set_module_args({
            'activationkey': 'key',
            'username': 'user',
            'password': 'pass',
            'state': 'absent',
        })

        def transport_request(host, handler, request_body, verbose=0):
            """Fake request"""
            if '<methodName>auth.login</methodName>' in request_body:
                return ['X' * 43]
            elif '<methodName>system.deleteSystems</methodName>' in request_body:
                return [1]

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.return_value = 0, '', ''  # successful execution, no output
            mock_is_registered = PropertyMock(return_value=True)
            mock_systemid = PropertyMock(return_value=12345)
            with patch.multiple(rhn_register.Rhn, systemid=mock_systemid, is_registered=mock_is_registered):
                with patch('ansible.modules.packaging.os.rhn_register.xmlrpc_client.Transport.request', side_effect=transport_request) as req:
                    with self.assertRaises(AnsibleExitJson) as result:
                        self.module.main()
                    self.assertTrue(result.exception.args[0]['changed'])
                self.assertEqual(req.call_count, 2)
            self.assertEqual(mock_systemid.call_count, 1)
            self.assertEqual(mock_is_registered.call_count, 1)
        self.assertFalse(run_command.called)
        self.assertEqual(mock_unlink.call_count, 1)

    @patch('os.unlink')
    def test_unregister_not_registered(self, mock_unlink):
        """Unregister a unregistered host (systemid missing)
        locally, check that result is unchanged"""

        mock_unlink.return_value = True

        set_module_args({
            'activationkey': 'key',
            'username': 'user',
            'password': 'pass',
            'state': 'absent',
        })

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            with patch.object(rhn_register.Rhn, 'is_registered', PropertyMock(return_value=False)) as mock_is_registered:
                with patch('ansible.modules.packaging.os.rhn_register.xmlrpc_client.Transport.request') as req:
                    with self.assertRaises(AnsibleExitJson) as result:
                        self.module.main()
                    self.assertFalse(result.exception.args[0]['changed'])
                self.assertFalse(req.called)
            self.assertEqual(mock_is_registered.call_count, 1)

        self.assertFalse(run_command.called)
        self.assertFalse(mock_unlink.called)

    @patch('os.unlink')
    def test_unregister_unknown_host(self, mock_unlink):
        """Unregister an unknown host (an host with a systemid available
        locally, check that result contains failed"""

        set_module_args({
            'activationkey': 'key',
            'username': 'user',
            'password': 'pass',
            'state': 'absent',
        })

        with patch.object(basic.AnsibleModule, 'run_command') as run_command:
            run_command.return_value = 0, '', ''  # successful execution, no output
            mock_is_registered = PropertyMock(return_value=True)
            mock_systemid = PropertyMock(return_value=12345)
            with patch.multiple(rhn_register.Rhn, systemid=mock_systemid, is_registered=mock_is_registered):
                error = xmlrpc_client.Fault(1003, 'The following systems were NOT deleted: 123456789')
                with patch('ansible.modules.packaging.os.rhn_register.xmlrpc_client.Transport.request',
                           side_effect=('X' * 43, error)) as req:
                    with self.assertRaises(AnsibleFailJson) as result:
                        self.module.main()
                    self.assertTrue(result.exception.args[0]['failed'])
                self.assertEqual(req.call_count, 2)
            self.assertEqual(mock_systemid.call_count, 1)
            self.assertEqual(mock_is_registered.call_count, 1)
        self.assertFalse(run_command.called)
        self.assertFalse(mock_unlink.called)
