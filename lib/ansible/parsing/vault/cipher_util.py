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


from ansible.errors import AnsibleVaultError
from ansible.module_utils._text import to_text


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

PYCRYPTO_UPGRADE = "ansible-vault requires a newer version of pycrypto than the one installed on your platform." \
    " You may fix this with OS-specific commands such as: yum install python-devel; rpm -e --nodeps python-crypto; pip install pycrypto"

CIPHER_DECRYPT_WHITELIST = frozenset((u'AES', u'AES256'))
CIPHER_ENCRYPT_WHITELIST = frozenset((u'AES256',))

CIPHER_MAPPING = {}

VaultAES256 = VaultAES = None

# We have to find a VaultAES256 implementation, error if we do not

# FIXME: remove this and turn it on when we have a cryptography impl
WARN_CRYPTOGRAPHY = False

try:
    from ansible.parsing.vault.ciphers._cryptography import VaultAES256
except ImportError as e:
    if WARN_CRYPTOGRAPHY:
        display.warning('yo, cryptography is better than pycrypto but we failed to import it: %s' % to_text(e))
    try:
        from ansible.parsing.vault.ciphers._pycrypto import VaultAES256
    except ImportError as e:
        # If we want to support not having either (assuming no vault usage) we could let this pass with warning
        raise AnsibleVaultError("ansible-vault needs either 'PyCrypto' or 'cryptography' python modules but neither was found: %s" % to_text(e))

# but we usually dont need a VaultAES implementation, so its ok if we dont find one. If we need it later and
# dont have it, we will throw an error then.
try:
    from ansible.parsing.vault.ciphers._cryptography import VaultAES
except ImportError as e:
    if WARN_CRYPTOGRAPHY:
        display.warning('yo, cryptography is better than pycrypto but we failed to import it: %s' % to_text(e))
    try:
        from ansible.parsing.vault.ciphers._pycrypto import VaultAES
    except ImportError as e:
        display.warning('huh, we didnt find an implementation of VaultAES but we probably dont need it anyway: %s ' % to_text(e))

if VaultAES256:
    CIPHER_MAPPING[u'AES256'] = VaultAES256
if VaultAES:
    CIPHER_MAPPING[u'AES'] = VaultAES


def get_decrypt_cipher(cipher_name):
    cipher_class = None
    if cipher_name not in CIPHER_DECRYPT_WHITELIST:
        msg = "{0} is not a valid decryption cipher_name. The valid names are: {1}".format(cipher_name,
                                                                                           ','.join(CIPHER_DECRYPT_WHITELIST))
        raise AnsibleVaultError(msg)

    cipher_class = CIPHER_MAPPING.get(cipher_name, None)
    if not cipher_class:
        raise AnsibleVaultError("{0} decryption cipher could not be found".format(cipher_name))

    return cipher_class


def get_encrypt_cipher(cipher_name):
    cipher_class = None
    if cipher_name not in CIPHER_ENCRYPT_WHITELIST:
        msg = "{0} is not a valid encryption cipher_name. The valid names are: {1}".format(cipher_name,
                                                                                           ','.join(CIPHER_ENCRYPT_WHITELIST))
        raise AnsibleVaultError(msg)

    cipher_class = CIPHER_MAPPING.get(cipher_name, None)
    if not cipher_class:
        raise AnsibleVaultError("{0} encryption cipher could not be found".format(cipher_name))

    return cipher_class
