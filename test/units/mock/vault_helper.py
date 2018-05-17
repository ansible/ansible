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

from ansible.module_utils._text import to_bytes

from ansible.parsing.vault import VaultSecret


class TextVaultSecret(VaultSecret):
    '''A secret piece of text. ie, a password. Tracks text encoding.

    The text encoding of the text may not be the default text encoding so
    we keep track of the encoding so we encode it to the same bytes.'''

    def __init__(self, text, encoding=None, errors=None, _bytes=None):
        super(TextVaultSecret, self).__init__()
        self.text = text
        self.encoding = encoding or 'utf-8'
        self._bytes = _bytes
        self.errors = errors or 'strict'

    @property
    def bytes(self):
        '''The text encoded with encoding, unless we specifically set _bytes.'''
        return self._bytes or to_bytes(self.text, encoding=self.encoding, errors=self.errors)
