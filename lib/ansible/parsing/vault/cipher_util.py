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

from collections import defaultdict

from ansible.errors import AnsibleVaultError

from ansible.plugins import cipher_loader

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

PYCRYPTO_UPGRADE = "ansible-vault requires a newer version of pycrypto than the one installed on your platform." \
    " You may fix this with OS-specific commands such as: yum install python-devel; rpm -e --nodeps python-crypto; pip install pycrypto"

CIPHER_DECRYPT_WHITELIST = frozenset((u'AES', u'AES256'))
CIPHER_ENCRYPT_WHITELIST = frozenset((u'AES256',))

# Which is better is a judgement call, and here is how we rank our crypto children
cipher_impl_preference = {'cryptography': 100,
                          'PyCrypto': 50,
                          'other': 10,
                          'no_impl': 0,
                          "Larry's Original Crypto Shack and Shoe Repair": -1}


def get_impl_score(cph_class):
    # if plugin doesnt provide implementation attr, then it gets 0 points. But
    # we can still rank something lower...
    impl = getattr(cph_class, 'implementation', 'no_impl')
    # and default to 0 for unknown impl as well
    score = cipher_impl_preference.get(impl, 0)
    return score


def build_cipher_mapping():
    cipher_class_gen = cipher_loader.all(class_only=True)

    # map cipher_name -> list of classes that provide it
    mapping = defaultdict(list)

    for cc in cipher_class_gen:
        # a VaultCipher without a 'name' attribute isnt useful
        if not hasattr(cc, 'name'):
            continue
        mapping[cc.name].append(cc)

    for cipher_name, cipher_classes in mapping.items():
        for class_name in cipher_classes:
            display.debug('Found (%s) cipher plugin %s' % (cipher_name, class_name))

    cipher_mapping = {}

    # set our prefered cipher to be the class with the highest score (last in the list when sorted via get_score())
    for c_name, c_classes in mapping.items():
        cipher_mapping[c_name] = sorted(c_classes, key=get_impl_score).pop()

    return cipher_mapping


cipher_mapping = build_cipher_mapping()


def get_decrypt_cipher(cipher_name):
    cipher_class = None
    if cipher_name not in CIPHER_DECRYPT_WHITELIST:
        msg = "{0} is not a valid decryption cipher_name. The valid names are: {1}".format(cipher_name,
                                                                                           ','.join(CIPHER_DECRYPT_WHITELIST))
        raise AnsibleVaultError(msg)

    cipher_class = cipher_mapping.get(cipher_name, None)
    if not cipher_class:
        raise AnsibleVaultError("{0} decryption cipher could not be found".format(cipher_name))

    display.vvvv('Using cipher plugin %s implementation of decrypt cipher %s' % (cipher_class, cipher_name))
    return cipher_class


def get_encrypt_cipher(cipher_name):
    cipher_class = None
    if cipher_name not in CIPHER_ENCRYPT_WHITELIST:
        msg = "{0} is not a valid encryption cipher_name. The valid names are: {1}".format(cipher_name,
                                                                                           ','.join(CIPHER_ENCRYPT_WHITELIST))
        raise AnsibleVaultError(msg)

    cipher_class = cipher_mapping.get(cipher_name, None)
    if not cipher_class:
        raise AnsibleVaultError("{0} encryption cipher could not be found".format(cipher_name))

    display.vvvv('Using cipher plugin %s implementation of encrypt cipher %s' % (cipher_class, cipher_name))

    return cipher_class
