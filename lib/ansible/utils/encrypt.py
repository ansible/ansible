# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import random
import string

from collections import namedtuple

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleAssertionError
from ansible.module_utils.six import text_type
from ansible.module_utils.common.text.converters import to_text, to_bytes
from ansible.utils.display import Display

PASSLIB_E = None
PASSLIB_AVAILABLE = False
try:
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


display = Display()

__all__ = ['do_encrypt']

DEFAULT_PASSWORD_LENGTH = 20


def random_password(length=DEFAULT_PASSWORD_LENGTH, chars=C.DEFAULT_PASSWORD_CHARS, seed=None):
    '''Return a random password string of length containing only chars

    :kwarg length: The number of characters in the new password.  Defaults to 20.
    :kwarg chars: The characters to choose from.  The default is all ascii
        letters, ascii digits, and these symbols ``.,:-_``
    '''
    if not isinstance(chars, text_type):
        raise AnsibleAssertionError('%s (%s) is not a text_type' % (chars, type(chars)))

    if seed is None:
        random_generator = random.SystemRandom()
    else:
        random_generator = random.Random(seed)
    return u''.join(random_generator.choice(chars) for dummy in range(length))


def random_salt(length=8):
    """Return a text string suitable for use as a salt for the hash functions we use to encrypt passwords.
    """
    # Note passlib salt values must be pure ascii so we can't let the user
    # configure this
    salt_chars = string.ascii_letters + string.digits + u'./'
    return random_password(length=length, chars=salt_chars)


class BaseHash(object):
    algo = namedtuple('algo', ['crypt_id', 'salt_size', 'implicit_rounds', 'salt_exact', 'implicit_ident'])
    algorithms = {
        'md5_crypt': algo(crypt_id='1', salt_size=8, implicit_rounds=None, salt_exact=False, implicit_ident=None),
        'bcrypt': algo(crypt_id='2b', salt_size=22, implicit_rounds=12, salt_exact=True, implicit_ident='2b'),
        'sha256_crypt': algo(crypt_id='5', salt_size=16, implicit_rounds=535000, salt_exact=False, implicit_ident=None),
        'sha512_crypt': algo(crypt_id='6', salt_size=16, implicit_rounds=656000, salt_exact=False, implicit_ident=None),
    }

    def __init__(self, algorithm):
        self.algorithm = algorithm


class PasslibHash(BaseHash):
    def __init__(self, algorithm):
        super(PasslibHash, self).__init__(algorithm)

        if not PASSLIB_AVAILABLE:
            raise AnsibleError("passlib must be installed and usable to hash with '%s'" % algorithm, orig_exc=PASSLIB_E)
        display.vv("Using passlib to hash input with '%s'" % algorithm)

        try:
            self.crypt_algo = getattr(passlib.hash, algorithm)
        except Exception:
            raise AnsibleError("passlib does not support '%s' algorithm" % algorithm)

    def hash(self, secret, salt=None, salt_size=None, rounds=None, ident=None):
        salt = self._clean_salt(salt)
        rounds = self._clean_rounds(rounds)
        ident = self._clean_ident(ident)
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
                raise AnsibleError("installed passlib version %s not supported" % passlib.__version__)
        except ValueError as e:
            raise AnsibleError("Could not hash the secret.", orig_exc=e)

        # passlib.hash should always return something or raise an exception.
        # Still ensure that there is always a result.
        # Otherwise an empty password might be assumed by some modules, like the user module.
        if not result:
            raise AnsibleError("failed to hash with algorithm '%s'" % self.algorithm)

        # Hashes from passlib.hash should be represented as ascii strings of hex
        # digits so this should not traceback.  If it's not representable as such
        # we need to traceback and then block such algorithms because it may
        # impact calling code.
        return to_text(result, errors='strict')


def passlib_or_crypt(secret, algorithm, salt=None, salt_size=None, rounds=None, ident=None):
    display.deprecated("passlib_or_crypt API is deprecated in favor of do_encrypt", version='2.20')
    return do_encrypt(secret, algorithm, salt=salt, salt_size=salt_size, rounds=rounds, ident=ident)


def do_encrypt(result, encrypt, salt_size=None, salt=None, ident=None, rounds=None):
    if PASSLIB_AVAILABLE:
        return PasslibHash(encrypt).hash(result, salt=salt, salt_size=salt_size, rounds=rounds, ident=ident)
    raise AnsibleError("Unable to encrypt nor hash, passlib must be installed", orig_exc=PASSLIB_E)
