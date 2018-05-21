from __future__ import absolute_import, division, print_function
__metaclass__ = type

import argparse
import os
import re
import sys

from packaging.version import Version, VERSION_PATTERN


class AnsibleVersionMunger(object):
    tag_offsets = dict(
        dev=0,
        a=100,
        b=200,
        rc=1000
    )

    # TODO: allow overrides here for packaging bump etc
    def __init__(self, raw_version, revision=None, codename=None):
        self._raw_version = raw_version
        self._revision = revision
        self._parsed_version = Version(raw_version)
        self._codename = codename
        self._parsed_regex_match = re.match(VERSION_PATTERN, raw_version, re.VERBOSE | re.IGNORECASE)

    @property
    def deb_version(self):
        v = self._parsed_version

        match = self._parsed_regex_match

        if v.is_prerelease:
            if match.group('pre'):
                tag_value = match.group('pre')
                tag_type = match.group('pre_l')
                tag_ver = match.group('pre_n')
            elif match.group('dev'):
                tag_type = "dev"
                tag_value = match.group('dev')
                tag_ver = match.group('dev_n')
            else:
                raise Exception("unknown prerelease type for version {0}".format(self._raw_version))

        elif v.is_postrelease:
            raise Exception("post-release identifiers are not supported")
        else:
            tag_type = None
            tag_value = ''
            tag_ver = 0

        # not a pre/post/dev release, just return base version
        if not tag_type:
            return '{base_version}'.format(base_version=self.base_version)

        # it is a pre/dev release, include the tag value with a ~
        return '{base_version}~{tag_value}'.format(base_version=self.base_version, tag_value=tag_value)

    @property
    def deb_release(self):
        return '1' if self._revision is None else str(self._revision)

    @property
    def rpm_release(self):
        v = self._parsed_version
        match = self._parsed_regex_match

        if v.is_prerelease:
            if match.group('pre'):
                tag_value = match.group('pre')
                tag_type = match.group('pre_l')
                tag_ver = match.group('pre_n')
            elif match.group('dev'):
                tag_type = "dev"
                tag_value = match.group('dev')
                tag_ver = match.group('dev_n')
            else:
                raise Exception("unknown prerelease type for version {0}".format(self._raw_version))

        elif v.is_postrelease:
            raise Exception("post-release identifiers are not supported")
        else:
            tag_type = None
            tag_value = ''
            tag_ver = 0

        # not a pre/post/dev release, just append revision (default 1)
        if not tag_type:
            if self._revision is None:
                self._revision = 1
            return '{revision}'.format(revision=self._revision)

        # cleanse tag value in case it starts with .
        tag_value = tag_value.strip('.')

        # coerce to int and None == 0
        tag_ver = int(tag_ver if tag_ver else 0)

        if self._revision is None:
            tag_offset = self.tag_offsets.get(tag_type)
            if tag_offset is None:
                raise Exception('no tag offset defined for tag {0}'.format(tag_type))
            pkgrel = '0.{0}'.format(tag_offset + tag_ver)
        else:
            pkgrel = self._revision

        return '{pkgrel}.{tag_value}'.format(pkgrel=pkgrel, tag_value=tag_value)

    @property
    def raw(self):
        return self._raw_version

    # return the x.y.z version without any other modifiers present
    @property
    def base_version(self):
        return self._parsed_version.base_version

    # return the x.y version without any other modifiers present
    @property
    def major_version(self):
        return re.match(r'^(\d+.\d+)', self._raw_version).group(1)

    @property
    def codename(self):
        return self._codename if self._codename else "UNKNOWN"


def main():
    parser = argparse.ArgumentParser(description='Extract/transform Ansible versions to various packaging formats')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--raw', action='store_true')
    group.add_argument('--majorversion', action='store_true')
    group.add_argument('--baseversion', action='store_true')
    group.add_argument('--debversion', action='store_true')
    group.add_argument('--debrelease', action='store_true')
    group.add_argument('--rpmrelease', action='store_true')
    group.add_argument('--codename', action='store_true')
    group.add_argument('--all', action='store_true')

    parser.add_argument('--revision', action='store', default='auto')

    args = parser.parse_args()

    mydir = os.path.dirname(__file__)
    release_loc = os.path.normpath(mydir + '/../../../lib')

    sys.path.insert(0, release_loc)

    from ansible import release

    rev = None
    if args.revision != 'auto':
        rev = args.revision

    v_raw = release.__version__
    codename = release.__codename__
    v = AnsibleVersionMunger(v_raw, revision=rev, codename=codename)

    if args.raw:
        print(v.raw)
    elif args.baseversion:
        print(v.base_version)
    elif args.majorversion:
        print(v.major_version)
    elif args.debversion:
        print(v.deb_version)
    elif args.debrelease:
        print(v.deb_release)
    elif args.rpmrelease:
        print(v.rpm_release)
    elif args.codename:
        print(v.codename)
    elif args.all:
        props = [name for (name, impl) in vars(AnsibleVersionMunger).items() if isinstance(impl, property)]

        for propname in props:
            print('{0}: {1}'.format(propname, getattr(v, propname)))

if __name__ == '__main__':
    main()
