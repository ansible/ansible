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

import fcntl
import textwrap
import os
import random
import subprocess
import sys
import time
import locale
import logging
import getpass
import errno
from struct import unpack, pack
from termios import TIOCGWINSZ
from multiprocessing import Lock

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.utils.color import stringc
from ansible.utils.unicode import to_bytes, to_unicode

try:
    # Python 2
    input = raw_input
except NameError:
    # Python 3
    pass


# These are module level as we currently fork and serialize the whole process and locks in the objects don't play well with that
debug_lock = Lock()

logger = None
#TODO: make this a logging callback instead
if C.DEFAULT_LOG_PATH:
    path = C.DEFAULT_LOG_PATH
    if (os.path.exists(path) and os.access(path, os.W_OK)) or os.access(os.path.dirname(path), os.W_OK):
        logging.basicConfig(filename=path, level=logging.DEBUG, format='%(asctime)s %(name)s %(message)s')
        mypid = str(os.getpid())
        user = getpass.getuser()
        logger = logging.getLogger("p=%s u=%s | " % (mypid, user))
    else:
        print("[WARNING]: log file at %s is not writeable and we cannot create it, aborting\n" % path, file=sys.stderr)


class Display:

    def __init__(self, verbosity=0):

        self.columns = None
        self.verbosity = verbosity

        # list of all deprecation messages to prevent duplicate display
        self._deprecations = {}
        self._warns        = {}
        self._errors       = {}

        self.cowsay = None
        self.noncow = C.ANSIBLE_COW_SELECTION

        self.set_cowsay_info()

        if self.cowsay:
            try:
                cmd = subprocess.Popen([self.cowsay, "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                (out, err) = cmd.communicate()
                self.cows_available = list(set(C.ANSIBLE_COW_WHITELIST).intersection(out.split()))
            except:
                # could not execute cowsay for some reason
                self.cowsay = False

        self._set_column_width()

    def set_cowsay_info(self):

        if not C.ANSIBLE_NOCOWS:
            if os.path.exists("/usr/bin/cowsay"):
                self.cowsay = "/usr/bin/cowsay"
            elif os.path.exists("/usr/games/cowsay"):
                self.cowsay = "/usr/games/cowsay"
            elif os.path.exists("/usr/local/bin/cowsay"):
                # BSD path for cowsay
                self.cowsay = "/usr/local/bin/cowsay"
            elif os.path.exists("/opt/local/bin/cowsay"):
                # MacPorts path for cowsay
                self.cowsay = "/opt/local/bin/cowsay"

    def display(self, msg, color=None, stderr=False, screen_only=False, log_only=False):
        """ Display a message to the user

        Note: msg *must* be a unicode string to prevent UnicodeError tracebacks.
        """ 

        # FIXME: this needs to be implemented
        #msg = utils.sanitize_output(msg)
        nocolor = msg
        if color:
            msg = stringc(msg, color)

        if not log_only:
            if not msg.endswith(u'\n'):
                msg2 = msg + u'\n'
            else:
                msg2 = msg

            msg2 = to_bytes(msg2, encoding=self._output_encoding(stderr=stderr))
            if sys.version_info >= (3,):
                # Convert back to text string on python3
                # We first convert to a byte string so that we get rid of
                # characters that are invalid in the user's locale
                msg2 = to_unicode(msg2, self._output_encoding(stderr=stderr))

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
            msg2 = nocolor.lstrip(u'\n')

            msg2 = to_bytes(msg2)
            if sys.version_info >= (3,):
                # Convert back to text string on python3
                # We first convert to a byte string so that we get rid of
                # characters that are invalid in the user's locale
                msg2 = to_unicode(msg2, self._output_encoding(stderr=stderr))

            if color == C.COLOR_ERROR:
                logger.error(msg2)
            else:
                logger.info(msg2)

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

    def debug(self, msg):
        if C.DEFAULT_DEBUG:
            debug_lock.acquire()
            self.display("%6d %0.5f: %s" % (os.getpid(), time.time(), msg), color=C.COLOR_DEBUG)
            debug_lock.release()

    def verbose(self, msg, host=None, caplevel=2):
        # FIXME: this needs to be implemented
        #msg = utils.sanitize_output(msg)
        if self.verbosity > caplevel:
            if host is None:
                self.display(msg, color=C.COLOR_VERBOSE)
            else:
                self.display("<%s> %s" % (host, msg), color=C.COLOR_VERBOSE, screen_only=True)

    def deprecated(self, msg, version=None, removed=False):
        ''' used to print out a deprecation message.'''

        if not removed and not C.DEPRECATION_WARNINGS:
            return

        if not removed:
            if version:
                new_msg = "[DEPRECATION WARNING]: %s.\nThis feature will be removed in version %s." % (msg, version)
            else:
                new_msg = "[DEPRECATION WARNING]: %s.\nThis feature will be removed in a future release." % (msg)
            new_msg = new_msg + " Deprecation warnings can be disabled by setting deprecation_warnings=False in ansible.cfg.\n\n"
        else:
            raise AnsibleError("[DEPRECATED]: %s.\nPlease update your playbooks." % msg)

        wrapped = textwrap.wrap(new_msg, self.columns, replace_whitespace=False, drop_whitespace=False)
        new_msg = "\n".join(wrapped) + "\n"

        if new_msg not in self._deprecations:
            self.display(new_msg.strip(), color=C.COLOR_DEPRECATE, stderr=True)
            self._deprecations[new_msg] = 1

    def warning(self, msg, formatted=False):

        if not formatted:
            new_msg = "\n[WARNING]: %s" % msg
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

    def banner(self, msg, color=None):
        '''
        Prints a header-looking line with stars taking up to 80 columns
        of width (3 columns, minimum)
        '''
        if self.cowsay:
            try:
                self.banner_cowsay(msg)
                return
            except OSError:
                self.warning("somebody cleverly deleted cowsay or something during the PB run.  heh.")

        msg = msg.strip()
        star_len = (79 - len(msg))
        if star_len < 0:
            star_len = 3
        stars = "*" * star_len
        self.display("\n%s %s" % (msg, stars), color=color)

    def banner_cowsay(self, msg, color=None):
        if ": [" in msg:
            msg = msg.replace("[","")
            if msg.endswith("]"):
                msg = msg[:-1]
        runcmd = [self.cowsay,"-W", "60"]
        if self.noncow:
            thecow = self.noncow
            if thecow == 'random':
                thecow = random.choice(self.cows_available)
            runcmd.append('-f')
            runcmd.append(thecow)
        runcmd.append(msg)
        cmd = subprocess.Popen(runcmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out, err) = cmd.communicate()
        self.display("%s\n" % out, color=color)

    def error(self, msg, wrap_text=True):
        if wrap_text:
            new_msg = u"\n[ERROR]: %s" % msg
            wrapped = textwrap.wrap(new_msg, self.columns)
            new_msg = u"\n".join(wrapped) + u"\n"
        else:
            new_msg = u"ERROR! " + msg
        if new_msg not in self._errors:
            self.display(new_msg, color=C.COLOR_ERROR, stderr=True)
            self._errors[new_msg] = 1

    @staticmethod
    def prompt(msg, private=False):
        prompt_string = to_bytes(msg, encoding=Display._output_encoding())
        if sys.version_info >= (3,):
            # Convert back into text on python3.  We do this double conversion
            # to get rid of characters that are illegal in the user's locale
            prompt_string = to_unicode(prompt_string)

        if private:
            return getpass.getpass(msg)
        else:
            return input(prompt_string)

    def do_var_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None):

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
        result = to_unicode(result, errors='strict')
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
        if os.isatty(0):
            tty_size = unpack('HHHH', fcntl.ioctl(0, TIOCGWINSZ, pack('HHHH', 0, 0, 0, 0)))[1]
        else:
            tty_size = 0
        self.columns = max(79, tty_size)
