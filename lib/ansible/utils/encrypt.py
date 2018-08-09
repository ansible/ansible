# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import crypt
import multiprocessing
import random
import string
import sys

from collections import namedtuple

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleAssertionError
from ansible.module_utils.six import text_type
from ansible.module_utils._text import to_text, to_bytes

PASSLIB_AVAILABLE = False
try:
    import passlib
    import passlib.hash
    from passlib.utils.handlers import HasRawSalt

    PASSLIB_AVAILABLE = True
except:
    pass

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

__all__ = ['do_encrypt']

_LOCK = multiprocessing.Lock()

DEFAULT_PASSWORD_LENGTH = 20


class BaseHash(object):
    algo = namedtuple('algo', ['crypt_id', 'salt_size', 'implicit_rounds'])
    algorithms = {
        'md5_crypt': algo(crypt_id='1', salt_size=8, implicit_rounds=None),
        'bcrypt': algo(crypt_id='2a', salt_size=22, implicit_rounds=None),
        'sha256_crypt': algo(crypt_id='5', salt_size=16, implicit_rounds=5000),
        'sha512_crypt': algo(crypt_id='6', salt_size=16, implicit_rounds=5000),
    }

    def __init__(self, algorithm, error_type):
        self.algorithm = algorithm
        self.error_type = error_type


class CryptHash(BaseHash):
    def __init__(self, algorithm, error_type):
        super(CryptHash, self).__init__(algorithm, error_type)

        if sys.platform.startswith('darwin'):
            raise self.error_type("crypt.crypt not supported on Mac OS X/Darwin, install passlib python module")

        if algorithm not in self.algorithms:
            raise self.error_type("crypt.crypt does not support '%s' algorithm" % self.algorithm)
        self.algo_data = self.algorithms[algorithm]

    def hash(self, secret, **settings):
        salt = self._salt(**settings)
        rounds = self._rounds(**settings)
        return self._encrypt(secret, salt, rounds)

    def _salt(self, **settings):
        salt_size = settings.get('salt_size') or self.algo_data.salt_size
        return settings.get('salt') or random_salt(salt_size)

    def _rounds(self, **settings):
        if settings.get('rounds') == self.algo_data.implicit_rounds:
            # Passlib does not include the rounds if it is the same as implict_rounds.
            # Make crypt lib behave the same, by not explicitly specifying the rounds in that case.
            return None
        return settings.get('rounds')

    def _encrypt(self, secret, salt, rounds):
        if rounds is None:
            saltstring = "$%s$%s" % (self.algo_data.crypt_id, salt)
        else:
            saltstring = "$%s$rounds=%d$%s" % (self.algo_data.crypt_id, rounds, salt)
        result = crypt.crypt(secret, saltstring)

        # crypt.crypt returns None if it cannot parse saltstring
        # None as result would be interpreted by the some modules (user module)
        # as no password at all.
        if not result:
            raise self.error_type("crypt.crypt does not support '%s' algorithm" % self.algorithm)

        return result


class PasslibHash(BaseHash):
    def __init__(self, algorithm, error_type):
        super(PasslibHash, self).__init__(algorithm, error_type)

        if not PASSLIB_AVAILABLE:
            raise error_type("passlib must be installed to hash with '%s'" % algorithm)

        try:
            self.crypt_algo = getattr(passlib.hash, algorithm)
        except:
            raise error_type("passlib does not support '%s' algorithm" % algorithm)

    def hash(self, secret, **settings):
        self._clean_salt(settings)
        self._clean_rounds(settings)
        return self._encrypt(secret, settings)

    def _clean_salt(self, settings):
        if "salt" in settings:
            if issubclass(self.crypt_algo, HasRawSalt):
                settings["salt"] = to_bytes(settings["salt"], encoding='ascii', errors='strict')
            else:
                settings["salt"] = to_text(settings["salt"], encoding='ascii', errors='strict')

    def _clean_rounds(self, settings):
        algo_data = self.algorithms.get(self.algorithm)
        if algo_data and algo_data.implicit_rounds and "rounds" not in settings:
            # Ensure passlib behaves the same as crypt in case no rounds were specified.
            # That means instead of using the passlib default for the rounds the crypt default is used.
            settings["rounds"] = algo_data.implicit_rounds

    def _encrypt(self, secret, settings):
        # starting with passlib 1.7 'using' and 'hash' should be used instead of 'encrypt'
        if hasattr(self.crypt_algo, 'hash'):
            result = self.crypt_algo.using(**settings).hash(secret)
        elif hasattr(self.crypt_algo, 'encrypt'):
            result = self.crypt_algo.encrypt(secret, **settings)
        else:
            raise self.error_type("installed passlib version %s not supported" % passlib.__version__)

        # passlib.hash should always return something or raise an exception.
        # Still ensure that there is always a result.
        # Otherwise an empty password might be assumed by some modules, like the user module.
        if not result:
            raise self.error_type("failed to hash with algorithm '%s'" % self.algorithm)

        # Hashes from passlib.hash should be represented as ascii strings of hex
        # digits so this should not traceback.  If it's not representable as such
        # we need to traceback and then blacklist such algorithms because it may
        # impact calling code.
        return to_text(result, errors='strict')


def passlib_or_crypt(secret, algorithm, error_type, **settings):
    if PASSLIB_AVAILABLE:
        return PasslibHash(algorithm, error_type).hash(secret, **settings)
    else:
        return CryptHash(algorithm, error_type).hash(secret, **settings)


def do_encrypt(result, encrypt, salt_size=None, salt=None):
    settings = {}
    if salt_size:
        settings['salt_size'] = salt_size
    elif salt:
        settings['salt'] = salt

    return passlib_or_crypt(result, encrypt, error_type=AnsibleError, **settings)


def random_salt(length):
    """Return a text string suitable for use as a salt for the hash functions we use to encrypt passwords.
    """
    # Note passlib salt values must be pure ascii so we can't let the user
    # configure this
    salt_chars = string.ascii_letters + string.digits + u'./'
    return random_password(length=length, chars=salt_chars)


def random_password(length=DEFAULT_PASSWORD_LENGTH, chars=C.DEFAULT_PASSWORD_CHARS):
    '''Return a random password string of length containing only chars

    :kwarg length: The number of characters in the new password.  Defaults to 20.
    :kwarg chars: The characters to choose from.  The default is all ascii
        letters, ascii digits, and these symbols ``.,:-_``
    '''
    if not isinstance(chars, text_type):
        raise AnsibleAssertionError('%s (%s) is not a text_type' % (chars, type(chars)))

    random_generator = random.SystemRandom()
    return u''.join(random_generator.choice(chars) for dummy in range(length))
