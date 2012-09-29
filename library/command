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

import subprocess
import sys
import datetime
import traceback
import shlex
import pipes
import os

DOCUMENTATION = '''
---
module: command
short_description: Executes a command on a remote node
description:
     - The command module takes the command name followed by a list of arguments, space delimited.
     - The given command will be executed on all selected nodes. It will not be
       processed through the shell, so variables like C($HOME) and operations
       like C("<"), C(">"), C("|"), and C("&") will not work. As such, all
       paths to commands must be fully qualified
options:
  free_form:
    description:
      - the command module takes a free form command to run
    required: true
    default: null
    aliases: []
  creates:
    description:
      - a filename, when it already exists, this step will B(not) be run.
    required: no
    default: null
  chdir:
    description:
      - cd into this directory before running the command
    version_added: "0.6"
    required: false
    default: null
examples:
   - code: command /sbin/shutdown -t now
     description: "Example from Ansible Playbooks"
   - code: command /usr/bin/make_database.sh arg1 arg2 creates=/path/to/database
     description: "I(creates) and I(chdir) can be specified after the command. For instance, if you only want to run a command if a certain file does not exist, use this."
notes:
    -  If you want to run a command through the shell (say you are using C(<),
       C(>), C(|), etc), you actually want the M(shell) module instead. The
       M(command) module is much more secure as it's not affected by the user's
       environment.
author: Michael DeHaan
'''

def main():

    # the command module is the one ansible module that does not take key=value args
    # hence don't copy this one if you are looking to build others!
    module = CommandModule(argument_spec=dict())

    shell = module.params['shell']
    chdir = module.params['chdir']
    args  = module.params['args']

    if args.strip() == '':
        module.fail_json(msg="no command given")

    if chdir:
        os.chdir(os.path.expanduser(chdir))

    if not shell:
        args = shlex.split(args)
    startd = datetime.datetime.now()

    try:
        cmd = subprocess.Popen(args, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = cmd.communicate()
    except (OSError, IOError), e:
        module.fail_json(cmd=args, msg=str(e))
    except:
        module.fail_json(msg=traceback.format_exc())

    endd = datetime.datetime.now()
    delta = endd - startd

    if out is None:
        out = ''
    if err is None:
        err = ''

    module.exit_json(
        cmd     = args,
        stdout  = out.strip(),
        stderr  = err.strip(),
        rc      = cmd.returncode,
        start   = str(startd),
        end     = str(endd),
        delta   = str(delta),
        changed = True
    )

# include magic from lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>

# only the command module should ever need to do this
# everything else should be simple key=value

class CommandModule(AnsibleModule):

    def _handle_aliases(self):
        pass

    def _check_invalid_arguments(self):
        pass

    def _load_params(self):
        ''' read the input and return a dictionary and the arguments string '''
        args = MODULE_ARGS
        items   = shlex.split(args)
        params = {}
        params['chdir'] = None
        params['shell'] = False
        if args.find("#USE_SHELL") != -1:
            args = args.replace("#USE_SHELL", "")
            params['shell'] = True

        check_args = shlex.split(args)
        l_args = []
        for x in check_args:
            if x.startswith("creates="):
                # do not run the command if the line contains creates=filename
                # and the filename already exists.  This allows idempotence
                # of command executions.
                (k,v) = x.split("=",1)
                if os.path.exists(v):
                    self.exit_json(
                        cmd=args,
                        stdout="skipped, since %s exists" % v,
                        skipped=True,
                        changed=False,
                        stderr=False,
                        rc=0
                    )
            elif x.startswith("removes="):
                # do not run the command if the line contains removes=filename
                # and the filename do not exists.  This allows idempotence
                # of command executions.
                (k,v) = x.split("=",1)
                if not os.path.exists(v):
                    self.exit_json(
                        cmd=args,
                        stdout="skipped, since %s do not exists" % v,
                        skipped=True,
                        changed=False,
                        stderr=False,
                        rc=0
                    )
            elif x.startswith("chdir="):
                (k,v) = x.split("=", 1)
                v = os.path.expanduser(v)
                if not (os.path.exists(v) and os.path.isdir(v)):
                    self.fail_json(msg="cannot change to directory '%s': path does not exist" % v)
                elif v[0] != '/':
                    self.fail_json(msg="the path for 'chdir' argument must be fully qualified")
                params['chdir'] = v
            else:
                l_args.append(x)
        params['args'] = " ".join([pipes.quote(x) for x in l_args])
        return (params, params['args'])

main()
