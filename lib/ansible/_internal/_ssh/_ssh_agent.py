# Copyright: Contributors to the Ansible project
# BSD 3 Clause License (see licenses/BSD-3-Clause.txt or https://opensource.org/license/bsd-3-clause/)

from __future__ import annotations

import binascii
import dataclasses
import enum
import functools
import hashlib
import socket
import types
import typing as t

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.dsa import (
        DSAParameterNumbers,
        DSAPrivateKey,
        DSAPublicKey,
        DSAPublicNumbers,
    )
    from cryptography.hazmat.primitives.asymmetric.ec import (
        EllipticCurve,
        EllipticCurvePrivateKey,
        EllipticCurvePublicKey,
        SECP256R1,
        SECP384R1,
        SECP521R1,
    )
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
    from cryptography.hazmat.primitives.asymmetric.rsa import (
        RSAPrivateKey,
        RSAPublicKey,
        RSAPublicNumbers,
    )
except ImportError:
    HAS_CRYPTOGRAPHY = False
else:
    HAS_CRYPTOGRAPHY = True

    CryptoPublicKey = t.Union[
        DSAPublicKey,
        EllipticCurvePublicKey,
        Ed25519PublicKey,
        RSAPublicKey,
    ]

    CryptoPrivateKey = t.Union[
        DSAPrivateKey,
        EllipticCurvePrivateKey,
        Ed25519PrivateKey,
        RSAPrivateKey,
    ]


if t.TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.dsa import DSAPrivateNumbers
    from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateNumbers
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateNumbers


_SSH_AGENT_CLIENT_SOCKET_TIMEOUT = 10
_SSH_AGENT_MAX_RESPONSE_BYTES = 256 * 1024  # not part of the RFC, just a safety measure


class ProtocolMsgNumbers(enum.IntEnum):
    # Responses
    SSH_AGENT_FAILURE = 5
    SSH_AGENT_SUCCESS = 6
    SSH_AGENT_IDENTITIES_ANSWER = 12
    SSH_AGENT_SIGN_RESPONSE = 14
    SSH_AGENT_EXTENSION_FAILURE = 28
    SSH_AGENT_EXTENSION_RESPONSE = 29

    # Constraints
    SSH_AGENT_CONSTRAIN_LIFETIME = 1
    SSH_AGENT_CONSTRAIN_CONFIRM = 2
    SSH_AGENT_CONSTRAIN_EXTENSION = 255

    # Requests
    SSH_AGENTC_REQUEST_IDENTITIES = 11
    SSH_AGENTC_SIGN_REQUEST = 13
    SSH_AGENTC_ADD_IDENTITY = 17
    SSH_AGENTC_REMOVE_IDENTITY = 18
    SSH_AGENTC_REMOVE_ALL_IDENTITIES = 19
    SSH_AGENTC_ADD_SMARTCARD_KEY = 20
    SSH_AGENTC_REMOVE_SMARTCARD_KEY = 21
    SSH_AGENTC_LOCK = 22
    SSH_AGENTC_UNLOCK = 23
    SSH_AGENTC_ADD_ID_CONSTRAINED = 25
    SSH_AGENTC_ADD_SMARTCARD_KEY_CONSTRAINED = 26
    SSH_AGENTC_EXTENSION = 27

    def to_blob(self) -> bytes:
        return bytes([self])


class SshAgentFailure(RuntimeError):
    """Server failure or unexpected response."""


# NOTE: Classes below somewhat represent "Data Type Representations Used in the SSH Protocols"
#       as specified by RFC4251


@t.runtime_checkable
class SupportsToBlob(t.Protocol):
    def to_blob(self) -> bytes: ...


@t.runtime_checkable
class SupportsFromBlob(t.Protocol):
    @classmethod
    def from_blob(cls, blob: memoryview | bytes) -> t.Self: ...

    @classmethod
    def consume_from_blob(cls, blob: memoryview | bytes) -> tuple[t.Self, memoryview | bytes]: ...


def _split_blob(blob: memoryview | bytes, length: int) -> tuple[memoryview | bytes, memoryview | bytes]:
    if len(blob) < length:
        raise ValueError("_split_blob: unexpected data length")
    return blob[:length], blob[length:]


