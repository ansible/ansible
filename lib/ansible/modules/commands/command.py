#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>, and others
# (c) 2016, Toshio Kuratomi <tkuratomi@ansible.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = '''
---
module: command
short_description: Executes a command on a remote node
version_added: historical
description:
     - The C(command) module takes the command name followed by a list of space-delimited arguments.
     - The given command will be executed on all selected nodes. It will not be
       processed through the shell, so variables like C($HOME) and operations
       like C("<"), C(">"), C("|"), C(";") and C("&") will not work (use the M(shell)
       module if you need these features).
     - For Windows targets, use the M(win_command) module instead.
options:
  free_form:
    description:
      - The command module takes a free form command to run.  There is no parameter actually named 'free form'.
        See the examples!
    required: yes
  creates:
    description:
      - A filename or (since 2.0) glob pattern, when it already exists, this step will B(not) be run.
  removes:
    description:
      - A filename or (since 2.0) glob pattern, when it does not exist, this step will B(not) be run.
    version_added: "0.8"
  chdir:
    description:
      - Change into this directory before running the command.
    version_added: "0.6"
  warn:
    description:
      - If command_warnings are on in ansible.cfg, do not warn about this particular line if set to C(no).
    type: bool
    default: 'yes'
    version_added: "1.8"
notes:
    -  If you want to run a command through the shell (say you are using C(<), C(>), C(|), etc), you actually want the M(shell) module instead.
       The C(command) module is much more secure as it's not affected by the user's environment.
    -  " C(creates), C(removes), and C(chdir) can be specified after the command.
       For instance, if you only want to run a command if a certain file does not exist, use this."
    -  The C(executable) parameter is removed since version 2.4. If you have a need for this parameter, use the M(shell) module instead.
    -  For Windows targets, use the M(win_command) module instead.
author:
    - Ansible Core Team
    - Michael DeHaan
'''

EXAMPLES = '''
- name: return motd to registered var
  command: cat /etc/motd
  register: mymotd

- name: Run the command if the specified file does not exist.
  command: /usr/bin/make_database.sh arg1 arg2 creates=/path/to/database

# You can also use the 'args' form to provide the options.
- name: This command will change the working directory to somedir/ and will only run when /path/to/database doesn't exist.
  command: /usr/bin/make_database.sh arg1 arg2
  args:
    chdir: somedir/
    creates: /path/to/database

- name: safely use templated variable to run command. Always use the quote filter to avoid injection issues.
  command: cat {{ myfile|quote }}
  register: myoutput
'''

import datetime
import glob
import os
import shlex

from ansible.module_utils.basic import AnsibleModule


def check_command(module, commandline):
    arguments = {'chown': 'owner', 'chmod': 'mode', 'chgrp': 'group',
                 'ln': 'state=link', 'mkdir': 'state=directory',
                 'rmdir': 'state=absent', 'rm': 'state=absent', 'touch': 'state=touch'}
    commands = {'hg': 'hg', 'curl': 'get_url or uri', 'wget': 'get_url or uri',
                'svn': 'subversion', 'service': 'service',
                'mount': 'mount', 'rpm': 'yum, dnf or zypper', 'yum': 'yum', 'apt-get': 'apt',
                'tar': 'unarchive', 'unzip': 'unarchive', 'sed': 'template or lineinfile',
                'dnf': 'dnf', 'zypper': 'zypper'}
    become = ['sudo', 'su', 'pbrun', 'pfexec', 'runas', 'pmrun']
    command = os.path.basename(commandline.split()[0])
    if command in arguments:
        module.warn("Consider using file module with %s rather than running %s" % (arguments[command], command))
    if command in commands:
        module.warn("Consider using %s module rather than running %s" % (commands[command], command))
    if command in become:
        module.warn("Consider using 'become', 'become_method', and 'become_user' rather than running %s" % (command,))


def main():

    # the command module is the one ansible module that does not take key=value args
    # hence don't copy this one if you are looking to build others!
    module = AnsibleModule(
        argument_spec=dict(
            _raw_params=dict(),
            _uses_shell=dict(type='bool', default=False),
            chdir=dict(type='path'),
            executable=dict(),
            creates=dict(type='path'),
            removes=dict(type='path'),
            warn=dict(type='bool', default=True),
        )
    )

    shell = module.params['_uses_shell']
    chdir = module.params['chdir']
    executable = module.params['executable']
    args = module.params['_raw_params']
    creates = module.params['creates']
    removes = module.params['removes']
    warn = module.params['warn']

    if not shell and executable:
        module.warn("As of Ansible 2.4, the parameter 'executable' is no longer supported with the 'command' module. Not using '%s'." % executable)
        executable = None

    if args.strip() == '':
        module.fail_json(rc=256, msg="no command given")

    if chdir:
        chdir = os.path.abspath(chdir)
        os.chdir(chdir)

    if creates:
        # do not run the command if the line contains creates=filename
        # and the filename already exists.  This allows idempotence
        # of command executions.
        if glob.glob(creates):
            module.exit_json(
                cmd=args,
                stdout="skipped, since %s exists" % creates,
                changed=False,
                rc=0
            )

    if removes:
        # do not run the command if the line contains removes=filename
        # and the filename does not exist.  This allows idempotence
        # of command executions.
        if not glob.glob(removes):
            module.exit_json(
                cmd=args,
                stdout="skipped, since %s does not exist" % removes,
                changed=False,
                rc=0
            )

    if warn:
        check_command(module, args)

    if not shell:
        args = shlex.split(args)
    startd = datetime.datetime.now()

    rc, out, err = module.run_command(args, executable=executable, use_unsafe_shell=shell, encoding=None)

    endd = datetime.datetime.now()
    delta = endd - startd

    if out is None:
        out = b''
    if err is None:
        err = b''

    result = dict(
        cmd=args,
        stdout=out.rstrip(b"\r\n"),
        stderr=err.rstrip(b"\r\n"),
        rc=rc,
        start=str(startd),
        end=str(endd),
        delta=str(delta),
        changed=True,
    )

    if rc != 0:
        module.fail_json(msg='non-zero return code', **result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
