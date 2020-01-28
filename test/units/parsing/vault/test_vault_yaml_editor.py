# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import yaml
import tempfile
import os

import pytest

from units.compat import unittest
from units.compat.mock import patch

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.parsing import vault
from ansible.parsing.vault import VaultLib, VaultEditor, AnsibleVaultError
from ansible.parsing.vault.vault_yaml_editor import VaultYAMLEditor

from ansible.module_utils._text import to_bytes, to_text

from units.mock.vault_helper import TextVaultSecret

@pytest.mark.skipif(not vault.HAS_CRYPTOGRAPHY,
                    reason="Skipping cryptography tests because cryptography is not installed")
class TestVaultYAMLEditor(unittest.TestCase):

    def setUp(self):
        self._test_dir = None
        self.vault_secret = self._secret("test-vault-password")

    def tearDown(self):
        self._test_dir = None

    def _create_test_dir(self):
        suffix = '_ansible_unit_test_%s_' % (self.__class__.__name__)
        return tempfile.mkdtemp(suffix=suffix)

    def _create_file(self, test_dir, name, content=None, symlink=False):
        file_path = os.path.join(test_dir, name)
        opened_file = open(file_path, 'wb')
        if content:
            opened_file.write(content)
        opened_file.close()
        return file_path

    def _secret(self, password):
        return TextVaultSecret(password)

    def _secrets(self, password):
        return [('default', self._secret(password))]

    def _vault_editor(self, vault_secrets=None, vault_password="password"):
        if vault_secrets is None:
            vault_secrets = self._secrets(vault_password)
        return VaultYAMLEditor(VaultLib(vault_secrets))

    def _write_file(self, content):
        self._test_dir = self._create_test_dir()
        return self._create_file(self._test_dir, 'src_file',
                                 content=content)

    def _read_file(self, path):
        with open(path, 'rb') as f:
            return f.read()

    def test_encrypt_file(self):
        verifier = SimpleEncryptedYAMLVerifier()
        editor = self._vault_editor()
        path = self._write_file(verifier.plaintext)

        editor.encrypt_file(path, self.vault_secret)

        plaintext = verifier.decrypt(self._read_file(path), editor.vault)
        assert plaintext == verifier.plaintext

    def test_decrypt_file(self):
        verifier = SimpleEncryptedYAMLVerifier()
        self._test_dir = self._create_test_dir()
        vault_editor = self._vault_editor()
        encrypted_yaml = verifier.encrypted(vault_editor.vault)
        path = self._write_file(encrypted_yaml)

        vault_editor.decrypt_file(path)

        assert self._read_file(path) == verifier.plaintext

    def test_rekey_file(self):
        verifier = SimpleEncryptedYAMLVerifier()
        vault_editor = self._vault_editor()
        encrypted_yaml = verifier.encrypted(vault_editor.vault)
        path = self._write_file(encrypted_yaml)

        new_password = 'password2:electricbugaloo'
        new_vault_secret = TextVaultSecret(new_password)
        new_vault_secrets = [('default', new_vault_secret)]

        vault_editor.rekey_file(path, new_vault_secret, 'default')

        rekeyed_yaml = self._read_file(path)
        rekey_vault = VaultLib(new_vault_secrets)
        plaintext = verifier.decrypt(rekeyed_yaml, rekey_vault)
        assert plaintext == verifier.plaintext

    def test_plaintext(self):
        verifier = SimpleEncryptedYAMLVerifier()
        vault_editor = self._vault_editor()
        encrypted_yaml = verifier.encrypted(vault_editor.vault)
        path = self._write_file(encrypted_yaml)

        plaintext = vault_editor.plaintext(path).encode('utf-8')

        assert plaintext == verifier.plaintext

    def test_encrypt_no_encryption_password(self):
        editor = VaultYAMLEditor(VaultLib([]))
        original_yaml = yaml.dump({'some_value': 'some_value'}).encode('utf-8')
        path = self._write_file(original_yaml)

        with pytest.raises(AnsibleVaultError) as excinfo:
            editor.encrypt_file(path, self.vault_secret)
        expected = 'A vault password must be specified to encrypt data'
        assert expected in str(excinfo.value)

        assert original_yaml == self._read_file(path)

    def test_encrypt_invalid_yaml(self):
        editor = self._vault_editor()
        invalid_yaml = '\t'.encode('utf-8')
        path = self._write_file(invalid_yaml)

        with pytest.raises(AnsibleParserError) as excinfo:
            editor.encrypt_file(path, self.vault_secret)
        assert 'Syntax Error while loading YAML' in str(excinfo.value)

        assert invalid_yaml == self._read_file(path)

    def test_decrypt_invalid_yaml(self):
        editor = self._vault_editor()
        invalid_yaml = '\t'.encode('utf-8')
        path = self._write_file(invalid_yaml)

        with pytest.raises(AnsibleParserError) as excinfo:
            editor.decrypt_file(path, self.vault_secret)
        assert 'Syntax Error while loading YAML' in str(excinfo.value)

        assert invalid_yaml == self._read_file(path)

    def test_plaintext_invalid_yaml(self):
        editor = self._vault_editor()
        invalid_yaml = '\t'.encode('utf-8')
        path = self._write_file(invalid_yaml)

        with pytest.raises(AnsibleParserError) as excinfo:
            editor.plaintext(path)
        assert 'Syntax Error while loading YAML' in str(excinfo.value)

        assert invalid_yaml == self._read_file(path)

    def test_rekey_invalid_yaml(self):
        editor = self._vault_editor()
        invalid_yaml = '\t'.encode('utf-8')
        path = self._write_file(invalid_yaml)

        with pytest.raises(AnsibleParserError) as excinfo:
            editor.rekey_file(path, self.vault_secret,
                              new_encrypt_vault_id='default')
        assert 'Syntax Error while loading YAML' in str(excinfo.value)

        assert invalid_yaml == self._read_file(path)

    def test_encrypt_non_strings(self):
        editor = self._vault_editor()
        invalid_yaml = yaml.dump({'some_value': 1}).encode('utf-8')
        path = self._write_file(invalid_yaml)

        with pytest.raises(AnsibleError) as excinfo:
            editor.encrypt_file(path, self.vault_secret)
        assert editor.NON_STRING_VALUE_MESSAGE.format(int) in str(excinfo.value)

        assert invalid_yaml == self._read_file(path)

    def test_encrypt_already_encrypted(self):
        editor = self._vault_editor()
        original_yaml = yaml.dump({'some_value': 'some_value'}).encode('utf-8')
        path = self._write_file(original_yaml)
        editor.encrypt_file(path, self.vault_secret)
        encrypted_yaml = self._read_file(path)

        with pytest.raises(AnsibleError) as excinfo:
            editor.encrypt_file(path, self.vault_secret)
        assert editor.ALREADY_ENCRYPTED_MESSAGE in str(excinfo.value)

        assert self._read_file(path) == encrypted_yaml

    def test_complex_data(self):
        editor = self._vault_editor()
        test_data = {
            'list_of_strings': ['one', 'two', 'three'],
            'nested_element': {
                'nested_string': 'nested string'
            },
            'list_of_nested_elements': [{ 'nested_item': 'nested list item' }]
        }
        original_yaml = yaml.dump(test_data)
        path = self._write_file(original_yaml.encode('utf-8'))
        editor.encrypt_file(path, self.vault_secret)

        assert yaml.load(editor.plaintext(path), Loader=yaml.SafeLoader) == \
            yaml.load(original_yaml, Loader=yaml.SafeLoader)

    # TODO: this is currently failing in the Python 2.7 tests
    def test_multiline_values(self):
        editor = self._vault_editor()
        test_data = {
            'multiline': 'one\ntwo\nthree',
        }
        original_yaml = yaml.dump(test_data)
        path = self._write_file(original_yaml.encode('utf-8'))
        editor.encrypt_file(path, self.vault_secret)

        assert editor.plaintext(path) == \
            'multiline: |-\n  one\n  two\n  three\n'

    def test_singleline_values(self):
        editor = self._vault_editor()
        test_data = {
            'singleline': 'one two three'
        }
        original_yaml = yaml.dump(test_data)
        path = self._write_file(original_yaml.encode('utf-8'))
        editor.encrypt_file(path, self.vault_secret)

        assert editor.plaintext(path) == \
            'singleline: one two three\n'

    def test_update_nodes(self):
        v = VaultYAMLEditor(None)
        test_data = {
            'list_of_strings': ['one', 'two', 'three'],
            'nested_element': {
                'nested_string': 'nested string'
            },
            'list_of_nested_elements': [{ 'nested_item': 'nested list item' }]
        }

        v._update_nodes(test_data, lambda node: node.upper())

        assert test_data == {
            'list_of_strings': ['ONE', 'TWO', 'THREE'],
            'nested_element': {
                'nested_string': 'NESTED STRING'
            },
            'list_of_nested_elements': [{ 'nested_item': 'NESTED LIST ITEM' }]
        }