class VariableSized:
    @classmethod
    def from_blob(cls, blob: memoryview | bytes) -> t.Self:
        raise NotImplementedError

    @classmethod
    def consume_from_blob(cls, blob: memoryview | bytes) -> tuple[t.Self, memoryview | bytes]:
        length = uint32.from_blob(blob[:4])
        blob = blob[4:]
        data, rest = _split_blob(blob, length)
        return cls.from_blob(data), rest


class uint32(int):
    def to_blob(self) -> bytes:
        return self.to_bytes(length=4, byteorder='big')

    @classmethod
    def from_blob(cls, blob: memoryview | bytes) -> t.Self:
        return cls.from_bytes(blob, byteorder='big')

    @classmethod
    def consume_from_blob(cls, blob: memoryview | bytes) -> tuple[t.Self, memoryview | bytes]:
        length = uint32(4)
        data, rest = _split_blob(blob, length)
        return cls.from_blob(data), rest


class mpint(int, VariableSized):
    def to_blob(self) -> bytes:
        if self < 0:
            raise ValueError("negative mpint not allowed")
        if self == 0:
            return uint32(self).to_blob()
        nbytes = (self.bit_length() + 8) // 8
        ret = bytearray(self.to_bytes(length=nbytes, byteorder='big'))
        ret[:0] = uint32(len(ret)).to_blob()
        return ret

    @classmethod
    def from_blob(cls, blob: memoryview | bytes) -> t.Self:
        if blob and blob[0] > 127:
            raise ValueError("Invalid data")
        return cls.from_bytes(blob, byteorder='big')


class constraints(bytes):
    def to_blob(self) -> bytes:
        return self


class binary_string(bytes, VariableSized):
    def to_blob(self) -> bytes:
        return uint32(len(self)).to_blob() + self

    @classmethod
    def from_blob(cls, blob: memoryview | bytes) -> t.Self:
        return cls(blob)


class unicode_string(str, VariableSized):
    def to_blob(self) -> bytes:
        val = self.encode('utf-8')
        return uint32(len(val)).to_blob() + val

    @classmethod
    def from_blob(cls, blob: memoryview | bytes) -> t.Self:
        return cls(bytes(blob).decode('utf-8'))


class KeyAlgo(VariableSized, enum.StrEnum):
    RSA = "ssh-rsa"
    DSA = "ssh-dss"
    ECDSA256 = "ecdsa-sha2-nistp256"
    SKECDSA256 = "sk-ecdsa-sha2-nistp256@openssh.com"
    ECDSA384 = "ecdsa-sha2-nistp384"
    ECDSA521 = "ecdsa-sha2-nistp521"
    ED25519 = "ssh-ed25519"
    SKED25519 = "sk-ssh-ed25519@openssh.com"
    RSASHA256 = "rsa-sha2-256"
    RSASHA512 = "rsa-sha2-512"

    @property
    def main_type(self) -> str:
        match self:
            case self.RSA:
                return 'RSA'
            case self.DSA:
                return 'DSA'
            case self.ECDSA256 | self.ECDSA384 | self.ECDSA521:
                return 'ECDSA'
            case self.ED25519:
                return 'ED25519'
            case _:
                raise NotImplementedError(self.name)

    def to_blob(self) -> bytes:
        b_self = self.encode('utf-8')
        return uint32(len(b_self)).to_blob() + b_self

    @classmethod
    def from_blob(cls, blob: memoryview | bytes) -> t.Self:
        return cls(bytes(blob).decode('utf-8'))


if HAS_CRYPTOGRAPHY:
    _ECDSA_KEY_TYPE: dict[KeyAlgo, type[EllipticCurve]] = {
        KeyAlgo.ECDSA256: SECP256R1,
        KeyAlgo.ECDSA384: SECP384R1,
        KeyAlgo.ECDSA521: SECP521R1,
    }


@dataclasses.dataclass
class Msg:
    def to_blob(self) -> bytes:
        rv = bytearray()
        for field in dataclasses.fields(self):
            fv = getattr(self, field.name)
            if isinstance(fv, SupportsToBlob):
                rv.extend(fv.to_blob())
            else:
                raise NotImplementedError(field.type)
        return rv

    @classmethod
    def from_blob(cls, blob: memoryview | bytes) -> t.Self:
        args: list[t.Any] = []
        for _field_name, field_type in t.get_type_hints(cls).items():
            if isinstance(field_type, SupportsFromBlob):
                fv, blob = field_type.consume_from_blob(blob)
                args.append(fv)
            else:
                raise NotImplementedError(str(field_type))
        return cls(*args)


