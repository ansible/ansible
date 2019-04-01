"""
Ephemeral Elliptic Curve Diffie-Hellman (ECDH) key exchange
RFC 5656, Section 4
"""

from hashlib import sha256, sha384, sha512
from paramiko.message import Message
from paramiko.py3compat import byte_chr, long
from paramiko.ssh_exception import SSHException
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from binascii import hexlify

_MSG_KEXECDH_INIT, _MSG_KEXECDH_REPLY = range(30, 32)
c_MSG_KEXECDH_INIT, c_MSG_KEXECDH_REPLY = [byte_chr(c) for c in range(30, 32)]


class KexNistp256:

    name = "ecdh-sha2-nistp256"
    hash_algo = sha256
    curve = ec.SECP256R1()

    def __init__(self, transport):
        self.transport = transport
        # private key, client public and server public keys
        self.P = long(0)
        self.Q_C = None
        self.Q_S = None

    def start_kex(self):
        self._generate_key_pair()
        if self.transport.server_mode:
            self.transport._expect_packet(_MSG_KEXECDH_INIT)
            return
        m = Message()
        m.add_byte(c_MSG_KEXECDH_INIT)
        # SEC1: V2.0  2.3.3 Elliptic-Curve-Point-to-Octet-String Conversion
        m.add_string(self.Q_C.public_numbers().encode_point())
        self.transport._send_message(m)
        self.transport._expect_packet(_MSG_KEXECDH_REPLY)

    def parse_next(self, ptype, m):
        if self.transport.server_mode and (ptype == _MSG_KEXECDH_INIT):
            return self._parse_kexecdh_init(m)
        elif not self.transport.server_mode and (ptype == _MSG_KEXECDH_REPLY):
            return self._parse_kexecdh_reply(m)
        raise SSHException(
            "KexECDH asked to handle packet type {:d}".format(ptype)
        )

    def _generate_key_pair(self):
        self.P = ec.generate_private_key(self.curve, default_backend())
        if self.transport.server_mode:
            self.Q_S = self.P.public_key()
            return
        self.Q_C = self.P.public_key()

    def _parse_kexecdh_init(self, m):
        Q_C_bytes = m.get_string()
        self.Q_C = ec.EllipticCurvePublicNumbers.from_encoded_point(
            self.curve, Q_C_bytes
        )
        K_S = self.transport.get_server_key().asbytes()
        K = self.P.exchange(ec.ECDH(), self.Q_C.public_key(default_backend()))
        K = long(hexlify(K), 16)
        # compute exchange hash
        hm = Message()
        hm.add(
            self.transport.remote_version,
            self.transport.local_version,
            self.transport.remote_kex_init,
            self.transport.local_kex_init,
        )
        hm.add_string(K_S)
        hm.add_string(Q_C_bytes)
        # SEC1: V2.0  2.3.3 Elliptic-Curve-Point-to-Octet-String Conversion
        hm.add_string(self.Q_S.public_numbers().encode_point())
        hm.add_mpint(long(K))
        H = self.hash_algo(hm.asbytes()).digest()
        self.transport._set_K_H(K, H)
        sig = self.transport.get_server_key().sign_ssh_data(H)
        # construct reply
        m = Message()
        m.add_byte(c_MSG_KEXECDH_REPLY)
        m.add_string(K_S)
        m.add_string(self.Q_S.public_numbers().encode_point())
        m.add_string(sig)
        self.transport._send_message(m)
        self.transport._activate_outbound()

    def _parse_kexecdh_reply(self, m):
        K_S = m.get_string()
        Q_S_bytes = m.get_string()
        self.Q_S = ec.EllipticCurvePublicNumbers.from_encoded_point(
            self.curve, Q_S_bytes
        )
        sig = m.get_binary()
        K = self.P.exchange(ec.ECDH(), self.Q_S.public_key(default_backend()))
        K = long(hexlify(K), 16)
        # compute exchange hash and verify signature
        hm = Message()
        hm.add(
            self.transport.local_version,
            self.transport.remote_version,
            self.transport.local_kex_init,
            self.transport.remote_kex_init,
        )
        hm.add_string(K_S)
        # SEC1: V2.0  2.3.3 Elliptic-Curve-Point-to-Octet-String Conversion
        hm.add_string(self.Q_C.public_numbers().encode_point())
        hm.add_string(Q_S_bytes)
        hm.add_mpint(K)
        self.transport._set_K_H(K, self.hash_algo(hm.asbytes()).digest())
        self.transport._verify_key(K_S, sig)
        self.transport._activate_outbound()


class KexNistp384(KexNistp256):
    name = "ecdh-sha2-nistp384"
    hash_algo = sha384
    curve = ec.SECP384R1()


class KexNistp521(KexNistp256):
    name = "ecdh-sha2-nistp521"
    hash_algo = sha512
    curve = ec.SECP521R1()
