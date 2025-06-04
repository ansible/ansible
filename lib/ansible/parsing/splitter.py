# (c) 2014 James Cammarata, <jcammarata@ansible.com>
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

from __future__ import annotations

import codecs
import re

from ansible.errors import AnsibleParserError
from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils._internal._datatag import AnsibleTagHelper
from ansible._internal._datatag._tags import Origin, TrustedAsTemplate
from ansible.parsing.quoting import unquote


# Decode escapes adapted from rspeer's answer here:
# http://stackoverflow.com/questions/4020539/process-escape-sequences-in-a-string-in-python
_HEXCHAR = '[a-fA-F0-9]'
_ESCAPE_SEQUENCE_RE = re.compile(r"""
    ( \\U{0}           # 8-digit hex escapes
    | \\u{1}           # 4-digit hex escapes
    | \\x{2}           # 2-digit hex escapes
    | \\N\{{[^}}]+\}}  # Unicode characters by name
    | \\[\\'"abfnrtv]  # Single-character escapes
    )""".format(_HEXCHAR * 8, _HEXCHAR * 4, _HEXCHAR * 2), re.UNICODE | re.VERBOSE)


def _decode_escapes(s):
    def decode_match(match):
        return codecs.decode(match.group(0), 'unicode-escape')

    return _ESCAPE_SEQUENCE_RE.sub(decode_match, s)


def parse_kv(args, check_raw=False):
    """
    Convert a string of key/value items to a dict. If any free-form params
    are found and the check_raw option is set to True, they will be added
    to a new parameter called '_raw_params'. If check_raw is not enabled,
    they will simply be ignored.
    """

    tags = []
    if origin_tag := Origin.get_tag(args):
        # NB: adjusting the column number is left as an exercise for the reader
        tags.append(origin_tag)
    if trusted_tag := TrustedAsTemplate.get_tag(args):
        tags.append(trusted_tag)

    args = to_text(args, nonstring='passthru')

    options = {}
    if args is not None:
        vargs = split_args(args)

        raw_params = []
        for orig_x in vargs:
            x = _decode_escapes(orig_x)
            if "=" in x:
                pos = 0
                try:
                    while True:
                        pos = x.index('=', pos + 1)
                        if pos > 0 and x[pos - 1] != '\\':
                            break
                except ValueError:
                    # ran out of string, but we must have some escaped equals,
                    # so replace those and append this to the list of raw params
                    raw_params.append(x.replace('\\=', '='))
                    continue

                k = x[:pos]
                v = x[pos + 1:]

                # FIXME: make the retrieval of this list of shell/command options a function, so the list is centralized
                if check_raw and k not in ('creates', 'removes', 'chdir', 'executable', 'warn', 'stdin', 'stdin_add_newline', 'strip_empty_ends'):
                    raw_params.append(orig_x)
                else:
                    options[k.strip()] = unquote(v.strip())
            else:
                raw_params.append(orig_x)

        # recombine the free-form params, if any were found, and assign
        # them to a special option for use later by the shell/command module
        if len(raw_params) > 0:
            options[u'_raw_params'] = join_args(raw_params)

    if tags:
        options = {AnsibleTagHelper.tag(k, tags): AnsibleTagHelper.tag(v, tags) for k, v in options.items()}

    if origin_tag:
        options = origin_tag.tag(options)

    return options


def _get_quote_state(token, quote_char):
    """
    the goal of this block is to determine if the quoted string
    is unterminated in which case it needs to be put back together
    """
    # the char before the current one, used to see if
    # the current character is escaped
    prev_char = None
    for idx, cur_char in enumerate(token):
        if idx > 0:
            prev_char = token[idx - 1]
        if cur_char in '"\'' and prev_char != '\\':
            if quote_char:
                if cur_char == quote_char:
                    quote_char = None
            else:
                quote_char = cur_char
    return quote_char


def _count_jinja2_blocks(token, cur_depth, open_token, close_token):
    """
    this function counts the number of opening/closing blocks for a
    given opening/closing type and adjusts the current depth for that
    block based on the difference
    """
    num_open = token.count(open_token)
    num_close = token.count(close_token)
    if num_open != num_close:
        cur_depth += (num_open - num_close)
        if cur_depth < 0:
            cur_depth = 0
    return cur_depth


def join_args(s):
    """
    Join the original cmd based on manipulations by split_args().
    This retains the original newlines and whitespaces.
    """
    result = ''
    for p in s:
        if len(result) == 0 or result.endswith('\n'):
            result += p
        else:
            result += ' ' + p
    return result


