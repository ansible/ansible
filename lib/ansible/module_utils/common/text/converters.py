# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# (c) 2016 Toshio Kuratomi <tkuratomi@ansible.com>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import codecs
import json

from ansible.module_utils.compat import typing as _t
from ansible.module_utils._internal import _no_six

try:
    codecs.lookup_error('surrogateescape')
    HAS_SURROGATEESCAPE = True
except LookupError:
    HAS_SURROGATEESCAPE = False


_COMPOSED_ERROR_HANDLERS = frozenset((None, 'surrogate_or_replace',
                                      'surrogate_or_strict',
                                      'surrogate_then_replace'))

_T = _t.TypeVar('_T')

_NonStringPassthru: _t.TypeAlias = _t.Literal['passthru']
_NonStringOther: _t.TypeAlias = _t.Literal['simplerepr', 'empty', 'strict']
_NonStringAll: _t.TypeAlias = _t.Union[_NonStringPassthru, _NonStringOther]


@_t.overload
def to_bytes(
    obj: object,
    encoding: str = 'utf-8',
    errors: str | None = None,
) -> bytes: ...


@_t.overload
def to_bytes(
    obj: bytes | str,
    encoding: str = 'utf-8',
    errors: str | None = None,
    nonstring: _NonStringPassthru = 'passthru',
) -> bytes: ...


@_t.overload
def to_bytes(
    obj: _T,
    encoding: str = 'utf-8',
    errors: str | None = None,
    nonstring: _NonStringPassthru = 'passthru',
) -> _T: ...


@_t.overload
def to_bytes(
    obj: object,
    encoding: str = 'utf-8',
    errors: str | None = None,
    nonstring: _NonStringOther = 'simplerepr',
) -> bytes: ...


def to_bytes(
    obj: _T,
    encoding: str = 'utf-8',
    errors: str | None = None,
    nonstring: _NonStringAll = 'simplerepr'
) -> _T | bytes:
    """Make sure that a string is a byte string

    :arg obj: An object to make sure is a byte string.  In most cases this
        will be either a text string or a byte string.  However, with
        ``nonstring='simplerepr'``, this can be used as a traceback-free
        version of ``str(obj)``.
    :kwarg encoding: The encoding to use to transform from a text string to
        a byte string.  Defaults to using 'utf-8'.
    :kwarg errors: The error handler to use if the text string is not
        encodable using the specified encoding.  Any valid `codecs error
        handler <https://docs.python.org/3/library/codecs.html#codec-base-classes>`_
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

            encoded_string = to_bytes(to_text(input_string, encoding='latin-1'), encoding='utf-8')

    .. version_changed:: 2.3

        Added the ``surrogate_then_replace`` error handler and made it the default error handler.
    """
    if isinstance(obj, bytes):
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

    if isinstance(obj, str):
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
                return b''
    elif nonstring == 'passthru':
        return obj
    elif nonstring == 'empty':
        return b''
    elif nonstring == 'strict':
        raise TypeError('obj must be a string type')
    else:
        raise TypeError('Invalid value %s for to_bytes\' nonstring parameter' % nonstring)

    return to_bytes(value, encoding=encoding, errors=errors)


@_t.overload
def to_text(
    obj: object,
    encoding: str = 'utf-8',
    errors: str | None = None,
) -> str: ...


@_t.overload
def to_text(
    obj: str | bytes,
    encoding: str = 'utf-8',
    errors: str | None = None,
    nonstring: _NonStringPassthru = 'passthru',
) -> str: ...


@_t.overload
def to_text(
    obj: _T,
    encoding: str = 'utf-8',
    errors: str | None = None,
    nonstring: _NonStringPassthru = 'passthru',
) -> _T: ...


@_t.overload
def to_text(
    obj: object,
    encoding: str = 'utf-8',
    errors: str | None = None,
    nonstring: _NonStringOther = 'simplerepr',
) -> str: ...


