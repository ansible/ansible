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

def split_args(args):
    '''
    Splits args on whitespace, but intelligently reassembles
    those that may have been split over a jinja2 block or quotes.

    When used in a remote module, we won't ever have to be concerned about
    jinja2 blocks, however this function is/will be used in the
    core portions as well before the args are templated.

    example input: a=b c=d
    example output: dict(a='b', c='d')

    Basically this is a variation shlex that has some more intelligence for
    how Ansible needs to use it.
    '''

    # FIXME: refactoring into smaller functions

    # the list of params parsed out of the arg string
    # this is going to be the result value when we are donei
    params = []

    # here we encode the args, so we have a uniform charset to
    # work with, and split on white space
    args = args.encode('utf-8')
    items = args.split()

    # iterate over the items, and reassemble any that may have been
    # split on a space inside a jinja2 block. 
    # ex if tokens are "{{", "foo", "}}" these go together

    # These variables are used
    # to keep track of the state of the parsing, since blocks and quotes
    # may be nested within each other.

    inside_quotes = False
    quote_char = None
    split_print_depth = 0
    split_block_depth = 0
    split_comment_depth = 0

    # now we loop over each split item, coalescing items if the white space
    # split occurred within quotes or a jinja2 block of some kind

    for item in items:

        item = item.strip()

        # store the previous quoting state for checking later
        was_inside_quotes = inside_quotes

        # determine the current quoting state
        # the goal of this block is to determine if the quoted string
        # is unterminated in which case it needs to be put back together

        bc = None # before_char
        for i in range(0, len(item)):  # use enumerate

            c = item[i]  # current_char

            if i > 0:
                bc = item[i-1]

            if c in ('"', "'"):
                if inside_quotes:
                    if c == quote_char and bc != '\\':
                        inside_quotes = False
                        quote_char = None
                else:
                    inside_quotes = True
                    quote_char = c

        # multiple conditions may append a token to the list of params,
        # so we keep track with this flag to make sure it only happens once
        # append means add to the end of the list, don't append means concatenate
        # it to the end of the last token
        appended = False

        # if we're inside quotes now, but weren't before, append the item
        # to the end of the list, since we'll tack on more to it later

        if inside_quotes and not was_inside_quotes:
            params.append(item)
            appended = True

        # otherwise, if we're inside any jinja2 block, inside quotes, or we were
        # inside quotes (but aren't now) concat this item to the last param
        # FIXME: just or these all together
        elif (split_print_depth or split_block_depth or split_comment_depth or inside_quotes or was_inside_quotes):
            params[-1] = "%s %s" % (params[-1], item)
            appended = True

        # these variables are used to determine the current depth of each jinja2
        # block type, by counting the number of openings and closing tags
        # FIXME: assumes Jinja2 seperators aren't changeable (also true elsewhere in ansible ATM)

        num_print_open    = item.count('{{')
        num_print_close   = item.count('}}')
        num_block_open    = item.count('{%')
        num_block_close   = item.count('%}')
        num_comment_open  = item.count('{#')
        num_comment_close = item.count('#}')

        # if the number of paired block tags is not the same, the depth has changed, so we calculate that here
        # and may append the current item to the params (if we haven't previously done so)

        # FIXME: DRY a bit
        if num_print_open != num_print_close:
            split_print_depth += (num_print_open - num_print_close)
            if not appended:
                params.append(item)
                appended = True
            if split_print_depth < 0:
                split_print_depth = 0

        if num_block_open != num_block_close:
            split_block_depth += (num_block_open - num_block_close)
            if not appended:
                params.append(item)
                appended = True
            if split_block_depth < 0:
                split_block_depth = 0

        if num_comment_open != num_comment_close:
            split_comment_depth += (num_comment_open - num_comment_close)
            if not appended:
                params.append(item)
                appended = True
            if split_comment_depth < 0:
                split_comment_depth = 0

        # finally, if we're at zero depth for all blocks and not inside quotes, and have not
        # yet appended anything to the list of params, we do so now

        if not (split_print_depth or split_block_depth or split_comment_depth) and not inside_quotes and not appended:
            params.append(item)

    # If we're done and things are not at zero depth or we're still inside quotes,
    # raise an error to indicate that the args were unbalanced

    if (split_print_depth or split_block_depth or split_comment_depth) or inside_quotes:
        raise Exception("error while splitting arguments, either an unbalanced jinja2 block or quotes")

    # finally, we decode each param back to the unicode it was in the arg string
    params = [x.decode('utf-8') for x in params]
    return params

