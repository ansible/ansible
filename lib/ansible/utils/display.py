# (c) 2014, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ctypes.util
import errno
import fcntl
import getpass
import locale
import logging
import os
import random
import subprocess
import sys
import textwrap
import time

from struct import unpack, pack
from termios import TIOCGWINSZ

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleAssertionError
from ansible.module_utils._text import to_bytes, to_text, to_native
from ansible.module_utils.six import with_metaclass, text_type
from ansible.utils.color import stringc
from ansible.utils.singleton import Singleton
from ansible.utils.unsafe_proxy import wrap_var

try:
    # Python 2
    input = raw_input
except NameError:
    # Python 3, we already have raw_input
    pass

_LIBC = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))
# Set argtypes, to avoid segfault if the wrong type is provided,
# restype is assumed to be c_int
_LIBC.wcwidth.argtypes = (ctypes.c_wchar,)
_LIBC.wcswidth.argtypes = (ctypes.c_wchar_p, ctypes.c_int)
# Max for c_int
_MAX_INT = 2 ** (ctypes.sizeof(ctypes.c_int) * 8 - 1) - 1

_LOCALE_INITIALIZED = False
_LOCALE_INITIALIZATION_ERR = None


def initialize_locale():
    """Set the locale to the users default setting
    and set ``_LOCALE_INITIALIZED`` to indicate whether
    ``get_text_width`` may run into trouble
    """
    global _LOCALE_INITIALIZED, _LOCALE_INITIALIZATION_ERR
    if _LOCALE_INITIALIZED is False:
        try:
            locale.setlocale(locale.LC_ALL, '')
        except locale.Error as e:
            _LOCALE_INITIALIZATION_ERR = e
        else:
            _LOCALE_INITIALIZED = True


def get_text_width(text):
    """Function that utilizes ``wcswidth`` or ``wcwidth`` to determine the
    number of columns used to display a text string.

    We try first with ``wcswidth``, and fallback to iterating each
    character and using wcwidth individually, falling back to a value of 0
    for non-printable wide characters

    On Py2, this depends on ``locale.setlocale(locale.LC_ALL, '')``,
    that in the case of Ansible is done in ``bin/ansible``
    """
    if not isinstance(text, text_type):
        raise TypeError('get_text_width requires text, not %s' % type(text))

    if _LOCALE_INITIALIZATION_ERR:
        Display().warning(
            'An error occurred while calling ansible.utils.display.initialize_locale '
            '(%s). This may result in incorrectly calculated text widths that can '
            'cause Display to print incorrect line lengths' % _LOCALE_INITIALIZATION_ERR
        )
    elif not _LOCALE_INITIALIZED:
        Display().warning(
            'ansible.utils.display.initialize_locale has not been called, '
            'this may result in incorrectly calculated text widths that can '
            'cause Display to print incorrect line lengths'
        )

    try:
        width = _LIBC.wcswidth(text, _MAX_INT)
    except ctypes.ArgumentError:
        width = -1
    if width != -1:
        return width

    width = 0
    counter = 0
    for c in text:
        counter += 1
        if c in (u'\x08', u'\x7f', u'\x94', u'\x1b'):
            # A few characters result in a subtraction of length:
            # BS, DEL, CCH, ESC
            # ESC is slightly different in that it's part of an escape sequence, and
            # while ESC is non printable, it's part of an escape sequence, which results
            # in a single non printable length
            width -= 1
            counter -= 1
            continue

        try:
            w = _LIBC.wcwidth(c)
        except ctypes.ArgumentError:
            w = -1
        if w == -1:
            # -1 signifies a non-printable character
            # use 0 here as a best effort
            w = 0
        width += w

    if width == 0 and counter and not _LOCALE_INITIALIZED:
        raise EnvironmentError(
            'ansible.utils.display.initialize_locale has not been called, '
            'and get_text_width could not calculate text width of %r' % text
        )

    # It doesn't make sense to have a negative printable width
    return width if width >= 0 else 0


class FilterBlackList(logging.Filter):
    def __init__(self, blacklist):
        self.blacklist = [logging.Filter(name) for name in blacklist]

    def filter(self, record):
        return not any(f.filter(record) for f in self.blacklist)


