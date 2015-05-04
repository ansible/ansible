# (c) 2012-2014, Toshio Kuraotmi <a.badger@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# to_bytes and to_unicode were written by Toshio Kuratomi for the
# python-kitchen library https://pypi.python.org/pypi/kitchen
# They are licensed in kitchen under the terms of the GPLv2+
# They were copied and modified for use in ansible by Toshio in Jan 2015
# (simply removing the deprecated features)

#: Aliases for the utf-8 codec
_UTF8_ALIASES = frozenset(('utf-8', 'UTF-8', 'utf8', 'UTF8', 'utf_8', 'UTF_8',
    'utf', 'UTF', 'u8', 'U8'))
#: Aliases for the latin-1 codec
_LATIN1_ALIASES = frozenset(('latin-1', 'LATIN-1', 'latin1', 'LATIN1',
    'latin', 'LATIN', 'l1', 'L1', 'cp819', 'CP819', '8859', 'iso8859-1',
    'ISO8859-1', 'iso-8859-1', 'ISO-8859-1'))

# EXCEPTION_CONVERTERS is defined below due to using to_unicode

def to_unicode(obj, encoding='utf-8', errors='replace', nonstring=None):
    '''Convert an object into a :class:`unicode` string

    :arg obj: Object to convert to a :class:`unicode` string.  This should
        normally be a byte :class:`str`
    :kwarg encoding: What encoding to try converting the byte :class:`str` as.
        Defaults to :term:`utf-8`
    :kwarg errors: If errors are found while decoding, perform this action.
        Defaults to ``replace`` which replaces the invalid bytes with
        a character that means the bytes were unable to be decoded.  Other
        values are the same as the error handling schemes in the `codec base
        classes
        <http://docs.python.org/library/codecs.html#codec-base-classes>`_.
        For instance ``strict`` which raises an exception and ``ignore`` which
        simply omits the non-decodable characters.
    :kwarg nonstring: How to treat nonstring values.  Possible values are:

        :simplerepr: Attempt to call the object's "simple representation"
            method and return that value.  Python-2.3+ has two methods that
            try to return a simple representation: :meth:`object.__unicode__`
            and :meth:`object.__str__`.  We first try to get a usable value
            from :meth:`object.__unicode__`.  If that fails we try the same
            with :meth:`object.__str__`.
        :empty: Return an empty :class:`unicode` string
        :strict: Raise a :exc:`TypeError`
        :passthru: Return the object unchanged
        :repr: Attempt to return a :class:`unicode` string of the repr of the
            object

        Default is ``simplerepr``

    :raises TypeError: if :attr:`nonstring` is ``strict`` and
        a non-:class:`basestring` object is passed in or if :attr:`nonstring`
        is set to an unknown value
    :raises UnicodeDecodeError: if :attr:`errors` is ``strict`` and
        :attr:`obj` is not decodable using the given encoding
    :returns: :class:`unicode` string or the original object depending on the
        value of :attr:`nonstring`.

    Usually this should be used on a byte :class:`str` but it can take both
    byte :class:`str` and :class:`unicode` strings intelligently.  Nonstring
    objects are handled in different ways depending on the setting of the
    :attr:`nonstring` parameter.

    The default values of this function are set so as to always return
    a :class:`unicode` string and never raise an error when converting from
    a byte :class:`str` to a :class:`unicode` string.  However, when you do
    not pass validly encoded text (or a nonstring object), you may end up with
    output that you don't expect.  Be sure you understand the requirements of
    your data, not just ignore errors by passing it through this function.
    '''
    # Could use isbasestring/isunicode here but we want this code to be as
    # fast as possible
    if isinstance(obj, basestring):
        if isinstance(obj, unicode):
            return obj
        if encoding in _UTF8_ALIASES:
            return unicode(obj, 'utf-8', errors)
        if encoding in _LATIN1_ALIASES:
            return unicode(obj, 'latin-1', errors)
        return obj.decode(encoding, errors)

    if not nonstring:
        nonstring = 'simplerepr'
    if nonstring == 'empty':
        return u''
    elif nonstring == 'passthru':
        return obj
    elif nonstring == 'simplerepr':
        try:
            simple = obj.__unicode__()
        except (AttributeError, UnicodeError):
            simple = None
        if not simple:
            try:
                simple = str(obj)
            except UnicodeError:
                try:
                    simple = obj.__str__()
                except (UnicodeError, AttributeError):
                    simple = u''
        if isinstance(simple, str):
            return unicode(simple, encoding, errors)
        return simple
    elif nonstring in ('repr', 'strict'):
        obj_repr = repr(obj)
        if isinstance(obj_repr, str):
            obj_repr = unicode(obj_repr, encoding, errors)
        if nonstring == 'repr':
            return obj_repr
        raise TypeError('to_unicode was given "%(obj)s" which is neither'
            ' a byte string (str) or a unicode string' %
            {'obj': obj_repr.encode(encoding, 'replace')})

    raise TypeError('nonstring value, %(param)s, is not set to a valid'
        ' action' % {'param': nonstring})

