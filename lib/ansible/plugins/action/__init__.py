# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from six.moves import StringIO
import base64
import json
import os
import random
import stat
import sys
import tempfile
import time

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.executor.module_common import modify_module
from ansible.parsing.utils.jsonify import jsonify
from ansible.utils.unicode import to_bytes

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

class ActionBase:

    '''
    This class is the base class for all action plugins, and defines
    code common to all actions. The base class handles the connection
    by putting/getting files and executing commands based on the current
    action in use.
    '''

    def __init__(self, task, connection, play_context, loader, templar, shared_loader_obj):
        self._task              = task
        self._connection        = connection
        self._play_context      = play_context
        self._loader            = loader
        self._templar           = templar
        self._shared_loader_obj = shared_loader_obj
        self._display           = display

        self._supports_check_mode = True

    def _configure_module(self, module_name, module_args, task_vars=dict()):
        '''
        Handles the loading and templating of the module code through the
        modify_module() function.
        '''

        # Search module path(s) for named module.
        module_suffixes = getattr(self._connection, 'default_suffixes', None)

        # Check to determine if PowerShell modules are supported, and apply
        # some fixes (hacks) to module name + args.
        if module_suffixes and '.ps1' in module_suffixes:
            # Use Windows versions of stat/file/copy modules when called from
            # within other action plugins.
            if module_name in ('stat', 'file', 'copy') and self._task.action != module_name:
                module_name = 'win_%s' % module_name
            # Remove extra quotes surrounding path parameters before sending to module.
            if module_name in ('win_stat', 'win_file', 'win_copy', 'slurp') and module_args and hasattr(self._connection._shell, '_unquote'):
                for key in ('src', 'dest', 'path'):
                    if key in module_args:
                        module_args[key] = self._connection._shell._unquote(module_args[key])

        module_path = self._shared_loader_obj.module_loader.find_plugin(module_name, module_suffixes)
        if module_path is None:
            # Use Windows version of ping module to check module paths when
            # using a connection that supports .ps1 suffixes.
            if module_suffixes and '.ps1' in module_suffixes:
                ping_module = 'win_ping'
            else:
                ping_module = 'ping'
            module_path2 = self._shared_loader_obj.module_loader.find_plugin(ping_module, module_suffixes)
            if module_path2 is not None:
                raise AnsibleError("The module %s was not found in configured module paths" % (module_name))
            else:
                raise AnsibleError("The module %s was not found in configured module paths. " \
                                   "Additionally, core modules are missing. If this is a checkout, " \
                                   "run 'git submodule update --init --recursive' to correct this problem." % (module_name))

        # insert shared code and arguments into the module
        (module_data, module_style, module_shebang) = modify_module(module_path, module_args, task_vars=task_vars)

        return (module_style, module_shebang, module_data)

    def _compute_environment_string(self):
        '''
        Builds the environment string to be used when executing the remote task.
        '''

        final_environment = dict()
        if self._task.environment is not None:
            environments = self._task.environment
            if not isinstance(environments, list):
                environments = [ environments ]

            for environment in environments:
                if environment is None:
                    continue
                if not isinstance(environment, dict):
                    raise AnsibleError("environment must be a dictionary, received %s (%s)" % (environment, type(environment)))
                # very deliberatly using update here instead of combine_vars, as
                # these environment settings should not need to merge sub-dicts
                final_environment.update(environment)

        return self._connection._shell.env_prefix(**final_environment)

    def _early_needs_tmp_path(self):
        '''
        Determines if a temp path should be created before the action is executed.
        '''

        # FIXME: modified from original, needs testing? Since this is now inside
        #        the action plugin, it should make it just this simple
        return getattr(self, 'TRANSFERS_FILES', False)

    def _late_needs_tmp_path(self, tmp, module_style):
        '''
        Determines if a temp path is required after some early actions have already taken place.
        '''
        if tmp and "tmp" in tmp:
            # tmp has already been created
            return False
        if not self._connection.has_pipelining or not C.ANSIBLE_SSH_PIPELINING or C.DEFAULT_KEEP_REMOTE_FILES or self._play_context.become:
            # tmp is necessary to store the module source code
            # or we want to keep the files on the target system
            return True
        if module_style != "new":
            # even when conn has pipelining, old style modules need tmp to store arguments
            return True
        return False

    # FIXME: return a datastructure in this function instead of raising errors -
    #        the new executor pipeline handles it much better that way
    def _make_tmp_path(self):
        '''
        Create and return a temporary path on a remote box.
        '''

        basefile = 'ansible-tmp-%s-%s' % (time.time(), random.randint(0, 2**48))
        use_system_tmp = False

        if self._play_context.become and self._play_context.become_user != 'root':
            use_system_tmp = True

        tmp_mode = None
        if self._play_context.remote_user != 'root' or self._play_context.become and self._play_context.become_user != 'root':
            tmp_mode = 0o755

        cmd = self._connection._shell.mkdtemp(basefile, use_system_tmp, tmp_mode)
        self._display.debug("executing _low_level_execute_command to create the tmp path")
        result = self._low_level_execute_command(cmd, None, sudoable=False)
        self._display.debug("done with creation of tmp path")

        # error handling on this seems a little aggressive?
        if result['rc'] != 0:
            if result['rc'] == 5:
                output = 'Authentication failure.'
            elif result['rc'] == 255 and self._connection.transport in ('ssh',):

                if self._play_context.verbosity > 3:
                    output = 'SSH encountered an unknown error. The output was:\n%s' % (result['stdout']+result['stderr'])
                else:
                    output = 'SSH encountered an unknown error during the connection. We recommend you re-run the command using -vvvv, which will enable SSH debugging output to help diagnose the issue'

            elif 'No space left on device' in result['stderr']:
                output = result['stderr']
            else:
                output = 'Authentication or permission failure.  In some cases, you may have been able to authenticate and did not have permissions on the remote directory. Consider changing the remote temp path in ansible.cfg to a path rooted in "/tmp". Failed command was: %s, exited with result %d' % (cmd, result['rc'])
            if 'stdout' in result and result['stdout'] != '':
                output = output + ": %s" % result['stdout']
            raise AnsibleError(output)

        # FIXME: do we still need to do this?
        #rc = self._connection._shell.join_path(utils.last_non_blank_line(result['stdout']).strip(), '')
        rc = self._connection._shell.join_path(result['stdout'].strip(), '').splitlines()[-1]

        # Catch failure conditions, files should never be
        # written to locations in /.
        if rc == '/':
            raise AnsibleError('failed to resolve remote temporary directory from %s: `%s` returned empty string' % (basefile, cmd))

        return rc

    def _remove_tmp_path(self, tmp_path):
        '''Remove a temporary path we created. '''

        if tmp_path and "-tmp-" in tmp_path:
            cmd = self._connection._shell.remove(tmp_path, recurse=True)
            # If we have gotten here we have a working ssh configuration.
            # If ssh breaks we could leave tmp directories out on the remote system.
            self._display.debug("calling _low_level_execute_command to remove the tmp path")
            self._low_level_execute_command(cmd, None, sudoable=False)
            self._display.debug("done removing the tmp path")

    def _transfer_data(self, remote_path, data):
        '''
        Copies the module data out to the temporary module path.
        '''

        if isinstance(data, dict):
            data = jsonify(data)

        afd, afile = tempfile.mkstemp()
        afo = os.fdopen(afd, 'w')
        try:
            data = to_bytes(data, errors='strict')
            afo.write(data)
        except Exception as e:
            #raise AnsibleError("failure encoding into utf-8: %s" % str(e))
            raise AnsibleError("failure writing module data to temporary file for transfer: %s" % str(e))

        afo.flush()
        afo.close()

        try:
            self._connection.put_file(afile, remote_path)
        finally:
            os.unlink(afile)

        return remote_path

    def _remote_chmod(self, tmp, mode, path, sudoable=False):
        '''
        Issue a remote chmod command
        '''

        cmd = self._connection._shell.chmod(mode, path)
        self._display.debug("calling _low_level_execute_command to chmod the remote path")
        res = self._low_level_execute_command(cmd, tmp, sudoable=sudoable)
        self._display.debug("done with chmod call")
        return res

    def _remote_checksum(self, tmp, path, all_vars):
        '''
        Takes a remote checksum and returns 1 if no file
        '''

        python_interp = all_vars.get('ansible_python_interpreter', 'python')

        cmd = self._connection._shell.checksum(path, python_interp)
        self._display.debug("calling _low_level_execute_command to get the remote checksum")
        data = self._low_level_execute_command(cmd, tmp, sudoable=True)
        self._display.debug("done getting the remote checksum")
        # FIXME: implement this function?
        #data2 = utils.last_non_blank_line(data['stdout'])
        try:
            data2 = data['stdout'].strip().splitlines()[-1]
            if data2 == '':
                # this may happen if the connection to the remote server
                # failed, so just return "INVALIDCHECKSUM" to avoid errors
                return "INVALIDCHECKSUM"
            else:
                return data2.split()[0]
        except IndexError:
            self._display.warning("Calculating checksum failed unusually, please report this to " + \
                "the list so it can be fixed\ncommand: %s\n----\noutput: %s\n----\n") % (cmd, data)
            # this will signal that it changed and allow things to keep going
            return "INVALIDCHECKSUM"

    def _remote_expand_user(self, path, tmp):
        ''' takes a remote path and performs tilde expansion on the remote host '''
        if not path.startswith('~'): # FIXME: Windows paths may start with "~ instead of just ~
            return path

        # FIXME: Can't use os.path.sep for Windows paths.
        split_path = path.split(os.path.sep, 1)
        expand_path = split_path[0]
        if expand_path == '~':
            if self._play_context.become and self._play_context.become_user:
                expand_path = '~%s' % self._play_context.become_user

        cmd = self._connection._shell.expand_user(expand_path)
        self._display.debug("calling _low_level_execute_command to expand the remote user path")
        data = self._low_level_execute_command(cmd, tmp, sudoable=False)
        self._display.debug("done expanding the remote user path")
        #initial_fragment = utils.last_non_blank_line(data['stdout'])
        initial_fragment = data['stdout'].strip().splitlines()[-1]

        if not initial_fragment:
            # Something went wrong trying to expand the path remotely.  Return
            # the original string
            return path

        if len(split_path) > 1:
            return self._connection._shell.join_path(initial_fragment, *split_path[1:])
        else:
            return initial_fragment

    def _filter_leading_non_json_lines(self, data):
        '''
        Used to avoid random output from SSH at the top of JSON output, like messages from
        tcagetattr, or where dropbear spews MOTD on every single command (which is nuts).

        need to filter anything which starts not with '{', '[', ', '=' or is an empty line.
        filter only leading lines since multiline JSON is valid.
        '''

        filtered_lines = StringIO()
        stop_filtering = False
        for line in data.splitlines():
            if stop_filtering or line.startswith('{') or line.startswith('['):
                stop_filtering = True
                filtered_lines.write(line + '\n')
        return filtered_lines.getvalue()

    def _execute_module(self, module_name=None, module_args=None, tmp=None, task_vars=dict(), persist_files=False, delete_remote_tmp=True):
        '''
        Transfer and run a module along with its arguments.
        '''

        # if a module name was not specified for this execution, use
        # the action from the task
        if module_name is None:
            module_name = self._task.action
        if module_args is None:
            module_args = self._task.args

        # set check mode in the module arguments, if required
        if self._play_context.check_mode and not self._task.always_run:
            if not self._supports_check_mode:
                raise AnsibleError("check mode is not supported for this operation")
            module_args['_ansible_check_mode'] = True

        # set no log in the module arguments, if required
        if self._play_context.no_log:
            module_args['_ansible_no_log'] = True

        (module_style, shebang, module_data) = self._configure_module(module_name=module_name, module_args=module_args, task_vars=task_vars)
        if not shebang:
            raise AnsibleError("module is missing interpreter line")

        # a remote tmp path may be necessary and not already created
        remote_module_path = None
        if not tmp and self._late_needs_tmp_path(tmp, module_style):
            tmp = self._make_tmp_path()

        if tmp:
            remote_module_path = self._connection._shell.join_path(tmp, module_name)

        # FIXME: async stuff here?
        #if (module_style != 'new' or async_jid is not None or not self._connection._has_pipelining or not C.ANSIBLE_SSH_PIPELINING or C.DEFAULT_KEEP_REMOTE_FILES):
        if remote_module_path:
            self._display.debug("transferring module to remote")
            self._transfer_data(remote_module_path, module_data)
            self._display.debug("done transferring module to remote")

        environment_string = self._compute_environment_string()

        if tmp and "tmp" in tmp and self._play_context.become and self._play_context.become_user != 'root':
            # deal with possible umask issues once sudo'ed to other user
            self._remote_chmod(tmp, 'a+r', remote_module_path)

        cmd = ""
        in_data = None

        # FIXME: all of the old-module style and async stuff has been removed from here, and
        #        might need to be re-added (unless we decide to drop support for old-style modules
        #        at this point and rework things to support non-python modules specifically)
        if self._connection.has_pipelining and C.ANSIBLE_SSH_PIPELINING and not C.DEFAULT_KEEP_REMOTE_FILES:
            in_data = module_data
        else:
            if remote_module_path:
                cmd = remote_module_path

        rm_tmp = None
        if tmp and "tmp" in tmp and not C.DEFAULT_KEEP_REMOTE_FILES and not persist_files and delete_remote_tmp:
            if not self._play_context.become or self._play_context.become_user == 'root':
                # not sudoing or sudoing to root, so can cleanup files in the same step
                rm_tmp = tmp

        cmd = self._connection._shell.build_module_command(environment_string, shebang, cmd, rm_tmp)
        cmd = cmd.strip()

        sudoable = True
        if module_name == "accelerate":
            # always run the accelerate module as the user
            # specified in the play, not the sudo_user
            sudoable = False

        self._display.debug("calling _low_level_execute_command() for command %s" % cmd)
        res = self._low_level_execute_command(cmd, tmp, sudoable=sudoable, in_data=in_data)
        self._display.debug("_low_level_execute_command returned ok")

        if tmp and "tmp" in tmp and not C.DEFAULT_KEEP_REMOTE_FILES and not persist_files and delete_remote_tmp:
            if self._play_context.become and self._play_context.become_user != 'root':
            # not sudoing to root, so maybe can't delete files as that other user
            # have to clean up temp files as original user in a second step
                cmd2 = self._connection._shell.remove(tmp, recurse=True)
                self._low_level_execute_command(cmd2, tmp, sudoable=False)

        try:
            data = json.loads(self._filter_leading_non_json_lines(res.get('stdout', '')))
        except ValueError:
            # not valid json, lets try to capture error
            data = dict(failed=True, parsed=False)
            if 'stderr' in res and res['stderr'].startswith('Traceback'):
                data['exception'] = res['stderr']
            else:
                data['msg'] = res.get('stdout', '')
                if 'stderr' in res:
                    data['msg'] += res['stderr']

        # pre-split stdout into lines, if stdout is in the data and there
        # isn't already a stdout_lines value there
        if 'stdout' in data and 'stdout_lines' not in data:
            data['stdout_lines'] = data.get('stdout', '').splitlines()

        # store the module invocation details back into the result
        if self._task.async != 0:
            data['invocation'] = dict(
                module_args = module_args,
                module_name = module_name,
            )

        self._display.debug("done with _execute_module (%s, %s)" % (module_name, module_args))
        return data

    def _low_level_execute_command(self, cmd, tmp, sudoable=True, in_data=None, executable=None):
        '''
        This is the function which executes the low level shell command, which
        may be commands to create/remove directories for temporary files, or to
        run the module code or python directly when pipelining.
        '''

        if executable is not None:
            cmd = executable + ' -c ' + cmd

        self._display.debug("in _low_level_execute_command() (%s)" % (cmd,))
        if not cmd:
            # this can happen with powershell modules when there is no analog to a Windows command (like chmod)
            self._display.debug("no command, exiting _low_level_execute_command()")
            return dict(stdout='', stderr='')

        if sudoable and self._play_context.become:
            self._display.debug("using become for this command")
            cmd = self._play_context.make_become_cmd(cmd, executable=executable)

        self._display.debug("executing the command %s through the connection" % cmd)
        rc, stdin, stdout, stderr = self._connection.exec_command(cmd, tmp, in_data=in_data, sudoable=sudoable)
        self._display.debug("command execution done")

        if not isinstance(stdout, basestring):
            out = ''.join(stdout.readlines())
        else:
            out = stdout

        if not isinstance(stderr, basestring):
            err = ''.join(stderr.readlines())
        else:
            err = stderr

        self._display.debug("done with _low_level_execute_command() (%s)" % (cmd,))
        if rc is None:
            rc = 0

        return dict(rc=rc, stdout=out, stdout_lines=out.splitlines(), stderr=err)

    def _get_first_available_file(self, faf, of=None, searchdir='files'):

        self._display.deprecated("first_available_file, use with_first_found or lookup('first_found',...) instead")
        for fn in faf:
            fn_orig = fn
            fnt = self._templar.template(fn)
            if self._task._role is not None:
                lead = self._task._role._role_path
            else:
                lead = fnt
            fnd = self._loader.path_dwim_relative(lead, searchdir, fnt)

            if not os.path.exists(fnd) and of is not None:
                if self._task._role is not None:
                    lead = self._task._role._role_path
                else:
                    lead = of
                fnd = self._loader.path_dwim_relative(lead, searchdir, of)

            if os.path.exists(fnd):
                return fnd

        return None

    def _get_diff_data(self, tmp, destination, source, task_vars, source_file=True):

        diff = {}
        self._display.debug("Going to peek to see if file has changed permissions")
        peek_result = self._execute_module(module_name='file', module_args=dict(path=destination, diff_peek=True), task_vars=task_vars, persist_files=True)

        if not('failed' in peek_result and peek_result['failed']) or peek_result.get('rc', 0) == 0:

            if peek_result['state'] == 'absent':
                diff['before'] = ''
            elif peek_result['appears_binary']:
                diff['dst_binary'] = 1
            elif peek_result['size'] > C.MAX_FILE_SIZE_FOR_DIFF:
                diff['dst_larger'] = C.MAX_FILE_SIZE_FOR_DIFF
            else:
                self._display.debug("Slurping the file %s" % source)
                dest_result = self._execute_module(module_name='slurp', module_args=dict(path=destination), task_vars=task_vars, persist_files=True)
                if 'content' in dest_result:
                    dest_contents = dest_result['content']
                    if dest_result['encoding'] == 'base64':
                        dest_contents = base64.b64decode(dest_contents)
                    else:
                        raise AnsibleError("unknown encoding in content option, failed: %s" % dest_result)
                    diff['before_header'] = destination
                    diff['before'] = dest_contents

            if source_file:
                self._display.debug("Reading local copy of the file %s" % source)
                try:
                    src = open(source)
                    src_contents = src.read(8192)
                    st = os.stat(source)
                except Exception as e:
                    raise AnsibleError("Unexpected error while reading source (%s) for diff: %s " % (source, str(e)))
                if "\x00" in src_contents:
                    diff['src_binary'] = 1
                elif st[stat.ST_SIZE] > C.MAX_FILE_SIZE_FOR_DIFF:
                    diff['src_larger'] = C.MAX_FILE_SIZE_FOR_DIFF
                else:
                    diff['after_header'] = source
                    diff['after'] = src_contents
            else:
                self._display.debug("source of file passed in")
                diff['after_header'] = 'dynamically generated'
                diff['after'] = source

        return diff