@dataclasses.dataclass
class PrivateKeyMsg(Msg):
    @staticmethod
    def from_private_key(private_key: CryptoPrivateKey) -> PrivateKeyMsg:
        match private_key:
            case RSAPrivateKey():
                rsa_pn: RSAPrivateNumbers = private_key.private_numbers()
                return RSAPrivateKeyMsg(
                    KeyAlgo.RSA,
                    mpint(rsa_pn.public_numbers.n),
                    mpint(rsa_pn.public_numbers.e),
                    mpint(rsa_pn.d),
                    mpint(rsa_pn.iqmp),
                    mpint(rsa_pn.p),
                    mpint(rsa_pn.q),
                )
            case DSAPrivateKey():
                dsa_pn: DSAPrivateNumbers = private_key.private_numbers()
                return DSAPrivateKeyMsg(
                    KeyAlgo.DSA,
                    mpint(dsa_pn.public_numbers.parameter_numbers.p),
                    mpint(dsa_pn.public_numbers.parameter_numbers.q),
                    mpint(dsa_pn.public_numbers.parameter_numbers.g),
                    mpint(dsa_pn.public_numbers.y),
                    mpint(dsa_pn.x),
                )
            case EllipticCurvePrivateKey():
                ecdsa_pn: EllipticCurvePrivateNumbers = private_key.private_numbers()
                key_size = private_key.key_size
                return EcdsaPrivateKeyMsg(
                    getattr(KeyAlgo, f'ECDSA{key_size}'),
                    unicode_string(f'nistp{key_size}'),
                    binary_string(
                        private_key.public_key().public_bytes(
                            encoding=serialization.Encoding.X962,
                            format=serialization.PublicFormat.UncompressedPoint,
                        )
                    ),
                    mpint(ecdsa_pn.private_value),
                )
            case Ed25519PrivateKey():
                public_bytes = private_key.public_key().public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw,
                )
                private_bytes = private_key.private_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PrivateFormat.Raw,
                    encryption_algorithm=serialization.NoEncryption(),
                )
                return Ed25519PrivateKeyMsg(
                    KeyAlgo.ED25519,
                    binary_string(public_bytes),
                    binary_string(private_bytes + public_bytes),
                )
            case _:
                raise NotImplementedError(private_key)


@dataclasses.dataclass(order=True, slots=True)
class RSAPrivateKeyMsg(PrivateKeyMsg):
    type: KeyAlgo
    n: mpint
    e: mpint
    d: mpint
    iqmp: mpint
    p: mpint
    q: mpint
    comment: unicode_string = dataclasses.field(default=unicode_string(''), compare=False)
    constraints: constraints = dataclasses.field(default=constraints(b''))


@dataclasses.dataclass(order=True, slots=True)
class DSAPrivateKeyMsg(PrivateKeyMsg):
    type: KeyAlgo
    p: mpint
    q: mpint
    g: mpint
    y: mpint
    x: mpint
    comment: unicode_string = dataclasses.field(default=unicode_string(''), compare=False)
    constraints: constraints = dataclasses.field(default=constraints(b''))


@dataclasses.dataclass(order=True, slots=True)
class EcdsaPrivateKeyMsg(PrivateKeyMsg):
    type: KeyAlgo
    ecdsa_curve_name: unicode_string
    Q: binary_string
    d: mpint
    comment: unicode_string = dataclasses.field(default=unicode_string(''), compare=False)
    constraints: constraints = dataclasses.field(default=constraints(b''))


@dataclasses.dataclass(order=True, slots=True)
class Ed25519PrivateKeyMsg(PrivateKeyMsg):
    type: KeyAlgo
    enc_a: binary_string
    k_env_a: binary_string
    comment: unicode_string = dataclasses.field(default=unicode_string(''), compare=False)
    constraints: constraints = dataclasses.field(default=constraints(b''))