def to_bytes(obj, encoding='utf-8', errors='replace', nonstring=None):
    '''Convert an object into a byte :class:`str`

    :arg obj: Object to convert to a byte :class:`str`.  This should normally
        be a :class:`unicode` string.
    :kwarg encoding: Encoding to use to convert the :class:`unicode` string
        into a byte :class:`str`.  Defaults to :term:`utf-8`.
    :kwarg errors: If errors are found while encoding, perform this action.
        Defaults to ``replace`` which replaces the invalid bytes with
        a character that means the bytes were unable to be encoded.  Other
        values are the same as the error handling schemes in the `codec base
        classes
        <http://docs.python.org/library/codecs.html#codec-base-classes>`_.
        For instance ``strict`` which raises an exception and ``ignore`` which
        simply omits the non-encodable characters.
    :kwarg nonstring: How to treat nonstring values.  Possible values are:

        :simplerepr: Attempt to call the object's "simple representation"
            method and return that value.  Python-2.3+ has two methods that
            try to return a simple representation: :meth:`object.__unicode__`
            and :meth:`object.__str__`.  We first try to get a usable value
            from :meth:`object.__str__`.  If that fails we try the same
            with :meth:`object.__unicode__`.
        :empty: Return an empty byte :class:`str`
        :strict: Raise a :exc:`TypeError`
        :passthru: Return the object unchanged
        :repr: Attempt to return a byte :class:`str` of the :func:`repr` of the
            object

        Default is ``simplerepr``.

    :raises TypeError: if :attr:`nonstring` is ``strict`` and
        a non-:class:`basestring` object is passed in or if :attr:`nonstring`
        is set to an unknown value.
    :raises UnicodeEncodeError: if :attr:`errors` is ``strict`` and all of the
        bytes of :attr:`obj` are unable to be encoded using :attr:`encoding`.
    :returns: byte :class:`str` or the original object depending on the value
        of :attr:`nonstring`.

    .. warning::

        If you pass a byte :class:`str` into this function the byte
        :class:`str` is returned unmodified.  It is **not** re-encoded with
        the specified :attr:`encoding`.  The easiest way to achieve that is::

            to_bytes(to_unicode(text), encoding='utf-8')

        The initial :func:`to_unicode` call will ensure text is
        a :class:`unicode` string.  Then, :func:`to_bytes` will turn that into
        a byte :class:`str` with the specified encoding.

    Usually, this should be used on a :class:`unicode` string but it can take
    either a byte :class:`str` or a :class:`unicode` string intelligently.
    Nonstring objects are handled in different ways depending on the setting
    of the :attr:`nonstring` parameter.

    The default values of this function are set so as to always return a byte
    :class:`str` and never raise an error when converting from unicode to
    bytes.  However, when you do not pass an encoding that can validly encode
    the object (or a non-string object), you may end up with output that you
    don't expect.  Be sure you understand the requirements of your data, not
    just ignore errors by passing it through this function.
    '''
    # Could use isbasestring, isbytestring here but we want this to be as fast
    # as possible
    if isinstance(obj, basestring):
        if isinstance(obj, str):
            return obj
        return obj.encode(encoding, errors)
    if not nonstring:
        nonstring = 'simplerepr'

    if nonstring == 'empty':
        return ''
    elif nonstring == 'passthru':
        return obj
    elif nonstring == 'simplerepr':
        try:
            simple = str(obj)
        except UnicodeError:
            try:
                simple = obj.__str__()
            except (AttributeError, UnicodeError):
                simple = None
        if not simple:
            try:
                simple = obj.__unicode__()
            except (AttributeError, UnicodeError):
                simple = ''
        if isinstance(simple, unicode):
            simple = simple.encode(encoding, 'replace')
        return simple
    elif nonstring in ('repr', 'strict'):
        try:
            obj_repr = obj.__repr__()
        except (AttributeError, UnicodeError):
            obj_repr = ''
        if isinstance(obj_repr, unicode):
            obj_repr =  obj_repr.encode(encoding, errors)
        else:
            obj_repr = str(obj_repr)
        if nonstring == 'repr':
            return obj_repr
        raise TypeError('to_bytes was given "%(obj)s" which is neither'
            ' a unicode string or a byte string (str)' % {'obj': obj_repr})

    raise TypeError('nonstring value, %(param)s, is not set to a valid'
        ' action' % {'param': nonstring})


# force the return value of a function to be unicode.  Use with partial to
# ensure that a filter will return unicode values.
def unicode_wrap(func, *args, **kwargs):
    return to_unicode(func(*args, **kwargs), nonstring='passthru')
