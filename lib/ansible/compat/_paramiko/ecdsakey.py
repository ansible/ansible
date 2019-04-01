# Copyright (C) 2003-2007  Robey Pointer <robeypointer@gmail.com>
#
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

"""
ECDSA keys
"""

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import (
    decode_dss_signature,
    encode_dss_signature,
)

from paramiko.common import four_byte
from paramiko.message import Message
from paramiko.pkey import PKey
from paramiko.ssh_exception import SSHException
from paramiko.util import deflate_long


class _ECDSACurve(object):
    """
    Represents a specific ECDSA Curve (nistp256, nistp384, etc).

    Handles the generation of the key format identifier and the selection of
    the proper hash function. Also grabs the proper curve from the 'ecdsa'
    package.
    """

    def __init__(self, curve_class, nist_name):
        self.nist_name = nist_name
        self.key_length = curve_class.key_size

        # Defined in RFC 5656 6.2
        self.key_format_identifier = "ecdsa-sha2-" + self.nist_name

        # Defined in RFC 5656 6.2.1
        if self.key_length <= 256:
            self.hash_object = hashes.SHA256
        elif self.key_length <= 384:
            self.hash_object = hashes.SHA384
        else:
            self.hash_object = hashes.SHA512

        self.curve_class = curve_class


class _ECDSACurveSet(object):
    """
    A collection to hold the ECDSA curves. Allows querying by oid and by key
    format identifier. The two ways in which ECDSAKey needs to be able to look
    up curves.
    """

    def __init__(self, ecdsa_curves):
        self.ecdsa_curves = ecdsa_curves

    def get_key_format_identifier_list(self):
        return [curve.key_format_identifier for curve in self.ecdsa_curves]

    def get_by_curve_class(self, curve_class):
        for curve in self.ecdsa_curves:
            if curve.curve_class == curve_class:
                return curve

    def get_by_key_format_identifier(self, key_format_identifier):
        for curve in self.ecdsa_curves:
            if curve.key_format_identifier == key_format_identifier:
                return curve

    def get_by_key_length(self, key_length):
        for curve in self.ecdsa_curves:
            if curve.key_length == key_length:
                return curve


