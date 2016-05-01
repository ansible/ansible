#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>, and others
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

import copy
import sys
import datetime
import glob
import traceback
import re
import shlex
import os

DOCUMENTATION = '''
---
module: command
short_description: Executes a command on a remote node
version_added: historical
description:
     - The M(command) module takes the command name followed by a list of space-delimited arguments.
     - The given command will be executed on all selected nodes. It will not be
       processed through the shell, so variables like C($HOME) and operations
       like C("<"), C(">"), C("|"), and C("&") will not work (use the M(shell)
       module if you need these features).
options:
  free_form:
    description:
      - the command module takes a free form command to run.  There is no parameter actually named 'free form'.
        See the examples!
    required: true
    default: null
  creates:
    description:
      - a filename or (since 2.0) glob pattern, when it already exists, this step will B(not) be run.
    required: no
    default: null
  removes:
    description:
      - a filename or (since 2.0) glob pattern, when it does not exist, this step will B(not) be run.
    version_added: "0.8"
    required: no
    default: null
  chdir:
    description:
      - cd into this directory before running the command
    version_added: "0.6"
    required: false
    default: null
  executable:
    description:
      - change the shell used to execute the command. Should be an absolute path to the executable.
    required: false
    default: null
    version_added: "0.9"
  warn:
    version_added: "1.8"
    default: yes
    description:
      - if command warnings are on in ansible.cfg, do not warn about this particular line if set to no/false.
    required: false
notes:
    -  If you want to run a command through the shell (say you are using C(<),
       C(>), C(|), etc), you actually want the M(shell) module instead. The
       M(command) module is much more secure as it's not affected by the user's
       environment.
    -  " C(creates), C(removes), and C(chdir) can be specified after the command. For instance, if you only want to run a command if a certain file does not exist, use this."
author: 
    - Ansible Core Team
    - Michael DeHaan
'''

EXAMPLES = '''
# Example from Ansible Playbooks.
- command: /sbin/shutdown -t now

# Run the command if the specified file does not exist.
- command: /usr/bin/make_database.sh arg1 arg2 creates=/path/to/database

# You can also use the 'args' form to provide the options. This command
# will change the working directory to somedir/ and will only run when
# /path/to/database doesn't exist.
- command: /usr/bin/make_database.sh arg1 arg2
  args:
    chdir: somedir/
    creates: /path/to/database
'''

# Dict of options and their defaults
OPTIONS = {'chdir': None,
           'creates': None,
           'executable': None,
           'NO_LOG': None,
           'removes': None,
           'warn': True,
           }

# This is a pretty complex regex, which functions as follows:
#
# 1. (^|\s)
# ^ look for a space or the beginning of the line
# 2. ({options_list})=
# ^ expanded to (chdir|creates|executable...)=
#   look for a valid param, followed by an '='
# 3. (?P<quote>[\'"])?
# ^ look for an optional quote character, which can either be
#   a single or double quote character, and store it for later
# 4. (.*?)
# ^ match everything in a non-greedy manner until...
# 5. (?(quote)(?<!\\)(?P=quote))((?<!\\)(?=\s)|$)
# ^ a non-escaped space or a non-escaped quote of the same kind
#   that was matched in the first 'quote' is found, or the end of
#   the line is reached
OPTIONS_REGEX = '|'.join(OPTIONS.keys())
PARAM_REGEX = re.compile(
    r'(^|\s)(' + OPTIONS_REGEX +
    r')=(?P<quote>[\'"])?(.*?)(?(quote)(?<!\\)(?P=quote))((?<!\\)(?=\s)|$)'
)


def check_command(commandline):
    arguments = { 'chown': 'owner', 'chmod': 'mode', 'chgrp': 'group',
                  'ln': 'state=link', 'mkdir': 'state=directory',
                  'rmdir': 'state=absent', 'rm': 'state=absent', 'touch': 'state=touch' }
    commands  = { 'git': 'git', 'hg': 'hg', 'curl': 'get_url or uri', 'wget': 'get_url or uri',
                  'svn': 'subversion', 'service': 'service',
                  'mount': 'mount', 'rpm': 'yum, dnf or zypper', 'yum': 'yum', 'apt-get': 'apt',
                  'tar': 'unarchive', 'unzip': 'unarchive', 'sed': 'template or lineinfile',
                  'rsync': 'synchronize', 'dnf': 'dnf', 'zypper': 'zypper' }
    become   = [ 'sudo', 'su', 'pbrun', 'pfexec', 'runas' ]
    warnings = list()
    command = os.path.basename(commandline.split()[0])
    if command in arguments:
        warnings.append("Consider using file module with %s rather than running %s" % (arguments[command], command))
    if command in commands:
        warnings.append("Consider using %s module rather than running %s" % (commands[command], command))
    if command in become:
        warnings.append("Consider using 'become', 'become_method', and 'become_user' rather than running %s" % (command,))
    return warnings


def main():

    # the command module is the one ansible module that does not take key=value args
    # hence don't copy this one if you are looking to build others!
    module = AnsibleModule(
        argument_spec=dict(
          _raw_params = dict(),
          _uses_shell = dict(type='bool', default=False),
          chdir = dict(),
          executable = dict(),
          creates = dict(),
          removes = dict(),
          warn = dict(type='bool', default=True),
        )
    )

    shell = module.params['_uses_shell']
    chdir = module.params['chdir']
    executable = module.params['executable']
    args  = module.params['_raw_params']
    creates  = module.params['creates']
    removes  = module.params['removes']
    warn = module.params['warn']

    if args.strip() == '':
        module.fail_json(rc=256, msg="no command given")

    if chdir:
        chdir = os.path.abspath(os.path.expanduser(chdir))
        os.chdir(chdir)

    if creates:
        # do not run the command if the line contains creates=filename
        # and the filename already exists.  This allows idempotence
        # of command executions.
        v = os.path.expanduser(creates)
        if glob.glob(v):
            module.exit_json(
                cmd=args,
                stdout="skipped, since %s exists" % v,
                changed=False,
                stderr=False,
                rc=0
            )

    if removes:
    # do not run the command if the line contains removes=filename
    # and the filename does not exist.  This allows idempotence
    # of command executions.
        v = os.path.expanduser(removes)
        if not glob.glob(v):
            module.exit_json(
                cmd=args,
                stdout="skipped, since %s does not exist" % v,
                changed=False,
                stderr=False,
                rc=0
            )

    warnings = list()
    if warn:
        warnings = check_command(args)

    if not shell:
        args = shlex.split(args)
    startd = datetime.datetime.now()

    rc, out, err = module.run_command(args, executable=executable, use_unsafe_shell=shell)

    endd = datetime.datetime.now()
    delta = endd - startd

    if out is None:
        out = ''
    if err is None:
        err = ''

    module.exit_json(
        cmd      = args,
        stdout   = out.rstrip("\r\n"),
        stderr   = err.rstrip("\r\n"),
        rc       = rc,
        start    = str(startd),
        end      = str(endd),
        delta    = str(delta),
        changed  = True,
        warnings = warnings
    )

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.splitter import *

main()
