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
import os

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
        os.chdir(chdir)

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
                args = args.replace(x,'')
            elif x.startswith("chdir="):
                (k,v) = x.split("=", 1)
                if not (os.path.exists(v) and os.path.isdir(v)):
                    self.fail_json(msg="cannot change to directory '%s': path does not exist" % v)
                elif v[0] != '/':
                    self.fail_json(msg="the path for 'chdir' argument must be fully qualified")
                params['chdir'] = v
                args = args.replace(x, '')
        params['args'] = args
        return (params, args)

main()