class FilterUserInjector(logging.Filter):
    """
    This is a filter which injects the current user as the 'user' attribute on each record. We need to add this filter
    to all logger handlers so that 3rd party libraries won't print an exception due to user not being defined.
    """

    try:
        username = getpass.getuser()
    except KeyError:
        # people like to make containers w/o actual valid passwd/shadow and use host uids
        username = 'uid=%s' % os.getuid()

    def filter(self, record):
        record.user = FilterUserInjector.username
        return True


logger = None
# TODO: make this a callback event instead
if getattr(C, 'DEFAULT_LOG_PATH'):
    path = C.DEFAULT_LOG_PATH
    if path and (os.path.exists(path) and os.access(path, os.W_OK)) or os.access(os.path.dirname(path), os.W_OK):
        # NOTE: level is kept at INFO to avoid security disclosures caused by certain libraries when using DEBUG
        logging.basicConfig(filename=path, level=logging.INFO,  # DO NOT set to logging.DEBUG
                            format='%(asctime)s p=%(process)d u=%(user)s n=%(name)s | %(message)s')

        logger = logging.getLogger('ansible')
        for handler in logging.root.handlers:
            handler.addFilter(FilterBlackList(getattr(C, 'DEFAULT_LOG_FILTER', [])))
            handler.addFilter(FilterUserInjector())
    else:
        print("[WARNING]: log file at %s is not writeable and we cannot create it, aborting\n" % path, file=sys.stderr)

# map color to log levels
color_to_log_level = {C.COLOR_ERROR: logging.ERROR,
                      C.COLOR_WARN: logging.WARNING,
                      C.COLOR_OK: logging.INFO,
                      C.COLOR_SKIP: logging.WARNING,
                      C.COLOR_UNREACHABLE: logging.ERROR,
                      C.COLOR_DEBUG: logging.DEBUG,
                      C.COLOR_CHANGED: logging.INFO,
                      C.COLOR_DEPRECATE: logging.WARNING,
                      C.COLOR_VERBOSE: logging.INFO}

b_COW_PATHS = (
    b"/usr/bin/cowsay",
    b"/usr/games/cowsay",
    b"/usr/local/bin/cowsay",  # BSD path for cowsay
    b"/opt/local/bin/cowsay",  # MacPorts path for cowsay
)