@dataclasses.dataclass
class PublicKeyMsg(Msg):
    @staticmethod
    def get_dataclass(type: KeyAlgo) -> type[
        t.Union[
            RSAPublicKeyMsg,
            EcdsaPublicKeyMsg,
            Ed25519PublicKeyMsg,
            DSAPublicKeyMsg,
        ]
    ]:
        match type:
            case KeyAlgo.RSA:
                return RSAPublicKeyMsg
            case KeyAlgo.ECDSA256 | KeyAlgo.ECDSA384 | KeyAlgo.ECDSA521:
                return EcdsaPublicKeyMsg
            case KeyAlgo.ED25519:
                return Ed25519PublicKeyMsg
            case KeyAlgo.DSA:
                return DSAPublicKeyMsg
            case _:
                raise NotImplementedError(type)

    @functools.cached_property
    def public_key(self) -> CryptoPublicKey:
        type: KeyAlgo = self.type
        match type:
            case KeyAlgo.RSA:
                return RSAPublicNumbers(self.e, self.n).public_key()
            case KeyAlgo.ECDSA256 | KeyAlgo.ECDSA384 | KeyAlgo.ECDSA521:
                curve = _ECDSA_KEY_TYPE[KeyAlgo(type)]
                return EllipticCurvePublicKey.from_encoded_point(curve(), self.Q)
            case KeyAlgo.ED25519:
                return Ed25519PublicKey.from_public_bytes(self.enc_a)
            case KeyAlgo.DSA:
                return DSAPublicNumbers(self.y, DSAParameterNumbers(self.p, self.q, self.g)).public_key()
            case _:
                raise NotImplementedError(type)

    @staticmethod
    def from_public_key(public_key: CryptoPublicKey) -> PublicKeyMsg:
        match public_key:
            case DSAPublicKey():
                dsa_pn: DSAPublicNumbers = public_key.public_numbers()
                return DSAPublicKeyMsg(
                    KeyAlgo.DSA,
                    mpint(dsa_pn.parameter_numbers.p),
                    mpint(dsa_pn.parameter_numbers.q),
                    mpint(dsa_pn.parameter_numbers.g),
                    mpint(dsa_pn.y),
                )
            case EllipticCurvePublicKey():
                return EcdsaPublicKeyMsg(
                    getattr(KeyAlgo, f'ECDSA{public_key.curve.key_size}'),
                    unicode_string(f'nistp{public_key.curve.key_size}'),
                    binary_string(
                        public_key.public_bytes(
                            encoding=serialization.Encoding.X962,
                            format=serialization.PublicFormat.UncompressedPoint,
                        )
                    ),
                )
            case Ed25519PublicKey():
                return Ed25519PublicKeyMsg(
                    KeyAlgo.ED25519,
                    binary_string(
                        public_key.public_bytes(
                            encoding=serialization.Encoding.Raw,
                            format=serialization.PublicFormat.Raw,
                        )
                    ),
                )
            case RSAPublicKey():
                rsa_pn: RSAPublicNumbers = public_key.public_numbers()
                return RSAPublicKeyMsg(KeyAlgo.RSA, mpint(rsa_pn.e), mpint(rsa_pn.n))
            case _:
                raise NotImplementedError(public_key)

    @functools.cached_property
    def fingerprint(self) -> str:
        return binascii.b2a_base64(hashlib.sha256(self.to_blob()).digest(), newline=False).rstrip(b'=').decode('utf-8')


@dataclasses.dataclass(order=True, slots=True)
class RSAPublicKeyMsg(PublicKeyMsg):
    type: KeyAlgo
    e: mpint
    n: mpint


@dataclasses.dataclass(order=True, slots=True)
class DSAPublicKeyMsg(PublicKeyMsg):
    type: KeyAlgo
    p: mpint
    q: mpint
    g: mpint
    y: mpint


@dataclasses.dataclass(order=True, slots=True)
class EcdsaPublicKeyMsg(PublicKeyMsg):
    type: KeyAlgo
    ecdsa_curve_name: unicode_string
    Q: binary_string


@dataclasses.dataclass(order=True, slots=True)
class Ed25519PublicKeyMsg(PublicKeyMsg):
    type: KeyAlgo
    enc_a: binary_string


@dataclasses.dataclass(order=True, frozen=True, slots=True)
class Identity:
    key: PublicKeyMsg
    comment: unicode_string


