# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import random
import secrets
import string
import warnings

from dataclasses import dataclass

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleAssertionError
from ansible.module_utils.common.text.converters import to_text, to_bytes
from ansible.utils.display import Display

PASSLIB_E = None
PASSLIB_AVAILABLE = False

try:
    # deprecated: description='warning suppression only required for Python 3.12 and earlier' python_version='3.12'
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message="'crypt' is deprecated and slated for removal in Python 3.13", category=DeprecationWarning)

        import passlib
        import passlib.hash
        from passlib.utils.handlers import HasRawSalt, PrefixWrapper
        try:
            from passlib.utils.binary import bcrypt64
        except ImportError:
            from passlib.utils import bcrypt64

    PASSLIB_AVAILABLE = True
except Exception as e:
    PASSLIB_E = e

CRYPT_E = None
HAS_CRYPT = False
try:
    from ansible._internal._encryption import _crypt
    HAS_CRYPT = True
except Exception as e:
    CRYPT_E = e


display = Display()

__all__ = ['do_encrypt']

DEFAULT_PASSWORD_LENGTH = 20


def random_password(length=DEFAULT_PASSWORD_LENGTH, chars=C.DEFAULT_PASSWORD_CHARS, seed=None):
    """Return a random password string of length containing only chars

    :kwarg length: The number of characters in the new password.  Defaults to 20.
    :kwarg chars: The characters to choose from.  The default is all ascii
        letters, ascii digits, and these symbols ``.,:-_``
    """
    if not isinstance(chars, str):
        raise AnsibleAssertionError(f'{chars=!r} ({type(chars)}) is not a {type(str)}.')

    if seed is None:
        random_generator = random.SystemRandom()
    else:
        random_generator = random.Random(seed)
    return u''.join(random_generator.choice(chars) for dummy in range(length))


_SALT_CHARS = string.ascii_letters + string.digits + './'
_VALID_SALT_CHARS = frozenset(_SALT_CHARS)


def random_salt(length=8):
    """Return a text string suitable for use as a salt for the hash functions we use to encrypt passwords.
    """
    # Note passlib salt values must be pure ascii so we can't let the user
    # configure this
    return random_password(length=length, chars=_SALT_CHARS)


@dataclass(frozen=True)
class _Algo:
    crypt_id: str
    salt_size: int
    implicit_rounds: int | None = None
    salt_exact: bool = False
    implicit_ident: str | None = None
    rounds_format: str | None = None
    requires_gensalt: bool = False


class BaseHash(object):
    algorithms = {
        'md5_crypt': _Algo(crypt_id='1', salt_size=8),
        'bcrypt': _Algo(crypt_id='2b', salt_size=22, implicit_rounds=12, salt_exact=True, implicit_ident='2b', rounds_format='cost'),
        'sha256_crypt': _Algo(crypt_id='5', salt_size=16, implicit_rounds=535000, rounds_format='rounds'),
        'sha512_crypt': _Algo(crypt_id='6', salt_size=16, implicit_rounds=656000, rounds_format='rounds'),
    }

    def __init__(self, algorithm):
        self.algorithm = algorithm
        display.vv(f"Using {self.__class__.__name__} to hash input with {algorithm!r}")


