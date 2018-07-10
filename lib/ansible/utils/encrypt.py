# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import multiprocessing
import random

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleAssertionError
from ansible.module_utils.six import text_type
from ansible.module_utils._text import to_text, to_bytes


PASSLIB_AVAILABLE = False
try:
    import passlib.hash
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


def do_encrypt(result, encrypt, salt_size=None, salt=None):
    if PASSLIB_AVAILABLE:
        try:
            crypt = getattr(passlib.hash, encrypt)
        except:
            raise AnsibleError("passlib does not support '%s' algorithm" % encrypt)

        if salt_size:
            result = crypt.encrypt(result, salt_size=salt_size)
        elif salt:
            if crypt._salt_is_bytes:
                salt = to_bytes(salt, encoding='ascii', errors='strict')
            else:
                salt = to_text(salt, encoding='ascii', errors='strict')
            result = crypt.encrypt(result, salt=salt)
        else:
            result = crypt.encrypt(result)
    else:
        raise AnsibleError("passlib must be installed to encrypt vars_prompt values")

    # Hashes from passlib.hash should be represented as ascii strings of hex
    # digits so this should not traceback.  If it's not representable as such
    # we need to traceback and then blacklist such algorithms because it may
    # impact calling code.
    return to_text(result, errors='strict')


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
