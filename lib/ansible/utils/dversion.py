# Copyright © 2024 mirabilos
# Adapted 2025 for Ansible by mirabilos <tglaser@b1-systems.de>
#
# Provided that these terms and disclaimer and all copyright notices
# are retained or reproduced in an accompanying document, permission
# is granted to deal in this work without restriction, including un-
# limited rights to use, publicly perform, distribute, sell, modify,
# merge, give away, or sublicence.
#
# This work is provided "AS IS" and WITHOUT WARRANTY of any kind, to
# the utmost extent permitted by applicable law, neither express nor
# implied; without malicious intent or gross negligence. In no event
# may a licensor, author or contributor be held liable for indirect,
# direct, other damage, loss, or other issues arising in any way out
# of dealing in the work, even if advised of the possibility of such
# damage or existence of a defect, except proven that it results out
# of said person's immediate fault when using the work as intended.

"""Implementation of sortable versions as in Debian

This module offers the class Version which represents
version strings (bytes, actually, but if you pass str
its UTF-8 encoding is used) that are sortable.

When run as main, argv is shown as sorted JSON array.
"""

from __future__ import annotations

__all__ = ['Version']

import re

# regex to determine Debian version number flavour
_hasepoch = re.compile(b'^(?:0|[1-9][0-9]*):')
_hasmaint = re.compile(b'-[0-9A-Za-z+.~]+$')
# regex to check Debian version number, [_hasepoch][_hasmaint]-indexed
_debverre = (
    (
        re.compile(b'^()([0-9A-Za-z.+~]+)()$'),
        re.compile(b'^()([0-9A-Za-z.+~-]+)-([0-9A-Za-z+.~]+)$'),
    ), (
        re.compile(b'^(0|[1-9][0-9]*):([0-9A-Za-z.+~]+)()$'),
        re.compile(b'^(0|[1-9][0-9]*):([0-9A-Za-z.+~-]+)-([0-9A-Za-z+.~]+)$'),
    ),
)
# split components into runs of digits and not-digits
_cmpsplit = re.compile(b'([0-9]+)')


# split component and normalise
def _cmpprep(v):
    if v is None:
        return None
    v = _cmpsplit.split(v)
    # form as list of pairs of runs (nōn-digit then digit)
    if v[-1] == b'':
        v.pop()
    else:
        v.append(b'0')
    # convert to comparison form even indexes: 0, 2, 4, …
    for i in range(0, len(v), 2):
        b = v[i]
        # pylint: disable-next=consider-using-generator
        v[i] = tuple([_alphprep(b[j:j + 1]) for j in range(len(b))])
    # convert to number the odd indexes: 1, 3, 5, …
    for i in range(1, len(v), 2):
        v[i] = int(v[i])
    return tuple(v)


# implement alphabetic ordering (~ before end,
# then letters, and finally everything else)
def _alphprep(ch):
    if ch == b'~':
        return -1
    if ch < b'A':
        return 128 + ord(ch)
    if ch <= b'Z':
        return ord(ch)
    if ch < b'a':
        return 128 + ord(ch)
    if ch <= b'z':
        return ord(ch)
    return 128 + ord(ch)


