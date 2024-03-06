# Copyright 2015 Abhijit Menon-Sen <ams@2ndQuadrant.com>
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

import re
from ansible.errors import AnsibleParserError, AnsibleError

# Components that match a numeric or alphanumeric begin:end or begin:end:step
# range expression inside square brackets.

numeric_range = r'''
    \[
        (?:[0-9]+:[0-9]+)               # numeric begin:end
        (?::[0-9]+)?                    # numeric :step (optional)
    \]
'''

hexadecimal_range = r'''
    \[
        (?:[0-9a-f]+:[0-9a-f]+)         # hexadecimal begin:end
        (?::[0-9]+)?                    # numeric :step (optional)
    \]
'''

alphanumeric_range = r'''
    \[
        (?:
            [a-z]:[a-z]|                # one-char alphabetic range
            [0-9]+:[0-9]+               # ...or a numeric one
        )
        (?::[0-9]+)?                    # numeric :step (optional)
    \]
'''

# Components that match a 16-bit portion of an IPv6 address in hexadecimal
# notation (0..ffff) or an 8-bit portion of an IPv4 address in decimal notation
# (0..255) or an [x:y(:z)] numeric range.

ipv6_component = r'''
    (?:
        [0-9a-f]{{1,4}}|                # 0..ffff
        {range}                         # or a numeric range
    )
'''.format(range=hexadecimal_range)

ipv4_component = r'''
    (?:
        [01]?[0-9]{{1,2}}|              # 0..199
        2[0-4][0-9]|                    # 200..249
        25[0-5]|                        # 250..255
        {range}                         # or a numeric range
    )
'''.format(range=numeric_range)

# A hostname label, e.g. 'foo' in 'foo.example.com'. Consists of alphanumeric
# characters plus dashes (and underscores) or valid ranges. The label may not
# start or end with a hyphen or an underscore. This is interpolated into the
# hostname pattern below. We don't try to enforce the 63-char length limit.

label = r'''
    (?:[\w]|{range})                    # Starts with an alphanumeric or a range
    (?:[\w_-]|{range})*                 # Then zero or more of the same or [_-]
    (?<![_-])                           # ...as long as it didn't end with [_-]
'''.format(range=alphanumeric_range)

patterns = {
    # This matches a square-bracketed expression with a port specification. What
    # is inside the square brackets is validated later.

    'bracketed_hostport': re.compile(
        r'''^
            \[(.+)\]                    # [host identifier]
            :([0-9]+)                   # :port number
            $
        ''', re.X
    ),

    # This matches a bare IPv4 address or hostname (or host pattern including
    # [x:y(:z)] ranges) with a port specification.

    'hostport': re.compile(
        r'''^
            ((?:                        # We want to match:
                [^:\[\]]                # (a non-range character
                |                       # ...or...
                \[[^\]]*\]              # a complete bracketed expression)
            )*)                         # repeated as many times as possible
            :([0-9]+)                   # followed by a port number
            $
        ''', re.X
    ),

    # This matches an IPv4 address, but also permits range expressions.

    'ipv4': re.compile(
        r'''^
            (?:{i4}\.){{3}}{i4}         # Three parts followed by dots plus one
            $
        '''.format(i4=ipv4_component), re.X | re.I
    ),

    # This matches an IPv6 address, but also permits range expressions.
    #
    # This expression looks complex, but it really only spells out the various
    # combinations in which the basic unit of an IPv6 address (0..ffff) can be
    # written, from :: to 1:2:3:4:5:6:7:8, plus the IPv4-in-IPv6 variants such
    # as ::ffff:192.0.2.3.
    #
    # Note that we can't just use ipaddress.ip_address() because we also have to
    # accept ranges in place of each component.

    'ipv6': re.compile(
        r'''^
            (?:{0}:){{7}}{0}|           # uncompressed: 1:2:3:4:5:6:7:8
            (?:{0}:){{1,6}}:|           # compressed variants, which are all
            (?:{0}:)(?::{0}){{1,6}}|    # a::b for various lengths of a,b
            (?:{0}:){{2}}(?::{0}){{1,5}}|
            (?:{0}:){{3}}(?::{0}){{1,4}}|
            (?:{0}:){{4}}(?::{0}){{1,3}}|
            (?:{0}:){{5}}(?::{0}){{1,2}}|
            (?:{0}:){{6}}(?::{0})|      # ...all with 2 <= a+b <= 7
            :(?::{0}){{1,6}}|           # ::ffff(:ffff...)
            {0}?::|                     # ffff::, ::
                                        # ipv4-in-ipv6 variants
            (?:0:){{6}}(?:{0}\.){{3}}{0}|
            ::(?:ffff:)?(?:{0}\.){{3}}{0}|
            (?:0:){{5}}ffff:(?:{0}\.){{3}}{0}
            $
        '''.format(ipv6_component), re.X | re.I
    ),

    # This matches a hostname or host pattern including [x:y(:z)] ranges.
    #
    # We roughly follow DNS rules here, but also allow ranges (and underscores).
    # In the past, no systematic rules were enforced about inventory hostnames,
    # but the parsing context (e.g. shlex.split(), fnmatch.fnmatch()) excluded
    # various metacharacters anyway.
    #
    # We don't enforce DNS length restrictions here (63 characters per label,
    # 253 characters total) or make any attempt to process IDNs.

    'hostname': re.compile(
        r'''^
            {label}                     # We must have at least one label
            (?:\.{label})*              # Followed by zero or more .labels
            $
        '''.format(label=label), re.X | re.I | re.UNICODE
    ),

}


def parse_address(address, allow_ranges=False):
    """
    Takes a string and returns a (host, port) tuple. If the host is None, then
    the string could not be parsed as a host identifier with an optional port
    specification. If the port is None, then no port was specified.

    The host identifier may be a hostname (qualified or not), an IPv4 address,
    or an IPv6 address. If allow_ranges is True, then any of those may contain
    [x:y] range specifications, e.g. foo[1:3] or foo[0:5]-bar[x-z].

    The port number is an optional :NN suffix on an IPv4 address or host name,
    or a mandatory :NN suffix on any square-bracketed expression: IPv6 address,
    IPv4 address, or host name. (This means the only way to specify a port for
    an IPv6 address is to enclose it in square brackets.)
    """

    # First, we extract the port number if one is specified.

    port = None
    for matching in ['bracketed_hostport', 'hostport']:
        m = patterns[matching].match(address)
        if m:
            (address, port) = m.groups()
            port = int(port)
            continue

    # What we're left with now must be an IPv4 or IPv6 address, possibly with
    # numeric ranges, or a hostname with alphanumeric ranges.

    host = None
    for matching in ['ipv4', 'ipv6', 'hostname']:
        m = patterns[matching].match(address)
        if m:
            host = address
            continue

    # If it isn't any of the above, we don't understand it.
    if not host:
        raise AnsibleError("Not a valid network hostname: %s" % address)

    # If we get to this point, we know that any included ranges are valid.
    # If the caller is prepared to handle them, all is well.
    # Otherwise we treat it as a parse failure.
    if not allow_ranges and '[' in host:
        raise AnsibleParserError("Detected range in host but was asked to ignore ranges")

    return (host, port)
