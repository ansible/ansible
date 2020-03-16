# Copyright (c) 2020 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re

from distutils.version import Version

from ansible.module_utils.six import text_type


# Regular expression taken from
# https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
SEMVER_RE = re.compile(
    r'''
    ^
        (?P<major>0|[1-9]\d*)
        \.
        (?P<minor>0|[1-9]\d*)
        \.
        (?P<patch>0|[1-9]\d*)
        (?:
            -
            (?P<prerelease>
                (?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)
                (?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*
            )
        )?
        (?:
            \+
            (?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*)
        )?
    $
    ''',
    flags=re.X
)


class _Alpha:
    """Class to easily allow comparing strings

    Largely this exists to make comparing an interger and a string on py3
    so that it works like py2.
    """
    def __init__(self, specifier):
        self.specifier = specifier

    def repr(self):
        return self.specifier

    def __eq__(self, other):
        if isinstance(other, _Alpha):
            return self.specifier == other.specifier
        elif isinstance(other, str):
            return self.specifier == other

        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if isinstance(other, _Alpha):
            return self.specifier < other.specifier
        elif isinstance(other, str):
            return self.specifier < other
        elif isinstance(other, _Numeric):
            return False

        raise ValueError

    def __gt__(self, other):
        return not self.__lt__(other)

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)


class _Numeric:
    """Class to easily allow comparing numbers

    Largely this exists to make comparing an interger and a string on py3
    so that it works like py2.
    """
    def __init__(self, specifier):
        self.specifier = int(specifier)

    def repr(self):
        return self.specifier

    def __eq__(self, other):
        if isinstance(other, _Numeric):
            return self.specifier == other.specifier
        elif isinstance(other, int):
            return self.specifier == other

        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if isinstance(other, _Numeric):
            return self.specifier < other.specifier
        elif isinstance(other, int):
            return self.specifier < other
        elif isinstance(other, _Alpha):
            return True

        raise ValueError

    def __gt__(self, other):
        return not self.__lt__(other)

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)


class SemanticVersion(Version):
    version_re = SEMVER_RE

    def __init__(self, vstring=None):
        self.vstring = vstring
        self.major = None
        self.minor = None
        self.patch = None
        self.prerelease = ()
        self.buildmetadata = ()

        if vstring:
            self.parse(vstring)

    def __repr__(self):
        return 'SemanticVersion(%r)' % self.vstring

    def parse(self, vstring):
        match = SEMVER_RE.match(vstring)
        if not match:
            raise ValueError("invalid semantic version '%s'" % vstring)

        (major, minor, patch, prerelease, buildmetadata) = match.group(1, 2, 3, 4, 5)
        self.major = int(major)
        self.minor = int(minor)
        self.patch = int(patch)

        if prerelease:
            self.prerelease = tuple(_Numeric(x) if x.isdigit() else _Alpha(x) for x in prerelease.split('.'))
        if buildmetadata:
            self.buildmetadata = tuple(_Numeric(x) if x.isdigit() else _Alpha(x) for x in buildmetadata.split('.'))

    @property
    def core(self):
        return self.major, self.minor, self.patch

    @property
    def is_prerelease(self):
        return self.major == 0 or self.prerelease

    def _cmp(self, other):
        if isinstance(other, str):
            other = SemanticVersion(other)

        if self.core != other.core:
            if self.core < other.core:
                return -1
            else:
                return 1

        if not any((self.prerelease, other.prerelease, self.buildmetadata, other.buildmetadata)):
            return 0

        val = 0

        if self.prerelease and not other.prerelease:
            val -= 1
        elif not self.prerelease and other.prerelease:
            val += 1
        elif self.prerelease and other.prerelease:
            if self.prerelease < other.prerelease:
                val -= 1
            elif self.prerelease > other.prerelease:
                val += 1

        if self.buildmetadata and not other.buildmetadata:
            val += 1
        elif not self.buildmetadata and other.buildmetadata:
            val -= 1
        elif self.buildmetadata and other.buildmetadata:
            if self.buildmetadata < other.buildmetadata:
                val -= 1
            elif self.buildmetadata > other.buildmetadata:
                val += 1

        return val

    # The Py2 and Py3 implementations of distutils.version.Version
    # are quite different, this makes the Py2 and Py3 implementations
    # the same
    def __eq__(self, other):
        return self._cmp(other) == 0

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self._cmp(other) < 0

    def __le__(self, other):
        return self._cmp(other) <= 0

    def __gt__(self, other):
        return self._cmp(other) > 0

    def __ge__(self, other):
        return self._cmp(other) >= 0
