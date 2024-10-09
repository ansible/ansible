# -*- coding: utf-8 -*-
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2016, Toshio Kuratomi <tkuratomi@ansible.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

import io
import os
import tempfile

import pytest
import unittest
from unittest.mock import patch, MagicMock

from ansible import errors
from ansible.module_utils.common.text.converters import to_bytes, to_text
from ansible.parsing import vault

from units.mock.loader import DictDataLoader
from units.mock.vault_helper import TextVaultSecret
from units.parsing.vault.methods.rot13 import patch_rot13_import

from ansible.parsing.vault import AnsibleVaultFormatError, AnsibleVaultError


class TestParseVaulttext(unittest.TestCase):
    def test(self):
        vaulttext_envelope = u'''$ANSIBLE_VAULT;1.1;AES256
33363965326261303234626463623963633531343539616138316433353830356566396130353436
3562643163366231316662386565383735653432386435610a306664636137376132643732393835
63383038383730306639353234326630666539346233376330303938323639306661313032396437
6233623062366136310a633866373936313238333730653739323461656662303864663666653563
3138'''

        b_vaulttext_envelope = to_bytes(vaulttext_envelope, errors='strict', encoding='utf-8')
        b_vaulttext, b_version, _name, vault_id = vault.parse_vaulttext_envelope(b_vaulttext_envelope)


class TestVaultSecret(unittest.TestCase):
    def test(self):
        secret = vault.VaultSecret()
        secret.load()
        self.assertIsNone(secret._bytes)

    def test_bytes(self):
        some_text = u'私はガラスを食べられます。それは私を傷つけません。'
        _bytes = to_bytes(some_text)
        secret = vault.VaultSecret(_bytes)
        secret.load()
        self.assertEqual(secret.bytes, _bytes)


class TestPromptVaultSecret(unittest.TestCase):
    def test_empty_prompt_formats(self):
        secret = vault.PromptVaultSecret(vault_id='test_id', prompt_formats=[])
        secret.load()
        self.assertIsNone(secret._bytes)

    @patch('ansible.parsing.vault.display.prompt', return_value='the_password')
    def test_prompt_formats_none(self, mock_display_prompt):
        secret = vault.PromptVaultSecret(vault_id='test_id')
        secret.load()
        self.assertEqual(secret._bytes, b'the_password')

    @patch('ansible.parsing.vault.display.prompt', return_value='the_password')
    def test_custom_prompt(self, mock_display_prompt):
        secret = vault.PromptVaultSecret(vault_id='test_id',
                                         prompt_formats=['The cow flies at midnight: '])
        secret.load()
        self.assertEqual(secret._bytes, b'the_password')

    @patch('ansible.parsing.vault.display.prompt', side_effect=EOFError)
    def test_prompt_eoferror(self, mock_display_prompt):
        secret = vault.PromptVaultSecret(vault_id='test_id')
        self.assertRaisesRegex(vault.AnsibleVaultError, 'EOFError.*test_id', secret.load)

    @patch('ansible.parsing.vault.display.prompt', side_effect=['first_password', 'second_password'])
    def test_prompt_passwords_dont_match(self, mock_display_prompt):
        secret = vault.PromptVaultSecret(vault_id='test_id',
                                         prompt_formats=['Vault password: ',
                                                         'Confirm Vault password: '])
        self.assertRaisesRegex(errors.AnsibleError, 'Passwords do not match', secret.load)


