#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Matt Martz <matt@sivel.net>
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

import datetime

try:
    import pexpect
    HAS_PEXPECT = True
except ImportError:
    HAS_PEXPECT = False


DOCUMENTATION = '''
---
module: expect
version_added: 2.0
short_description: Executes a command and responds to prompts
description:
     - The M(expect) module executes a command and responds to prompts
     - The given command will be executed on all selected nodes. It will not be
       processed through the shell, so variables like C($HOME) and operations
       like C("<"), C(">"), C("|"), and C("&") will not work
options:
  command:
    description:
      - the command module takes command to run.
    required: true
  creates:
    description:
      - a filename, when it already exists, this step will B(not) be run.
    required: false
  removes:
    description:
      - a filename, when it does not exist, this step will B(not) be run.
    required: false
  chdir:
    description:
      - cd into this directory before running the command
    required: false
  responses:
    description:
      - Mapping of expected string and string to respond with
    required: true
  timeout:
    description:
      - Amount of time in seconds to wait for the expected strings
    default: 30
  echo:
    description:
      - Whether or not to echo out your response strings
    default: false
requirements:
  - python >= 2.6
  - pexpect >= 3.3
notes:
  - If you want to run a command through the shell (say you are using C(<),
    C(>), C(|), etc), you must specify a shell in the command such as
    C(/bin/bash -c "/path/to/something | grep else")
author: "Matt Martz (@sivel)"
'''

EXAMPLES = '''
- expect:
    command: passwd username
    responses:
      (?i)password: "MySekretPa$$word"
'''


def main():
    module = AnsibleModule(
        argument_spec=dict(
            command=dict(required=True),
            chdir=dict(),
            creates=dict(),
            removes=dict(),
            responses=dict(type='dict', required=True),
            timeout=dict(type='int', default=30),
            echo=dict(type='bool', default=False),
        )
    )

    if not HAS_PEXPECT:
        module.fail_json(msg='The pexpect python module is required')

    chdir = module.params['chdir']
    args = module.params['command']
    creates = module.params['creates']
    removes = module.params['removes']
    responses = module.params['responses']
    timeout = module.params['timeout']
    echo = module.params['echo']

    events = dict()
    for key, value in responses.iteritems():
        events[key.decode()] = u'%s\n' % value.rstrip('\n').decode()

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
        if os.path.exists(v):
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
        if not os.path.exists(v):
            module.exit_json(
                cmd=args,
                stdout="skipped, since %s does not exist" % v,
                changed=False,
                stderr=False,
                rc=0
            )

    startd = datetime.datetime.now()

    try:
        out, rc = pexpect.runu(args, timeout=timeout, withexitstatus=True,
                               events=events, cwd=chdir, echo=echo)
    except pexpect.ExceptionPexpect, e:
        module.fail_json(msg='%s' % e)

    endd = datetime.datetime.now()
    delta = endd - startd

    if out is None:
        out = ''

    module.exit_json(
        cmd=args,
        stdout=out.rstrip('\r\n'),
        rc=rc,
        start=str(startd),
        end=str(endd),
        delta=str(delta),
        changed=True,
    )

# import module snippets
from ansible.module_utils.basic import *

main()
