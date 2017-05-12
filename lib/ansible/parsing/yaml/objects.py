# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import yaml

from ansible.module_utils.six import text_type
from ansible.module_utils._text import to_bytes


class AnsibleBaseYAMLObject(object):
    '''
    the base class used to sub-class python built-in objects
    so that we can add attributes to them during yaml parsing

    '''
    _data_source = None
    _line_number = 0
    _column_number = 0

    def _get_ansible_position(self):
        return (self._data_source, self._line_number, self._column_number)

    def _set_ansible_position(self, obj):
        try:
            (src, line, col) = obj
        except (TypeError, ValueError):
            raise AssertionError(
                'ansible_pos can only be set with a tuple/list '
                'of three values: source, line number, column number'
            )
        self._data_source = src
        self._line_number = line
        self._column_number = col

    ansible_pos = property(_get_ansible_position, _set_ansible_position)


class AnsibleMapping(AnsibleBaseYAMLObject, dict):
    ''' sub class for dictionaries '''
    pass


class AnsibleUnicode(AnsibleBaseYAMLObject, text_type):
    ''' sub class for unicode objects '''
    pass


class AnsibleSequence(AnsibleBaseYAMLObject, list):
    ''' sub class for lists '''
    pass


class AnsibleVaultEncryptedUnicode(AnsibleUnicode):
    __UNSAFE__ = True
    __ENCRYPTED__ = True

    @classmethod
    def from_plaintext_and_vault(cls, seq, vault):
        if not vault:
            raise vault.AnsibleVaultError('Error creating AnsibleVaultEncryptedUnicode, invalid vault (%s) provided' % vault)

        b_ciphertext = vault.encrypt(seq)
        avu = cls(seq)
        avu.b_ciphertext = b_ciphertext
        avu.vault = vault
        return avu

    @classmethod
    def from_ciphertext_and_vault(cls, b_ciphertext, vault):
        if not vault:
            raise vault.AnsibleVaultError('Error creating AnsibleVaultEncryptedUnicode, invalid vault (%s) provided' % vault)

        plaintext = vault.decrypt(b_ciphertext)

        avu = cls(plaintext)
        avu.b_ciphertext = b_ciphertext
        avu.vault = vault
        return avu

    def __init__(self, seq):
        super(AnsibleVaultEncryptedUnicode, self).__init__(seq)
        self.vault = None
        self.b_ciphertext = None