class TestFileVaultSecret(unittest.TestCase):
    def setUp(self):
        self.vault_password = "test-vault-password"
        text_secret = TextVaultSecret(self.vault_password)
        self.vault_secrets = [('foo', text_secret)]

    def test(self):
        secret = vault.FileVaultSecret()
        self.assertIsNone(secret._bytes)

    def test_repr_empty(self):
        secret = vault.FileVaultSecret()
        self.assertEqual(repr(secret), "FileVaultSecret()")

    def test_repr(self):
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        fake_loader = DictDataLoader({tmp_file.name: 'sdfadf'})

        secret = vault.FileVaultSecret(loader=fake_loader, filename=tmp_file.name)
        filename = tmp_file.name
        tmp_file.close()
        self.assertEqual(repr(secret), "FileVaultSecret(filename='%s')" % filename)

    def test_empty_bytes(self):
        secret = vault.FileVaultSecret()
        self.assertIsNone(secret.bytes)

    def test_file(self):
        password = 'some password'

        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file.write(to_bytes(password))
        tmp_file.close()

        fake_loader = DictDataLoader({tmp_file.name: 'sdfadf'})

        secret = vault.FileVaultSecret(loader=fake_loader, filename=tmp_file.name)
        secret.load()

        os.unlink(tmp_file.name)

        self.assertEqual(secret.bytes, to_bytes(password))

    def test_file_empty(self):

        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file.write(to_bytes(''))
        tmp_file.close()

        fake_loader = DictDataLoader({tmp_file.name: ''})

        secret = vault.FileVaultSecret(loader=fake_loader, filename=tmp_file.name)
        self.assertRaisesRegex(vault.AnsibleVaultPasswordError,
                               'Invalid vault password was provided from file.*%s' % tmp_file.name,
                               secret.load)

        os.unlink(tmp_file.name)

    def test_file_not_a_directory(self):
        filename = '/dev/null/foobar'
        fake_loader = DictDataLoader({filename: 'sdfadf'})

        secret = vault.FileVaultSecret(loader=fake_loader, filename=filename)
        self.assertRaisesRegex(errors.AnsibleError,
                               '.*Could not read vault password file.*/dev/null/foobar.*Not a directory',
                               secret.load)

    def test_file_not_found(self):
        tmp_file = tempfile.NamedTemporaryFile()
        filename = os.path.realpath(tmp_file.name)
        tmp_file.close()

        fake_loader = DictDataLoader({filename: 'sdfadf'})

        secret = vault.FileVaultSecret(loader=fake_loader, filename=filename)
        self.assertRaisesRegex(errors.AnsibleError,
                               '.*Could not read vault password file.*%s.*' % filename,
                               secret.load)


class TestScriptVaultSecret(unittest.TestCase):
    def test(self):
        secret = vault.ScriptVaultSecret()
        self.assertIsNone(secret._bytes)

    def _mock_popen(self, mock_popen, return_code=0, stdout=b'', stderr=b''):
        def communicate():
            return stdout, stderr
        mock_popen.return_value = MagicMock(returncode=return_code)
        mock_popen_instance = mock_popen.return_value
        mock_popen_instance.communicate = communicate

    @patch('ansible.parsing.vault.subprocess.Popen')
    def test_read_file(self, mock_popen):
        self._mock_popen(mock_popen, stdout=b'some_password')
        secret = vault.ScriptVaultSecret()
        with patch.object(secret, 'loader') as mock_loader:
            mock_loader.is_executable = MagicMock(return_value=True)
            secret.load()

    @patch('ansible.parsing.vault.subprocess.Popen')
    def test_read_file_empty(self, mock_popen):
        self._mock_popen(mock_popen, stdout=b'')
        secret = vault.ScriptVaultSecret()
        with patch.object(secret, 'loader') as mock_loader:
            mock_loader.is_executable = MagicMock(return_value=True)
            self.assertRaisesRegex(vault.AnsibleVaultPasswordError,
                                   'Invalid vault password was provided from script',
                                   secret.load)

    @patch('ansible.parsing.vault.subprocess.Popen')
    def test_read_file_os_error(self, mock_popen):
        self._mock_popen(mock_popen)
        mock_popen.side_effect = OSError('That is not an executable')
        secret = vault.ScriptVaultSecret()
        with patch.object(secret, 'loader') as mock_loader:
            mock_loader.is_executable = MagicMock(return_value=True)
            self.assertRaisesRegex(errors.AnsibleError,
                                   'Problem running vault password script.*',
                                   secret.load)

    @patch('ansible.parsing.vault.subprocess.Popen')
    def test_read_file_not_executable(self, mock_popen):
        self._mock_popen(mock_popen)
        secret = vault.ScriptVaultSecret()
        with patch.object(secret, 'loader') as mock_loader:
            mock_loader.is_executable = MagicMock(return_value=False)
            self.assertRaisesRegex(vault.AnsibleVaultError,
                                   'The vault password script .* was not executable',
                                   secret.load)

    @patch('ansible.parsing.vault.subprocess.Popen')
    def test_read_file_non_zero_return_code(self, mock_popen):
        stderr = b'That did not work for a random reason'
        rc = 37

        self._mock_popen(mock_popen, return_code=rc, stderr=stderr)
        secret = vault.ScriptVaultSecret(filename='/dev/null/some_vault_secret')
        with patch.object(secret, 'loader') as mock_loader:
            mock_loader.is_executable = MagicMock(return_value=True)
            self.assertRaisesRegex(errors.AnsibleError,
                                   r'Vault password script.*returned non-zero \(%s\): %s' % (rc, stderr),
                                   secret.load)