def to_text(
    obj: _T,
    encoding: str = 'utf-8',
    errors: str | None = None,
    nonstring: _NonStringAll = 'simplerepr'
) -> _T | str:
    """Make sure that a string is a text string

    :arg obj: An object to make sure is a text string.  In most cases this
        will be either a text string or a byte string.  However, with
        ``nonstring='simplerepr'``, this can be used as a traceback-free
        version of ``str(obj)``.
    :kwarg encoding: The encoding to use to transform from a byte string to
        a text string.  Defaults to using 'utf-8'.
    :kwarg errors: The error handler to use if the byte string is not
        decodable using the specified encoding.  Any valid `codecs error
        handler <https://docs.python.org/3/library/codecs.html#codec-base-classes>`_
        may be specified.   We support three additional error strategies
        specifically aimed at helping people to port code:

            :surrogate_or_strict: Will use surrogateescape if it is a valid
                handler, otherwise it will use strict
            :surrogate_or_replace: Will use surrogateescape if it is a valid
                handler, otherwise it will use replace.
            :surrogate_then_replace: Does the same as surrogate_or_replace but
                `was added for symmetry with the error handlers in
                :func:`ansible.module_utils.common.text.converters.to_bytes` (Added in Ansible 2.3)

        Because surrogateescape was added in Python3 this usually means that
        Python3 will use `surrogateescape` and Python2 will use the fallback
        error handler. Note that the code checks for surrogateescape when the
        module is imported.  If you have a backport of `surrogateescape` for
        python2, be sure to register the error handler prior to importing this
        module.

        The default until Ansible-2.2 was `surrogate_or_replace`
        In Ansible-2.3 this defaults to `surrogate_then_replace` for symmetry
        with :func:`ansible.module_utils.common.text.converters.to_bytes` .
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
    if isinstance(obj, str):
        return obj

    if errors in _COMPOSED_ERROR_HANDLERS:
        if HAS_SURROGATEESCAPE:
            errors = 'surrogateescape'
        elif errors == 'surrogate_or_strict':
            errors = 'strict'
        else:
            errors = 'replace'

    if isinstance(obj, bytes):
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
                return ''
    elif nonstring == 'passthru':
        return obj
    elif nonstring == 'empty':
        return ''
    elif nonstring == 'strict':
        raise TypeError('obj must be a string type')
    else:
        raise TypeError('Invalid value %s for to_text\'s nonstring parameter' % nonstring)

    return to_text(value, encoding=encoding, errors=errors)


to_native = to_text


def jsonify(data, **kwargs):
    from ansible.module_utils.common import json as _common_json
    # from ansible.module_utils.common.warnings import deprecate

    # deprecated: description='deprecate jsonify()' core_version='2.23'
    # deprecate(
    #     msg="The `jsonify` function is deprecated.",
    #     version="2.27",
    #     # help_text="",  # DTFIX-FUTURE: fill in this help text
    # )

    return json.dumps(data, cls=_common_json._get_legacy_encoder(), _decode_bytes=True, **kwargs)


def container_to_bytes(d, encoding='utf-8', errors='surrogate_or_strict'):
    """ Recursively convert dict keys and values to byte str

        Specialized for json return because this only handles, lists, tuples,
        and dict container types (the containers that the json module returns)
    """
    # DTFIX-FUTURE: deprecate

    if isinstance(d, str):
        return to_bytes(d, encoding=encoding, errors=errors)
    elif isinstance(d, dict):
        return dict(container_to_bytes(o, encoding, errors) for o in d.items())
    elif isinstance(d, list):
        return [container_to_bytes(o, encoding, errors) for o in d]
    elif isinstance(d, tuple):
        return tuple(container_to_bytes(o, encoding, errors) for o in d)
    else:
        return d


def container_to_text(d, encoding='utf-8', errors='surrogate_or_strict'):
    """Recursively convert dict keys and values to text str

    Specialized for json return because this only handles, lists, tuples,
    and dict container types (the containers that the json module returns)
    """
    # DTFIX-FUTURE: deprecate

    if isinstance(d, bytes):
        # Warning, can traceback
        return to_text(d, encoding=encoding, errors=errors)
    elif isinstance(d, dict):
        return dict(container_to_text(o, encoding, errors) for o in d.items())
    elif isinstance(d, list):
        return [container_to_text(o, encoding, errors) for o in d]
    elif isinstance(d, tuple):
        return tuple(container_to_text(o, encoding, errors) for o in d)
    else:
        return d


def __getattr__(importable_name):
    return _no_six.deprecate(importable_name, __name__, "binary_type", "text_type", "iteritems")
