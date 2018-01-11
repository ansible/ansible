# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Toshio Kuratomi <a.badger@gmail.com>, 2016
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
#

"""
.. warn:: This module_util is currently internal implementation.
    We want to evaluate this code for stability and API suitability before
    making backwards compatibility guarantees.  The API may change between
    releases.  Do not use this unless you are willing to port your module code.
"""
import codecs

from ansible.module_utils.six import PY3, text_type, binary_type


try:
    codecs.lookup_error('surrogateescape')
    HAS_SURROGATEESCAPE = True
except LookupError:
    HAS_SURROGATEESCAPE = False


_COMPOSED_ERROR_HANDLERS = frozenset((None, 'surrogate_or_replace',
                                      'surrogate_or_strict',
                                      'surrogate_then_replace'))


def to_bytes(obj, encoding='utf-8', errors=None, nonstring='simplerepr'):
    """Make sure that a string is a byte string

    :arg obj: An object to make sure is a byte string.  In most cases this
        will be either a text string or a byte string.  However, with
        ``nonstring='simplerepr'``, this can be used as a traceback-free
        version of ``str(obj)``.
    :kwarg encoding: The encoding to use to transform from a text string to
        a byte string.  Defaults to using 'utf-8'.
    :kwarg errors: The error handler to use if the text string is not
        encodable using the specified encoding.  Any valid `codecs error
        handler <https://docs.python.org/2/library/codecs.html#codec-base-classes>`_
        may be specified. There are three additional error strategies
        specifically aimed at helping people to port code.  The first two are:

            :surrogate_or_strict: Will use ``surrogateescape`` if it is a valid
                handler, otherwise it will use ``strict``
            :surrogate_or_replace: Will use ``surrogateescape`` if it is a valid
                handler, otherwise it will use ``replace``.

        Because ``surrogateescape`` was added in Python3 this usually means that
        Python3 will use ``surrogateescape`` and Python2 will use the fallback
        error handler. Note that the code checks for ``surrogateescape`` when the
        module is imported.  If you have a backport of ``surrogateescape`` for
        Python2, be sure to register the error handler prior to importing this
        module.

        The last error handler is:

            :surrogate_then_replace: Will use ``surrogateescape`` if it is a valid
                handler.  If encoding with ``surrogateescape`` would traceback,
                surrogates are first replaced with a replacement characters
                and then the string is encoded using ``replace`` (which replaces
                the rest of the nonencodable bytes).  If ``surrogateescape`` is
                not present it will simply use ``replace``.  (Added in Ansible 2.3)
                This strategy is designed to never traceback when it attempts
                to encode a string.

        The default until Ansible-2.2 was ``surrogate_or_replace``
        From Ansible-2.3 onwards, the default is ``surrogate_then_replace``.

    :kwarg nonstring: The strategy to use if a nonstring is specified in
        ``obj``.  Default is 'simplerepr'.  Valid values are:

        :simplerepr: The default.  This takes the ``str`` of the object and
            then returns the bytes version of that string.
        :empty: Return an empty byte string
        :passthru: Return the object passed in
        :strict: Raise a :exc:`TypeError`

    :returns: Typically this returns a byte string.  If a nonstring object is
        passed in this may be a different type depending on the strategy
        specified by nonstring.  This will never return a text string.

    .. note:: If passed a byte string, this function does not check that the
        string is valid in the specified encoding.  If it's important that the
        byte string is in the specified encoding do::

            encoded_string = to_bytes(to_text(input_string, 'latin-1'), 'utf-8')

    .. version_changed:: 2.3

        Added the ``surrogate_then_replace`` error handler and made it the default error handler.
    """
    if isinstance(obj, binary_type):
        return obj

    # We're given a text string
    # If it has surrogates, we know because it will decode
    original_errors = errors
    if errors in _COMPOSED_ERROR_HANDLERS:
        if HAS_SURROGATEESCAPE:
            errors = 'surrogateescape'
        elif errors == 'surrogate_or_strict':
            errors = 'strict'
        else:
            errors = 'replace'

    if isinstance(obj, text_type):
        try:
            # Try this first as it's the fastest
            return obj.encode(encoding, errors)
        except UnicodeEncodeError:
            if original_errors in (None, 'surrogate_then_replace'):
                # We should only reach this if encoding was non-utf8 original_errors was
                # surrogate_then_escape and errors was surrogateescape

                # Slow but works
                return_string = obj.encode('utf-8', 'surrogateescape')
                return_string = return_string.decode('utf-8', 'replace')
                return return_string.encode(encoding, 'replace')
            raise

    # Note: We do these last even though we have to call to_bytes again on the
    # value because we're optimizing the common case
    if nonstring == 'simplerepr':
        try:
            value = str(obj)
        except UnicodeError:
            try:
                value = repr(obj)
            except UnicodeError:
                # Giving up
                return to_bytes('')
    elif nonstring == 'passthru':
        return obj
    elif nonstring == 'empty':
        # python2.4 doesn't have b''
        return to_bytes('')
    elif nonstring == 'strict':
        raise TypeError('obj must be a string type')
    else:
        raise TypeError('Invalid value %s for to_bytes\' nonstring parameter' % nonstring)

    return to_bytes(value, encoding, errors)