# compare two Version objects ⇒ -1 or 0 or 1
def _cmpv(self, other):
    if not isinstance(other, Version):
        return NotImplemented
    # epoch, if present
    if self._cmp[0] < other._cmp[0]:
        return -1
    if self._cmp[0] > other._cmp[0]:
        return 1
    # Debian: upstream version
    # else: entire string
    a = list(self._cmp[1])
    b = list(other._cmp[1])
    # pad with NUL equivalent at the end
    n = max(len(a), len(b))
    while len(a) < n:
        a.extend(((), 0))
    while len(b) < n:
        b.extend(((), 0))
    # loop over (nōn-digit run, digit run) pairs
    for i in range(0, n, 2):
        # the nōn-digit run
        aa = list(a[i])
        bb = list(b[i])
        # pad with NUL (so ~ = -1 works)
        nn = max(len(aa), len(bb))
        while len(aa) < nn:
            aa.append(0)
        while len(bb) < nn:
            bb.append(0)
        for j in range(nn):
            if aa < bb:
                return -1
            if aa > bb:
                return 1
        # and the digit run
        if a[i + 1] < b[i + 1]:
            return -1
        if a[i + 1] > b[i + 1]:
            return 1
    # if Debian revision absent…
    if self._cmp[2] is None:
        if other._cmp[2] is None:
            # in both
            return 0
        # the shorter is smaller then
        return -1
    elif other._cmp[2] is None:
        return 1
    # both present, like upstream version
    a = list(self._cmp[2])
    b = list(other._cmp[2])
    n = max(len(a), len(b))
    while len(a) < n:
        a.extend(((), 0))
    while len(b) < n:
        b.extend(((), 0))
    for i in range(0, n, 2):
        aa = list(a[i])
        bb = list(b[i])
        nn = max(len(aa), len(bb))
        while len(aa) < nn:
            aa.append(0)
        while len(bb) < nn:
            bb.append(0)
        for j in range(nn):
            if aa < bb:
                return -1
            if aa > bb:
                return 1
        if a[i + 1] < b[i + 1]:
            return -1
        if a[i + 1] > b[i + 1]:
            return 1
    return 0


class Version:
    """Sortable representation of a version.

    The usual comparisons (<, >, <=, >=, ==, !=) can be used,
    or a containing list can be sorted; use str or bytes, not
    repr, to output. Versions with isDebianVersion() == False
    are sorted as "upstream version" with no epoch.
    """

    def __init__(self, ver, _only_for_testing=False):
        if isinstance(ver, str):
            self._repr = '"%s"' % ver
            self._str = ver
            ver = ver.encode('UTF-8')
        elif isinstance(ver, bytes):
            self._repr = str(ver)
            self._str = self._repr
        elif _only_for_testing:
            # uses argument unchecked! dversion-t.py only!
            self._deb = (ver[0], ver[1], ver[2])
            ver = b'' + self._deb[1]
            if self._deb[0] != 0:
                ver = str(self._deb[0]).encode('ASCII') + b':' + ver
            if self._deb[2] is not None:
                ver += b'-' + self._deb[2]
            self._repr = str(ver)
            self._str = self._repr
            self._cmp = (self._deb[0], _cmpprep(self._deb[1]), _cmpprep(self._deb[2]))
            self._hash = hash(self._cmp)
            return
        else:
            raise ValueError('Version is not bytes or str')
        if ver == b'':
            raise ValueError('empty Version')
        self._ver = ver
        depoch = _hasepoch.search(ver) and 1 or 0
        dmaint = _hasmaint.search(ver) and 1 or 0
        dparse = _debverre[depoch][dmaint].fullmatch(ver)
        if dparse is None:
            self._deb = False
            dm = [0, ver, None]
        else:
            dm = list(dparse.groups())
            if depoch == 0:
                dm[0] = 0
            else:
                dm[0] = int(dm[0])
            if dmaint == 0:
                dm[2] = None
            if dm[0] <= 2147483647:
                self._deb = tuple(dm)
            else:
                self._deb = False
        dm[1] = _cmpprep(dm[1])
        dm[2] = _cmpprep(dm[2])
        self._cmp = tuple(dm)
        self._hash = hash(self._cmp)

    def __repr__(self):
        return 'Version(%s)' % self._repr

    def __str__(self):
        return self._str

    def __bytes__(self):
        return self._ver

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        return _cmpv(self, other) == 0

    def __ne__(self, other):
        return _cmpv(self, other) != 0

    def __lt__(self, other):
        return _cmpv(self, other) < 0

    def __le__(self, other):
        return _cmpv(self, other) <= 0

    def __gt__(self, other):
        return _cmpv(self, other) > 0

    def __ge__(self, other):
        return _cmpv(self, other) >= 0

    def isDebianVersion(self):
        """Return whether this is a valid Debian version.

        Returns False if not, a three-tuple (epoch:int32,
        upstream:bytes, revision:bytes-or-None) if it is.
        """
        return self._deb


if __name__ == "__main__":
    import sys
    import json
    lst = [Version(x) for x in sys.argv[1:]]
    lst.sort()
    print(json.dumps(lst, allow_nan=False, default=str))