class SshAgentClient:
    def __init__(self, auth_sock: str) -> None:
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.settimeout(_SSH_AGENT_CLIENT_SOCKET_TIMEOUT)
        self._sock.connect(auth_sock)

    def close(self) -> None:
        self._sock.close()

    def __enter__(self) -> t.Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None:
        self.close()

    def _read_all(self, bytes_to_read: int) -> bytes:
        data_read = bytearray()
        while bytes_to_read:
            data = self._sock.recv(bytes_to_read)
            if not data:
                raise ConnectionError("agent: connection closed")
            bytes_to_read -= len(data)
            data_read.extend(data)
        return bytes(data_read)

    def send(self, msg: bytes) -> bytes:
        length = uint32(len(msg)).to_blob()
        self._sock.sendall(length + msg)
        bufsize = uint32.from_blob(self._read_all(4))
        if bufsize > _SSH_AGENT_MAX_RESPONSE_BYTES:
            raise SshAgentFailure("agent: response too large")
        resp = self._read_all(bufsize)
        if resp[0] == ProtocolMsgNumbers.SSH_AGENT_FAILURE:
            raise SshAgentFailure('agent: failure')
        return resp

    def remove_all(self) -> None:
        self.send(ProtocolMsgNumbers.SSH_AGENTC_REMOVE_ALL_IDENTITIES.to_blob())

    def remove(self, public_key: CryptoPublicKey) -> None:
        key_blob = PublicKeyMsg.from_public_key(public_key).to_blob()
        self.send(ProtocolMsgNumbers.SSH_AGENTC_REMOVE_IDENTITY.to_blob() + uint32(len(key_blob)).to_blob() + key_blob)

    def add(
        self,
        private_key: CryptoPrivateKey,
        comment: str | None = None,
        lifetime: int | None = None,
        confirm: bool | None = None,
    ) -> None:
        key_msg = PrivateKeyMsg.from_private_key(private_key)
        key_msg.comment = unicode_string(comment or '')
        if lifetime:
            key_msg.constraints += constraints([ProtocolMsgNumbers.SSH_AGENT_CONSTRAIN_LIFETIME]).to_blob() + uint32(lifetime).to_blob()
        if confirm:
            key_msg.constraints += constraints([ProtocolMsgNumbers.SSH_AGENT_CONSTRAIN_CONFIRM]).to_blob()

        if key_msg.constraints:
            msg = ProtocolMsgNumbers.SSH_AGENTC_ADD_ID_CONSTRAINED.to_blob()
        else:
            msg = ProtocolMsgNumbers.SSH_AGENTC_ADD_IDENTITY.to_blob()
        msg += key_msg.to_blob()
        self.send(msg)

    def list(self) -> list[Identity]:
        req = ProtocolMsgNumbers.SSH_AGENTC_REQUEST_IDENTITIES.to_blob()
        r = memoryview(bytearray(self.send(req)))
        if r[0] != ProtocolMsgNumbers.SSH_AGENT_IDENTITIES_ANSWER:
            raise SshAgentFailure('agent: non-identities answer received for identities list')

        blob = r[1:]
        nkeys, blob = uint32.consume_from_blob(blob)
        rv = []
        for i in range(nkeys):
            key_blob, blob = self._consume_field(blob)

            peek_key_algo, dummy = self._consume_field(key_blob)
            pub_key_msg_cls = PublicKeyMsg.get_dataclass(KeyAlgo(bytes(peek_key_algo).decode('utf-8')))

            comment_blob, blob = self._consume_field(blob)

            rv.append(Identity(pub_key_msg_cls.from_blob(key_blob), unicode_string.from_blob(comment_blob)))

        if blob:
            raise SshAgentFailure("agent: received more keys than advertised")

        return rv

    @staticmethod
    def _consume_field(blob: memoryview | bytes) -> tuple[memoryview | bytes, memoryview | bytes]:
        length = uint32.from_blob(blob[:4])
        blob = blob[4:]
        data, rest = _split_blob(blob, length)
        return data, rest

    def __contains__(self, public_key: CryptoPublicKey) -> bool:
        msg = PublicKeyMsg.from_public_key(public_key)
        return any(i.key == msg for i in self.list())


@functools.cache
def key_data_into_crypto_objects(key_data: bytes, passphrase: bytes | None) -> tuple[CryptoPrivateKey, CryptoPublicKey, str]:
    private_key = serialization.ssh.load_ssh_private_key(key_data, passphrase)
    public_key = private_key.public_key()
    fingerprint = PublicKeyMsg.from_public_key(public_key).fingerprint

    return private_key, public_key, fingerprint
