# Vendored copy of https://github.com/python/cpython/blob/3680ebed7f3e529d01996dd0318601f9f0d02b4b/Lib/pty.py
# PSF License (see licenses/PSF-license.txt or https://opensource.org/licenses/Python-2.0)
"""Pseudo terminal utilities."""

# Bugs: No signal handling.  Doesn't set child termios and window size.
#       Only tested on Linux, FreeBSD, and macOS.
# See:  W. Richard Stevens. 1992.  Advanced Programming in the
#       UNIX Environment.  Chapter 19.
# Author: Steen Lumholt -- with additions by Guido.
from __future__ import annotations

from select import select
import os
import sys
import tty

# names imported directly for test mocking purposes
from os import close, waitpid
from tty import setraw, tcgetattr, tcsetattr

__all__ = ["openpty", "fork", "spawn"]

STDIN_FILENO = 0
STDOUT_FILENO = 1
STDERR_FILENO = 2

CHILD = 0

def openpty():
    """openpty() -> (parent_fd, child_fd)
    Open a pty parent/child pair, using os.openpty() if possible."""

    try:
        return os.openpty()
    except (AttributeError, OSError):
        pass
    parent_fd, child_name = _open_terminal()
    child_fd = child_open(child_name)
    return parent_fd, child_fd

def master_open():
    """master_open() -> (parent_fd, child_name)
    Open a pty parent and return the fd, and the filename of the child end.
    Deprecated, use openpty() instead."""

    try:
        parent_fd, child_fd = os.openpty()
    except (AttributeError, OSError):
        pass
    else:
        child_name = os.ttyname(child_fd)
        os.close(child_fd)
        return parent_fd, child_name

    return _open_terminal()

def _open_terminal():
    """Open pty parent and return (parent_fd, tty_name)."""
    for x in 'pqrstuvwxyzPQRST':
        for y in '0123456789abcdef':
            pty_name = '/dev/pty' + x + y
            try:
                fd = os.open(pty_name, os.O_RDWR)
            except OSError:
                continue
            return (fd, '/dev/tty' + x + y)
    raise OSError('out of pty devices')

def child_open(tty_name):
    """child_open(tty_name) -> child_fd
    Open the pty child and acquire the controlling terminal, returning
    opened filedescriptor.
    Deprecated, use openpty() instead."""

    result = os.open(tty_name, os.O_RDWR)
    try:
        from fcntl import ioctl, I_PUSH
    except ImportError:
        return result
    try:
        ioctl(result, I_PUSH, "ptem")
        ioctl(result, I_PUSH, "ldterm")
    except OSError:
        pass
    return result

def fork():
    """fork() -> (pid, parent_fd)
    Fork and make the child a session leader with a controlling terminal."""

    try:
        pid, fd = os.forkpty()
    except (AttributeError, OSError):
        pass
    else:
        if pid == CHILD:
            try:
                os.setsid()
            except OSError:
                # os.forkpty() already set us session leader
                pass
        return pid, fd

    parent_fd, child_fd = openpty()
    pid = os.fork()
    if pid == CHILD:
        # Establish a new session.
        os.setsid()
        os.close(parent_fd)

        # Child fd becomes stdin/stdout/stderr of child.
        os.dup2(child_fd, STDIN_FILENO)
        os.dup2(child_fd, STDOUT_FILENO)
        os.dup2(child_fd, STDERR_FILENO)
        if child_fd > STDERR_FILENO:
            os.close(child_fd)

        # Explicitly open the tty to make it become a controlling tty.
        tmp_fd = os.open(os.ttyname(STDOUT_FILENO), os.O_RDWR)
        os.close(tmp_fd)
    else:
        os.close(child_fd)

    # Parent and child process.
    return pid, parent_fd

def _writen(fd, data):
    """Write all the data to a descriptor."""
    while data:
        n = os.write(fd, data)
        data = data[n:]

def _read(fd):
    """Default read function."""
    return os.read(fd, 1024)

def _copy(parent_fd, parent_read=_read, stdin_read=_read):
    """Parent copy loop.
    Copies
            pty parent -> standard output   (parent_read)
            standard input -> pty parent    (stdin_read)"""
    fds = [parent_fd, STDIN_FILENO]
    while fds:
        rfds, _wfds, _xfds = select(fds, [], [])

        if parent_fd in rfds:
            # Some OSes signal EOF by returning an empty byte string,
            # some throw OSErrors.
            try:
                data = parent_read(parent_fd)
            except OSError:
                data = b""
            if not data:  # Reached EOF.
                return    # Assume the child process has exited and is
                          # unreachable, so we clean up.
            else:
                os.write(STDOUT_FILENO, data)

        if STDIN_FILENO in rfds:
            data = stdin_read(STDIN_FILENO)
            if not data:
                fds.remove(STDIN_FILENO)
            else:
                _writen(parent_fd, data)

def spawn(argv, parent_read=_read, stdin_read=_read):
    """Create a spawned process."""
    if isinstance(argv, str):
        argv = (argv,)
    sys.audit('pty.spawn', argv)

    pid, parent_fd = fork()
    if pid == CHILD:
        os.execlp(argv[0], *argv)

    try:
        mode = tcgetattr(STDIN_FILENO)
        setraw(STDIN_FILENO)
        restore = True
    except tty.error:    # This is the same as termios.error
        restore = False

    try:
        _copy(parent_fd, parent_read, stdin_read)
    finally:
        if restore:
            tcsetattr(STDIN_FILENO, tty.TCSAFLUSH, mode)

    close(parent_fd)
    return waitpid(pid, 0)[1]
