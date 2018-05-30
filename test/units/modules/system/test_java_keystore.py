# -*- coding: utf-8 -*-

# Copyright (c) 2018, Ansible Project
# Copyright (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from units.modules.utils import ModuleTestCase, set_module_args
from ansible.compat.tests.mock import patch
from ansible.compat.tests.mock import Mock
from ansible.module_utils.basic import AnsibleModule
from ansible.modules.system.java_keystore import create_jks, cert_changed, ArgumentSpec


class TestCreateJavaKeystore(ModuleTestCase):
    """Test the creation of a Java keystore."""

    def setUp(self):
        """Setup."""
        super(TestCreateJavaKeystore, self).setUp()
        self.spec = ArgumentSpec()
        self.mock_create_file = patch('ansible.modules.system.java_keystore.create_file',
                                      side_effect=lambda path, content: path)
        self.mock_run_commands = patch('ansible.modules.system.java_keystore.run_commands')
        self.run_commands = self.mock_run_commands.start()
        self.create_file = self.mock_create_file.start()

    def tearDown(self):
        """Teardown."""
        super(TestCreateJavaKeystore, self).tearDown()
        self.mock_create_file.stop()
        self.mock_run_commands.stop()

    def test_create_jks_success(self):
        set_module_args(dict(
            certificate='cert-foo',
            private_key='private-foo',
            dest='/etc/security/keystore.jks',
            name='foo',
            password='changeit'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        module.exit_json = Mock()

        with patch('os.remove', return_value=True):
            self.run_commands.side_effect = lambda args, kwargs: (0, '', '')
            create_jks(module, "test", "openssl", "keytool", "/etc/security/keystore.jks", "changeit")
            module.exit_json.assert_called_once_with(
                changed=True,
                cmd="keytool -importkeystore "
                    "-destkeystore '/etc/security/keystore.jks' "
                    "-srckeystore '/tmp/keystore.p12' -srcstoretype pkcs12 -alias 'test' "
                    "-deststorepass 'changeit' -srcstorepass 'changeit' -noprompt",
                msg='',
                rc=0,
                stdout_lines=''
            )

    def test_create_jks_fail_export_pkcs12(self):
        set_module_args(dict(
            certificate='cert-foo',
            private_key='private-foo',
            dest='/etc/security/keystore.jks',
            name='foo',
            password='changeit'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        module.fail_json = Mock()

        with patch('os.remove', return_value=True):
            self.run_commands.side_effect = [(1, '', ''), (0, '', '')]
            create_jks(module, "test", "openssl", "keytool", "/etc/security/keystore.jks", "changeit")
            module.fail_json.assert_called_once_with(
                cmd="openssl pkcs12 -export -name 'test' "
                    "-in '/tmp/foo.crt' -inkey '/tmp/foo.key' "
                    "-out '/tmp/keystore.p12' "
                    "-passout 'pass:changeit'",
                msg='',
                rc=1
            )

    def test_create_jks_fail_import_key(self):
        set_module_args(dict(
            certificate='cert-foo',
            private_key='private-foo',
            dest='/etc/security/keystore.jks',
            name='foo',
            password='changeit'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        module.fail_json = Mock()

        with patch('os.remove', return_value=True):
            self.run_commands.side_effect = [(0, '', ''), (1, '', '')]
            create_jks(module, "test", "openssl", "keytool", "/etc/security/keystore.jks", "changeit")
            module.fail_json.assert_called_once_with(
                cmd="keytool -importkeystore "
                    "-destkeystore '/etc/security/keystore.jks' "
                    "-srckeystore '/tmp/keystore.p12' -srcstoretype pkcs12 -alias 'test' "
                    "-deststorepass 'changeit' -srcstorepass 'changeit' -noprompt",
                msg='',
                rc=1
            )


class TestCertChanged(ModuleTestCase):
    """Test if the cert has changed."""

    def setUp(self):
        """Setup."""
        super(TestCertChanged, self).setUp()
        self.spec = ArgumentSpec()
        self.mock_create_file = patch('ansible.modules.system.java_keystore.create_file',
                                      side_effect=lambda path, content: path)
        self.mock_run_commands = patch('ansible.modules.system.java_keystore.run_commands')
        self.run_commands = self.mock_run_commands.start()
        self.create_file = self.mock_create_file.start()

    def tearDown(self):
        """Teardown."""
        super(TestCertChanged, self).tearDown()
        self.mock_create_file.stop()
        self.mock_run_commands.stop()

    def test_cert_unchanged_same_fingerprint(self):
        set_module_args(dict(
            certificate='cert-foo',
            private_key='private-foo',
            dest='/etc/security/keystore.jks',
            name='foo',
            password='changeit'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        with patch('os.remove', return_value=True):
            self.run_commands.side_effect = [(0, 'foo=abcd:1234:efgh', ''), (0, 'foo: abcd:1234:efgh', '')]
            result = cert_changed(module, "openssl", "keytool", "/etc/security/keystore.jks", "changeit", 'foo')
            self.assertFalse(result, 'Fingerprint is identical')

    def test_cert_changed_fingerprint_mismatch(self):
        set_module_args(dict(
            certificate='cert-foo',
            private_key='private-foo',
            dest='/etc/security/keystore.jks',
            name='foo',
            password='changeit'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        with patch('os.remove', return_value=True):
            self.run_commands.side_effect = [(0, 'foo=abcd:1234:efgh', ''), (0, 'foo: wxyz:9876:stuv', '')]
            result = cert_changed(module, "openssl", "keytool", "/etc/security/keystore.jks", "changeit", 'foo')
            self.assertTrue(result, 'Fingerprint mismatch')

    def test_cert_changed_alias_does_not_exist(self):
        set_module_args(dict(
            certificate='cert-foo',
            private_key='private-foo',
            dest='/etc/security/keystore.jks',
            name='foo',
            password='changeit'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        with patch('os.remove', return_value=True):
            self.run_commands.side_effect = [(0, 'foo=abcd:1234:efgh', ''),
                                             (1, 'keytool error: java.lang.Exception: Alias <foo> does not exist', '')]
            result = cert_changed(module, "openssl", "keytool", "/etc/security/keystore.jks", "changeit", 'foo')
            self.assertTrue(result, 'Certificate does not exist')

    def test_cert_changed_fail_read_cert(self):
        set_module_args(dict(
            certificate='cert-foo',
            private_key='private-foo',
            dest='/etc/security/keystore.jks',
            name='foo',
            password='changeit'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        module.fail_json = Mock()

        with patch('os.remove', return_value=True):
            self.run_commands.side_effect = [(1, '', 'Oops'), (0, 'foo: wxyz:9876:stuv', '')]
            cert_changed(module, "openssl", "keytool", "/etc/security/keystore.jks", "changeit", 'foo')
            module.fail_json.assert_called_once_with(
                cmd="openssl x509 -noout -in /tmp/foo.crt -fingerprint -sha1",
                msg='',
                err='Oops',
                rc=1
            )

    def test_cert_changed_fail_read_keystore(self):
        set_module_args(dict(
            certificate='cert-foo',
            private_key='private-foo',
            dest='/etc/security/keystore.jks',
            name='foo',
            password='changeit'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        module.fail_json = Mock(return_value=True)

        with patch('os.remove', return_value=True):
            self.run_commands.side_effect = [(0, 'foo: wxyz:9876:stuv', ''), (1, '', 'Oops')]
            cert_changed(module, "openssl", "keytool", "/etc/security/keystore.jks", "changeit", 'foo')
            module.fail_json.assert_called_with(
                cmd="keytool -list -alias 'foo' -keystore '/etc/security/keystore.jks' -storepass 'changeit'",
                msg='',
                err='Oops',
                rc=1
            )
