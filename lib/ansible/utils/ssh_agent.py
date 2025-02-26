# Copyright: Contributors to the Ansible project
# BSD 3 Clause License (see licenses/BSD-3-Clause.txt or https://opensource.org/license/bsd-3-clause/)

from __future__ import annotations

import binascii
import copy
import dataclasses
import enum
import hashlib
import socket
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
    from cryptography.hazmat.primitives.serialization import ssh

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
except ImportError:
    HAS_CRYPTOGRAPHY = False
else:
    HAS_CRYPTOGRAPHY = True


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


class SshAgentFailure(Exception):
    ...


# NOTE: Classes below somewhat represent "Data Type Representations Used in the SSH Protocols"
#       as specified by RFC4251

@t.runtime_checkable
class SupportsToBlob(t.Protocol):
    def to_blob(self) -> bytes:
        ...


@t.runtime_checkable
class SupportsFromBlob(t.Protocol):
    @classmethod
    def from_blob(cls, blob: memoryview | bytes) -> t.Self:
        ...

    @classmethod
    def consume_from_blob(cls, blob: memoryview | bytes) -> tuple[t.Self, memoryview | bytes]:
        ...


class VariableSized:
    @classmethod
    def from_blob(cls, blob: memoryview | bytes) -> t.Self:
        raise NotImplementedError

    @classmethod
    def consume_from_blob(cls, blob: memoryview | bytes) -> tuple[t.Self, memoryview | bytes]:
        length = uint32.from_blob(blob[:4])
        blob = blob[4:]
        return cls.from_blob(blob[:length]), blob[length:]


class uint32(int):
    def to_blob(self) -> bytes:
        return self.to_bytes(length=4, byteorder='big')

    @classmethod
    def from_blob(cls, blob: memoryview | bytes) -> t.Self:
        return cls.from_bytes(blob, byteorder='big')

    @classmethod
    def consume_from_blob(cls, blob: memoryview | bytes) -> tuple[t.Self, memoryview | bytes]:
        length = uint32(4)
        return cls.from_blob(blob[:length]), blob[length:]


class mpint(int, VariableSized):
    def to_blob(self) -> bytes:
        if self < 0:
            raise ValueError("negative mpint not allowed")
        if not self:
            return b""
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
        if length := len(self):
            return uint32(length).to_blob() + self
        else:
            return b""

    @classmethod
    def from_blob(cls, blob: memoryview | bytes) -> t.Self:
        return cls(blob)


class unicode_string(str, VariableSized):
    def to_blob(self) -> bytes:
        val = self.encode('utf-8')
        if length := len(val):
            return uint32(length).to_blob() + val
        else:
            return b""

    @classmethod
    def from_blob(cls, blob: memoryview | bytes) -> t.Self:
        return cls(bytes(blob).decode('utf-8'))


class KeyAlgo(str, VariableSized, enum.Enum):
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
    def main_type(self):
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


@dataclasses.dataclass(order=True, slots=True)
class AgentLockMsg(Msg):
    passphrase: binary_string


@dataclasses.dataclass
class PrivateKeyMsg(Msg):
    @staticmethod
    def from_private_key(private_key):
        match private_key:
            case RSAPrivateKey():
                pn = private_key.private_numbers()
                return RSAPrivateKeyMsg(
                    KeyAlgo.RSA,
                    pn.public_numbers.n,
                    pn.public_numbers.e,
                    pn.d,
                    pn.iqmp,
                    pn.p,
                    pn.q,
                )
            case DSAPrivateKey():
                pn = private_key.private_numbers()
                return DSAPrivateKeyMsg(
                    KeyAlgo.DSA,
                    pn.public_numbers.parameter_numbers.p,
                    pn.public_numbers.parameter_numbers.q,
                    pn.public_numbers.parameter_numbers.g,
                    pn.public_numbers.y,
                    pn.x,
                )
            case EllipticCurvePrivateKey():
                pn = private_key.private_numbers()
                key_size = private_key.key_size
                return EcdsaPrivateKeyMsg(
                    getattr(KeyAlgo, f'ECDSA{key_size}'),
                    unicode_string(f'nistp{key_size}'),
                    binary_string(private_key.public_key().public_bytes(
                        encoding=serialization.Encoding.X962,
                        format=serialization.PublicFormat.UncompressedPoint
                    )),
                    pn.private_value,
                )
            case Ed25519PrivateKey():
                public_bytes = private_key.public_key().public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw,
                )
                private_bytes = private_key.private_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PrivateFormat.Raw,
                    encryption_algorithm=serialization.NoEncryption()
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
    comments: unicode_string = dataclasses.field(default=unicode_string(''), compare=False)
    constraints: constraints = dataclasses.field(default=constraints(b''))