class ECDSAKey(PKey):
    """
    Representation of an ECDSA key which can be used to sign and verify SSH2
    data.
    """

    _ECDSA_CURVES = _ECDSACurveSet(
        [
            _ECDSACurve(ec.SECP256R1, "nistp256"),
            _ECDSACurve(ec.SECP384R1, "nistp384"),
            _ECDSACurve(ec.SECP521R1, "nistp521"),
        ]
    )

    def __init__(
        self,
        msg=None,
        data=None,
        filename=None,
        password=None,
        vals=None,
        file_obj=None,
        validate_point=True,
    ):
        self.verifying_key = None
        self.signing_key = None
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
            self.signing_key, self.verifying_key = vals
            c_class = self.signing_key.curve.__class__
            self.ecdsa_curve = self._ECDSA_CURVES.get_by_curve_class(c_class)
        else:
            # Must set ecdsa_curve first; subroutines called herein may need to
            # spit out our get_name(), which relies on this.
            key_type = msg.get_text()
            # But this also means we need to hand it a real key/curve
            # identifier, so strip out any cert business. (NOTE: could push
            # that into _ECDSACurveSet.get_by_key_format_identifier(), but it
            # feels more correct to do it here?)
            suffix = "-cert-v01@openssh.com"
            if key_type.endswith(suffix):
                key_type = key_type[: -len(suffix)]
            self.ecdsa_curve = self._ECDSA_CURVES.get_by_key_format_identifier(
                key_type
            )
            key_types = self._ECDSA_CURVES.get_key_format_identifier_list()
            cert_types = [
                "{}-cert-v01@openssh.com".format(x) for x in key_types
            ]
            self._check_type_and_load_cert(
                msg=msg, key_type=key_types, cert_type=cert_types
            )
            curvename = msg.get_text()
            if curvename != self.ecdsa_curve.nist_name:
                raise SSHException(
                    "Can't handle curve of type {}".format(curvename)
                )

            pointinfo = msg.get_binary()
            try:
                numbers = ec.EllipticCurvePublicNumbers.from_encoded_point(
                    self.ecdsa_curve.curve_class(), pointinfo
                )
            except ValueError:
                raise SSHException("Invalid public key")
            self.verifying_key = numbers.public_key(backend=default_backend())

    @classmethod
    def supported_key_format_identifiers(cls):
        return cls._ECDSA_CURVES.get_key_format_identifier_list()

    def asbytes(self):
        key = self.verifying_key
        m = Message()
        m.add_string(self.ecdsa_curve.key_format_identifier)
        m.add_string(self.ecdsa_curve.nist_name)

        numbers = key.public_numbers()

        key_size_bytes = (key.curve.key_size + 7) // 8

        x_bytes = deflate_long(numbers.x, add_sign_padding=False)
        x_bytes = b"\x00" * (key_size_bytes - len(x_bytes)) + x_bytes

        y_bytes = deflate_long(numbers.y, add_sign_padding=False)
        y_bytes = b"\x00" * (key_size_bytes - len(y_bytes)) + y_bytes

        point_str = four_byte + x_bytes + y_bytes
        m.add_string(point_str)
        return m.asbytes()

    def __str__(self):
        return self.asbytes()

    def __hash__(self):
        return hash(
            (
                self.get_name(),
                self.verifying_key.public_numbers().x,
                self.verifying_key.public_numbers().y,
            )
        )

    def get_name(self):
        return self.ecdsa_curve.key_format_identifier

    def get_bits(self):
        return self.ecdsa_curve.key_length

    def can_sign(self):
        return self.signing_key is not None

    def sign_ssh_data(self, data):
        ecdsa = ec.ECDSA(self.ecdsa_curve.hash_object())
        sig = self.signing_key.sign(data, ecdsa)
        r, s = decode_dss_signature(sig)

        m = Message()
        m.add_string(self.ecdsa_curve.key_format_identifier)
        m.add_string(self._sigencode(r, s))
        return m

    def verify_ssh_sig(self, data, msg):
        if msg.get_text() != self.ecdsa_curve.key_format_identifier:
            return False
        sig = msg.get_binary()
        sigR, sigS = self._sigdecode(sig)
        signature = encode_dss_signature(sigR, sigS)

        try:
            self.verifying_key.verify(
                signature, data, ec.ECDSA(self.ecdsa_curve.hash_object())
            )
        except InvalidSignature:
            return False
        else:
            return True

    def write_private_key_file(self, filename, password=None):
        self._write_private_key_file(
            filename,
            self.signing_key,
            serialization.PrivateFormat.TraditionalOpenSSL,
            password=password,
        )

    def write_private_key(self, file_obj, password=None):
        self._write_private_key(
            file_obj,
            self.signing_key,
            serialization.PrivateFormat.TraditionalOpenSSL,
            password=password,
        )

    @classmethod
    def generate(cls, curve=ec.SECP256R1(), progress_func=None, bits=None):
        """
        Generate a new private ECDSA key.  This factory function can be used to
        generate a new host key or authentication key.

        :param progress_func: Not used for this type of key.
        :returns: A new private key (`.ECDSAKey`) object
        """
        if bits is not None:
            curve = cls._ECDSA_CURVES.get_by_key_length(bits)
            if curve is None:
                raise ValueError("Unsupported key length: {:d}".format(bits))
            curve = curve.curve_class()

        private_key = ec.generate_private_key(curve, backend=default_backend())
        return ECDSAKey(vals=(private_key, private_key.public_key()))

    # ...internals...

    def _from_private_key_file(self, filename, password):
        data = self._read_private_key_file("EC", filename, password)
        self._decode_key(data)

    def _from_private_key(self, file_obj, password):
        data = self._read_private_key("EC", file_obj, password)
        self._decode_key(data)

    def _decode_key(self, data):
        try:
            key = serialization.load_der_private_key(
                data, password=None, backend=default_backend()
            )
        except (ValueError, AssertionError) as e:
            raise SSHException(str(e))

        self.signing_key = key
        self.verifying_key = key.public_key()
        curve_class = key.curve.__class__
        self.ecdsa_curve = self._ECDSA_CURVES.get_by_curve_class(curve_class)

    def _sigencode(self, r, s):
        msg = Message()
        msg.add_mpint(r)
        msg.add_mpint(s)
        return msg.asbytes()

    def _sigdecode(self, sig):
        msg = Message(sig)
        r = msg.get_mpint()
        s = msg.get_mpint()
        return r, s
