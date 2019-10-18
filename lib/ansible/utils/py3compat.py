# -*- coding: utf-8 -*-
#
# (c) 2018, Toshio Kuratomi <a.badger@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Note that the original author of this, Toshio Kuratomi, is trying to submit this to six.  If
# successful, the code in six will be available under six's more liberal license:
# https://mail.python.org/pipermail/python-porting/2018-July/000539.html

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys

from ansible.module_utils.six import PY3
from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.common._collections_compat import MutableMapping

__all__ = ('environ',)


class _TextEnviron(MutableMapping):
    """
    Utility class to return text strings from the environment instead of byte strings

    Mimics the behaviour of os.environ on Python3
    """
    def __init__(self, env=None, encoding=None):
        if env is None:
            env = os.environ
        self._raw_environ = env
        self._value_cache = {}
        # Since we're trying to mimic Python3's os.environ, use sys.getfilesystemencoding()
        # instead of utf-8
        if encoding is None:
            # Since we're trying to mimic Python3's os.environ, use sys.getfilesystemencoding()
            # instead of utf-8
            self.encoding = sys.getfilesystemencoding()
        else:
            self.encoding = encoding

    def __delitem__(self, key):
        del self._raw_environ[key]

    def __getitem__(self, key):
        value = self._raw_environ[key]
        if PY3:
            return value
        # Cache keys off of the undecoded values to handle any environment variables which change
        # during a run
        if value not in self._value_cache:
            self._value_cache[value] = to_text(value, encoding=self.encoding,
                                               nonstring='passthru', errors='surrogate_or_strict')
        return self._value_cache[value]

    def __setitem__(self, key, value):
        self._raw_environ[key] = to_bytes(value, encoding=self.encoding, nonstring='strict',
                                          errors='surrogate_or_strict')

    def __iter__(self):
        return self._raw_environ.__iter__()

    def __len__(self):
        return len(self._raw_environ)


environ = _TextEnviron(encoding='utf-8')
