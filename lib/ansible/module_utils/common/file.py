# Copyright (c) 2018, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import errno
import os
import re
import shutil
import stat
import sys
import tempfile

import typing as t

from pathlib import Path

try:
    import selinux
    HAVE_SELINUX = True
except ImportError:
    HAVE_SELINUX = False

from ansible.module_utils.common.text.converters import to_bytes, to_text

if t.TYPE_CHECKING:
    Path_type = t.Union[bytes, str, os.PathLike]
    SEEntry = t.Union[str, None]
    SEContext = t.Union[t.List[SEEntry], None]

DEFAULT_SELINUX_CONTEXT: SEContext = [None, None, None]

FILE_ATTRIBUTES = {
    'A': 'noatime',
    'a': 'append',
    'c': 'compressed',
    'C': 'nocow',
    'd': 'nodump',
    'D': 'dirsync',
    'e': 'extents',
    'E': 'encrypted',
    'h': 'blocksize',
    'i': 'immutable',
    'I': 'indexed',
    'j': 'journalled',
    'N': 'inline',
    's': 'zero',
    'S': 'synchronous',
    't': 'notail',
    'T': 'blockroot',
    'u': 'undelete',
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


def unfrackpath(path: Path_type, follow: bool = True, basedir: Path_type | None = None) -> str:
    '''
    Returns a path that is free of symlinks (if follow=True), environment variables, relative path traversals and symbols (~)

    :arg path: A byte or text string representing a path to be canonicalized
    :arg follow: A boolean to indicate of symlinks should be resolved or not
    :arg basedir: A byte string, text string, PathLike object, or `None`
        representing where a relative path should be resolved from.
        `None` will be substituted for the current working directory.
    :raises UnicodeDecodeError: If the canonicalized version of the path
        contains non-utf8 byte sequences.
    :rtype: A text string (unicode on pyyhon2, str on python3).
    :returns: An absolute path with symlinks, environment variables, and tilde
        expanded.  Note that this does not check whether a path exists.

    example::
        '$HOME/../../var/mail' becomes '/var/spool/mail'
    '''

    if basedir is None:
        basedir = Path.cwd()
    else:
        basedir = Path(to_text(basedir, errors='surrogate_or_strict'))
        if basedir.is_file():
            basedir = basedir.parent

    final_path = Path(os.path.expandvars(to_text(path, errors='surrogate_or_strict'))).expanduser()

    if not final_path.is_absolute():
        final_path = basedir / final_path

    if follow and final_path.is_symlink():
        # TODO: move to Path.readlink() once python 3.8 is history
        final_path = os.readlink(to_text(final_path, errors='surrogate_or_strict'))

    return os.path.normpath(to_text(final_path, errors='surrogate_or_strict'))


def is_executable(path: Path_type) -> bool:
    # This function's signature needs to be repeated
    # as the first line of its docstring.
    # This method is reused by the basic module,
    # the repetition helps the basic module's html documentation come out right.
    # http://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#confval-autodoc_docstring_signature
    '''is_executable(path)

    is the given path executable?

    :arg path: The path of the file to check.

    Limitations:

    * Does not account for FSACLs.
    * Most times we really want to know "Can the current user execute this
      file".  This function does not tell us that, only if any execute bit is set.
    '''
    # These are all bitfields so first bitwise-or all the permissions we're
    # looking for, then bitwise-and with the file's mode to determine if any
    # execute bits are set.
    return bool((stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) & os.stat(path)[stat.ST_MODE])


def format_attributes(attributes: list) -> list:
    attribute_list = [FILE_ATTRIBUTES.get(attr) for attr in attributes if attr in FILE_ATTRIBUTES]
    return attribute_list


def get_flags_from_attributes(attributes: list) -> str:
    flags = [key for key, attr in FILE_ATTRIBUTES.items() if attr in attributes]
    return ''.join(flags)


def get_file_arg_spec() -> dict:
    return dict(
        mode=dict(type='raw'),
        owner=dict(),
        group=dict(),
        seuser=dict(),
        serole=dict(),
        selevel=dict(),
        setype=dict(),
        attributes=dict(aliases=['attr']),
    )


def find_mount_point(path: Path_type) -> str:
    '''
        Takes a path and returns its mount point

    :param path: a string type with a filesystem path
    :returns: the path to the mount point as a text type
    '''
    b_path = to_bytes(unfrackpath(path, follow=True), errors='surrogate_or_strict')
    while not os.path.ismount(b_path):
        b_path = os.path.dirname(b_path)

    return to_text(b_path, errors='surrogate_or_strict')


def write_unsafely(src: Path_type, dest: Path_type):
    '''
        sadly there are some situations where we cannot ensure atomicity, but only if
        the user insists and we get the appropriate error we update the file unsafely
    '''
    try:
        with open(dest, 'wb') as out_dest, open(src, 'rb') as in_src:
            shutil.copyfileobj(in_src, out_dest)
    except (shutil.Error, OSError, IOError) as e:
        raise OSError(f'Could not write data to file ({dest!r}) from ({src!r}): {e!r}')


def atomic_move(src: Path_type, dest: Path_type, unsafe_writes: bool = False, keep_dest_attrs: bool = True, special_fs: list[str] | None = None):
    '''atomically move src to dest, copying attributes from dest, returns true on success
    it uses os.rename to ensure this as it is an atomic operation, rest of the function is
    to work around limitations, corner cases and ensure selinux context is saved if possible'''
    context = None
    dest_stat = None
    b_src = to_bytes(src, errors='surrogate_or_strict')
    b_dest = to_bytes(dest, errors='surrogate_or_strict')
    if os.path.exists(b_dest) and keep_dest_attrs:
        try:
            dest_stat = os.stat(b_dest)
            os.chown(b_src, dest_stat.st_uid, dest_stat.st_gid)
            shutil.copystat(b_dest, b_src)
        except OSError as e:
            if e.errno != errno.EPERM:
                raise
        if is_selinux_enabled():
            context = get_path_selinux_context(dest)
    else:
        if is_selinux_enabled():
            context = get_path_default_selinux_context(dest)

    creating = not os.path.exists(b_dest)

    try:
        # Optimistically try a rename, solves some corner cases and can avoid useless work, throws exception if not atomic.
        os.rename(b_src, b_dest)
    except (IOError, OSError) as e:
        if e.errno not in [errno.EPERM, errno.EXDEV, errno.EACCES, errno.ETXTBSY, errno.EBUSY]:
            # only try workarounds for errno 18 (cross device), 1 (not permitted),  13 (permission denied)
            # and 26 (text file busy) which happens on vagrant synced folders and other 'exotic' non posix file systems
            raise OSError(f'Could not replace file "{src!r}" to "{dest!r}": {e!r}')
        else:
            # Use bytes here.  In the shippable CI, this fails with
            # a UnicodeError with surrogateescape'd strings for an unknown
            # reason (doesn't happen in a local Ubuntu16.04 VM)
            b_dest_dir = os.path.dirname(b_dest)
            b_suffix = os.path.basename(b_dest)
            error_msg = None
            tmp_dest_name = None
            try:
                tmp_dest_fd, tmp_dest_name = tempfile.mkstemp(prefix=b'.ansible_tmp', dir=b_dest_dir, suffix=b_suffix)
            except (OSError, IOError) as e:
                error_msg = 'The destination directory (%r) is not writable by the current user. Error was: %r' % (os.path.dirname(dest), e)
            finally:
                if error_msg:
                    if unsafe_writes:
                        write_unsafely(b_src, b_dest)
                    else:
                        raise OSError(error_msg)

            if tmp_dest_name:
                b_tmp_dest_name = to_bytes(tmp_dest_name, errors='surrogate_or_strict')

                try:
                    try:
                        # close tmp file handle before file operations to prevent text file busy errors on vboxfs synced folders (windows host)
                        os.close(tmp_dest_fd)
                        # leaves tmp file behind when sudo and not root
                        try:
                            shutil.move(b_src, b_tmp_dest_name, copy_function=shutil.copy if keep_dest_attrs else shutil.copy2)
                        except OSError:
                            # cleanup will happen by 'rm' of tmpdir
                            # copy2 will preserve some metadata
                            if keep_dest_attrs:
                                shutil.copy(b_src, b_tmp_dest_name)
                            else:
                                shutil.copy2(b_src, b_tmp_dest_name)

                        if is_selinux_enabled():
                            set_selinux_context(b_tmp_dest_name, context, special_fs, False)
                        try:
                            tmp_stat = os.stat(b_tmp_dest_name)
                            if keep_dest_attrs and dest_stat and (tmp_stat.st_uid != dest_stat.st_uid or tmp_stat.st_gid != dest_stat.st_gid):
                                os.chown(b_tmp_dest_name, dest_stat.st_uid, dest_stat.st_gid)
                        except OSError as e:
                            if e.errno != errno.EPERM:
                                raise
                        try:
                            os.rename(b_tmp_dest_name, b_dest)
                        except (shutil.Error, OSError, IOError) as e:
                            if unsafe_writes and e.errno == errno.EBUSY:
                                write_unsafely(b_tmp_dest_name, b_dest)
                            else:
                                raise OSError('Unable to make %r into to %r, failed final rename from %r: %r' %
                                              (src, dest, b_tmp_dest_name, e))
                    except (shutil.Error, OSError, IOError) as e:
                        if unsafe_writes:
                            write_unsafely(b_src, b_dest)
                        else:
                            raise OSError('Failed to replace file "%r" to "%r": %r' % (src, dest, e))
                finally:
                    if os.path.exists(b_tmp_dest_name):
                        try:
                            os.unlink(b_tmp_dest_name)
                        except OSError as e:
                            sys.stderr.write(f"Could not cleanup '{b_tmp_dest_name!r}': {e!r}")
    if creating:
        # make sure the file has the correct permissions
        # based on the current value of umask
        umask = os.umask(0)
        os.umask(umask)
        os.chmod(b_dest, S_IRWU_RWG_RWO & ~umask)
        try:
            os.chown(b_dest, os.geteuid(), os.getegid())
        except OSError:
            # We're okay with trying our best here.  If the user is not
            # root (or old Unices) they won't be able to chown.
            pass

    if is_selinux_enabled():
        # rename might not preserve context
        set_selinux_context(dest, context, special_fs, False)


# SELINUX ############
def is_selinux_enabled() -> bool:
    return bool(HAVE_SELINUX and selinux.is_selinux_enabled() == 1)


def is_selinux_mls_enabled() -> bool:
    return bool(HAVE_SELINUX and selinux.is_selinux_mls_enabled() == 1)


if is_selinux_mls_enabled():
    # mls adds security level/4th field
    if DEFAULT_SELINUX_CONTEXT is not None:  # typechecking
        DEFAULT_SELINUX_CONTEXT.append(None)


def is_special_selinux_path(path: Path_type, special_fs: t.Union[list[str], None] = None) -> tuple[bool, SEContext]:
    """
    Returns a tuple containing (True, selinux_context) if the given path is on a
    NFS or other 'special' fs  mount point, otherwise the return will be (False, None).
    """
    is_special = False
    special_context = DEFAULT_SELINUX_CONTEXT
    if special_fs is None:
        special_fs = []

    try:
        with open('/proc/mounts', 'r') as f:
            mount_data = f.readlines()

        path_mount_point = Path(find_mount_point(path))

        for line in mount_data:
            if is_special:
                break
            (device, mount_point, fstype, options, rest) = line.split(' ', 4)
            if path_mount_point.samefile(mount_point):
                for fs in special_fs:
                    if fs in fstype:
                        special_context = get_path_selinux_context(path_mount_point)
                        is_special = True
                        break
    except (OSError, IOError):
        # can ignore fs errors, will just not flag as special
        pass

    return (is_special, special_context)


def _seresult_to_context(ret: list[t.Any]) -> SEContext:
    context = DEFAULT_SELINUX_CONTEXT
    if ret[0] != -1:
        # Limit split to 4 because the selevel, the last in the list,
        # may contain ':' characters
        context = ret[1].split(':', 3)
    return context


def get_path_default_selinux_context(path: Path_type, mode: int = 0) -> SEContext:

    context = DEFAULT_SELINUX_CONTEXT
    if is_selinux_enabled():
        context = _seresult_to_context(selinux.matchpathcon(to_text(path, errors='surrogate_or_strict'), mode))
    return context


def get_path_selinux_context(path: Path_type) -> SEContext:

    context = DEFAULT_SELINUX_CONTEXT
    try:
        context = _seresult_to_context(selinux.lgetfilecon_raw(to_text(path, errors='surrogate_or_strict')))
    except OSError as e:
        if e.errno == errno.ENOENT:
            msg = f'path ({path!r}) does not exist'
        else:
            msg = f'failed to retrieve selinux context for "{path!r}"'
        raise OSError(msg)

    return context


def set_selinux_context(path: Path_type, context: SEContext, special_fs: list[str] | None = None, simulate: bool = False) -> tuple[SEContext, SEContext]:

    cur_context = get_path_selinux_context(path)
    new_context = DEFAULT_SELINUX_CONTEXT

    if is_selinux_enabled():
        new_context = cur_context
        # Iterate over the current context instead of the
        # argument context, which may have selevel.
        (is_special_se, sp_context) = is_special_selinux_path(path, special_fs)
        if is_special_se:
            new_context = sp_context
        elif None not in (context, cur_context, new_context):
            for i in range(len(cur_context)):  # type: ignore
                if len(context) > i:  # type: ignore
                    if context[i] is not None and context[i] != cur_context[i]:  # type: ignore
                        new_context[i] = context[i]  # type: ignore
                    elif context[i] is None:  # type: ignore
                        new_context[i] = cur_context[i]  # type: ignore

        if cur_context != new_context and not simulate:
            rc = selinux.lsetfilecon(str(path), ':'.join([x or '' for x in new_context]))  # type: ignore
            if rc != 0:
                raise OSError('Settting selinux context to "{new_context!r}" failed')

    return cur_context, new_context
