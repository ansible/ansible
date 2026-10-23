# Copyright (c) Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

"""Helpers for Linux extended attributes (xattrs).

These wrap ``os.listxattr``/``os.getxattr``/``os.setxattr``/``os.removexattr``
so other parts of Ansible (the ``copy`` and ``file`` modules, ``atomic_move``,
the ``template`` action plugin, and external xattr modules) can share one
implementation.

``security.selinux`` is excluded from every operation here. SELinux contexts
are managed through the dedicated ``seuser``/``serole``/``setype``/``selevel``
parameters, so reading or rewriting that xattr through the generic path would
conflict with that machinery.
"""

from __future__ import annotations

import base64
import os

SELINUX_XATTR = 'security.selinux'

PRESERVE_MODES = ('no', 'target', 'source', 'merge')
ERROR_MODES = ('fail', 'warn', 'ignore')


def xattrs_supported():
    """Return True if the running Python on this platform exposes xattr syscalls."""
    return hasattr(os, 'listxattr')


def read_xattrs(path, follow_symlinks=True):
    """Read every xattr on *path* and return ``{name: bytes_value}``.

    ``security.selinux`` is skipped.

    Returns ``None`` if the platform does not expose xattr syscalls at all.
    Raises ``OSError`` if the filesystem refuses (``ENOTSUP``) or the listing
    itself fails — callers decide how loud that should be.
    """
    if not xattrs_supported():
        return None
    names = os.listxattr(path, follow_symlinks=follow_symlinks)
    result = {}
    for name in names:
        if name == SELINUX_XATTR:
            continue
        try:
            result[name] = os.getxattr(path, name, follow_symlinks=follow_symlinks)
        except OSError:
            # Individual attribute disappeared between listxattr and getxattr,
            # or we lost read permission for it. Skip rather than abort the batch.
            continue
    return result


def encode_xattrs(xattrs):
    """Encode ``{name: bytes}`` as ``{name: base64-str}`` for JSON transport."""
    return {name: base64.b64encode(value).decode('ascii') for name, value in xattrs.items()}


def decode_xattrs(encoded):
    """Decode ``{name: base64-str}`` back into ``{name: bytes}``."""
    return {name: base64.b64decode(value) for name, value in encoded.items()}


def diff_xattrs(current, desired, *, exact):
    """Return ``(to_set, to_remove)`` describing how to make *current* match *desired*.

    ``to_set`` is a dict of attributes whose value differs (or is missing) and
    must be written. ``to_remove`` is a list of attributes present in *current*
    but not in *desired*; populated only when ``exact`` is true.
    """
    to_set = {name: value for name, value in desired.items() if current.get(name) != value}
    to_remove = []
    if exact:
        to_remove = [name for name in current if name not in desired]
    return to_set, to_remove


def apply_xattrs(path, desired, *, exact, follow_symlinks=True):
    """Make xattrs on *path* match *desired* (``{name: bytes}``).

    When ``exact`` is true, attributes on *path* that are not in *desired*
    (other than ``security.selinux``) are removed.

    Returns ``(changed, to_set, to_remove)``. Raises ``OSError`` on syscall
    failure — the caller decides whether to fail/warn/ignore.
    """
    current = read_xattrs(path, follow_symlinks=follow_symlinks) or {}
    to_set, to_remove = diff_xattrs(current, desired, exact=exact)
    changed = bool(to_set) or bool(to_remove)
    for name, value in to_set.items():
        os.setxattr(path, name, value, follow_symlinks=follow_symlinks)
    for name in to_remove:
        if name == SELINUX_XATTR:
            continue
        try:
            os.removexattr(path, name, follow_symlinks=follow_symlinks)
        except OSError:
            # Race with another writer, or attribute was already gone. Ignore.
            pass
    return changed, to_set, to_remove


def reconcile_desired(mode, source_xattrs, target_xattrs):
    """Compute the desired xattr set on the destination given the *mode*.

    *source_xattrs* and *target_xattrs* are each ``{name: bytes}`` (or ``None``
    when unavailable). Returns ``(desired_dict, exact)`` where *exact* tells
    :func:`apply_xattrs` whether to strip attributes not in *desired*.
    """
    if mode not in PRESERVE_MODES:
        raise ValueError("invalid preserve_xattrs mode: %r" % (mode,))
    src = source_xattrs or {}
    tgt = target_xattrs or {}
    if mode == 'no':
        return {}, True
    if mode == 'target':
        return dict(tgt), True
    if mode == 'source':
        return dict(src), True
    # merge: target's attrs + source's attrs, source wins on overlap.
    merged = dict(tgt)
    merged.update(src)
    return merged, True