class CryptHash(BaseHash):
    algorithms = {
        **BaseHash.algorithms,
        'yescrypt': _Algo(crypt_id='y', salt_size=16, implicit_rounds=5, rounds_format='cost', requires_gensalt=True, salt_exact=True),
    }

    def __init__(self, algorithm: str) -> None:
        super(CryptHash, self).__init__(algorithm)

        if not HAS_CRYPT:
            raise AnsibleError("crypt cannot be used as the 'libxcrypt' library is not installed or is unusable.") from CRYPT_E

        if algorithm not in self.algorithms:
            raise AnsibleError(f"crypt does not support {self.algorithm!r} algorithm")

        self.algo_data = self.algorithms[algorithm]

        if self.algo_data.requires_gensalt and not _crypt.HAS_CRYPT_GENSALT:
            raise AnsibleError(f"{self.algorithm!r} algorithm requires libxcrypt")

    def hash(self, secret: str, salt: str | None = None, salt_size: int | None = None, rounds: int | None = None, ident: str | None = None) -> str:
        rounds = self._rounds(rounds)
        ident = self._ident(ident)

        if _crypt.HAS_CRYPT_GENSALT:
            saltstring = self._gensalt(ident, rounds, salt, salt_size)
        else:
            saltstring = self._build_saltstring(ident, rounds, salt, salt_size)

        return self._hash(secret, saltstring)

    def _validate_salt_size(self, salt_size: int | None) -> int:
        if salt_size is not None and not isinstance(salt_size, int):
            raise TypeError('salt_size must be an integer')
        salt_size = salt_size or self.algo_data.salt_size
        if self.algo_data.salt_exact and salt_size != self.algo_data.salt_size:
            raise AnsibleError(f"invalid salt size supplied ({salt_size}), expected {self.algo_data.salt_size}")
        elif not self.algo_data.salt_exact and salt_size > self.algo_data.salt_size:
            raise AnsibleError(f"invalid salt size supplied ({salt_size}), expected at most {self.algo_data.salt_size}")
        return salt_size

    def _salt(self, salt: str | None, salt_size: int | None) -> str:
        salt_size = self._validate_salt_size(salt_size)
        ret = salt or random_salt(salt_size)
        if not set(ret).issubset(_VALID_SALT_CHARS):
            raise AnsibleError("invalid characters in salt")
        if self.algo_data.salt_exact and len(ret) != self.algo_data.salt_size:
            raise AnsibleError(f"invalid salt size supplied ({len(ret)}), expected {self.algo_data.salt_size}")
        elif not self.algo_data.salt_exact and len(ret) > self.algo_data.salt_size:
            raise AnsibleError(f"invalid salt size supplied ({len(ret)}), expected at most {self.algo_data.salt_size}")
        return ret

    def _rounds(self, rounds: int | None) -> int | None:
        return rounds or self.algo_data.implicit_rounds

    def _ident(self, ident: str | None) -> str | None:
        return ident or self.algo_data.crypt_id

    def _gensalt(self, ident: str, rounds: int | None, salt: str | None, salt_size: int | None) -> str:
        if salt is None:
            salt_size = self._validate_salt_size(salt_size)
            rbytes = secrets.token_bytes(salt_size)
        else:
            salt = self._salt(salt, salt_size)
            rbytes = to_bytes(salt)

        prefix = f'${ident}$'
        count = rounds or 0

        try:
            salt_bytes = _crypt.crypt_gensalt(to_bytes(prefix), count, rbytes)
            return to_text(salt_bytes, errors='strict')
        except (NotImplementedError, ValueError) as e:
            raise AnsibleError(f"Failed to generate salt for {self.algorithm!r} algorithm") from e

    def _build_saltstring(self, ident: str, rounds: int | None, salt: str | None, salt_size: int | None) -> str:
        salt = self._salt(salt, salt_size)
        saltstring = f'${ident}' if ident else ''
        if rounds:
            if self.algo_data.rounds_format == 'cost':
                saltstring += f'${rounds}'
            else:
                saltstring += f'$rounds={rounds}'
        saltstring += f'${salt}'
        return saltstring

    def _hash(self, secret: str, saltstring: str) -> str:
        try:
            result = _crypt.crypt(to_bytes(secret), to_bytes(saltstring))
        except (OSError, ValueError) as e:
            raise AnsibleError(f"crypt does not support {self.algorithm!r} algorithm") from e

        return to_text(result, errors='strict')


