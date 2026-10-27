# Copyright (c) 2018, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import os
import stat
import re
import typing as t


# Keys are ordered the way lsattr prints flags and _sort_attr_flags() relies on
# that, so do not reorder them. The order is taken from flags_array in
# lib/e2p/pf.c in e2fsprogs, which print_flags() walks once per file; neither
# chattr(1) nor lsattr(1) documents it, both listing flags alphabetically
# instead. The last three are no longer printed by current lsattr and are kept
# for older versions.
FILE_ATTRIBUTES = {
    's': 'zero',
    'u': 'undelete',
    'S': 'synchronous',
    'D': 'dirsync',
    'i': 'immutable',
    'a': 'append',
    'd': 'nodump',
    'A': 'noatime',
    'c': 'compressed',
    'E': 'encrypted',
    'j': 'journalled',
    'I': 'indexed',
    't': 'notail',
    'T': 'blockroot',
    'e': 'extents',
    'C': 'nocow',
    'x': 'dax',
    'F': 'casefold',
    'N': 'inline',
    'P': 'projinherit',
    'V': 'verity',
    'm': 'nocompress',
    'h': 'blocksize',
    'X': 'compressedraw',
    'Z': 'compresseddirty',
}


# Used for parsing symbolic file perms
MODE_OPERATOR_RE = re.compile(r'[+=-]')
USERS_RE = re.compile(r'[^ugo]')
PERMS_RE = re.compile(r'[^rwxXstugo]')


S_IRANY = 0o0444  # read by user, group, others
S_IWANY = 0o0222  # write by user, group, others
S_IXANY = 0o0111  # execute by user, group, others
S_IRWU_RWG_RWO = S_IRANY | S_IWANY  # read, write by user, group, others
S_IRWU_RG_RO = S_IRANY | stat.S_IWUSR  # read by user, group, others and write only by user
S_IRWXU_RXG_RXO = S_IRANY | S_IXANY | stat.S_IWUSR  # read, execute by user, group, others and write only by user
_PERM_BITS = 0o7777             # file mode permission bits
_EXEC_PERM_BITS = S_IXANY       # execute permission bits
_DEFAULT_PERM = S_IRWU_RWG_RWO  # default file permission bits


def is_executable(path):
    # This function's signature needs to be repeated
    # as the first line of its docstring.
    # This method is reused by the basic module,
    # the repetition helps the basic module's html documentation come out right.
    # http://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#confval-autodoc_docstring_signature
    """is_executable(path)

    is the given path executable?

    :arg path: The path of the file to check.

    Limitations:

    * Does not account for FSACLs.
    * Most times we really want to know "Can the current user execute this
      file".  This function does not tell us that, only if any execute bit is set.
    """
    # These are all bitfields so first bitwise-or all the permissions we're
    # looking for, then bitwise-and with the file's mode to determine if any
    # execute bits are set.
    return ((stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) & os.stat(path)[stat.ST_MODE])


def format_attributes(attributes):
    attribute_list = [FILE_ATTRIBUTES.get(attr) for attr in attributes if attr in FILE_ATTRIBUTES]
    return attribute_list


def get_flags_from_attributes(attributes):
    flags = [key for key, attr in FILE_ATTRIBUTES.items() if attr in attributes]
    return ''.join(flags)


def _sort_attr_flags(flags: t.Iterable[str]) -> str:
    """Return ``flags`` as a string ordered the way lsattr prints them, unknown flags last."""
    flags = set(flags)
    known = [flag for flag in FILE_ATTRIBUTES if flag in flags]
    return ''.join(known + sorted(flags.difference(FILE_ATTRIBUTES)))


def get_file_arg_spec():
    arg_spec = dict(
        mode=dict(type='raw'),
        owner=dict(),
        group=dict(),
        seuser=dict(),
        serole=dict(),
        selevel=dict(),
        setype=dict(),
        attributes=dict(aliases=['attr']),
    )
    return arg_spec
