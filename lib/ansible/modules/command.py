# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>, and others
# Copyright: (c) 2016, Toshio Kuratomi <tkuratomi@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = r"""
---
module: command
short_description: Execute commands on targets
version_added: historical
description:
     - The M(ansible.builtin.command) module takes the command name followed by a list of space-delimited arguments.
     - The given command will be executed on all selected nodes.
     - The command(s) will not be
       processed through the shell, so variables like C($HOSTNAME) and operations
       like C("*"), C("<"), C(">"), C("|"), C(";") and C("&") will not work.
       Use the M(ansible.builtin.shell) module if you need these features.
     - To create C(command) tasks that are easier to read than the ones using space-delimited
       arguments, pass parameters using the C(args) L(task keyword,https://docs.ansible.com/ansible/latest/reference_appendices/playbooks_keywords.html#task)
       or use O(cmd) parameter.
     - Either a free form command or O(cmd) parameter is required, see the examples.
     - For Windows targets, use the M(ansible.windows.win_command) module instead.
extends_documentation_fragment:
    - action_common_attributes
    - action_common_attributes.raw
attributes:
    check_mode:
        details: while the command itself is arbitrary and cannot be subject to the check mode semantics it adds O(creates)/O(removes) options as a workaround
        support: partial
    diff_mode:
        support: none
    platform:
      support: full
      platforms: posix
    raw:
      support: full
options:
  expand_argument_vars:
    description:
      - Expands the arguments that are variables, for example C($HOME) will be expanded before being passed to the
        command to run.
      - Set to V(false) to disable expansion and treat the value as a literal argument.
    type: bool
    default: true
    version_added: "2.16"
  free_form:
    description:
      - The command module takes a free form string as a command to run.
      - There is no actual parameter named C(free_form).
  cmd:
    type: str
    description:
      - The command to run.
  argv:
    type: list
    elements: str
    description:
      - Passes the command as a list rather than a string.
      - Use O(argv) to avoid quoting values that would otherwise be interpreted incorrectly (for example "user name").
      - Only the string (free form) or the list (argv) form can be provided, not both.  One or the other must be provided.
    version_added: "2.6"
  creates:
    type: path
    description:
      - A filename or (since 2.0) glob pattern. If a matching file already exists, this step B(will not) be run.
      - This is checked before O(removes) is checked.
  removes:
    type: path
    description:
      - A filename or (since 2.0) glob pattern. If a matching file exists, this step B(will) be run.
      - This is checked after O(creates) is checked.
    version_added: "0.8"
  chdir:
    type: path
    description:
      - Change into this directory before running the command.
    version_added: "0.6"
  stdin:
    description:
      - Set the stdin of the command directly to the specified value.
    type: str
    version_added: "2.4"
  stdin_add_newline:
    type: bool
    default: yes
    description:
      - If set to V(true), append a newline to stdin data.
    version_added: "2.8"
  strip_empty_ends:
    description:
      - Strip empty lines from the end of stdout/stderr in result.
    version_added: "2.8"
    type: bool
    default: yes
notes:
    -  If you want to run a command through the shell (say you are using C(<), C(>), C(|), and so on),
       you actually want the M(ansible.builtin.shell) module instead.
       Parsing shell metacharacters can lead to unexpected commands being executed if quoting is not done correctly so it is more secure to
       use the M(ansible.builtin.command) module when possible.
    -  O(creates), O(removes), and O(chdir) can be specified after the command.
       For instance, if you only want to run a command if a certain file does not exist, use this.
    -  Check mode is supported when passing O(creates) or O(removes). If running in check mode and either of these are specified, the module will
       check for the existence of the file and report the correct changed status. If these are not supplied, the task will be skipped.
    -  The O(ignore:executable) parameter is removed since version 2.4. If you have a need for this parameter, use the M(ansible.builtin.shell) module instead.
    -  For Windows targets, use the M(ansible.windows.win_command) module instead.
    -  For rebooting systems, use the M(ansible.builtin.reboot) or M(ansible.windows.win_reboot) module.
    -  If the command returns non UTF-8 data, it must be encoded to avoid issues. This may necessitate using M(ansible.builtin.shell) so the output
       can be piped through C(base64).
seealso:
- module: ansible.builtin.raw
- module: ansible.builtin.script
- module: ansible.builtin.shell
- module: ansible.windows.win_command
author:
    - Ansible Core Team
    - Michael DeHaan
"""

EXAMPLES = r"""
- name: Return motd to registered var
  ansible.builtin.command: cat /etc/motd
  register: mymotd

# free-form (string) arguments, all arguments on one line
- name: Run command if /path/to/database does not exist (without 'args')
  ansible.builtin.command: /usr/bin/make_database.sh db_user db_name creates=/path/to/database

# free-form (string) arguments, some arguments on separate lines with the 'args' keyword
# 'args' is a task keyword, passed at the same level as the module
- name: Run command if /path/to/database does not exist (with 'args' keyword)
  ansible.builtin.command: /usr/bin/make_database.sh db_user db_name
  args:
    creates: /path/to/database

# 'cmd' is module parameter
- name: Run command if /path/to/database does not exist (with 'cmd' parameter)
  ansible.builtin.command:
    cmd: /usr/bin/make_database.sh db_user db_name
    creates: /path/to/database

- name: Change the working directory to somedir/ and run the command as db_owner if /path/to/database does not exist
  ansible.builtin.command: /usr/bin/make_database.sh db_user db_name
  become: yes
  become_user: db_owner
  args:
    chdir: somedir/
    creates: /path/to/database

# argv (list) arguments, each argument on a separate line, 'args' keyword not necessary
# 'argv' is a parameter, indented one level from the module
- name: Use 'argv' to send a command as a list - leave 'command' empty
  ansible.builtin.command:
    argv:
      - /usr/bin/make_database.sh
      - Username with whitespace
      - dbname with whitespace
    creates: /path/to/database

- name: Run command using argv with mixed argument formats
  ansible.builtin.command:
    argv:
      - /path/to/binary
      - -v
      - --debug
      - --longopt
      - value for longopt
      - --other-longopt=value for other longopt
      - positional

- name: Safely use templated variable to run command. Always use the quote filter to avoid injection issues
  ansible.builtin.command: cat {{ myfile|quote }}
  register: myoutput
"""

RETURN = r"""
msg:
  description: changed
  returned: always
  type: bool
  sample: True
start:
  description: The command execution start time.
  returned: always
  type: str
  sample: '2017-09-29 22:03:48.083128'
end:
  description: The command execution end time.
  returned: always
  type: str
  sample: '2017-09-29 22:03:48.084657'
delta:
  description: The command execution delta time.
  returned: always
  type: str
  sample: '0:00:00.001529'
stdout:
  description: The command standard output.
  returned: always
  type: str
  sample: 'Clustering node rabbit@slave1 with rabbit@master …'
stderr:
  description: The command standard error.
  returned: always
  type: str
  sample: 'ls cannot access foo: No such file or directory'
cmd:
  description: The command executed by the task.
  returned: always
  type: list
  sample:
  - echo
  - hello
rc:
  description: The command return code (0 means success).
  returned: always
  type: int
  sample: 0
stdout_lines:
  description: The command standard output split in lines.
  returned: always
  type: list
  sample: [u'Clustering node rabbit@slave1 with rabbit@master …']
stderr_lines:
  description: The command standard error split in lines.
  returned: always
  type: list
  sample: [u'ls cannot access foo: No such file or directory', u'ls …']
"""

import datetime
import glob
import os
import shlex

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native, to_bytes, to_text
from ansible.module_utils.common.collections import is_iterable
from ansible.module_utils.shell import get_command_args


def main():

    # the command module is the one ansible module that does not take key=value args
    # hence don't copy this one if you are looking to build others!
    # NOTE: ensure splitter.py is kept in sync for exceptions
    module = AnsibleModule(
        argument_spec=get_command_args(),
        supports_check_mode=True,
    )
    shell = module.params['_uses_shell']
    chdir = module.params['chdir']
    executable = module.params['executable']
    args = module.params['_raw_params']
    argv = module.params['argv']
    creates = module.params['creates']
    removes = module.params['removes']
    stdin = module.params['stdin']
    stdin_add_newline = module.params['stdin_add_newline']
    strip = module.params['strip_empty_ends']
    expand_argument_vars = module.params['expand_argument_vars']

    # we promised these in 'always' ( _lines get auto-added on action plugin)
    r = {'changed': False, 'stdout': '', 'stderr': '', 'rc': None, 'cmd': None, 'start': None, 'end': None, 'delta': None, 'msg': ''}

    if not shell and executable:
        module.warn("As of Ansible 2.4, the parameter 'executable' is no longer supported with the 'command' module. Not using '%s'." % executable)
        executable = None

    if (not args or args.strip() == '') and not argv:
        r['rc'] = 256
        r['msg'] = "no command given"
        module.fail_json(**r)

    if args and argv:
        r['rc'] = 256
        r['msg'] = "only command or argv can be given, not both"
        module.fail_json(**r)

    if not shell and args:
        args = shlex.split(args)

    args = args or argv
    # All args must be strings
    if is_iterable(args, include_strings=False):
        args = [to_native(arg, errors='surrogate_or_strict', nonstring='simplerepr') for arg in args]

    r['cmd'] = args

    if chdir:
        chdir = to_bytes(chdir, errors='surrogate_or_strict')

        try:
            os.chdir(chdir)
        except (IOError, OSError) as e:
            r['msg'] = 'Unable to change directory before execution: %s' % to_text(e)
            module.fail_json(**r)

    # check_mode partial support, since it only really works in checking creates/removes
    if module.check_mode:
        shoulda = "Would"
    else:
        shoulda = "Did"

    # special skips for idempotence if file exists (assumes command creates)
    if creates:
        if glob.glob(creates):
            r['msg'] = "%s not run command since '%s' exists" % (shoulda, creates)
            r['stdout'] = "skipped, since %s exists" % creates  # TODO: deprecate

            r['rc'] = 0

    # special skips for idempotence if file does not exist (assumes command removes)
    if not r['msg'] and removes:
        if not glob.glob(removes):
            r['msg'] = "%s not run command since '%s' does not exist" % (shoulda, removes)
            r['stdout'] = "skipped, since %s does not exist" % removes  # TODO: deprecate
            r['rc'] = 0

    if r['msg']:
        module.exit_json(**r)

    r['changed'] = True

    # actually executes command (or not ...)
    if not module.check_mode:
        r['start'] = datetime.datetime.now()
        r['rc'], r['stdout'], r['stderr'] = module.run_command(args, executable=executable, use_unsafe_shell=shell, encoding=None,
                                                               data=stdin, binary_data=(not stdin_add_newline),
                                                               expand_user_and_vars=expand_argument_vars)
        r['end'] = datetime.datetime.now()
    else:
        # this is partial check_mode support, since we end up skipping if we get here
        r['rc'] = 0
        r['msg'] = "Command would have run if not in check mode"
        if creates is None and removes is None:
            r['skipped'] = True
            # skipped=True and changed=True are mutually exclusive
            r['changed'] = False

    # convert to text for jsonization and usability
    if r['start'] is not None and r['end'] is not None:
        # these are datetime objects, but need them as strings to pass back
        r['delta'] = to_text(r['end'] - r['start'])
        r['end'] = to_text(r['end'])
        r['start'] = to_text(r['start'])

    if strip:
        r['stdout'] = to_text(r['stdout']).rstrip("\r\n")
        r['stderr'] = to_text(r['stderr']).rstrip("\r\n")

    if r['rc'] != 0:
        r['msg'] = 'non-zero return code'
        module.fail_json(**r)

    module.exit_json(**r)


if __name__ == '__main__':
    main()