class TestScriptIsClient(unittest.TestCase):
    def test_randomname(self):
        filename = 'randomname'
        res = vault.script_is_client(filename)
        self.assertFalse(res)

    def test_something_dash_client(self):
        filename = 'something-client'
        res = vault.script_is_client(filename)
        self.assertTrue(res)

    def test_something_dash_client_somethingelse(self):
        filename = 'something-client-somethingelse'
        res = vault.script_is_client(filename)
        self.assertFalse(res)

    def test_something_dash_client_py(self):
        filename = 'something-client.py'
        res = vault.script_is_client(filename)
        self.assertTrue(res)

    def test_full_path_something_dash_client_py(self):
        filename = '/foo/bar/something-client.py'
        res = vault.script_is_client(filename)
        self.assertTrue(res)

    def test_full_path_something_dash_client(self):
        filename = '/foo/bar/something-client'
        res = vault.script_is_client(filename)
        self.assertTrue(res)

    def test_full_path_something_dash_client_in_dir(self):
        filename = '/foo/bar/something-client/but/not/filename'
        res = vault.script_is_client(filename)
        self.assertFalse(res)


class TestGetFileVaultSecret(unittest.TestCase):
    def test_file(self):
        password = 'some password'

        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file.write(to_bytes(password))
        tmp_file.close()

        fake_loader = DictDataLoader({tmp_file.name: 'sdfadf'})

        secret = vault.get_file_vault_secret(filename=tmp_file.name, loader=fake_loader)
        secret.load()

        os.unlink(tmp_file.name)

        self.assertEqual(secret.bytes, to_bytes(password))

    def test_file_not_a_directory(self):
        filename = '/dev/null/foobar'
        fake_loader = DictDataLoader({filename: 'sdfadf'})

        self.assertRaisesRegex(errors.AnsibleError,
                               '.*The vault password file %s was not found.*' % filename,
                               vault.get_file_vault_secret,
                               filename=filename,
                               loader=fake_loader)

    def test_file_not_found(self):
        tmp_file = tempfile.NamedTemporaryFile()
        filename = os.path.realpath(tmp_file.name)
        tmp_file.close()

        fake_loader = DictDataLoader({filename: 'sdfadf'})

        self.assertRaisesRegex(errors.AnsibleError,
                               '.*The vault password file %s was not found.*' % filename,
                               vault.get_file_vault_secret,
                               filename=filename,
                               loader=fake_loader)


class TestVaultIsEncrypted(unittest.TestCase):

    def test_bytes_not_encrypted(self):
        b_data = b"foobar"
        self.assertFalse(vault.is_encrypted(b_data))

    def test_bytes_encrypted(self):
        b_data = b"$ANSIBLE_VAULT;9.9;TEST\nansible filler"
        self.assertTrue(vault.is_encrypted(b_data))

    def test_text_not_encrypted(self):
        b_data = to_text(b"foobar")
        self.assertFalse(vault.is_encrypted(b_data))

    def test_text_encrypted(self):
        b_data = to_text(b"$ANSIBLE_VAULT;9.9;TEST\nansible filler")
        self.assertTrue(vault.is_encrypted(b_data))

    def test_invalid_text_not_ascii(self):
        data = u"$ANSIBLE_VAULT;9.9;TEST\n%s" % u"ァ ア ィ イ ゥ ウ ェ エ ォ オ カ ガ キ ギ ク グ ケ "
        self.assertFalse(vault.is_encrypted(data))

    def test_invalid_bytes_not_ascii(self):
        data = u"$ANSIBLE_VAULT;9.9;TEST\n%s" % u"ァ ア ィ イ ゥ ウ ェ エ ォ オ カ ガ キ ギ ク グ ケ "
        b_data = to_bytes(data, encoding='utf-8')
        self.assertFalse(vault.is_encrypted(b_data))


