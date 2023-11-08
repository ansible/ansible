# Copyright: Contributors to the Ansible project
# BSD 3 Clause License (see licenses/BSD-3-Clause.txt or https://opensource.org/license/bsd-3-clause/)

from __future__ import annotations

import binascii
import collections.abc
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


class SshAgentFailure(Exception):
    ...


class mpint(int):
    ...


class byte(int):
    ...


class constraints(bytes):
    ...


class Protocol(enum.IntEnum):
    # Responses
    SSH_AGENT_FAILURE = 5
    SSH_AGENT_SUCCESS = 6
    SSH_AGENT_EXTENSION_FAILURE = 28
    SSH_AGENT_IDENTITIES_ANSWER = 12
    SSH_AGENT_SIGN_RESPONSE = 14

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


class KeyAlgo(str, enum.Enum):
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


if HAS_CRYPTOGRAPHY:
    _ECDSA_KEY_TYPE: dict[KeyAlgo, type[EllipticCurve]] = {
        KeyAlgo.ECDSA256: SECP256R1,
        KeyAlgo.ECDSA384: SECP384R1,
        KeyAlgo.ECDSA521: SECP521R1,
    }


@dataclasses.dataclass
class Msg:
    ...


@dataclasses.dataclass(order=True, slots=True)
class AgentLockMsg(Msg):
    passphrase: bytes


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
                    f'nistp{key_size}',
                    private_key.public_key().public_bytes(
                        encoding=serialization.Encoding.X962,
                        format=serialization.PublicFormat.UncompressedPoint
                    ),
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
                    public_bytes,
                    private_bytes + public_bytes,
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
    comments: str = dataclasses.field(default='')
    constraints: constraints = dataclasses.field(default=constraints(b''))


@dataclasses.dataclass(order=True, slots=True)
class DSAPrivateKeyMsg(PrivateKeyMsg):
    type: KeyAlgo
    p: mpint
    q: mpint
    g: mpint
    y: mpint
    x: mpint
    comments: str = dataclasses.field(default='')
    constraints: constraints = dataclasses.field(default=constraints(b''))


@dataclasses.dataclass(order=True, slots=True)
class EcdsaPrivateKeyMsg(PrivateKeyMsg):
    type: KeyAlgo
    ecdsa_curve_name: str
    Q: bytes
    d: mpint
    comments: str = dataclasses.field(default='')
    constraints: constraints = dataclasses.field(default=constraints(b''))