# NOTE: this test is outside of the class above as the capsys parameter wasn't
# being handled correctly.
@patch('sys.stdin.read')
def test_something(patched_stdin_read, capsys):
    vault_secrets = [('default', TextVaultSecret('password'))]
    verifier = SimpleEncryptedYAMLVerifier()
    editor = VaultYAMLEditor(VaultLib(vault_secrets))
    patched_stdin_read.return_value = verifier.plaintext

    editor.encrypt_file('-', vault_secrets)

    out, _err = capsys.readouterr()
    assert verifier.plaintext == verifier.decrypt(out.encode('utf-8'),
                                                  editor.vault)

class SimpleEncryptedYAMLVerifier(object):
    # This class provides some tools for parsing, encrypting and decrypting a
    # very simple YAML file with an encrypted vault value. It's used for
    # testing the core functions of the VaultYAMLEditor.
    #
    # This verifier is highly dependent of the Ansible Vault YAML
    # implementation. Here is an example of the encrypted vault YAML:
    # (password: password)
    #
    # secret: !vault |
    #   $ANSIBLE_VAULT;1.1;AES256
    #   32613233656265346638653636356632613639343635656635376564306334386464343732323933
    #   6536653964633466363866386638616539326233323265320a393061623033646435656565613762
    #   35333237323230613762336565393531663861613436633636326331393632336532363333306331
    #   3030376432633736350a623931303664326362313830653961343036313066643061343762386238
    #   3130
    #

    @property
    def plaintext(self):
        return "secret: code\n".encode('utf-8')

    def decrypt(self, content, vault):
        lines = content.decode().split('\n')
        key = lines[0].split(':')[0]
        cipher_lines = lines[1:]
        cipher_text = "\n".join([line.strip() for line in cipher_lines])
        cipher_bytes = cipher_text.encode('utf-8')
        plaintext = vault.decrypt(cipher_bytes).decode()
        return "{}: {}\n".format(key, plaintext).encode('utf-8')

    def encrypted(self, vault):
        cipher_text = vault.encrypt('code').decode()
        cipher_lines = cipher_text.split('\n')
        cipher_indented = ['  ' + line for line in cipher_lines]
        yaml_bytes = ("\n".join(['secret: !vault |'] + cipher_indented) + '\n').encode('utf-8')
        return yaml_bytes
