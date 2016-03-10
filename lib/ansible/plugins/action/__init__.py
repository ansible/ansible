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

import base64
import json
import os
import pipes
import random
import re
import stat
import tempfile
import time
from abc import ABCMeta, abstractmethod

from ansible.compat.six import binary_type, text_type, iteritems, with_metaclass

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleConnectionFailure
from ansible.executor.module_common import modify_module
from ansible.parsing.utils.jsonify import jsonify
from ansible.utils.unicode import to_bytes, to_unicode

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ActionBase(with_metaclass(ABCMeta, object)):

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
        # Backwards compat: self._display isn't really needed, just import the global display and use that.
        self._display           = display

        self._supports_check_mode = True

    @abstractmethod
    def run(self, tmp=None, task_vars=None):
        """ Action Plugins should implement this method to perform their
        tasks.  Everything else in this base class is a helper method for the
        action plugin to do that.

        :kwarg tmp: Temporary directory.  Sometimes an action plugin sets up
            a temporary directory and then calls another module.  This parameter
            allows us to reuse the same directory for both.
        :kwarg task_vars: The variables (host vars, group vars, config vars,
            etc) associated with this task.
        :returns: dictionary of results from the module

        Implementors of action modules may find the following variables especially useful:

        * Module parameters.  These are stored in self._task.args
        """
        # store the module invocation details into the results
        results =  {}
        if self._task.async == 0:
            results['invocation'] = dict(
                module_name = self._task.action,
                module_args = self._task.args,
            )
        return results

    def _configure_module(self, module_name, module_args, task_vars=None):
        '''
        Handles the loading and templating of the module code through the
        modify_module() function.
        '''
        if task_vars is None:
            task_vars = dict()

        # Search module path(s) for named module.
        for mod_type in self._connection.module_implementation_preferences:
            # Check to determine if PowerShell modules are supported, and apply
            # some fixes (hacks) to module name + args.
            if mod_type == '.ps1':
                # win_stat, win_file, and win_copy are not just like their
                # python counterparts but they are compatible enough for our
                # internal usage
                if module_name in ('stat', 'file', 'copy') and self._task.action != module_name:
                    module_name = 'win_%s' % module_name

                # Remove extra quotes surrounding path parameters before sending to module.
                if module_name in ('win_stat', 'win_file', 'win_copy', 'slurp') and module_args and hasattr(self._connection._shell, '_unquote'):
                    for key in ('src', 'dest', 'path'):
                        if key in module_args:
                            module_args[key] = self._connection._shell._unquote(module_args[key])

            module_path = self._shared_loader_obj.module_loader.find_plugin(module_name, mod_type)
            if module_path:
                break
        else:  # This is a for-else: http://bit.ly/1ElPkyg
            # Use Windows version of ping module to check module paths when
            # using a connection that supports .ps1 suffixes. We check specifically
            # for win_ping here, otherwise the code would look for ping.ps1
            if '.ps1' in self._connection.module_implementation_preferences:
                ping_module = 'win_ping'
            else:
                ping_module = 'ping'
            module_path2 = self._shared_loader_obj.module_loader.find_plugin(ping_module, self._connection.module_implementation_preferences)
            if module_path2 is not None:
                raise AnsibleError("The module %s was not found in configured module paths" % (module_name))
            else:
                raise AnsibleError("The module %s was not found in configured module paths. "
                                   "Additionally, core modules are missing. If this is a checkout, "
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

            # the environments as inherited need to be reversed, to make
            # sure we merge in the parent's values first so those in the
            # block then task 'win' in precedence
            environments.reverse()
            for environment in environments:
                if environment is None:
                    continue
                temp_environment = self._templar.template(environment)
                if not isinstance(temp_environment, dict):
                    raise AnsibleError("environment must be a dictionary, received %s (%s)" % (temp_environment, type(temp_environment)))
                # very deliberately using update here instead of combine_vars, as
                # these environment settings should not need to merge sub-dicts
                final_environment.update(temp_environment)

        final_environment = self._templar.template(final_environment)
        return self._connection._shell.env_prefix(**final_environment)

    def _early_needs_tmp_path(self):
        '''
        Determines if a temp path should be created before the action is executed.
        '''

        return getattr(self, 'TRANSFERS_FILES', False)

    def _late_needs_tmp_path(self, tmp, module_style):
        '''
        Determines if a temp path is required after some early actions have already taken place.
        '''
        if tmp and "tmp" in tmp:
            # tmp has already been created
            return False
        if not self._connection.has_pipelining or not self._play_context.pipelining or C.DEFAULT_KEEP_REMOTE_FILES or self._play_context.become_method == 'su':
            # tmp is necessary to store the module source code
            # or we want to keep the files on the target system
            return True
        if module_style != "new":
            # even when conn has pipelining, old style modules need tmp to store arguments
            return True
        return False

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
        result = self._low_level_execute_command(cmd, sudoable=False)

        # error handling on this seems a little aggressive?
        if result['rc'] != 0:
            if result['rc'] == 5:
                output = 'Authentication failure.'
            elif result['rc'] == 255 and self._connection.transport in ('ssh',):

                if self._play_context.verbosity > 3:
                    output = u'SSH encountered an unknown error. The output was:\n%s%s' % (result['stdout'], result['stderr'])
                else:
                    output = (u'SSH encountered an unknown error during the connection.'
                            ' We recommend you re-run the command using -vvvv, which will enable SSH debugging output to help diagnose the issue')

            elif u'No space left on device' in result['stderr']:
                output = result['stderr']
            else:
                output = ('Authentication or permission failure.'
                        ' In some cases, you may have been able to authenticate and did not have permissions on the remote directory.'
                        ' Consider changing the remote temp path in ansible.cfg to a path rooted in "/tmp".'
                        ' Failed command was: %s, exited with result %d' % (cmd, result['rc']))
            if 'stdout' in result and result['stdout'] != u'':
                output = output + u": %s" % result['stdout']
            raise AnsibleConnectionFailure(output)

        try:
            rc = self._connection._shell.join_path(result['stdout'].strip(), u'').splitlines()[-1]
        except IndexError:
            # stdout was empty or just space, set to / to trigger error in next if
            rc = '/'

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
            self._low_level_execute_command(cmd, sudoable=False)

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

    def _remote_chmod(self, mode, path, sudoable=False):
        '''
        Issue a remote chmod command
        '''

        cmd = self._connection._shell.chmod(mode, path)
        res = self._low_level_execute_command(cmd, sudoable=sudoable)
        return res

    def _execute_remote_stat(self, path, all_vars, follow, tmp=None):
        '''
        Get information from remote file.
        '''
        module_args=dict(
           path=path,
           follow=follow,
           get_md5=False,
           get_checksum=True,
           checksum_algo='sha1',
        )
        mystat = self._execute_module(module_name='stat', module_args=module_args, task_vars=all_vars, tmp=tmp, delete_remote_tmp=(tmp is None))

        if 'failed' in mystat and mystat['failed']:
            raise AnsibleError('Failed to get information on remote file (%s): %s' % (path, mystat['msg']))

        if not mystat['stat']['exists']:
            # empty might be matched, 1 should never match, also backwards compatible
            mystat['stat']['checksum'] = '1'

        # happens sometimes when it is a dir and not on bsd
        if not 'checksum' in mystat['stat']:
            mystat['stat']['checksum'] = ''

        return mystat['stat']

    def _remote_checksum(self, path, all_vars):
        '''
        Produces a remote checksum given a path,
        Returns a number 0-4 for specific errors instead of checksum, also ensures it is different
        0 = unknown error
        1 = file does not exist, this might not be an error
        2 = permissions issue
        3 = its a directory, not a file
        4 = stat module failed, likely due to not finding python
        '''
        x = "0" # unknown error has occured
        try:
            remote_stat = self._execute_remote_stat(path, all_vars, follow=False)
            if remote_stat['exists'] and remote_stat['isdir']:
                x = "3" # its a directory not a file
            else:
                x = remote_stat['checksum'] # if 1, file is missing
        except AnsibleError as e:
            errormsg = to_unicode(e)
            if errormsg.endswith('Permission denied'):
                x = "2" # cannot read file
            elif errormsg.endswith('MODULE FAILURE'):
                x = "4" # python not found or module uncaught exception
        finally:
            return x


    def _remote_expand_user(self, path):
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
        data = self._low_level_execute_command(cmd, sudoable=False)
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
        idx = 0
        for line in data.splitlines(True):
            if line.startswith((u'{', u'[')):
                break
            idx = idx + len(line)

        return data[idx:]

    def _strip_success_message(self, data):
        '''
        Removes the BECOME-SUCCESS message from the data.
        '''
        if data.strip().startswith('BECOME-SUCCESS-'):
            data = re.sub(r'^((\r)?\n)?BECOME-SUCCESS.*(\r)?\n', '', data)
        return data

    def _execute_module(self, module_name=None, module_args=None, tmp=None, task_vars=None, persist_files=False, delete_remote_tmp=True):
        '''
        Transfer and run a module along with its arguments.
        '''
        if task_vars is None:
            task_vars = dict()

        # if a module name was not specified for this execution, use
        # the action from the task
        if module_name is None:
            module_name = self._task.action
        if module_args is None:
            module_args = self._task.args

        # set check mode in the module arguments, if required
        if self._play_context.check_mode:
            if not self._supports_check_mode:
                raise AnsibleError("check mode is not supported for this operation")
            module_args['_ansible_check_mode'] = True
        else:
            module_args['_ansible_check_mode'] = False

        # set no log in the module arguments, if required
        module_args['_ansible_no_log'] = self._play_context.no_log or C.DEFAULT_NO_TARGET_SYSLOG

        # set debug in the module arguments, if required
        module_args['_ansible_debug'] = C.DEFAULT_DEBUG

        # let module know we are in diff mode
        module_args['_ansible_diff'] = self._play_context.diff

        # let module know our verbosity
        module_args['_ansible_verbosity'] = self._display.verbosity

        (module_style, shebang, module_data) = self._configure_module(module_name=module_name, module_args=module_args, task_vars=task_vars)
        if not shebang:
            raise AnsibleError("module (%s) is missing interpreter line" % module_name)

        # a remote tmp path may be necessary and not already created
        remote_module_path = None
        args_file_path = None
        if not tmp and self._late_needs_tmp_path(tmp, module_style):
            tmp = self._make_tmp_path()

        if tmp:
            remote_module_filename = self._connection._shell.get_remote_filename(module_name)
            remote_module_path = self._connection._shell.join_path(tmp, remote_module_filename)
            if module_style in ['old', 'non_native_want_json']:
                # we'll also need a temp file to hold our module arguments
                args_file_path = self._connection._shell.join_path(tmp, 'args')

        if remote_module_path or module_style != 'new':
            display.debug("transferring module to remote")
            self._transfer_data(remote_module_path, module_data)
            if module_style == 'old':
                # we need to dump the module args to a k=v string in a file on
                # the remote system, which can be read and parsed by the module
                args_data = ""
                for k,v in iteritems(module_args):
                    args_data += '%s="%s" ' % (k, pipes.quote(text_type(v)))
                self._transfer_data(args_file_path, args_data)
            elif module_style == 'non_native_want_json':
                self._transfer_data(args_file_path, json.dumps(module_args))
            display.debug("done transferring module to remote")

        environment_string = self._compute_environment_string()

        if tmp and "tmp" in tmp and self._play_context.become and self._play_context.become_user != 'root':
            # deal with possible umask issues once sudo'ed to other user
            self._remote_chmod('a+r', remote_module_path)
            if args_file_path is not None:
                self._remote_chmod('a+r', args_file_path)

        cmd = ""
        in_data = None

        if self._connection.has_pipelining and self._play_context.pipelining and not C.DEFAULT_KEEP_REMOTE_FILES and module_style == 'new':
            in_data = module_data
        else:
            if remote_module_path:
                cmd = remote_module_path

        rm_tmp = None
        if tmp and "tmp" in tmp and not C.DEFAULT_KEEP_REMOTE_FILES and not persist_files and delete_remote_tmp:
            if not self._play_context.become or self._play_context.become_user == 'root':
                # not sudoing or sudoing to root, so can cleanup files in the same step
                rm_tmp = tmp

        cmd = self._connection._shell.build_module_command(environment_string, shebang, cmd, arg_path=args_file_path, rm_tmp=rm_tmp)
        cmd = cmd.strip()

        sudoable = True
        if module_name == "accelerate":
            # always run the accelerate module as the user
            # specified in the play, not the sudo_user
            sudoable = False

        res = self._low_level_execute_command(cmd, sudoable=sudoable, in_data=in_data)

        if tmp and "tmp" in tmp and not C.DEFAULT_KEEP_REMOTE_FILES and not persist_files and delete_remote_tmp:
            if self._play_context.become and self._play_context.become_user != 'root':
                # not sudoing to root, so maybe can't delete files as that other user
                # have to clean up temp files as original user in a second step
                cmd2 = self._connection._shell.remove(tmp, recurse=True)
                self._low_level_execute_command(cmd2, sudoable=False)

        try:
            data = json.loads(self._filter_leading_non_json_lines(res.get('stdout', u'')))
        except ValueError:
            # not valid json, lets try to capture error
            data = dict(failed=True, parsed=False)
            if 'stderr' in res and res['stderr'].startswith(u'Traceback'):
                data['exception'] = res['stderr']
            else:
                data['msg'] = "MODULE FAILURE"
                data['module_stdout'] = res.get('stdout', u'')
                if 'stderr' in res:
                    data['module_stderr'] = res['stderr']

        # pre-split stdout into lines, if stdout is in the data and there
        # isn't already a stdout_lines value there
        if 'stdout' in data and 'stdout_lines' not in data:
            data['stdout_lines'] = data.get('stdout', u'').splitlines()

        display.debug("done with _execute_module (%s, %s)" % (module_name, module_args))
        return data

    def _low_level_execute_command(self, cmd, sudoable=True, in_data=None, executable=C.DEFAULT_EXECUTABLE, encoding_errors='replace'):
        '''
        This is the function which executes the low level shell command, which
        may be commands to create/remove directories for temporary files, or to
        run the module code or python directly when pipelining.

        :kwarg encoding_errors: If the value returned by the command isn't
            utf-8 then we have to figure out how to transform it to unicode.
            If the value is just going to be displayed to the user (or
            discarded) then the default of 'replace' is fine.  If the data is
            used as a key or is going to be written back out to a file
            verbatim, then this won't work.  May have to use some sort of
            replacement strategy (python3 could use surrogateescape)
        '''

        display.debug("_low_level_execute_command(): starting")
        if not cmd:
            # this can happen with powershell modules when there is no analog to a Windows command (like chmod)
            display.debug("_low_level_execute_command(): no command, exiting")
            return dict(stdout='', stderr='')

        allow_same_user = C.BECOME_ALLOW_SAME_USER
        same_user = self._play_context.become_user == self._play_context.remote_user
        if sudoable and self._play_context.become and (allow_same_user or not same_user):
            display.debug("_low_level_execute_command(): using become for this command")
            cmd = self._play_context.make_become_cmd(cmd, executable=executable)

        if executable is not None and self._connection.allow_executable:
            cmd = executable + ' -c ' + pipes.quote(cmd)

        display.debug("_low_level_execute_command(): executing: %s" % (cmd,))
        rc, stdout, stderr = self._connection.exec_command(cmd, in_data=in_data, sudoable=sudoable)

        # stdout and stderr may be either a file-like or a bytes object.
        # Convert either one to a text type
        if isinstance(stdout, binary_type):
            out = to_unicode(stdout, errors=encoding_errors)
        elif not isinstance(stdout, text_type):
            out = to_unicode(b''.join(stdout.readlines()), errors=encoding_errors)
        else:
            out = stdout

        if isinstance(stderr, binary_type):
            err = to_unicode(stderr, errors=encoding_errors)
        elif not isinstance(stderr, text_type):
            err = to_unicode(b''.join(stderr.readlines()), errors=encoding_errors)
        else:
            err = stderr

        if rc is None:
            rc = 0

        # be sure to remove the BECOME-SUCCESS message now
        out = self._strip_success_message(out)

        display.debug("_low_level_execute_command() done: rc=%d, stdout=%s, stderr=%s" % (rc, stdout, stderr))
        return dict(rc=rc, stdout=out, stdout_lines=out.splitlines(), stderr=err)

    def _get_first_available_file(self, faf, of=None, searchdir='files'):

        display.deprecated("first_available_file, use with_first_found or lookup('first_found',...) instead")
        for fn in faf:
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

    def _get_diff_data(self, destination, source, task_vars, source_file=True):

        diff = {}
        display.debug("Going to peek to see if file has changed permissions")
        peek_result = self._execute_module(module_name='file', module_args=dict(path=destination, diff_peek=True), task_vars=task_vars, persist_files=True)

        if not('failed' in peek_result and peek_result['failed']) or peek_result.get('rc', 0) == 0:

            if peek_result['state'] == 'absent':
                diff['before'] = ''
            elif peek_result['appears_binary']:
                diff['dst_binary'] = 1
            elif C.MAX_FILE_SIZE_FOR_DIFF > 0 and peek_result['size'] > C.MAX_FILE_SIZE_FOR_DIFF:
                diff['dst_larger'] = C.MAX_FILE_SIZE_FOR_DIFF
            else:
                display.debug("Slurping the file %s" % source)
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
                st = os.stat(source)
                if C.MAX_FILE_SIZE_FOR_DIFF > 0 and st[stat.ST_SIZE] > C.MAX_FILE_SIZE_FOR_DIFF:
                    diff['src_larger'] = C.MAX_FILE_SIZE_FOR_DIFF
                else:
                    display.debug("Reading local copy of the file %s" % source)
                    try:
                        src = open(source)
                        src_contents = src.read()
                    except Exception as e:
                        raise AnsibleError("Unexpected error while reading source (%s) for diff: %s " % (source, str(e)))

                    if "\x00" in src_contents:
                        diff['src_binary'] = 1
                    else:
                        diff['after_header'] = source
                        diff['after'] = src_contents
            else:
                display.debug("source of file passed in")
                diff['after_header'] = 'dynamically generated'
                diff['after'] = source

        if self._play_context.no_log:
            if 'before' in diff:
                diff["before"] = ""
            if 'after' in diff:
                diff["after"] = " [[ Diff output has been hidden because 'no_log: true' was specified for this result ]]"

        return diff
