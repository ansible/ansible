# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distrubuted in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.

import bcrypt

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher

import nacl.signing

import six

from paramiko.message import Message
from paramiko.pkey import PKey
from paramiko.py3compat import b
from paramiko.ssh_exception import SSHException, PasswordRequiredException


OPENSSH_AUTH_MAGIC = b"openssh-key-v1\x00"


def unpad(data):
    # At the moment, this is only used for unpadding private keys on disk. This
    # really ought to be made constant time (possibly by upstreaming this logic
    # into pyca/cryptography).
    padding_length = six.indexbytes(data, -1)
    if padding_length > 16:
        raise SSHException("Invalid key")
    for i in range(1, padding_length + 1):
        if six.indexbytes(data, -i) != (padding_length - i + 1):
            raise SSHException("Invalid key")
    return data[:-padding_length]


class Ed25519Key(PKey):
    """
    Representation of an `Ed25519 <https://ed25519.cr.yp.to/>`_ key.

    .. note::
        Ed25519 key support was added to OpenSSH in version 6.5.

    .. versionadded:: 2.2
    .. versionchanged:: 2.3
        Added a ``file_obj`` parameter to match other key classes.
    """

    def __init__(
        self, msg=None, data=None, filename=None, password=None, file_obj=None
    ):
        self.public_blob = None
        verifying_key = signing_key = None
        if msg is None and data is not None:
            msg = Message(data)
        if msg is not None:
            self._check_type_and_load_cert(
                msg=msg,
                key_type="ssh-ed25519",
                cert_type="ssh-ed25519-cert-v01@openssh.com",
            )
            verifying_key = nacl.signing.VerifyKey(msg.get_binary())
        elif filename is not None:
            with open(filename, "r") as f:
                data = self._read_private_key("OPENSSH", f)
        elif file_obj is not None:
            data = self._read_private_key("OPENSSH", file_obj)

        if filename or file_obj:
            signing_key = self._parse_signing_key_data(data, password)

        if signing_key is None and verifying_key is None:
            raise ValueError("need a key")

        self._signing_key = signing_key
        self._verifying_key = verifying_key

    def _parse_signing_key_data(self, data, password):
        from paramiko.transport import Transport

        # We may eventually want this to be usable for other key types, as
        # OpenSSH moves to it, but for now this is just for Ed25519 keys.
        # This format is described here:
        # https://github.com/openssh/openssh-portable/blob/master/PROTOCOL.key
        # The description isn't totally complete, and I had to refer to the
        # source for a full implementation.
        message = Message(data)
        if message.get_bytes(len(OPENSSH_AUTH_MAGIC)) != OPENSSH_AUTH_MAGIC:
            raise SSHException("Invalid key")

        ciphername = message.get_text()
        kdfname = message.get_text()
        kdfoptions = message.get_binary()
        num_keys = message.get_int()

        if kdfname == "none":
            # kdfname of "none" must have an empty kdfoptions, the ciphername
            # must be "none"
            if kdfoptions or ciphername != "none":
                raise SSHException("Invalid key")
        elif kdfname == "bcrypt":
            if not password:
                raise PasswordRequiredException(
                    "Private key file is encrypted"
                )
            kdf = Message(kdfoptions)
            bcrypt_salt = kdf.get_binary()
            bcrypt_rounds = kdf.get_int()
        else:
            raise SSHException("Invalid key")

        if ciphername != "none" and ciphername not in Transport._cipher_info:
            raise SSHException("Invalid key")

        public_keys = []
        for _ in range(num_keys):
            pubkey = Message(message.get_binary())
            if pubkey.get_text() != "ssh-ed25519":
                raise SSHException("Invalid key")
            public_keys.append(pubkey.get_binary())

        private_ciphertext = message.get_binary()
        if ciphername == "none":
            private_data = private_ciphertext
        else:
            cipher = Transport._cipher_info[ciphername]
            key = bcrypt.kdf(
                password=b(password),
                salt=bcrypt_salt,
                desired_key_bytes=cipher["key-size"] + cipher["block-size"],
                rounds=bcrypt_rounds,
                # We can't control how many rounds are on disk, so no sense
                # warning about it.
                ignore_few_rounds=True,
            )
            decryptor = Cipher(
                cipher["class"](key[: cipher["key-size"]]),
                cipher["mode"](key[cipher["key-size"] :]),
                backend=default_backend(),
            ).decryptor()
            private_data = (
                decryptor.update(private_ciphertext) + decryptor.finalize()
            )

        message = Message(unpad(private_data))
        if message.get_int() != message.get_int():
            raise SSHException("Invalid key")

        signing_keys = []
        for i in range(num_keys):
            if message.get_text() != "ssh-ed25519":
                raise SSHException("Invalid key")
            # A copy of the public key, again, ignore.
            public = message.get_binary()
            key_data = message.get_binary()
            # The second half of the key data is yet another copy of the public
            # key...
            signing_key = nacl.signing.SigningKey(key_data[:32])
            # Verify that all the public keys are the same...
            assert (
                signing_key.verify_key.encode()
                == public
                == public_keys[i]
                == key_data[32:]
            )
            signing_keys.append(signing_key)
            # Comment, ignore.
            message.get_binary()

        if len(signing_keys) != 1:
            raise SSHException("Invalid key")
        return signing_keys[0]

    def asbytes(self):
        if self.can_sign():
            v = self._signing_key.verify_key
        else:
            v = self._verifying_key
        m = Message()
        m.add_string("ssh-ed25519")
        m.add_string(v.encode())
        return m.asbytes()

    def __hash__(self):
        if self.can_sign():
            v = self._signing_key.verify_key
        else:
            v = self._verifying_key
        return hash((self.get_name(), v))

    def get_name(self):
        return "ssh-ed25519"

    def get_bits(self):
        return 256

    def can_sign(self):
        return self._signing_key is not None

    def sign_ssh_data(self, data):
        m = Message()
        m.add_string("ssh-ed25519")
        m.add_string(self._signing_key.sign(data).signature)
        return m

    def verify_ssh_sig(self, data, msg):
        if msg.get_text() != "ssh-ed25519":
            return False

        try:
            self._verifying_key.verify(data, msg.get_binary())
        except nacl.exceptions.BadSignatureError:
            return False
        else:
            return True