class Display(with_metaclass(Singleton, object)):

    def __init__(self, verbosity=0):

        self.columns = None
        self.verbosity = verbosity

        # list of all deprecation messages to prevent duplicate display
        self._deprecations = {}
        self._warns = {}
        self._errors = {}

        self.b_cowsay = None
        self.noncow = C.ANSIBLE_COW_SELECTION

        self.set_cowsay_info()

        if self.b_cowsay:
            try:
                cmd = subprocess.Popen([self.b_cowsay, "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                (out, err) = cmd.communicate()
                self.cows_available = set([to_text(c) for c in out.split()])
                if C.ANSIBLE_COW_ACCEPTLIST and any(C.ANSIBLE_COW_ACCEPTLIST):
                    self.cows_available = set(C.ANSIBLE_COW_ACCEPTLIST).intersection(self.cows_available)
            except Exception:
                # could not execute cowsay for some reason
                self.b_cowsay = False

        self._set_column_width()

    def set_cowsay_info(self):
        if C.ANSIBLE_NOCOWS:
            return

        if C.ANSIBLE_COW_PATH:
            self.b_cowsay = C.ANSIBLE_COW_PATH
        else:
            for b_cow_path in b_COW_PATHS:
                if os.path.exists(b_cow_path):
                    self.b_cowsay = b_cow_path

    def display(self, msg, color=None, stderr=False, screen_only=False, log_only=False, newline=True):
        """ Display a message to the user

        Note: msg *must* be a unicode string to prevent UnicodeError tracebacks.
        """

        nocolor = msg

        if not log_only:

            has_newline = msg.endswith(u'\n')
            if has_newline:
                msg2 = msg[:-1]
            else:
                msg2 = msg

            if color:
                msg2 = stringc(msg2, color)

            if has_newline or newline:
                msg2 = msg2 + u'\n'

            msg2 = to_bytes(msg2, encoding=self._output_encoding(stderr=stderr))
            if sys.version_info >= (3,):
                # Convert back to text string on python3
                # We first convert to a byte string so that we get rid of
                # characters that are invalid in the user's locale
                msg2 = to_text(msg2, self._output_encoding(stderr=stderr), errors='replace')

            # Note: After Display() class is refactored need to update the log capture
            # code in 'bin/ansible-connection' (and other relevant places).
            if not stderr:
                fileobj = sys.stdout
            else:
                fileobj = sys.stderr

            fileobj.write(msg2)

            try:
                fileobj.flush()
            except IOError as e:
                # Ignore EPIPE in case fileobj has been prematurely closed, eg.
                # when piping to "head -n1"
                if e.errno != errno.EPIPE:
                    raise

        if logger and not screen_only:
            # We first convert to a byte string so that we get rid of
            # color and characters that are invalid in the user's locale
            msg2 = to_bytes(nocolor.lstrip(u'\n'))

            if sys.version_info >= (3,):
                # Convert back to text string on python3
                msg2 = to_text(msg2, self._output_encoding(stderr=stderr))

            lvl = logging.INFO
            if color:
                # set logger level based on color (not great)
                try:
                    lvl = color_to_log_level[color]
                except KeyError:
                    # this should not happen, but JIC
                    raise AnsibleAssertionError('Invalid color supplied to display: %s' % color)
            # actually log
            logger.log(lvl, msg2)

    def v(self, msg, host=None):
        return self.verbose(msg, host=host, caplevel=0)

    def vv(self, msg, host=None):
        return self.verbose(msg, host=host, caplevel=1)

    def vvv(self, msg, host=None):
        return self.verbose(msg, host=host, caplevel=2)

    def vvvv(self, msg, host=None):
        return self.verbose(msg, host=host, caplevel=3)

    def vvvvv(self, msg, host=None):
        return self.verbose(msg, host=host, caplevel=4)

    def vvvvvv(self, msg, host=None):
        return self.verbose(msg, host=host, caplevel=5)

    def debug(self, msg, host=None):
        if C.DEFAULT_DEBUG:
            if host is None:
                self.display("%6d %0.5f: %s" % (os.getpid(), time.time(), msg), color=C.COLOR_DEBUG)
            else:
                self.display("%6d %0.5f [%s]: %s" % (os.getpid(), time.time(), host, msg), color=C.COLOR_DEBUG)

    def verbose(self, msg, host=None, caplevel=2):

        to_stderr = C.VERBOSE_TO_STDERR
        if self.verbosity > caplevel:
            if host is None:
                self.display(msg, color=C.COLOR_VERBOSE, stderr=to_stderr)
            else:
                self.display("<%s> %s" % (host, msg), color=C.COLOR_VERBOSE, stderr=to_stderr)

    def get_deprecation_message(self, msg, version=None, removed=False, date=None, collection_name=None):
        ''' used to print out a deprecation message.'''
        msg = msg.strip()
        if msg and msg[-1] not in ['!', '?', '.']:
            msg += '.'

        if collection_name == 'ansible.builtin':
            collection_name = 'ansible-core'

        if removed:
            header = '[DEPRECATED]: {0}'.format(msg)
            removal_fragment = 'This feature was removed'
            help_text = 'Please update your playbooks.'
        else:
            header = '[DEPRECATION WARNING]: {0}'.format(msg)
            removal_fragment = 'This feature will be removed'
            # FUTURE: make this a standalone warning so it only shows up once?
            help_text = 'Deprecation warnings can be disabled by setting deprecation_warnings=False in ansible.cfg.'

        if collection_name:
            from_fragment = 'from {0}'.format(collection_name)
        else:
            from_fragment = ''

        if date:
            when = 'in a release after {0}.'.format(date)
        elif version:
            when = 'in version {0}.'.format(version)
        else:
            when = 'in a future release.'

        message_text = ' '.join(f for f in [header, removal_fragment, from_fragment, when, help_text] if f)

        return message_text

    def deprecated(self, msg, version=None, removed=False, date=None, collection_name=None):
        if not removed and not C.DEPRECATION_WARNINGS:
            return

        message_text = self.get_deprecation_message(msg, version=version, removed=removed, date=date, collection_name=collection_name)

        if removed:
            raise AnsibleError(message_text)

        wrapped = textwrap.wrap(message_text, self.columns, drop_whitespace=False)
        message_text = "\n".join(wrapped) + "\n"

        if message_text not in self._deprecations:
            self.display(message_text.strip(), color=C.COLOR_DEPRECATE, stderr=True)
            self._deprecations[message_text] = 1

    def warning(self, msg, formatted=False):

        if not formatted:
            new_msg = "[WARNING]: %s" % msg
            wrapped = textwrap.wrap(new_msg, self.columns)
            new_msg = "\n".join(wrapped) + "\n"
        else:
            new_msg = "\n[WARNING]: \n%s" % msg

        if new_msg not in self._warns:
            self.display(new_msg, color=C.COLOR_WARN, stderr=True)
            self._warns[new_msg] = 1

    def system_warning(self, msg):
        if C.SYSTEM_WARNINGS:
            self.warning(msg)

    def banner(self, msg, color=None, cows=True):
        '''
        Prints a header-looking line with cowsay or stars with length depending on terminal width (3 minimum)
        '''
        msg = to_text(msg)

        if self.b_cowsay and cows:
            try:
                self.banner_cowsay(msg)
                return
            except OSError:
                self.warning("somebody cleverly deleted cowsay or something during the PB run.  heh.")

        msg = msg.strip()
        try:
            star_len = self.columns - get_text_width(msg)
        except EnvironmentError:
            star_len = self.columns - len(msg)
        if star_len <= 3:
            star_len = 3
        stars = u"*" * star_len
        self.display(u"\n%s %s" % (msg, stars), color=color)

    def banner_cowsay(self, msg, color=None):
        if u": [" in msg:
            msg = msg.replace(u"[", u"")
            if msg.endswith(u"]"):
                msg = msg[:-1]
        runcmd = [self.b_cowsay, b"-W", b"60"]
        if self.noncow:
            thecow = self.noncow
            if thecow == 'random':
                thecow = random.choice(list(self.cows_available))
            runcmd.append(b'-f')
            runcmd.append(to_bytes(thecow))
        runcmd.append(to_bytes(msg))
        cmd = subprocess.Popen(runcmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out, err) = cmd.communicate()
        self.display(u"%s\n" % to_text(out), color=color)

    def error(self, msg, wrap_text=True):
        if wrap_text:
            new_msg = u"\n[ERROR]: %s" % msg
            wrapped = textwrap.wrap(new_msg, self.columns)
            new_msg = u"\n".join(wrapped) + u"\n"
        else:
            new_msg = u"ERROR! %s" % msg
        if new_msg not in self._errors:
            self.display(new_msg, color=C.COLOR_ERROR, stderr=True)
            self._errors[new_msg] = 1

    @staticmethod
    def prompt(msg, private=False):
        prompt_string = to_bytes(msg, encoding=Display._output_encoding())
        if sys.version_info >= (3,):
            # Convert back into text on python3.  We do this double conversion
            # to get rid of characters that are illegal in the user's locale
            prompt_string = to_text(prompt_string)

        if private:
            return getpass.getpass(prompt_string)
        else:
            return input(prompt_string)

    def do_var_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None, unsafe=None):

        result = None
        if sys.__stdin__.isatty():

            do_prompt = self.prompt

            if prompt and default is not None:
                msg = "%s [%s]: " % (prompt, default)
            elif prompt:
                msg = "%s: " % prompt
            else:
                msg = 'input for %s: ' % varname

            if confirm:
                while True:
                    result = do_prompt(msg, private)
                    second = do_prompt("confirm " + msg, private)
                    if result == second:
                        break
                    self.display("***** VALUES ENTERED DO NOT MATCH ****")
            else:
                result = do_prompt(msg, private)
        else:
            result = None
            self.warning("Not prompting as we are not in interactive mode")

        # if result is false and default is not None
        if not result and default is not None:
            result = default

        if encrypt:
            # Circular import because encrypt needs a display class
            from ansible.utils.encrypt import do_encrypt
            result = do_encrypt(result, encrypt, salt_size, salt)

        # handle utf-8 chars
        result = to_text(result, errors='surrogate_or_strict')

        if unsafe:
            result = wrap_var(result)
        return result

    @staticmethod
    def _output_encoding(stderr=False):
        encoding = locale.getpreferredencoding()
        # https://bugs.python.org/issue6202
        # Python2 hardcodes an obsolete value on Mac.  Use MacOSX defaults
        # instead.
        if encoding in ('mac-roman',):
            encoding = 'utf-8'
        return encoding

    def _set_column_width(self):
        if os.isatty(1):
            tty_size = unpack('HHHH', fcntl.ioctl(1, TIOCGWINSZ, pack('HHHH', 0, 0, 0, 0)))[1]
        else:
            tty_size = 0
        self.columns = max(79, tty_size - 1)