class PasslibHash(BaseHash):
    def __init__(self, algorithm):
        super(PasslibHash, self).__init__(algorithm)

        if not PASSLIB_AVAILABLE:
            raise AnsibleError(f"The passlib Python package must be installed to hash with the {algorithm!r} algorithm.") from PASSLIB_E

        try:
            self.crypt_algo = getattr(passlib.hash, algorithm)
        except Exception:
            raise AnsibleError(f"Installed passlib version {passlib.__version__} does not support the {algorithm!r} algorithm.") from None

    def hash(self, secret, salt=None, salt_size=None, rounds=None, ident=None):
        salt = self._clean_salt(salt)
        rounds = self._clean_rounds(rounds)
        ident = self._clean_ident(ident)
        if salt_size is not None and not isinstance(salt_size, int):
            raise TypeError("salt_size must be an integer")
        return self._hash(secret, salt=salt, salt_size=salt_size, rounds=rounds, ident=ident)

    def _clean_ident(self, ident):
        ret = None
        if not ident:
            if self.algorithm in self.algorithms:
                return self.algorithms.get(self.algorithm).implicit_ident
            return ret
        if self.algorithm == 'bcrypt':
            return ident
        return ret

    def _clean_salt(self, salt):
        if not salt:
            return None
        elif issubclass(self.crypt_algo.wrapped if isinstance(self.crypt_algo, PrefixWrapper) else self.crypt_algo, HasRawSalt):
            ret = to_bytes(salt, encoding='ascii', errors='strict')
        else:
            ret = to_text(salt, encoding='ascii', errors='strict')

        # Ensure the salt has the correct padding
        if self.algorithm == 'bcrypt':
            ret = bcrypt64.repair_unused(ret)

        return ret

    def _clean_rounds(self, rounds):
        algo_data = self.algorithms.get(self.algorithm)
        if rounds:
            return rounds
        elif algo_data and algo_data.implicit_rounds:
            # The default rounds used by passlib depend on the passlib version.
            # For consistency ensure that passlib behaves the same as crypt in case no rounds were specified.
            # Thus use the crypt defaults.
            return algo_data.implicit_rounds
        else:
            return None

    def _hash(self, secret, salt, salt_size, rounds, ident):
        # Not every hash algorithm supports every parameter.
        # Thus create the settings dict only with set parameters.
        settings = {}
        if salt:
            settings['salt'] = salt
        if salt_size:
            settings['salt_size'] = salt_size
        if rounds:
            settings['rounds'] = rounds
        if ident:
            settings['ident'] = ident

        # starting with passlib 1.7 'using' and 'hash' should be used instead of 'encrypt'
        try:
            if hasattr(self.crypt_algo, 'hash'):
                result = self.crypt_algo.using(**settings).hash(secret)
            elif hasattr(self.crypt_algo, 'encrypt'):
                result = self.crypt_algo.encrypt(secret, **settings)
            else:
                raise ValueError(f"Installed passlib version {passlib.__version__} is not supported.")
        except ValueError as ex:
            raise AnsibleError("Could not hash the secret.") from ex

        # passlib.hash should always return something or raise an exception.
        # Still ensure that there is always a result.
        # Otherwise an empty password might be assumed by some modules, like the user module.
        if not result:
            raise AnsibleError(f"Failed to hash with passlib using the {self.algorithm!r} algorithm.")

        # Hashes from passlib.hash should be represented as ascii strings of hex
        # digits so this should not traceback.  If it's not representable as such
        # we need to traceback and then block such algorithms because it may
        # impact calling code.
        return to_text(result, errors='strict')


def do_encrypt(result, algorithm, salt_size=None, salt=None, ident=None, rounds=None):
    if HAS_CRYPT and algorithm in CryptHash.algorithms:
        return CryptHash(algorithm).hash(result, salt=salt, salt_size=salt_size, rounds=rounds, ident=ident)
    elif PASSLIB_AVAILABLE:
        # TODO: deprecate passlib
        return PasslibHash(algorithm).hash(result, salt=salt, salt_size=salt_size, rounds=rounds, ident=ident)
    elif not PASSLIB_AVAILABLE and algorithm not in CryptHash.algorithms:
        # When passlib support is removed, this branch can be removed too
        raise AnsibleError(f"crypt does not support {algorithm!r} algorithm")
    raise AnsibleError("Unable to encrypt nor hash, either libxcrypt (recommended), crypt, or passlib must be installed.") from CRYPT_E