def split_args(args):
    """
    Splits args on whitespace, but intelligently reassembles
    those that may have been split over a jinja2 block or quotes.

    When used in a remote module, we won't ever have to be concerned about
    jinja2 blocks, however this function is/will be used in the
    core portions as well before the args are templated.

    example input: a=b c="foo bar"
    example output: ['a=b', 'c="foo bar"']

    Basically this is a variation shlex that has some more intelligence for
    how Ansible needs to use it.
    """

    if not args:
        return []

    # the list of params parsed out of the arg string
    # this is going to be the result value when we are done
    params = []

    # Initial split on newlines
    items = args.split('\n')

    # iterate over the tokens, and reassemble any that may have been
    # split on a space inside a jinja2 block.
    # ex if tokens are "{{", "foo", "}}" these go together

    # These variables are used
    # to keep track of the state of the parsing, since blocks and quotes
    # may be nested within each other.

    quote_char = None
    inside_quotes = False
    print_depth = 0  # used to count nested jinja2 {{ }} blocks
    block_depth = 0  # used to count nested jinja2 {% %} blocks
    comment_depth = 0  # used to count nested jinja2 {# #} blocks

    # now we loop over each split chunk, coalescing tokens if the white space
    # split occurred within quotes or a jinja2 block of some kind
    for (itemidx, item) in enumerate(items):

        # we split on spaces and newlines separately, so that we
        # can tell which character we split on for reassembly
        # inside quotation characters
        tokens = item.split(' ')

        line_continuation = False
        for (idx, token) in enumerate(tokens):

            # Empty entries means we have subsequent spaces
            # We want to hold onto them so we can reconstruct them later
            if len(token) == 0 and idx != 0:
                # Make sure there is a params item to store result in.
                if not params:
                    params.append('')

                params[-1] += ' '
                continue

            # if we hit a line continuation character, but
            # we're not inside quotes, ignore it and continue
            # on to the next token while setting a flag
            if token == '\\' and not inside_quotes:
                line_continuation = True
                continue

            # store the previous quoting state for checking later
            was_inside_quotes = inside_quotes
            quote_char = _get_quote_state(token, quote_char)
            inside_quotes = quote_char is not None

            # multiple conditions may append a token to the list of params,
            # so we keep track with this flag to make sure it only happens once
            # append means add to the end of the list, don't append means concatenate
            # it to the end of the last token
            appended = False

            # if we're inside quotes now, but weren't before, append the token
            # to the end of the list, since we'll tack on more to it later
            # otherwise, if we're inside any jinja2 block, inside quotes, or we were
            # inside quotes (but aren't now) concat this token to the last param
            if inside_quotes and not was_inside_quotes and not (print_depth or block_depth or comment_depth):
                params.append(token)
                appended = True
            elif print_depth or block_depth or comment_depth or inside_quotes or was_inside_quotes:
                if idx == 0 and was_inside_quotes:
                    params[-1] = "%s%s" % (params[-1], token)
                else:
                    spacer = ''
                    if idx > 0:
                        spacer = ' '
                    params[-1] = "%s%s%s" % (params[-1], spacer, token)
                appended = True

            # if the number of paired block tags is not the same, the depth has changed, so we calculate that here
            # and may append the current token to the params (if we haven't previously done so)
            prev_print_depth = print_depth
            print_depth = _count_jinja2_blocks(token, print_depth, "{{", "}}")
            if print_depth != prev_print_depth and not appended:
                params.append(token)
                appended = True

            prev_block_depth = block_depth
            block_depth = _count_jinja2_blocks(token, block_depth, "{%", "%}")
            if block_depth != prev_block_depth and not appended:
                params.append(token)
                appended = True

            prev_comment_depth = comment_depth
            comment_depth = _count_jinja2_blocks(token, comment_depth, "{#", "#}")
            if comment_depth != prev_comment_depth and not appended:
                params.append(token)
                appended = True

            # finally, if we're at zero depth for all blocks and not inside quotes, and have not
            # yet appended anything to the list of params, we do so now
            if not (print_depth or block_depth or comment_depth) and not inside_quotes and not appended and token != '':
                params.append(token)

        # if this was the last token in the list, and we have more than
        # one item (meaning we split on newlines), add a newline back here
        # to preserve the original structure
        if len(items) > 1 and itemidx != len(items) - 1 and not line_continuation:
            # Make sure there is a params item to store result in.
            if not params:
                params.append('')

            params[-1] += '\n'

    # If we're done and things are not at zero depth or we're still inside quotes,
    # raise an error to indicate that the args were unbalanced
    if print_depth or block_depth or comment_depth or inside_quotes:
        raise AnsibleParserError(u"failed at splitting arguments, either an unbalanced jinja2 block or quotes: {0}".format(args))

    return params
