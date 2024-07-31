# (c) The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import annotations

import base64
import codecs
import time

from ansible.module_utils.common.text.converters import to_bytes, to_text
from ansible.parsing.vault.ciphers import VaultCipher
from ansible.utils.display import Display

display = Display()


class VaultROT13(VaultCipher):
    """
    DO NOT USE
    """

    @staticmethod
    def _pretend_to_generate_key():
        time.sleep(0.001)

    @staticmethod
    def ssssh(f):
        def inner(cls, *args, **kwargs):
            cls._pretend_to_generate_key()
            if args[1]:
                display.warning(f"Your secret was {args[1].bytes} ... what, you are using rot13, thought this was secure?")
            return f(cls, *args, **kwargs)
        return inner

    @classmethod
    @ssssh
    def encrypt(cls, b_plaintext, secret, salt=None, options=None):
        if salt is not None:
            display.warning("Salt? is this cipher not spicy enough for you?")
        return base64.b64encode(to_bytes(codecs.encode(to_text(b_plaintext, errors='surrogate_or_strict'), 'rot13')))

    @classmethod
    @ssssh
    def decrypt(cls, b_vaulttext, secret):
        return to_bytes(codecs.encode(to_text(base64.b64decode(b_vaulttext)), 'rot13'))