@dataclasses.dataclass(order=True, slots=True)
class DSAPrivateKeyMsg(PrivateKeyMsg):
    type: KeyAlgo
    p: mpint
    q: mpint
    g: mpint
    y: mpint
    x: mpint
    comments: unicode_string = dataclasses.field(default=unicode_string(''), compare=False)
    constraints: constraints = dataclasses.field(default=constraints(b''))


@dataclasses.dataclass(order=True, slots=True)
class EcdsaPrivateKeyMsg(PrivateKeyMsg):
    type: KeyAlgo
    ecdsa_curve_name: unicode_string
    Q: binary_string
    d: mpint
    comments: unicode_string = dataclasses.field(default=unicode_string(''), compare=False)
    constraints: constraints = dataclasses.field(default=constraints(b''))


@dataclasses.dataclass(order=True, slots=True)
class Ed25519PrivateKeyMsg(PrivateKeyMsg):
    type: KeyAlgo
    enc_a: binary_string
    k_env_a: binary_string
    comments: unicode_string = dataclasses.field(default=unicode_string(''), compare=False)
    constraints: constraints = dataclasses.field(default=constraints(b''))


@dataclasses.dataclass
class PublicKeyMsg(Msg):
    @staticmethod
    def get_dataclass(
            type: KeyAlgo
    ) -> type[t.Union[
            RSAPublicKeyMsg,
            EcdsaPublicKeyMsg,
            Ed25519PublicKeyMsg,
            DSAPublicKeyMsg
    ]]:
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

    def public_key(self) -> CryptoPublicKey:
        type = self.type  # type: ignore[attr-defined]
        match type:
            case KeyAlgo.RSA:
                return RSAPublicNumbers(
                    self.e,  # type: ignore[attr-defined]
                    self.n  # type: ignore[attr-defined]
                ).public_key()
            case KeyAlgo.ECDSA256 | KeyAlgo.ECDSA384 | KeyAlgo.ECDSA521:
                curve = _ECDSA_KEY_TYPE[KeyAlgo(type)]
                return EllipticCurvePublicKey.from_encoded_point(
                    curve(),
                    self.Q  # type: ignore[attr-defined]
                )
            case KeyAlgo.ED25519:
                return Ed25519PublicKey.from_public_bytes(
                    self.enc_a  # type: ignore[attr-defined]
                )
            case KeyAlgo.DSA:
                return DSAPublicNumbers(
                    self.y,  # type: ignore[attr-defined]
                    DSAParameterNumbers(
                        self.p,  # type: ignore[attr-defined]
                        self.q,  # type: ignore[attr-defined]
                        self.g  # type: ignore[attr-defined]
                    )
                ).public_key()
            case _:
                raise NotImplementedError(type)

    @staticmethod
    def from_public_key(public_key):
        match public_key:
            case DSAPublicKey():
                pn = public_key.public_numbers()
                return DSAPublicKeyMsg(
                    KeyAlgo.DSA,
                    pn.parameter_numbers.p,
                    pn.parameter_numbers.q,
                    pn.parameter_numbers.g,
                    pn.y
                )
            case EllipticCurvePublicKey():
                return EcdsaPublicKeyMsg(
                    getattr(KeyAlgo, f'ECDSA{public_key.curve.key_size}'),
                    unicode_string(f'nistp{public_key.curve.key_size}'),
                    binary_string(public_key.public_bytes(
                        encoding=serialization.Encoding.X962,
                        format=serialization.PublicFormat.UncompressedPoint
                    ))
                )
            case Ed25519PublicKey():
                return Ed25519PublicKeyMsg(
                    KeyAlgo.ED25519,
                    binary_string(public_key.public_bytes(
                        encoding=serialization.Encoding.Raw,
                        format=serialization.PublicFormat.Raw,
                    ))
                )
            case RSAPublicKey():
                pn = public_key.public_numbers()
                return RSAPublicKeyMsg(
                    KeyAlgo.RSA,
                    pn.e,
                    pn.n
                )
            case _:
                raise NotImplementedError(public_key)

    def fingerprint(self):
        digest = hashlib.sha256()
        msg = copy.copy(self)
        msg.comments = unicode_string('')
        k = msg.to_blob()
        digest.update(k)
        return binascii.b2a_base64(
            digest.digest(),
            newline=False
        ).rstrip(b'=').decode('utf-8')


