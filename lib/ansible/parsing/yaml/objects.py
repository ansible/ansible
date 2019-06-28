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
from ansible.module_utils._text import to_bytes, to_text, to_native


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


# Unicode like object that is not evaluated (decrypted) until it needs to be
# TODO: is there a reason these objects are subclasses for YAMLObject?
class AnsibleVaultEncryptedUnicode(yaml.YAMLObject, AnsibleBaseYAMLObject):
    __UNSAFE__ = True
    __ENCRYPTED__ = True
    yaml_tag = u'!vault'

    @classmethod
    def from_plaintext(cls, seq, vault, secret):
        if not vault:
            raise vault.AnsibleVaultError('Error creating AnsibleVaultEncryptedUnicode, invalid vault (%s) provided' % vault)

        ciphertext = vault.encrypt(seq, secret)
        avu = cls(ciphertext)
        avu.vault = vault
        return avu

    def __init__(self, ciphertext):
        '''A AnsibleUnicode with a Vault attribute that can decrypt it.

        ciphertext is a byte string (str on PY2, bytestring on PY3).

        The .data attribute is a property that returns the decrypted plaintext
        of the ciphertext as a PY2 unicode or PY3 string object.
        '''
        super(AnsibleVaultEncryptedUnicode, self).__init__()

        # after construction, calling code has to set the .vault attribute to a vaultlib object
        self.vault = None
        self._ciphertext = to_bytes(ciphertext)

    @property
    def data(self):
        if not self.vault:
            # FIXME: raise exception?
            return self._ciphertext
        return to_text(self.vault.decrypt(self._ciphertext))

    @data.setter
    def data(self, value):
        self._ciphertext = value

    def __repr__(self):
        return repr(self.data)

    # Compare a regular str/text_type with the decrypted hypertext
    def __eq__(self, other):
        if self.vault:
            return other == self.data
        return False

    def __hash__(self):
        return id(self)

    def __ne__(self, other):
        if self.vault:
            return other != self.data
        return True

    def __str__(self):
        return to_native(self.data, errors='surrogate_or_strict')

    def __unicode__(self):
        return to_text(self.data, errors='surrogate_or_strict')

    def encode(self, encoding=None, errors=None):
        return self.data.encode(encoding, errors)
