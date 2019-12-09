# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import re
from distutils.version import LooseVersion
from functools import total_ordering


@total_ordering
class SemanticVersion(object):
    """
    Minimal implementation of the semver.org specification.

    Inspired from https://github.com/rbarrois/python-semanticversion

    """
    version_re = re.compile(r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9a-zA-Z.-]+))?(?:\+([0-9a-zA-Z.-]+))?$')

    def __init__(self, version_string):
        self.version_string = version_string

    @property
    def is_prerelease(self):
        """Return True if this is a pre-release. """
        match = self.version_re.match(self.version_string)
        if not match:
            return False
        _, _, _, prerelease, _ = match.groups()
        return bool(prerelease)

    @property
    def loose_version(self):
        """ Return a distutils.version.LooseVersion for this version. """
        match = self.version_re.match(self.version_string)
        major, minor, patch, _, _ = match.groups()
        return LooseVersion('%s.%s.%s' % (major, minor, patch))

    def __eq__(self, other):
        if self.is_prerelease or other.is_prerelease:
            # TODO: compare prereleases according to semver spec
            raise NotImplementedError('distutils cannot compare semver prereleases')
        return self.loose_version == other.loose_version

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self.loose_version < other.loose_version

    def __str__(self):
        return self.version_string

    def __repr__(self):
        return "SemanticVersion(%s)" % self.version_string
