from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import yaml
import sys

from ansible.module_utils.six import PY3
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode, AnsibleUnicode
from ansible.utils.unsafe_proxy import AnsibleUnsafeText, AnsibleUnsafeBytes
from ansible.parsing.vault import VaultEditor, VaultLib, AnsibleVaultError
from ansible.parsing.yaml.dumper import AnsibleDumper
from ansible.parsing.utils.yaml import from_yaml

# A custom Dumper is created here that uses AnsibleDumper representers but
# overrides the str representer to choose a format style based on the string.
# This needs a bit of work to behave correctly in Python 2.7
class VaultAnsibleDumper(yaml.SafeDumper):
    pass

def represent_str(self, data):
    tag = None
    if '\n' in data:
        style = '|'
    else:
        style = None
    tag = u'tag:yaml.org,2002:str'
    return self.represent_scalar(tag, data, style=style)

VaultAnsibleDumper.yaml_representers = AnsibleDumper.yaml_representers.copy()
yaml.add_representer(str, represent_str, Dumper=VaultAnsibleDumper)

class VaultYAMLEditor(VaultEditor):

    ALREADY_ENCRYPTED_MESSAGE = \
        'Already encrypted value found, all values must be plain strings'
    NON_STRING_VALUE_MESSAGE = \
        'Value of type {} found, all values must be strings.'

    def __init__(self, vault=None):
        self.vault = vault or VaultLib()

    def encrypt_file(self, filename, secret, vault_id=None, output_file=None):
        filename = self._real_path(filename)
        data = self._read_yaml(filename)
        self._update_nodes(data, self._encrypt_string_value)
        self._write_yaml(data, output_file or filename)

    def plaintext(self, file_name):
        data = self._read_yaml(file_name)
        self._decrypt_yaml_values(data)
        return self._dump_yaml(data)

    def decrypt_file(self, filename, output_file=None):
        filename = self._real_path(filename)
        data = self._read_yaml(filename)
        self._decrypt_yaml_values(data)
        self._write_yaml(data, output_file or filename)

    def rekey_file(self, file_name, new_vault_secret, new_encrypt_vault_id):
        file_name = self._real_path(file_name)
        data = self._read_yaml(file_name)
        rekey_vault = VaultLib(secrets=[(new_encrypt_vault_id,
                                         new_vault_secret)])
        self._rekey_yaml_values(data, rekey_vault)
        self._write_yaml(data, file_name)

    def _dump_yaml(self, data):
        return yaml.dump(data, Dumper=VaultAnsibleDumper, default_flow_style=False,
                         sort_keys=False)

    def _write_yaml(self, data, filename):
        encrypted_yaml = self._dump_yaml(data)
        self.write_data(encrypted_yaml, filename)

    def _decrypt_yaml_values(self, data):
        return self._update_nodes(data, self._decrypt_string_value)

    def _rekey_yaml_values(self, data, rekey_vault):
        return self._update_nodes(data,
                                  self._make_rekey_encrypted_value(rekey_vault))

    def _encrypt_string_value(self, value):
        if isinstance(value, str):
            encrypted_value = self.vault.encrypt(str(value))
            return AnsibleVaultEncryptedUnicode(encrypted_value)
        if isinstance(value, AnsibleUnicode):
            encrypted_value = self.vault.encrypt(str(value))
            return AnsibleVaultEncryptedUnicode(encrypted_value)
        if isinstance(value, AnsibleVaultEncryptedUnicode):
            raise AnsibleVaultError(self.ALREADY_ENCRYPTED_MESSAGE)
        raise AnsibleVaultError(
            self.NON_STRING_VALUE_MESSAGE.format(type(value)))

    def _decrypt_string_value(self, value):
        if isinstance(value, AnsibleVaultEncryptedUnicode):
            return value.data
        return value

    def _make_rekey_encrypted_value(self, rekey_vault):
        def rekey_encrypted_value(value):
            if isinstance(value, AnsibleVaultEncryptedUnicode):
                encrypted_value = rekey_vault.encrypt(str(value.data))
                return AnsibleVaultEncryptedUnicode(encrypted_value)
            return value
        return rekey_encrypted_value

    def _read_yaml(self, file_name):
        file_name = self._real_path(file_name)
        if file_name == '-':
            data = from_yaml(sys.stdin.read(), file_name=file_name,
                             vault_secrets=self.vault.secrets)
        else:
            with open(file_name, "rb") as fh:
                data = from_yaml(fh, file_name=file_name,
                                 vault_secrets=self.vault.secrets)
        return data

    def _update_nodes(self, obj, fn):
        '''
        Walk every element in a nested python data dictonary/list structure and
        apply fn(value) to every value that isn't a list or dict. This
        updates the data structure in-place.
        '''
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    self._update_nodes(value, fn)
                else:
                    obj[key] = fn(value)
        if isinstance(obj, list):
            for index, value in enumerate(obj):
                if isinstance(value, (dict, list)):
                    self._update_nodes(value, fn)
                else:
                    obj[index] = fn(value)
        return obj
