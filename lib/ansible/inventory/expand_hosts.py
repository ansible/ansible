# (c) 2012, Zettar Inc.
# Written by Chin Fang <fangchin@zettar.com>
#
# This file is part of Ansible
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
#

'''
This module is for enhancing ansible's inventory parsing capability such
that it can deal with hostnames specified using a simple pattern in the
form of [beg:end], example: [1:5], [a:c], [D:G]. If beg is not specified,
it defaults to 0.

If beg is given and is left-zero-padded, e.g. '001', it is taken as a
formatting hint when the range is expanded. e.g. [001:010] is to be
expanded into 001, 002 ...009, 010.

Note that when beg is specified with left zero padding, then the length of
end must be the same as that of beg, else an exception is raised.
'''
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import string

from ansible import errors

def detect_range(line = None):
    '''
    A helper function that checks a given host line to see if it contains
    a range pattern described in the docstring above.

    Returnes True if the given line contains a pattern, else False.
    '''
    if '[' in line:
        return True
    else:
        return False

def expand_hostname_range(line = None):
    '''
    A helper function that expands a given line that contains a pattern
    specified in top docstring, and returns a list that consists of the
    expanded version.

    The '[' and ']' characters are used to maintain the pseudo-code
    appearance. They are replaced in this function with '|' to ease
    string splitting.

    References: http://ansible.github.com/patterns.html#hosts-and-groups
    '''
    all_hosts = []
    if line:
        # A hostname such as db[1:6]-node is considered to consists
        # three parts:
        # head: 'db'
        # nrange: [1:6]; range() is a built-in. Can't use the name
        # tail: '-node'

        # Add support for multiple ranges in a host so:
        # db[01:10:3]node-[01:10]
        # - to do this we split off at the first [...] set, getting the list
        #   of hosts and then repeat until none left.
        # - also add an optional third parameter which contains the step. (Default: 1)
        #   so range can be [01:10:2] -> 01 03 05 07 09

        (head, nrange, tail) = line.replace('[','|',1).replace(']','|',1).split('|')
        bounds = nrange.split(":")
        if len(bounds) != 2 and len(bounds) != 3:
            raise errors.AnsibleError("host range must be begin:end or begin:end:step")
        beg = bounds[0]
        end = bounds[1]
        if len(bounds) == 2:
            step = 1
        else:
            step = bounds[2]
        if not beg:
            beg = "0"
        if not end:
            raise errors.AnsibleError("host range must specify end value")
        if beg[0] == '0' and len(beg) > 1:
            rlen = len(beg) # range length formatting hint
            if rlen != len(end):
                raise errors.AnsibleError("host range must specify equal-length begin and end formats")
            fill = lambda _: str(_).zfill(rlen)  # range sequence
        else:
            fill = str

        try:
            i_beg = string.ascii_letters.index(beg)
            i_end = string.ascii_letters.index(end)
            if i_beg > i_end:
                raise errors.AnsibleError("host range must have begin <= end")
            seq = list(string.ascii_letters[i_beg:i_end+1:int(step)])
        except ValueError:  # not an alpha range
            seq = range(int(beg), int(end)+1, int(step))

        for rseq in seq:
            hname = ''.join((head, fill(rseq), tail))

            if detect_range(hname):
                all_hosts.extend( expand_hostname_range( hname ) )
            else:
                all_hosts.append(hname)

        return all_hosts
