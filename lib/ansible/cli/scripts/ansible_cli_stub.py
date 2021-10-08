# -*- coding: utf-8 -*-
# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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


import errno
import os
import shutil
import sys
import traceback

# Used for determining if the system is running a new enough python version
# and should only restrict on our documented minimum versions
_PY38_MIN = sys.version_info[:2] >= (3, 8)
if not _PY38_MIN:
    raise SystemExit(
        'ERROR: Ansible requires Python 3.8 or newer on the controller. '
        'Current version: %s' % ''.join(sys.version.splitlines())
    )


# These lines appear after the PY38 check, to ensure the "friendly" error happens before
# any invalid syntax appears in other files that may get imported
from ansible import context
from ansible.errors import AnsibleError, AnsibleOptionsError, AnsibleParserError
from ansible.module_utils._text import to_text

from pathlib import Path


class LastResort(object):
    # OUTPUT OF LAST RESORT
    def display(self, msg, log_only=None):
        print(msg, file=sys.stderr)

    def error(self, msg, wrap_text=None):
        print(msg, file=sys.stderr)


def cli_executor(cls):
    display = LastResort()

    try:  # bad ANSIBLE_CONFIG or config options can force ugly stacktrace
        import ansible.constants as C
        from ansible.utils.display import Display, initialize_locale
    except AnsibleOptionsError as e:
        display.error(to_text(e), wrap_text=False)
        sys.exit(5)

    initialize_locale()

    try:
        display = Display()
        display.debug("starting run")

        ansible_dir = Path("~/.ansible").expanduser()
        try:
            ansible_dir.mkdir(mode=0o700)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                display.warning(
                    "Failed to create the directory '%s': %s" % (ansible_dir, to_text(exc, errors='surrogate_or_replace'))
                )
        else:
            display.debug("Created the '%s' directory" % ansible_dir)

        try:
            args = [to_text(a, errors='surrogate_or_strict') for a in sys.argv]
        except UnicodeError:
            display.error('Command line args are not in utf-8, unable to continue.  Ansible currently only understands utf-8')
            display.display(u"The full traceback was:\n\n%s" % to_text(traceback.format_exc()))
            exit_code = 6
        else:
            cli = cls(args)
            exit_code = cli.run()

    except AnsibleOptionsError as e:
        cli.parser.print_help()
        display.error(to_text(e), wrap_text=False)
        exit_code = 5
    except AnsibleParserError as e:
        display.error(to_text(e), wrap_text=False)
        exit_code = 4
# TQM takes care of these, but leaving comment to reserve the exit codes
#    except AnsibleHostUnreachable as e:
#        display.error(str(e))
#        exit_code = 3
#    except AnsibleHostFailed as e:
#        display.error(str(e))
#        exit_code = 2
    except AnsibleError as e:
        display.error(to_text(e), wrap_text=False)
        exit_code = 1
    except KeyboardInterrupt:
        display.error("User interrupted execution")
        exit_code = 99
    except Exception as e:
        if C.DEFAULT_DEBUG:
            # Show raw stacktraces in debug mode, It also allow pdb to
            # enter post mortem mode.
            raise
        have_cli_options = bool(context.CLIARGS)
        display.error("Unexpected Exception, this is probably a bug: %s" % to_text(e), wrap_text=False)
        if not have_cli_options or have_cli_options and context.CLIARGS['verbosity'] > 2:
            log_only = False
            if hasattr(e, 'orig_exc'):
                display.vvv('\nexception type: %s' % to_text(type(e.orig_exc)))
                why = to_text(e.orig_exc)
                if to_text(e) != why:
                    display.vvv('\noriginal msg: %s' % why)
        else:
            display.display("to see the full traceback, use -vvv")
            log_only = True
        display.display(u"the full traceback was:\n\n%s" % to_text(traceback.format_exc()), log_only=log_only)
        exit_code = 250

    sys.exit(exit_code)
