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


# Unicode like object that is not evaluated (decrypted) until it needs to be
# TODO: is there a reason these objects are subclasses for YAMLObject?
class AnsibleVaultEncryptedUnicode(yaml.YAMLObject, AnsibleUnicode):
    __UNSAFE__ = True
    __ENCRYPTED__ = True
    yaml_tag = u'!vault'

    @classmethod
    def from_plaintext(cls, seq, vault):
        if not vault:
            raise vault.AnsibleVaultError('Error creating AnsibleVaultEncryptedUnicode, invalid vault (%s) provided' % vault)

        ciphertext = vault.encrypt(seq)
        avu = cls(ciphertext)
        avu.vault = vault
        return avu

    def __init__(self, ciphertext):
        '''A AnsibleUnicode with a Vault attribute that can decrypt it.

        ciphertext is a byte string (str on PY2, bytestring on PY3).

        The .data atttribute is a property that returns the decrypted plaintext
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
        return self.vault.decrypt(self._ciphertext).decode()

    @data.setter
    def data(self, value):
        self._ciphertext = value

    def __repr__(self):
        return repr(self.data)

    def __iter__(self):
        return iter(self.data)

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

    def __add__(self, other):
        return self.data + other

    def __len__(self, *args, **kwargs):
        return len(self.data, *args, **kwargs)

    def __getitem__(self, key):
        return self.data[key]

    def __getslice__(self, i, j):
        return self.data.__getslice__(i, j)

    def __format__(self, *args, **kwargs):
        return self.data.__format__(*args, **kwargs)

    def __contains__(self, *args, **kwargs):
        return self.data.__contains__(*args, **kwargs)

    def __str__(self):
        return str(self.data)

    def __unicode__(self):
        return unicode(self.data)

    def encode(self, encoding=None, errors='strict'):
        return self.data.encode(encoding, errors)

    def capitalize(self):
        return self.data.capitalize()

    def center(self, *args, **kwargs):
        return self.data.center(*args, **kwargs)

    def count(self, *args, **kwargs):
        return self.data.count(*args, **kwargs)

    def decode(self, *args, **kwargs):
        return self.data.decode(*args, **kwargs)

    def endswith(self, *args, **kwargs):
        return self.data.endswith(*args, **kwargs)

    def placeh(self, *args, **kwargs):
        return self.data.placeh(*args, **kwargs)

    def expandtabs(self, *args, **kwargs):
        return self.data.expandtabs(*args, **kwargs)

    def format(self, *args, **kwargs):
        return self.data.format(*args, **kwargs)

    def index(self, *args, **kwargs):
        return self.data.index(*args, **kwargs)

    def isalnum(self, *args, **kwargs):
        return self.data.isalnum(*args, **kwargs)

    def isalpha(self, *args, **kwargs):
        return self.data.isalpha(*args, **kwargs)

    def isdigit(self, *args, **kwargs):
        return self.data.isdigit(*args, **kwargs)

    def islower(self, *args, **kwargs):
        return self.data.islower(*args, **kwargs)

    def isspace(self, *args, **kwargs):
        return self.data.isspace(*args, **kwargs)

    def istitle(self, *args, **kwargs):
        return self.data.istitle(*args, **kwargs)

    def isupper(self, *args, **kwargs):
        return self.data.isupper(*args, **kwargs)

    def join(self, *args, **kwargs):
        return self.data.join(*args, **kwargs)

    def ljust(self, *args, **kwargs):
        return self.data.ljust(*args, **kwargs)

    def lower(self, *args, **kwargs):
        return self.data.lower(*args, **kwargs)

    def lstrip(self, chars=None):
        return self.data.lstrip(chars)

    def partition(self, *args, **kwargs):
        return self.data.partition(*args, **kwargs)

    def replace(self, old, new, count=None):
        if count is not None:
            return self.data.replace(old, new, count)
        return self.data.replace(old, new)

    def rfind(self, *args, **kwargs):
        return self.data.rfind(*args, **kwargs)

    def rpartition(self, sep):
        return self.data.rpartition(sep)

    def rsplit(self, sep=None, maxsplit=-1):
        return self.data.rsplit(sep, maxsplit)

    def rstrip(self, chars=None):
        return self.data.rstrip(chars)

    def split(self, sep=None, maxsplit=-1):
        return self.data.split(sep, maxsplit)

    def splitlines(self, *args, **kwargs):
        return self.data.splitlines(*args, **kwargs)

    def startswith(self, *args, **kwargs):
        return self.data.startswith(*args, **kwargs)

    def strip(self, *args, **kwargs):
        return self.data.strip(*args, **kwargs)

    def swapcase(self, *args, **kwargs):
        return self.data.swapcase(*args, **kwargs)

    def title(self):
        return self.data.title()

    def translate(self, *args, **kwargs):
        return self.data.translate(*args, **kwargs)

    def upper(self, *args, **kwargs):
        return self.data.upper(*args, **kwargs)

    def zfill(self, *args, **kwargs):
        return self.data.zfill(*args, **kwargs)

    def isnumberic(self, *args, **kwargs):
        return self.data.isnumberic(*args, **kwargs)

    def isdecimal(self, *args, **kwargs):
        return self.data.isdecimal(*args, **kwargs)

    # py3 only

    def casefold(self, *args, **kwargs):
        return self.data.casefold(*args, **kwargs)

    def format_map(self, *args, **kwargs):
        return self.data.format_map(*args, **kwargs)


#    def placeh(self, *args, **kwargs):
#        return self.data.placeh(*args, **kwargs)

#    def placeh(self, *args, **kwargs):
#        return self.data.placeh(*args, **kwargs)
