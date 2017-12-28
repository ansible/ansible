# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
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


def _get_quote_state(token, quote_char):
    '''
    the goal of this block is to determine if the quoted string
    is unterminated in which case it needs to be put back together
    '''
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
    '''
    this function counts the number of opening/closing blocks for a
    given opening/closing type and adjusts the current depth for that
    block based on the difference
    '''
    num_open = token.count(open_token)
    num_close = token.count(close_token)
    if num_open != num_close:
        cur_depth += (num_open - num_close)
        if cur_depth < 0:
            cur_depth = 0
    return cur_depth


def split_args(args):
    '''
    Splits args on whitespace, but intelligently reassembles
    those that may have been split over a jinja2 block or quotes.

    When used in a remote module, we won't ever have to be concerned about
    jinja2 blocks, however this function is/will be used in the
    core portions as well before the args are templated.

    example input: a=b c="foo bar"
    example output: ['a=b', 'c="foo bar"']

    Basically this is a variation shlex that has some more intelligence for
    how Ansible needs to use it.
    '''

    # the list of params parsed out of the arg string
    # this is going to be the result value when we are donei
    params = []

    # here we encode the args, so we have a uniform charset to
    # work with, and split on white space
    args = args.strip()
    try:
        args = args.encode('utf-8')
        do_decode = True
    except UnicodeDecodeError:
        do_decode = False
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
    for itemidx, item in enumerate(items):

        # we split on spaces and newlines separately, so that we
        # can tell which character we split on for reassembly
        # inside quotation characters
        tokens = item.strip().split(' ')

        line_continuation = False
        for idx, token in enumerate(tokens):

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
            if inside_quotes and not was_inside_quotes:
                params.append(token)
                appended = True
            elif print_depth or block_depth or comment_depth or inside_quotes or was_inside_quotes:
                if idx == 0 and not inside_quotes and was_inside_quotes:
                    params[-1] = "%s%s" % (params[-1], token)
                elif len(tokens) > 1:
                    spacer = ''
                    if idx > 0:
                        spacer = ' '
                    params[-1] = "%s%s%s" % (params[-1], spacer, token)
                else:
                    spacer = ''
                    if not params[-1].endswith('\n') and idx == 0:
                        spacer = '\n'
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
            if not params[-1].endswith('\n') or item == '':
                params[-1] += '\n'

        # always clear the line continuation flag
        line_continuation = False

    # If we're done and things are not at zero depth or we're still inside quotes,
    # raise an error to indicate that the args were unbalanced
    if print_depth or block_depth or comment_depth or inside_quotes:
        raise Exception("error while splitting arguments, either an unbalanced jinja2 block or quotes")

    # finally, we decode each param back to the unicode it was in the arg string
    if do_decode:
        params = [x.decode('utf-8') for x in params]

    return params


def is_quoted(data):
    return len(data) > 0 and (data[0] == '"' and data[-1] == '"' or data[0] == "'" and data[-1] == "'")


def unquote(data):
    ''' removes first and last quotes from a string, if the string starts and ends with the same quotes '''
    if is_quoted(data):
        return data[1:-1]
    return data