class TestVaultIsEncryptedFile(unittest.TestCase):
    def test_binary_file_handle_not_encrypted(self):
        b_data = b"foobar"
        b_data_fo = io.BytesIO(b_data)
        self.assertFalse(vault.is_encrypted_file(b_data_fo))

    def test_text_file_handle_not_encrypted(self):
        data = u"foobar"
        data_fo = io.StringIO(data)
        self.assertFalse(vault.is_encrypted_file(data_fo))

    def test_binary_file_handle_encrypted(self):
        b_data = b"$ANSIBLE_VAULT;9.9;TEST\nansible filler"
        b_data_fo = io.BytesIO(b_data)
        self.assertTrue(vault.is_encrypted_file(b_data_fo))

    def test_text_file_handle_encrypted(self):
        data = u"$ANSIBLE_VAULT;9.9;TEST\nansible filler"
        data_fo = io.StringIO(data)
        self.assertTrue(vault.is_encrypted_file(data_fo))

    def test_binary_file_handle_invalid(self):
        data = u"$ANSIBLE_VAULT;9.9;TEST\n%s" % u"ァ ア ィ イ ゥ ウ ェ エ ォ オ カ ガ キ ギ ク グ ケ "
        b_data = to_bytes(data)
        b_data_fo = io.BytesIO(b_data)
        self.assertFalse(vault.is_encrypted_file(b_data_fo, count=-1))

    def test_text_file_handle_invalid(self):
        data = u"$ANSIBLE_VAULT;9.9;TEST\n%s" % u"ァ ア ィ イ ゥ ウ ェ エ ォ オ カ ガ キ ギ ク グ ケ "
        data_fo = io.StringIO(data)
        self.assertFalse(vault.is_encrypted_file(data_fo, count=-1))

    def test_file_already_read_from_finds_header(self):
        b_data = b"$ANSIBLE_VAULT;9.9;TEST\nansible\ntesting\nfile pos"
        b_data_fo = io.BytesIO(b_data)
        b_data_fo.read(42)  # Arbitrary number less than str length
        self.assertTrue(vault.is_encrypted_file(b_data_fo))

    def test_file_already_read_from_saves_file_pos(self):
        b_data = b"$ANSIBLE_VAULT;9.9;TEST\n%ansible\ntesting\nfile pos"
        b_data_fo = io.BytesIO(b_data)
        b_data_fo.read(42)  # Arbitrary number less than str length
        vault.is_encrypted_file(b_data_fo)
        self.assertEqual(b_data_fo.tell(), 42)

    def test_file_with_offset(self):
        b_data = b"JUNK$ANSIBLE_VAULT;9.9;TEST\nansible\ntesting\nfile pos"
        b_data_fo = io.BytesIO(b_data)
        self.assertTrue(vault.is_encrypted_file(b_data_fo, start_pos=4))

    def test_file_with_count(self):
        b_data = b"$ANSIBLE_VAULT;9.9;TEST\nansible\ntesting\nfile pos"
        vault_length = len(b_data)
        b_data = b_data + u'ァ ア'.encode('utf-8')
        b_data_fo = io.BytesIO(b_data)
        self.assertTrue(vault.is_encrypted_file(b_data_fo, count=vault_length))

    def test_file_with_offset_and_count(self):
        b_data = b"$ANSIBLE_VAULT;9.9;TEST\nansible\ntesting\nfile pos"
        vault_length = len(b_data)
        b_data = b'JUNK' + b_data + u'ァ ア'.encode('utf-8')
        b_data_fo = io.BytesIO(b_data)
        self.assertTrue(vault.is_encrypted_file(b_data_fo, start_pos=4, count=vault_length))


class TestMatchSecrets(unittest.TestCase):
    def test_empty_tuple(self):
        secrets = [tuple()]
        vault_ids = ['vault_id_1']
        self.assertRaises(ValueError,
                          vault.match_secrets,
                          secrets, vault_ids)

    def test_empty_secrets(self):
        matches = vault.match_secrets([], ['vault_id_1'])
        self.assertEqual(matches, [])

    def test_single_match(self):
        secret = TextVaultSecret('password')
        matches = vault.match_secrets([('default', secret)], ['default'])
        self.assertEqual(matches, [('default', secret)])

    def test_no_matches(self):
        secret = TextVaultSecret('password')
        matches = vault.match_secrets([('default', secret)], ['not_default'])
        self.assertEqual(matches, [])

    def test_multiple_matches(self):
        secrets = [('vault_id1', TextVaultSecret('password1')),
                   ('vault_id2', TextVaultSecret('password2')),
                   ('vault_id1', TextVaultSecret('password3')),
                   ('vault_id4', TextVaultSecret('password4'))]
        vault_ids = ['vault_id1', 'vault_id4']
        matches = vault.match_secrets(secrets, vault_ids)

        self.assertEqual(len(matches), 3)
        expected = [('vault_id1', TextVaultSecret('password1')),
                    ('vault_id1', TextVaultSecret('password3')),
                    ('vault_id4', TextVaultSecret('password4'))]
        self.assertEqual([x for x, y in matches],
                         [a for a, b in expected])