@dataclasses.dataclass(order=True, slots=True)
class RSAPublicKeyMsg(PublicKeyMsg):
    type: KeyAlgo
    e: mpint
    n: mpint
    comments: unicode_string = dataclasses.field(default=unicode_string(''), compare=False)


@dataclasses.dataclass(order=True, slots=True)
class DSAPublicKeyMsg(PublicKeyMsg):
    type: KeyAlgo
    p: mpint
    q: mpint
    g: mpint
    y: mpint
    comments: unicode_string = dataclasses.field(default=unicode_string(''), compare=False)


@dataclasses.dataclass(order=True, slots=True)
class EcdsaPublicKeyMsg(PublicKeyMsg):
    type: KeyAlgo
    ecdsa_curve_name: unicode_string
    Q: binary_string
    comments: unicode_string = dataclasses.field(default=unicode_string(''), compare=False)


@dataclasses.dataclass(order=True, slots=True)
class Ed25519PublicKeyMsg(PublicKeyMsg):
    type: KeyAlgo
    enc_a: binary_string
    comments: unicode_string = dataclasses.field(default=unicode_string(''), compare=False)


@dataclasses.dataclass(order=True, slots=True)
class KeyList(Msg):
    nkeys: uint32
    keys: PublicKeyMsgList

    def __post_init__(self):
        if self.nkeys != len(self.keys):
            raise SshAgentFailure(
                "agent: invalid number of keys received for identities list"
            )


@dataclasses.dataclass(order=True, slots=True)
class PublicKeyMsgList(Msg):
    keys: list[PublicKeyMsg]

    def __iter__(self):
        yield from self.keys

    def __len__(self):
        return len(self.keys)

    @classmethod
    def from_blob(cls, blob: memoryview | bytes) -> t.Self:
        ...

    @classmethod
    def consume_from_blob(cls, blob: memoryview | bytes) -> tuple[t.Self, memoryview | bytes]:
        args: list[PublicKeyMsg] = []
        while blob:
            prev_blob = blob
            key_blob, key_blob_length, comment_blob = cls._consume_field(blob)

            peek_key_algo, _length, _blob = cls._consume_field(key_blob)
            pub_key_msg_cls = PublicKeyMsg.get_dataclass(
                KeyAlgo(bytes(peek_key_algo).decode('utf-8'))
            )

            _fv, comment_blob_length, blob = cls._consume_field(comment_blob)
            key_plus_comment = (
                prev_blob[4: (4 + key_blob_length) + (4 + comment_blob_length)]
            )

            args.append(pub_key_msg_cls.from_blob(key_plus_comment))
        return cls(args), b""

    @staticmethod
    def _consume_field(
            blob: memoryview | bytes
    ) -> tuple[memoryview | bytes, uint32, memoryview | bytes]:
        length = uint32.from_blob(blob[:4])
        blob = blob[4:]
        return blob[:length], length, blob[length:]