def to_text(obj, encoding='utf-8', errors=None, nonstring='simplerepr'):
    """Make sure that a string is a text string

    :arg obj: An object to make sure is a text string.  In most cases this
        will be either a text string or a byte string.  However, with
        ``nonstring='simplerepr'``, this can be used as a traceback-free
        version of ``str(obj)``.
    :kwarg encoding: The encoding to use to transform from a byte string to
        a text string.  Defaults to using 'utf-8'.
    :kwarg errors: The error handler to use if the byte string is not
        decodable using the specified encoding.  Any valid `codecs error
        handler <https://docs.python.org/2/library/codecs.html#codec-base-classes>`_
        may be specified.   We support three additional error strategies
        specifically aimed at helping people to port code:

            :surrogate_or_strict: Will use surrogateescape if it is a valid
                handler, otherwise it will use strict
            :surrogate_or_replace: Will use surrogateescape if it is a valid
                handler, otherwise it will use replace.
            :surrogate_then_replace: Does the same as surrogate_or_replace but
                `was added for symmetry with the error handlers in
                :func:`ansible.module_utils._text.to_bytes` (Added in Ansible 2.3)

        Because surrogateescape was added in Python3 this usually means that
        Python3 will use `surrogateescape` and Python2 will use the fallback
        error handler. Note that the code checks for surrogateescape when the
        module is imported.  If you have a backport of `surrogateescape` for
        python2, be sure to register the error handler prior to importing this
        module.

        The default until Ansible-2.2 was `surrogate_or_replace`
        In Ansible-2.3 this defaults to `surrogate_then_replace` for symmetry
        with :func:`ansible.module_utils._text.to_bytes` .
    :kwarg nonstring: The strategy to use if a nonstring is specified in
        ``obj``.  Default is 'simplerepr'.  Valid values are:

        :simplerepr: The default.  This takes the ``str`` of the object and
            then returns the text version of that string.
        :empty: Return an empty text string
        :passthru: Return the object passed in
        :strict: Raise a :exc:`TypeError`

    :returns: Typically this returns a text string.  If a nonstring object is
        passed in this may be a different type depending on the strategy
        specified by nonstring.  This will never return a byte string.
        From Ansible-2.3 onwards, the default is `surrogate_then_replace`.

    .. version_changed:: 2.3

        Added the surrogate_then_replace error handler and made it the default error handler.
    """
    if isinstance(obj, text_type):
        return obj

    if errors in _COMPOSED_ERROR_HANDLERS:
        if HAS_SURROGATEESCAPE:
            errors = 'surrogateescape'
        elif errors == 'surrogate_or_strict':
            errors = 'strict'
        else:
            errors = 'replace'

    if isinstance(obj, binary_type):
        # Note: We don't need special handling for surrogate_then_replace
        # because all bytes will either be made into surrogates or are valid
        # to decode.
        return obj.decode(encoding, errors)

    # Note: We do these last even though we have to call to_text again on the
    # value because we're optimizing the common case
    if nonstring == 'simplerepr':
        try:
            value = str(obj)
        except UnicodeError:
            try:
                value = repr(obj)
            except UnicodeError:
                # Giving up
                return u''
    elif nonstring == 'passthru':
        return obj
    elif nonstring == 'empty':
        return u''
    elif nonstring == 'strict':
        raise TypeError('obj must be a string type')
    else:
        raise TypeError('Invalid value %s for to_text\'s nonstring parameter' % nonstring)

    return to_text(value, encoding, errors)


#: :py:func:`to_native`
#:      Transform a variable into the native str type for the python version
#:
#:      On Python2, this is an alias for
#:      :func:`~ansible.module_utils.to_bytes`.  On Python3 it is an alias for
#:      :func:`~ansible.module_utils.to_text`.  It makes it easier to
#:      transform a variable into the native str type for the python version
#:      the code is running on.  Use this when constructing the message to
#:      send to exceptions or when dealing with an API that needs to take
#:      a native string.  Example::
#:
#:          try:
#:              1//0
#:          except ZeroDivisionError as e:
#:              raise MyException('Encountered and error: %s' % to_native(e))
if PY3:
    to_native = to_text
else:
    to_native = to_bytes