@dataclasses.dataclass(order=True, slots=True)
class Ed25519PrivateKeyMsg(PrivateKeyMsg):
    type: KeyAlgo
    enc_a: bytes
    k_env_a: bytes
    comments: str = dataclasses.field(default='')
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
                    f'nistp{public_key.curve.key_size}',
                    public_key.public_bytes(
                        encoding=serialization.Encoding.X962,
                        format=serialization.PublicFormat.UncompressedPoint
                    )
                )
            case Ed25519PublicKey():
                return Ed25519PublicKeyMsg(
                    KeyAlgo.ED25519,
                    public_key.public_bytes(
                        encoding=serialization.Encoding.Raw,
                        format=serialization.PublicFormat.Raw,
                    )
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
        msg.comments = ''
        k = encode(msg)
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
    comments: str = dataclasses.field(default='')


@dataclasses.dataclass(order=True, slots=True)
class DSAPublicKeyMsg(PublicKeyMsg):
    type: KeyAlgo
    p: mpint
    q: mpint
    g: mpint
    y: mpint
    comments: str = dataclasses.field(default='')


@dataclasses.dataclass(order=True, slots=True)
class EcdsaPublicKeyMsg(PublicKeyMsg):
    type: KeyAlgo
    ecdsa_curve_name: str
    Q: bytes
    comments: str = dataclasses.field(default='')


@dataclasses.dataclass(order=True, slots=True)
class Ed25519PublicKeyMsg(PublicKeyMsg):
    type: KeyAlgo
    enc_a: bytes
    comments: str = dataclasses.field(default='')


@dataclasses.dataclass(order=True, slots=True)
class KeyList(Msg):
    nkeys: int
    keys: list[PublicKeyMsg]

    def __init__(self, nkeys, *args):
        self.nkeys = nkeys
        self.keys = args


def _to_bytes(val: int, length: int) -> bytes:
    return val.to_bytes(length=length, byteorder='big')


def _from_bytes(val: bytes) -> int:
    return int.from_bytes(val, byteorder='big')


def _to_mpint(val: int) -> bytes:
    if val < 0:
        raise ValueError("negative mpint not allowed")
    if not val:
        return b""
    nbytes = (val.bit_length() + 8) // 8
    ret = bytearray(_to_bytes(val, nbytes))
    ret[:0] = _to_bytes(len(ret), 4)
    return ret


def _from_mpint(val: bytes) -> int:
    if val and val[0] > 127:
        raise ValueError("Invalid data")
    return _from_bytes(val)


def encode_dataclass(msg: Msg) -> collections.abc.Iterator[bytes]:
    for field in dataclasses.fields(msg):
        fv = getattr(msg, field.name)
        match field.type:
            case 'mpint':
                yield _to_mpint(fv)
            case 'int':  # uint32
                yield _to_bytes(fv, 4)
            case 'bool' | 'byte' | 'Protocol':
                yield _to_bytes(fv, 1)
            case 'str' | 'KeyAlgo':
                if fv:
                    fv = fv.encode('utf-8')
                    yield _to_bytes(len(fv), 4)
                    yield fv
            case 'bytes':
                if fv:
                    yield _to_bytes(len(fv), 4)
                    yield fv
            case 'constraints':
                yield fv
            case _:
                raise NotImplementedError(field.type)


def parse_annotation(type: t.Any) -> tuple[str, str]:
    if type.count('[') > 1:
        raise NotImplementedError()
    main, _sep, sub = type.removesuffix(']').partition('[')
    return main, sub


def _consume_field(
        blob: memoryview,
        type: t.Any | None = None
) -> tuple[memoryview, int, memoryview]:
    match type:
        case 'int':
            length = 4
        case 'bool' | 'byte' | 'Protocol':
            length = 1
        case _:
            length = _from_bytes(blob[:4])
            blob = blob[4:]
    return blob[:length], length, blob[length:]


def decode_dataclass(blob: memoryview, dataclass: type[Msg]) -> Msg:
    fi = 0
    args: list[t.Any] = []
    fields = dataclasses.fields(dataclass)
    while blob:
        field = fields[fi]
        prev_blob = blob
        fv, length, blob = _consume_field(blob, type=field.type)
        main_type, sub_type = parse_annotation(field.type)
        match main_type:
            case 'mpint':
                args.append(_from_mpint(fv))
            case 'int':  # uint32
                args.append(_from_bytes(fv))
            case 'Protocol':
                args.append(Protocol(_from_bytes(fv)))
            case 'bool' | 'byte':
                args.append(_from_bytes(fv))
            case 'KeyAlgo':
                args.append(KeyAlgo(fv.tobytes().decode('utf-8')))
            case 'str':
                args.append(fv.tobytes().decode('utf-8'))
            case 'bytes':
                args.append(bytes(fv))
            case 'list':
                # Lists should always be last
                match sub_type:
                    case 'PublicKeyMsg':
                        peek, _length, _blob = _consume_field(fv)
                        sub = PublicKeyMsg.get_dataclass(
                            KeyAlgo(peek.tobytes().decode('utf-8'))
                        )

                        _fv, cl, blob = _consume_field(blob)
                        key_plus_comment = (
                            prev_blob[4:length + cl + 8]
                        )
                    case _:
                        raise NotImplementedError(sub_type)

                args.append(decode_dataclass(key_plus_comment, sub))
                fi -= 1  # We are in a list, don't move to the next field
            case _:
                raise NotImplementedError(field.type)

        fi += 1
    return dataclass(*args)


def encode(msg: Protocol | Msg) -> bytes:
    if isinstance(msg, Protocol):
        payload = bytes([msg])
    else:
        payload = b''.join(encode_dataclass(msg))
    return payload


class Client:
    def __init__(self, auth_sock: str):
        self._auth_sock = auth_sock
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.connect(auth_sock)

    def terminate(self):
        self._ssh_agent.terminate()

    def close(self):
        self._sock.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def send(self, msg: bytes) -> bytes:
        length = _to_bytes(len(msg), 4)
        self._sock.sendall(length + msg)
        bufsize = _from_bytes(self._sock.recv(4))
        resp = self._sock.recv(bufsize)
        if resp[0] == Protocol.SSH_AGENT_FAILURE:
            raise SshAgentFailure('agent: failure')
        return resp

    def remove_all(self):
        msg = encode(Protocol.SSH_AGENTC_REMOVE_ALL_IDENTITIES)
        self.send(msg)
        return True

    def remove(self, public_key: CryptoPublicKey):
        msg = encode(Protocol.SSH_AGENTC_REMOVE_IDENTITY)
        key_blob = encode(
            PublicKeyMsg.from_public_key(public_key)
        )
        msg += _to_bytes(len(key_blob), 4)
        msg += key_blob
        self.send(msg)
        return True

    def add(
            self,
            private_key: CryptoPrivateKey,
            comments: str | None = None,
            lifetime: int | None = None,
            confirm: bool | None = None,
    ):
        key_msg = PrivateKeyMsg.from_private_key(private_key)
        key_msg.comments = comments or ''
        if lifetime:
            key_msg.constraints += constraints(
                [Protocol.SSH_AGENT_CONSTRAIN_LIFETIME]
            ) + _to_bytes(lifetime, 4)
        if confirm:
            key_msg.constraints += constraints(
                [Protocol.SSH_AGENT_CONSTRAIN_CONFIRM]
            )

        if key_msg.constraints:
            msg = encode(Protocol.SSH_AGENTC_ADD_ID_CONSTRAINED)
        else:
            msg = encode(Protocol.SSH_AGENTC_ADD_IDENTITY)
        msg += encode(key_msg)
        self.send(msg)
        return True

    def list(self) -> KeyList:
        req = encode(Protocol.SSH_AGENTC_REQUEST_IDENTITIES)
        r = memoryview(bytearray(self.send(req)))
        if r[0] != Protocol.SSH_AGENT_IDENTITIES_ANSWER:
            raise SshAgentFailure(
                'agent: non-identities answer received for identities list'
            )
        return t.cast(KeyList, decode_dataclass(r[1:], KeyList))

    def lock(self, passphrase: bytes):
        msg = encode(Protocol.SSH_AGENTC_LOCK)
        msg += encode(AgentLockMsg(passphrase))
        self.send(msg)
        return True

    def unlock(self, passphrase: bytes):
        msg = encode(Protocol.SSH_AGENTC_UNLOCK)
        msg += encode(AgentLockMsg(passphrase))
        self.send(msg)
        return True

    def __contains__(self, public_key: CryptoPublicKey) -> bool:
        for key in self.list().keys:
            if key.public_key() == public_key:
                return True
        return False


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
