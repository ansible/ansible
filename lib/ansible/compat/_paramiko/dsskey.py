# Copyright (C) 2003-2007  Robey Pointer <robeypointer@gmail.com>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.

"""
DSS keys.
"""

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives.asymmetric.utils import (
    decode_dss_signature,
    encode_dss_signature,
)

from paramiko import util
from paramiko.common import zero_byte
from paramiko.ssh_exception import SSHException
from paramiko.message import Message
from paramiko.ber import BER, BERException
from paramiko.pkey import PKey


class DSSKey(PKey):
    """
    Representation of a DSS key which can be used to sign an verify SSH2
    data.
    """

    def __init__(
        self,
        msg=None,
        data=None,
        filename=None,
        password=None,
        vals=None,
        file_obj=None,
    ):
        self.p = None
        self.q = None
        self.g = None
        self.y = None
        self.x = None
        self.public_blob = None
        if file_obj is not None:
            self._from_private_key(file_obj, password)
            return
        if filename is not None:
            self._from_private_key_file(filename, password)
            return
        if (msg is None) and (data is not None):
            msg = Message(data)
        if vals is not None:
            self.p, self.q, self.g, self.y = vals
        else:
            self._check_type_and_load_cert(
                msg=msg,
                key_type="ssh-dss",
                cert_type="ssh-dss-cert-v01@openssh.com",
            )
            self.p = msg.get_mpint()
            self.q = msg.get_mpint()
            self.g = msg.get_mpint()
            self.y = msg.get_mpint()
        self.size = util.bit_length(self.p)

    def asbytes(self):
        m = Message()
        m.add_string("ssh-dss")
        m.add_mpint(self.p)
        m.add_mpint(self.q)
        m.add_mpint(self.g)
        m.add_mpint(self.y)
        return m.asbytes()

    def __str__(self):
        return self.asbytes()

    def __hash__(self):
        return hash((self.get_name(), self.p, self.q, self.g, self.y))

    def get_name(self):
        return "ssh-dss"

    def get_bits(self):
        return self.size

    def can_sign(self):
        return self.x is not None

    def sign_ssh_data(self, data):
        key = dsa.DSAPrivateNumbers(
            x=self.x,
            public_numbers=dsa.DSAPublicNumbers(
                y=self.y,
                parameter_numbers=dsa.DSAParameterNumbers(
                    p=self.p, q=self.q, g=self.g
                ),
            ),
        ).private_key(backend=default_backend())
        sig = key.sign(data, hashes.SHA1())
        r, s = decode_dss_signature(sig)

        m = Message()
        m.add_string("ssh-dss")
        # apparently, in rare cases, r or s may be shorter than 20 bytes!
        rstr = util.deflate_long(r, 0)
        sstr = util.deflate_long(s, 0)
        if len(rstr) < 20:
            rstr = zero_byte * (20 - len(rstr)) + rstr
        if len(sstr) < 20:
            sstr = zero_byte * (20 - len(sstr)) + sstr
        m.add_string(rstr + sstr)
        return m

    def verify_ssh_sig(self, data, msg):
        if len(msg.asbytes()) == 40:
            # spies.com bug: signature has no header
            sig = msg.asbytes()
        else:
            kind = msg.get_text()
            if kind != "ssh-dss":
                return 0
            sig = msg.get_binary()

        # pull out (r, s) which are NOT encoded as mpints
        sigR = util.inflate_long(sig[:20], 1)
        sigS = util.inflate_long(sig[20:], 1)

        signature = encode_dss_signature(sigR, sigS)

        key = dsa.DSAPublicNumbers(
            y=self.y,
            parameter_numbers=dsa.DSAParameterNumbers(
                p=self.p, q=self.q, g=self.g
            ),
        ).public_key(backend=default_backend())
        try:
            key.verify(signature, data, hashes.SHA1())
        except InvalidSignature:
            return False
        else:
            return True

    def write_private_key_file(self, filename, password=None):
        key = dsa.DSAPrivateNumbers(
            x=self.x,
            public_numbers=dsa.DSAPublicNumbers(
                y=self.y,
                parameter_numbers=dsa.DSAParameterNumbers(
                    p=self.p, q=self.q, g=self.g
                ),
            ),
        ).private_key(backend=default_backend())

        self._write_private_key_file(
            filename,
            key,
            serialization.PrivateFormat.TraditionalOpenSSL,
            password=password,
        )

    def write_private_key(self, file_obj, password=None):
        key = dsa.DSAPrivateNumbers(
            x=self.x,
            public_numbers=dsa.DSAPublicNumbers(
                y=self.y,
                parameter_numbers=dsa.DSAParameterNumbers(
                    p=self.p, q=self.q, g=self.g
                ),
            ),
        ).private_key(backend=default_backend())

        self._write_private_key(
            file_obj,
            key,
            serialization.PrivateFormat.TraditionalOpenSSL,
            password=password,
        )

    @staticmethod
    def generate(bits=1024, progress_func=None):
        """
        Generate a new private DSS key.  This factory function can be used to
        generate a new host key or authentication key.

        :param int bits: number of bits the generated key should be.
        :param progress_func: Unused
        :return: new `.DSSKey` private key
        """
        numbers = dsa.generate_private_key(
            bits, backend=default_backend()
        ).private_numbers()
        key = DSSKey(
            vals=(
                numbers.public_numbers.parameter_numbers.p,
                numbers.public_numbers.parameter_numbers.q,
                numbers.public_numbers.parameter_numbers.g,
                numbers.public_numbers.y,
            )
        )
        key.x = numbers.x
        return key

    # ...internals...

    def _from_private_key_file(self, filename, password):
        data = self._read_private_key_file("DSA", filename, password)
        self._decode_key(data)

    def _from_private_key(self, file_obj, password):
        data = self._read_private_key("DSA", file_obj, password)
        self._decode_key(data)

    def _decode_key(self, data):
        # private key file contains:
        # DSAPrivateKey = { version = 0, p, q, g, y, x }
        try:
            keylist = BER(data).decode()
        except BERException as e:
            raise SSHException("Unable to parse key file: " + str(e))
        if type(keylist) is not list or len(keylist) < 6 or keylist[0] != 0:
            raise SSHException(
                "not a valid DSA private key file (bad ber encoding)"
            )
        self.p = keylist[1]
        self.q = keylist[2]
        self.g = keylist[3]
        self.y = keylist[4]
        self.x = keylist[5]
        self.size = util.bit_length(self.p)
