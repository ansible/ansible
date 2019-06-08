# Copyright (c) 2019, Andrey Tuzhilin <andrei.tuzhilin@gmail.com>
#
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Licenses for incorporated software
# ==================================
# This source file contains code derived from the original
# Passlib saslprep implementation, which is available under the following license:
#
#     Copyright (c) 2008-2017 Assurance Technologies, LLC.
#     All rights reserved.
#
#     Redistribution and use in source and binary forms, with or without
#     modification, are permitted provided that the following conditions are
#     met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#     * Neither the name of Assurance Technologies, nor the names of the
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#
#     THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#     "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#     LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#     A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#     OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#     SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#     LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#     DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#     THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#     (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#     OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""An implementation of RFC4013 SASLprep.
This code is mostly a copy of saslpre implementation available at
https://bitbucket.org/ecollins/passlib/src/default/passlib/utils/__init__.py
"""

import sys
from ansible.module_utils.six import text_type
from unicodedata import normalize


class NoStringPrepError(Exception):
    """Local python installation does not have a stringprep module"""
    pass


try:
    import stringprep
except ImportError:
    HAVE_STRINGPREP = False

    # replace saslprep() with stub when stringprep is missing
    def saslprep(source, param="value"):
        """stub for saslprep()"""
        raise NoStringPrepError("saslprep() support requires the 'stringprep' "
                                "module, which is missing")
else:
    HAVE_STRINGPREP = True

    def saslprep(source, param="value"):
        """Normalizes unicode strings using SASLPrep stringprep profile.

        The SASLPrep profile is defined in :rfc:`4013`.
        It provides a uniform scheme for normalizing unicode usernames
        and passwords before performing byte-value sensitive operations
        such as hashing. Among other things, it normalizes diacritic
        representations, removes non-printing characters, and forbids
        invalid characters such as ``\\n``. Properly internationalized
        applications should run user passwords through this function
        before hashing.

        :arg source:
            unicode string to normalize & validate

        :param param:
            Optional noun identifying source parameter in error messages
            (Defaults to the string ``"value"``). This is mainly useful to make the caller's error
            messages make more sense contextually.

        :raises ValueError:
            if any characters forbidden by the SASLPrep profile are encountered.

        :raises TypeError:
            if input is not :class:`!unicode`

        :returns:
            normalized unicode string

        .. note::

            This function is not available under Jython,
            as the Jython stdlib is missing the :mod:`!stringprep` module
            (`Jython issue 1758320 <http://bugs.jython.org/issue1758320>`_).

        .. versionadded:: 1.6
        """
        # saslprep - http://tools.ietf.org/html/rfc4013
        # stringprep - http://tools.ietf.org/html/rfc3454
        #              http://docs.python.org/library/stringprep.html

        # validate type
        if not isinstance(source, text_type):
            raise TypeError("input must be of type %s, not %s" % (text_type, type(source)))

        str_join = u''.join
        _USPACE = u" "
        _UEMPTY = u""

        # mapping stage
        #   - map non-ascii spaces to U+0020 (stringprep C.1.2)
        #   - strip 'commonly mapped to nothing' chars (stringprep B.1)
        in_table_c12 = stringprep.in_table_c12
        in_table_b1 = stringprep.in_table_b1
        data = str_join(
            _USPACE if in_table_c12(c) else c
            for c in source
            if not in_table_b1(c)
        )

        # normalize to KC form
        data = normalize('NFKC', data)
        if not data:
            return _UEMPTY

        # check for invalid bi-directional strings.
        # stringprep requires the following:
        #   - chars in C.8 must be prohibited.
        #   - if any R/AL chars in string:
        #       - no L chars allowed in string
        #       - first and last must be R/AL chars
        # this checks if start/end are R/AL chars. if so, prohibited loop
        # will forbid all L chars. if not, prohibited loop will forbid all
        # R/AL chars instead. in both cases, prohibited loop takes care of C.8.
        is_ral_char = stringprep.in_table_d1
        if is_ral_char(data[0]):
            if not is_ral_char(data[-1]):
                raise ValueError("malformed bidi sequence in " + param)
            # forbid L chars within R/AL sequence.
            is_forbidden_bidi_char = stringprep.in_table_d2
        else:
            # forbid R/AL chars if start not setup correctly; L chars allowed.
            is_forbidden_bidi_char = is_ral_char

        # check for prohibited output - stringprep tables A.1, B.1, C.1.2, C.2 - C.9
        in_table_a1 = stringprep.in_table_a1
        in_table_c21_c22 = stringprep.in_table_c21_c22
        in_table_c3 = stringprep.in_table_c3
        in_table_c4 = stringprep.in_table_c4
        in_table_c5 = stringprep.in_table_c5
        in_table_c6 = stringprep.in_table_c6
        in_table_c7 = stringprep.in_table_c7
        in_table_c8 = stringprep.in_table_c8
        in_table_c9 = stringprep.in_table_c9
        for c in data:
            # check for chars mapping stage should have removed
            if in_table_b1(c):
                raise AssertionError("failed to strip B.1 in mapping stage")
            if in_table_c12(c):
                raise AssertionError("failed to replace C.1.2 in mapping stage")

            # check for forbidden chars
            if in_table_a1(c):
                raise ValueError("unassigned code points forbidden in " + param)
            if in_table_c21_c22(c):
                raise ValueError("control characters forbidden in " + param)
            if in_table_c3(c):
                raise ValueError("private use characters forbidden in " + param)
            if in_table_c4(c):
                raise ValueError("non-char code points forbidden in " + param)
            if in_table_c5(c):
                raise ValueError("surrogate codes forbidden in " + param)
            if in_table_c6(c):
                raise ValueError("non-plaintext chars forbidden in " + param)
            if in_table_c7(c):
                # XXX: should these have been caught by normalize?
                # if so, should change this to an assert
                raise ValueError("non-canonical chars forbidden in " + param)
            if in_table_c8(c):
                raise ValueError("display-modifying / deprecated chars "
                                 "forbidden in" + param)
            if in_table_c9(c):
                raise ValueError("tagged characters forbidden in " + param)

            # do bidi constraint check chosen by bidi init, above
            if is_forbidden_bidi_char(c):
                raise ValueError("forbidden bidi character in " + param)

        return data