@pytest.mark.usefixtures(patch_rot13_import.__name__)
class TestVaultLib(unittest.TestCase):
    def setUp(self):
        self.vault_password = "test-vault-password"
        text_secret = TextVaultSecret(self.vault_password)
        self.vault_secrets = [('default', text_secret),
                              ('test_id', text_secret)]
        self.v = vault.VaultLib(self.vault_secrets)

    def test_encrypt(self):
        plaintext = u'Some text to encrypt in a café'
        b_vaulttext = self.v.encrypt(plaintext, method_name='rot13')

        self.assertIsInstance(b_vaulttext, bytes)

        b_header = b'$ANSIBLE_VAULT;1.1;ROT13\n'
        self.assertEqual(b_vaulttext[:len(b_header)], b_header)

    def test_encrypt_vault_id(self):
        plaintext = u'Some text to encrypt in a café'
        b_vaulttext = self.v.encrypt(plaintext, vault_id='test_id', method_name='rot13')

        self.assertIsInstance(b_vaulttext, bytes)

        b_header = b'$ANSIBLE_VAULT;1.2;ROT13;test_id\n'
        self.assertEqual(b_vaulttext[:len(b_header)], b_header)

    def test_encrypt_bytes(self):

        plaintext = to_bytes(u'Some text to encrypt in a café')
        b_vaulttext = self.v.encrypt(plaintext, method_name='rot13')

        self.assertIsInstance(b_vaulttext, bytes)

        b_header = b'$ANSIBLE_VAULT;1.1;ROT13\n'
        self.assertEqual(b_vaulttext[:len(b_header)], b_header)

    def test_encrypt_no_secret_empty_secrets(self):
        vault_secrets = []
        v = vault.VaultLib(vault_secrets)

        plaintext = u'Some text to encrypt in a café'
        self.assertRaisesRegex(vault.AnsibleVaultError,
                               '.*A vault password must be specified to encrypt data.*',
                               v.encrypt,
                               plaintext)

    def test_decrypt_no_secrets(self):
        vl = vault.VaultLib([])

        with pytest.raises(AnsibleVaultError) as err:
            vl.decrypt(b'$ANSIBLE_VAULT;1.1;V2', filename=None)

        assert "password must be specified" in err.value.message

    def test_format_vaulttext_envelope(self):
        method_name = "TEST"
        b_ciphertext = b"ansible"
        b_vaulttext = vault.format_vaulttext_envelope(b_ciphertext,
                                                      method_name,
                                                      version=self.v.b_version,
                                                      vault_id='default')
        b_lines = b_vaulttext.split(b'\n')
        self.assertGreater(len(b_lines), 1, msg="failed to properly add header")

        b_header = b_lines[0]

        b_header_parts = b_header.split(b';')
        self.assertEqual(len(b_header_parts), 4, msg="header has the wrong number of parts")
        self.assertEqual(b_header_parts[0], b'$ANSIBLE_VAULT', msg="header does not start with $ANSIBLE_VAULT")
        self.assertEqual(b_header_parts[1], self.v.b_version, msg="header version is incorrect")
        self.assertEqual(b_header_parts[2], b'TEST', msg="header does not end with method name")

        # And just to verify, lets parse the results and compare
        b_ciphertext2, b_version2, method_name2, vault_id2 = \
            vault.parse_vaulttext_envelope(b_vaulttext)
        self.assertEqual(b_ciphertext, b_ciphertext2)
        self.assertEqual(self.v.b_version, b_version2)
        self.assertEqual(method_name, method_name2)
        self.assertEqual('default', vault_id2)

    def test_parse_vaulttext_envelope(self):
        b_vaulttext = b"$ANSIBLE_VAULT;1.1;TEST\nansible"
        b_ciphertext, b_version, method_name, vault_id = vault.parse_vaulttext_envelope(b_vaulttext)
        b_lines = b_ciphertext.split(b'\n')
        self.assertEqual(b_lines[0], b"ansible", msg="Payload was not properly split from the header")
        self.assertEqual(method_name, u'TEST', msg="method name was not properly set")
        self.assertEqual(b_version, b"1.1", msg="version was not properly set")

    def test_parse_vaulttext_envelope_crlf(self):
        b_vaulttext = b"$ANSIBLE_VAULT;1.1;TEST\r\nansible"
        b_ciphertext, b_version, method_name, vault_id = vault.parse_vaulttext_envelope(b_vaulttext)
        b_lines = b_ciphertext.split(b'\n')
        self.assertEqual(b_lines[0], b"ansible", msg="Payload was not properly split from the header")
        self.assertEqual(method_name, u'TEST', msg="method name was not properly set")
        self.assertEqual(b_version, b"1.1", msg="version was not properly set")

    def test_parse_vaulttext_envelope_bad_version(self):
        b_vaulttext = b"$ANSIBLE_VAULT;9.0;TEST\r\nThis is not valid'"
        with pytest.raises(AnsibleVaultFormatError) as err:
            ignore = vault.parse_vaulttext_envelope(b_vaulttext)
        assert "Unsupported vault version" in err.value.message

    def test_parse_vaulttext_envelope_bad(self):
        b_vaulttext = b"$ANSIBLE_VAULT;this is not valid\n at all"
        with pytest.raises(AnsibleVaultFormatError) as err:
            ignore = vault.parse_vaulttext_envelope(b_vaulttext)
        assert "Incorrect vault header" in err.value.message

    def test_parse_vaulttext_envelope_bad_match(self):
        b_vaulttext = b"$ANSIBLE_VAULT;1.1;TEST;TESTID\r\nThis is not a valid\n ansible vault'"
        with pytest.raises(AnsibleVaultFormatError) as err:
            ignore = vault.parse_vaulttext_envelope(b_vaulttext)
        assert "Vault header size mismatch" in err.value.message

    def test_parse_vaulttext_envelope_bad_format(self):
        b_vaulttext = [b"$ANSIBLE_VAULT;1.1;TEST;TESTID\r\nThis is not a valid\n ansible vault'"]
        with pytest.raises(AnsibleVaultFormatError) as err:
            ignore = vault.parse_vaulttext_envelope(b_vaulttext)
        assert "Vault envelope format is invalid" in err.value.message

    def test_decrypt_decrypted(self):
        plaintext = u"ansible"
        self.assertRaises(errors.AnsibleError, self.v.decrypt, plaintext)

        b_plaintext = b"ansible"
        self.assertRaises(errors.AnsibleError, self.v.decrypt, b_plaintext)

    def test_method_not_set(self):
        plaintext = u"ansible"
        vaulttext = self.v.encrypt(plaintext, method_name='rot13')
        assert b'ROT13' in vaulttext

    def test_bogus_options(self):
        with pytest.raises(AnsibleVaultFormatError):
            self.v.encrypt("whatever", salt=b"bogus, should fail", method_name='rot13')

    def test_bogus_method_encrypt(self):
        vl = vault.VaultLib(self.vault_secrets)

        with pytest.raises(AnsibleVaultError) as err:
            vl.encrypt(b'blah', method_name="bogus")

        assert "Unsupported vault method" in err.value.message

    def test_bogus_method_decrypt(self):
        with pytest.raises(AnsibleVaultError) as err:
            self.v.decrypt(b'$ANSIBLE_VAULT;1.1;BOGUS\n')

        assert "Unsupported vault method" in err.value.message


@pytest.mark.parametrize('vault_id', ('new\nline', 'semi;colon'))
@pytest.mark.usefixtures(patch_rot13_import.__name__)
def test_encrypt_vault_id_with_invalid_character(vault_id: str) -> None:
    vault_lib = vault.VaultLib([('default', TextVaultSecret('password'))])

    with pytest.raises(ValueError) as error:
        vault_lib.encrypt('', vault_id=vault_id, method_name='rot13')

    assert str(error.value).startswith('Invalid character')
