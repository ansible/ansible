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

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


# TODO: vault_envelope to plugin
# TODO: decide where envelope starts/stops
class VaultCipherBase:
    # TODO: add a 'cipher_options' arg for cipher specific info?
    def encrypt(self, b_plaintext, b_password):
        # return b_ciphertext (as bytes) (not the entire envelope, but the encrypted ciphertext and signatures/hmacs/salts/etc
        # ready to be wrapped in a vault envelope
        pass

    def decrypt(self, b_vaulttext, b_password):
        # b_vaulttest is bytes of text from the vault format after the header has been split off.
        # Basically, whatever self.encrypt() returns, self.decrypt() should take as its first argument and vice versa
        # returns b_plaintext bytes
        pass
