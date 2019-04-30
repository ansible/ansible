# coding: utf-8
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import sys
from collections import UserString
from distutils.version import LooseVersion

# Pylint doesn't understand Python3 namespace modules.
from ..commands import Command  # pylint: disable=relative-beyond-top-level
from .. import errors  # pylint: disable=relative-beyond-top-level


class VersionStr(UserString):
    def __init__(self, string):
        super().__init__(string.strip())
        self.ver_obj = LooseVersion(string)


def transform_args(args):
    # Make it possible to sort versions in the jinja2 templates
    new_versions = []
    for version in args.versions:
        new_versions.append(VersionStr(version))
    args.versions = new_versions

    return args


def write_message(filename, message):
    if filename != '-':
        with open(filename, 'w') as out_file:
            out_file.write(message)
    else:
        sys.stdout.write('\n\n')
        sys.stdout.write(message)


class ReleaseAnnouncementCommand(Command):
    name = 'release-announcement'

    @classmethod
    def init_parser(cls, add_parser):
        parser = add_parser(cls.name,
                            description="Generate email and twitter announcements from template")

        parser.add_argument("--version", dest="versions", type=str, required=True, action='append',
                            help="Versions of Ansible to announce")
        parser.add_argument("--name", type=str, required=True, help="Real name to use on emails")
        parser.add_argument("--email-out", type=str, default="-",
                            help="Filename to place the email announcement into")
        parser.add_argument("--twitter-out", type=str, default="-",
                            help="Filename to place the twitter announcement into")

    @classmethod
    def main(cls, args):
        if sys.version_info < (3, 6):
            raise errors.DependencyError('The {0} subcommand needs Python-3.6+'
                                         ' to run'.format(cls.name))

        # Import here because these functions are invalid on Python-3.5 and the command plugins and
        # init_parser() method need to be compatible with Python-3.4+ for now.
        # Pylint doesn't understand Python3 namespace modules.
        from .. announce import create_short_message, create_long_message  # pylint: disable=relative-beyond-top-level

        args = transform_args(args)

        twitter_message = create_short_message(args.versions)
        email_message = create_long_message(args.versions, args.name)

        write_message(args.twitter_out, twitter_message)
        write_message(args.email_out, email_message)
        return 0
