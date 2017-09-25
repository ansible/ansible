# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Ted Timmons <ted@timmons.me>, 2017.
# Most of this was originally added by other creators in the postgresql_user module.
# All rights reserved.
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

__metaclass__ = type

try:
    import psycopg2
    import psycopg2.extras
    import psycopg2.extensions
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

import ctypes
import ctypes.util
import re
import string

try:
    # quote_ident is available since Psycopg 2.7
    from psycopg2.extensions import quote_ident
    HAS_PSYCOPG2_QUOTE_IDENT = True
except ImportError:
    HAS_PSYCOPG2_QUOTE_IDENT = False


class unionPthreadMutex(ctypes.Union):
    _pack_ = True
    _fields_ = [
        ('__size', ctypes.c_char * 40),  # sizeof(struct___pthread_mutex_s)
        ('__align', ctypes.c_int64),
        ('PADDING_0', ctypes.c_ubyte * 32),
    ]


class structConnectionObject(ctypes.Structure):
    _pack_ = True
    _fields_ = [
        ('ob_refcnt', ctypes.c_int64),
        ('ob_type', ctypes.c_void_p),
        ('lock', unionPthreadMutex),
        ('dsn', ctypes.c_void_p),
        ('critical', ctypes.c_void_p),
        ('encoding', ctypes.c_void_p),
        ('closed', ctypes.c_int64),
        ('mark', ctypes.c_int64),
        ('status', ctypes.c_int32),
        ('PADDING_0', ctypes.c_ubyte * 4),
        ('tpc_xid', ctypes.c_void_p),
        ('async', ctypes.c_int64),
        ('protocol', ctypes.c_int32),
        ('server_version', ctypes.c_int32),
        ('pgconn', ctypes.c_void_p),
        # fields after pgconn can be ignored
    ]

try:
    assert not HAS_PSYCOPG2_QUOTE_IDENT and psycopg2.__libpq_version__ >= 90000

    libpq = ctypes.cdll.LoadLibrary(ctypes.util.find_library('pq'))
    libpq.PQescapeIdentifier.argtypes = (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t)
    libpq.PQescapeIdentifier.restype = ctypes.c_void_p
    libpq.PQfreemem.argtypes = (ctypes.c_void_p,)
    libpq.PQfreemem.restype = None

    HAS_LIBPQ_QUOTE_IDENT = True
except Exception:
    HAS_LIBPQ_QUOTE_IDENT = False


if not HAS_LIBPQ_QUOTE_IDENT:
    class UnquotedIdentifier(object):
        """Allow unquoted identifiers only
        See https://www.postgresql.org/docs/current/static/sql-syntax-lexical.html#SQL-SYNTAX-IDENTIFIERS
        """
        EXTENSION_PATTERN = r'[^\W\d][\w_\$]+$'

        def __init__(self, identifier):
            self.identifier = identifier

        def getquoted(self):
            if re.match(self.EXTENSION_PATTERN, self.identifier):
                return self.identifier
            else:
                raise Exception('%r is not a valid identifier' % self.identifier)

    if HAS_PSYCOPG2:
        psycopg2.extensions.register_adapter(UnquotedIdentifier, lambda identifier: identifier)


class LibraryError(Exception):
    pass


def ensure_libs(sslrootcert=None):
    if not HAS_PSYCOPG2:
        raise LibraryError('psycopg2 is not installed. we need psycopg2.')
    if sslrootcert and psycopg2.__version__ < '2.4.3':
        raise LibraryError('psycopg2 must be at least 2.4.3 in order to use the ssl_rootcert parameter')

    # no problems
    return None


def postgres_common_argument_spec():
    return dict(
        login_user=dict(default='postgres'),
        login_password=dict(default='', no_log=True),
        login_host=dict(default=''),
        login_unix_socket=dict(default=''),
        port=dict(type='int', default=5432),
        ssl_mode=dict(default='prefer', choices=['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']),
        ssl_rootcert=dict(),
    )


class EscapeIdentifierCursor(object):
    """Escape identifiers using psycopg2.extensions.quote_ident if available,
    else try with libpq.PQescapeIdentifier. If both are not available,
    identifiers are not escaped."""

    __metaclass__ = type

    def execute(self, query, vars=None, identifiers=None):
        """Replace string.Template placeholder ${...} by identifiers if any"""
        if identifiers:
            query = string.Template(query)
            if HAS_PSYCOPG2_QUOTE_IDENT:
                query = query.substitute(dict((name, quote_ident(value, self)) for name, value in identifiers.items()))
            elif HAS_LIBPQ_QUOTE_IDENT:
                query = query.substitute(dict((name, self.escape_identifier(value)) for name, value in identifiers.items()))
            else:
                if vars is None:
                    vars = {}
                if identifiers:
                    self.module.warn('Unable to escape identifiers')
                query = query.substitute(dict((name, '%%(%s)s' % name) for name in identifiers.keys()))
                vars.update(dict((name, UnquotedIdentifier(value)) for name, value in identifiers.items()))

        return super(EscapeIdentifierCursor, self).execute(query, vars=vars)

    def escape_identifier(self, identifier):
        assert not HAS_PSYCOPG2_QUOTE_IDENT and HAS_LIBPQ_QUOTE_IDENT
        _connection = ctypes.cast(ctypes.c_void_p(id(self.connection)), ctypes.POINTER(structConnectionObject)).contents
        escaped = libpq.PQescapeIdentifier(_connection.pgconn, ctypes.c_char_p(identifier), ctypes.c_size_t(len(identifier)))
        try:
            return ctypes.cast(escaped, ctypes.c_char_p).value
        finally:
            if escaped is not None:
                libpq.PQfreemem(escaped)


def escape_identifier_cursor(module, cursor=None):
    """Create a cursor allowing to escape identifiers: 'cursor.execute' method
    accepts an identifier dictionary. When not empty, string.Template
    placeholders ${...} in query will be replaced by escaped identifiers.

    Usage: connection.cursor(cursor_factory=escape_identifier_cursor(module, cursor=psycopg2.extras.DictCursor)"""
    if cursor is None:
        cursor = psycopg2.extensions.cursor
    return type("Cursor", (EscapeIdentifierCursor, cursor), {'module': module})
