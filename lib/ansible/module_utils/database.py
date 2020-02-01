# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2014, Toshio Kuratomi <tkuratomi@ansible.com>
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


class SQLParseError(Exception):
    pass


class UnclosedQuoteError(SQLParseError):
    pass


# maps a type of identifier to the maximum number of dot levels that are
# allowed to specify that identifier.  For example, a database column can be
# specified by up to 4 levels: database.schema.table.column
_PG_IDENTIFIER_TO_DOT_LEVEL = dict(
    database=1,
    schema=2,
    table=3,
    column=4,
    role=1,
    tablespace=1,
    sequence=3,
    publication=1,
)
_MYSQL_IDENTIFIER_TO_DOT_LEVEL = dict(database=1, table=2, column=3, role=1, vars=1)


def _find_end_quote(identifier, quote_char):
    accumulate = 0
    while True:
        try:
            quote = identifier.index(quote_char)
        except ValueError:
            raise UnclosedQuoteError
        accumulate = accumulate + quote
        try:
            next_char = identifier[quote + 1]
        except IndexError:
            return accumulate
        if next_char == quote_char:
            try:
                identifier = identifier[quote + 2:]
                accumulate = accumulate + 2
            except IndexError:
                raise UnclosedQuoteError
        else:
            return accumulate


def _identifier_parse(identifier, quote_char):
    if not identifier:
        raise SQLParseError('Identifier name unspecified or unquoted trailing dot')

    already_quoted = False
    if identifier.startswith(quote_char):
        already_quoted = True
        try:
            end_quote = _find_end_quote(identifier[1:], quote_char=quote_char) + 1
        except UnclosedQuoteError:
            already_quoted = False
        else:
            if end_quote < len(identifier) - 1:
                if identifier[end_quote + 1] == '.':
                    dot = end_quote + 1
                    first_identifier = identifier[:dot]
                    next_identifier = identifier[dot + 1:]
                    further_identifiers = _identifier_parse(next_identifier, quote_char)
                    further_identifiers.insert(0, first_identifier)
                else:
                    raise SQLParseError('User escaped identifiers must escape extra quotes')
            else:
                further_identifiers = [identifier]

    if not already_quoted:
        try:
            dot = identifier.index('.')
        except ValueError:
            identifier = identifier.replace(quote_char, quote_char * 2)
            identifier = ''.join((quote_char, identifier, quote_char))
            further_identifiers = [identifier]
        else:
            if dot == 0 or dot >= len(identifier) - 1:
                identifier = identifier.replace(quote_char, quote_char * 2)
                identifier = ''.join((quote_char, identifier, quote_char))
                further_identifiers = [identifier]
            else:
                first_identifier = identifier[:dot]
                next_identifier = identifier[dot + 1:]
                further_identifiers = _identifier_parse(next_identifier, quote_char)
                first_identifier = first_identifier.replace(quote_char, quote_char * 2)
                first_identifier = ''.join((quote_char, first_identifier, quote_char))
                further_identifiers.insert(0, first_identifier)

    return further_identifiers


def pg_quote_identifier(identifier, id_type):
    identifier_fragments = _identifier_parse(identifier, quote_char='"')
    if len(identifier_fragments) > _PG_IDENTIFIER_TO_DOT_LEVEL[id_type]:
        raise SQLParseError('PostgreSQL does not support %s with more than %i dots' % (id_type, _PG_IDENTIFIER_TO_DOT_LEVEL[id_type]))
    return '.'.join(identifier_fragments)


def mysql_quote_identifier(identifier, id_type):
    identifier_fragments = _identifier_parse(identifier, quote_char='`')
    if (len(identifier_fragments) - 1) > _MYSQL_IDENTIFIER_TO_DOT_LEVEL[id_type]:
        raise SQLParseError('MySQL does not support %s with more than %i dots' % (id_type, _MYSQL_IDENTIFIER_TO_DOT_LEVEL[id_type]))

    special_cased_fragments = []
    for fragment in identifier_fragments:
        if fragment == '`*`':
            special_cased_fragments.append('*')
        else:
            special_cased_fragments.append(fragment)

    return '.'.join(special_cased_fragments)
