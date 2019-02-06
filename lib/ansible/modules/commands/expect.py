#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: expect
version_added: '2.0'
short_description: Executes a command and responds to prompts.
description:
     - The C(expect) module executes a command and responds to prompts.
     - The given command will be executed on all selected nodes. It will not be
       processed through the shell, so variables like C($HOME) and operations
       like C("<"), C(">"), C("|"), and C("&") will not work.
options:
  command:
    description:
      - The command module takes command to run.
    required: true
  creates:
    description:
      - A filename, when it already exists, this step will B(not) be run.
  removes:
    description:
      - A filename, when it does not exist, this step will B(not) be run.
  chdir:
    description:
      - Change into this directory before running the command.
  responses:
    description:
      - Mapping of expected string/regex and string to respond with. If the
        response is a list, successive matches return successive
        responses. List functionality is new in 2.1.
    required: true
  timeout:
    description:
      - Amount of time in seconds to wait for the expected strings. Use
        C(null) to disable timeout.
    default: 30
  echo:
    description:
      - Whether or not to echo out your response strings.
    default: false
    type: bool
requirements:
  - python >= 2.6
  - pexpect >= 3.3
notes:
  - If you want to run a command through the shell (say you are using C(<),
    C(>), C(|), etc), you must specify a shell in the command such as
    C(/bin/bash -c "/path/to/something | grep else").
  - The question, or key, under I(responses) is a python regex match. Case
    insensitive searches are indicated with a prefix of C(?i).
  - By default, if a question is encountered multiple times, its string
    response will be repeated. If you need different responses for successive
    question matches, instead of a string response, use a list of strings as
    the response. The list functionality is new in 2.1.
  - The M(expect) module is designed for simple scenarios. For more complex
    needs, consider the use of expect code with the M(shell) or M(script)
    modules. (An example is part of the M(shell) module documentation)
seealso:
- module: script
- module: shell
author: "Matt Martz (@sivel)"
'''

EXAMPLES = r'''
- name: Case insensitive password string match
  expect:
    command: passwd username
    responses:
      (?i)password: "MySekretPa$$word"
  # you don't want to show passwords in your logs
  no_log: true

- name: Generic question with multiple different responses
  expect:
    command: /path/to/custom/command
    responses:
      Question:
        - response1
        - response2
        - response3
'''

import datetime
import os
import traceback

PEXPECT_IMP_ERR = None
try:
    import pexpect
    HAS_PEXPECT = True
except ImportError:
    PEXPECT_IMP_ERR = traceback.format_exc()
    HAS_PEXPECT = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native, to_text


def response_closure(module, question, responses):
    resp_gen = (u'%s\n' % to_text(r).rstrip(u'\n') for r in responses)

    def wrapped(info):
        try:
            return next(resp_gen)
        except StopIteration:
            module.fail_json(msg="No remaining responses for '%s', "
                                 "output was '%s'" %
                                 (question,
                                  info['child_result_list'][-1]))

    return wrapped


def main():
    module = AnsibleModule(
        argument_spec=dict(
            command=dict(required=True),
            chdir=dict(type='path'),
            creates=dict(type='path'),
            removes=dict(type='path'),
            responses=dict(type='dict', required=True),
            timeout=dict(type='int', default=30),
            echo=dict(type='bool', default=False),
        )
    )

    if not HAS_PEXPECT:
        module.fail_json(msg=missing_required_lib("pexpect"),
                         exception=PEXPECT_IMP_ERR)

    chdir = module.params['chdir']
    args = module.params['command']
    creates = module.params['creates']
    removes = module.params['removes']
    responses = module.params['responses']
    timeout = module.params['timeout']
    echo = module.params['echo']

    events = dict()
    for key, value in responses.items():
        if isinstance(value, list):
            response = response_closure(module, key, value)
        else:
            response = u'%s\n' % to_text(value).rstrip(u'\n')

        events[to_text(key)] = response

    if args.strip() == '':
        module.fail_json(rc=256, msg="no command given")

    if chdir:
        chdir = os.path.abspath(chdir)
        os.chdir(chdir)

    if creates:
        # do not run the command if the line contains creates=filename
        # and the filename already exists.  This allows idempotence
        # of command executions.
        if os.path.exists(creates):
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
        if not os.path.exists(removes):
            module.exit_json(
                cmd=args,
                stdout="skipped, since %s does not exist" % removes,
                changed=False,
                rc=0
            )

    startd = datetime.datetime.now()

    try:
        try:
            # Prefer pexpect.run from pexpect>=4
            out, rc = pexpect.run(args, timeout=timeout, withexitstatus=True,
                                  events=events, cwd=chdir, echo=echo,
                                  encoding='utf-8')
        except TypeError:
            # Use pexpect.runu in pexpect>=3.3,<4
            out, rc = pexpect.runu(args, timeout=timeout, withexitstatus=True,
                                   events=events, cwd=chdir, echo=echo)
    except (TypeError, AttributeError) as e:
        # This should catch all insufficient versions of pexpect
        # We deem them insufficient for their lack of ability to specify
        # to not echo responses via the run/runu functions, which would
        # potentially leak sensentive information
        module.fail_json(msg='Insufficient version of pexpect installed '
                             '(%s), this module requires pexpect>=3.3. '
                             'Error was %s' % (pexpect.__version__, to_native(e)))
    except pexpect.ExceptionPexpect as e:
        module.fail_json(msg='%s' % to_native(e), exception=traceback.format_exc())

    endd = datetime.datetime.now()
    delta = endd - startd

    if out is None:
        out = ''

    result = dict(
        cmd=args,
        stdout=out.rstrip('\r\n'),
        rc=rc,
        start=str(startd),
        end=str(endd),
        delta=str(delta),
        changed=True,
    )

    if rc is None:
        module.fail_json(msg='command exceeded timeout', **result)
    elif rc != 0:
        module.fail_json(msg='non-zero return code', **result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