class SshAgentClient:
    def __init__(self, auth_sock: str):
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.connect(auth_sock)

    def close(self):
        self._sock.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def send(self, msg: bytes) -> bytes:
        length = uint32(len(msg)).to_blob()
        self._sock.sendall(length + msg)
        bufsize = uint32.from_blob(self._sock.recv(4))
        resp = self._sock.recv(bufsize)
        if resp[0] == ProtocolMsgNumbers.SSH_AGENT_FAILURE:
            raise SshAgentFailure('agent: failure')
        return resp

    def remove_all(self):
        self.send(
            ProtocolMsgNumbers.SSH_AGENTC_REMOVE_ALL_IDENTITIES.to_blob()
        )

    def remove(self, public_key: CryptoPublicKey):
        key_blob = PublicKeyMsg.from_public_key(public_key).to_blob()
        self.send(
            ProtocolMsgNumbers.SSH_AGENTC_REMOVE_IDENTITY.to_blob() +
            uint32(len(key_blob)).to_blob() + key_blob
        )

    def add(
            self,
            private_key: CryptoPrivateKey,
            comments: unicode_string | None = None,
            lifetime: int | None = None,
            confirm: bool | None = None,
    ):
        key_msg = PrivateKeyMsg.from_private_key(private_key)
        key_msg.comments = unicode_string(comments or '')
        if lifetime:
            key_msg.constraints += constraints(
                [ProtocolMsgNumbers.SSH_AGENT_CONSTRAIN_LIFETIME]
            ).to_blob() + uint32(lifetime).to_blob()
        if confirm:
            key_msg.constraints += constraints(
                [ProtocolMsgNumbers.SSH_AGENT_CONSTRAIN_CONFIRM]
            ).to_blob()

        if key_msg.constraints:
            msg = ProtocolMsgNumbers.SSH_AGENTC_ADD_ID_CONSTRAINED.to_blob()
        else:
            msg = ProtocolMsgNumbers.SSH_AGENTC_ADD_IDENTITY.to_blob()
        msg += key_msg.to_blob()
        self.send(msg)

    def list(self) -> KeyList:
        req = ProtocolMsgNumbers.SSH_AGENTC_REQUEST_IDENTITIES.to_blob()
        r = memoryview(bytearray(self.send(req)))
        if r[0] != ProtocolMsgNumbers.SSH_AGENT_IDENTITIES_ANSWER:
            raise SshAgentFailure(
                'agent: non-identities answer received for identities list'
            )
        return KeyList.from_blob(r[1:])

    def lock(self, passphrase: bytes):
        self.send(
            ProtocolMsgNumbers.SSH_AGENTC_LOCK.to_blob() + AgentLockMsg(binary_string(passphrase)).to_blob()
        )

    def unlock(self, passphrase: bytes):
        self.send(
            ProtocolMsgNumbers.SSH_AGENTC_UNLOCK.to_blob() + AgentLockMsg(binary_string(passphrase)).to_blob()
        )

    def __contains__(self, public_key: CryptoPublicKey) -> bool:
        msg = PublicKeyMsg.from_public_key(public_key)
        return msg in self.list().keys


def load_private_key(key_data: bytes, passphrase: bytes) -> CryptoPrivateKey:
    try:
        private_key = ssh.load_ssh_private_key(
            key_data,
            password=passphrase,
        )
    except ValueError:
        # Old keys generated by ssh-agent may not adhere to the strict
        # definition of what ``load_ssh_private_key`` expects, fall
        # back to generic PEM private key loading
        private_key = serialization.load_pem_private_key(
            key_data,
            password=passphrase,
        )  # type: CryptoPrivateKey # type: ignore[no-redef]
    allowed_types = t.get_args(CryptoPrivateKey)
    if not isinstance(private_key, allowed_types):
        type_names = (o.__name__ for o in allowed_types)
        raise ValueError(
            f'key_data must be one of {", ".join(type_names)} not, '
            f'{private_key.__class__.__name__}'
        )
    return private_key
