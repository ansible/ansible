#!/usr/bin/env python3
# coding: utf-8
# PYTHON_ARGCOMPLETE_OK
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import argparse
import os.path
import sys

from straight.plugin import load

try:
    import argcomplete
except ImportError:
    argcomplete = None


def build_lib_path(this_script=__file__):
    """Return path to the common build library directory"""
    hacking_dir = os.path.dirname(this_script)
    libdir = os.path.abspath(os.path.join(hacking_dir, 'build_library'))

    return libdir


sys.path.insert(0, build_lib_path())

from build_ansible import commands, errors


def create_arg_parser(program_name):
    """
    Creates a command line argument parser

    :arg program_name: The name of the script.  Used in help texts
    """
    parser = argparse.ArgumentParser(prog=program_name,
                                     description="Implements utilities to build Ansible")
    return parser


def main():
    """
    Main entrypoint of the script

    "It all starts here"
    """
    subcommands = load('build_ansible.command_plugins', subclasses=commands.Command)

    arg_parser = create_arg_parser(os.path.basename(sys.argv[0]))
    subparsers = arg_parser.add_subparsers(title='Subcommands', dest='command',
                                           help='for help use build-ansible.py SUBCOMMANDS -h')
    subcommands.pipe('init_parser', subparsers.add_parser)

    if argcomplete:
        argcomplete.autocomplete(arg_parser)

    args = arg_parser.parse_args(sys.argv[1:])
    if args.command is None:
        print('Please specify a subcommand to run')
        sys.exit(1)

    for subcommand in subcommands:
        if subcommand.name == args.command:
            command = subcommand
            break
    else:
        # Note: We should never trigger this because argparse should shield us from it
        print('Error: {0} was not a recognized subcommand'.format(args.command))
        sys.exit(1)

    try:
        retval = command.main(args)
    except errors.DependencyError as e:
        print(e)
        sys.exit(2)

    sys.exit(retval)


if __name__ == '__main__':
    main()
