# Copyright: (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import base64
import os
import stat
from abc import ABCMeta, abstractmethod

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleActionSkip, AnsibleActionFail
from ansible.module_utils._text import to_text
from ansible.module_utils.six import string_types, with_metaclass
from ansible.release import __version__
from ansible.vars.clean import remove_internal_keys


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

    # A set of valid arguments
    _VALID_ARGS = frozenset([])

    def __init__(self, task, connection, play_context, loader, templar, shared_loader_obj):
        self._task = task
        self._connection = connection
        self._target = connection.get_target()
        self._play_context = play_context
        self._loader = loader
        self._templar = templar
        self._shared_loader_obj = shared_loader_obj
        self._cleanup_remote_tmp = False

        self._supports_check_mode = True
        self._supports_async = False

        # Backwards compat: self._display isn't really needed, just import the global display and use that.
        self._display = display

    @abstractmethod
    def run(self, tmp=None, task_vars=None):
        """ Action Plugins should implement this method to perform their
        tasks.  Everything else in this base class is a helper method for the
        action plugin to do that.

        :kwarg tmp: Deprecated parameter.  This is no longer used.  An action plugin that calls
            another one and wants to use the same remote tmp for both should set
            self._connection._shell.tmpdir rather than this parameter.
        :kwarg task_vars: The variables (host vars, group vars, config vars,
            etc) associated with this task.
        :returns: dictionary of results from the module

        Implementors of action modules may find the following variables especially useful:

        * Module parameters.  These are stored in self._task.args
        """

        result = {}

        if tmp is not None:
            result['warning'] = ['ActionModule.run() no longer honors the tmp parameter. Action'
                                 ' plugins should set self._connection._shell.tmpdir to share'
                                 ' the tmpdir']
        del tmp

        if self._task.async_val and not self._supports_async:
            raise AnsibleActionFail('async is not supported for this task.')
        elif self._play_context.check_mode and not self._supports_check_mode:
            raise AnsibleActionSkip('check mode is not supported for this task.')
        elif self._task.async_val and self._play_context.check_mode:
            raise AnsibleActionFail('check mode and async cannot be used on same task.')

        # Error if invalid argument is passed
        if self._VALID_ARGS:
            task_opts = frozenset(self._task.args.keys())
            bad_opts = task_opts.difference(self._VALID_ARGS)
            if bad_opts:
                raise AnsibleActionFail('Invalid options for %s: %s' % (self._task.action, ','.join(list(bad_opts))))

        if self._connection._shell.tmpdir is None and self._early_needs_tmp_path():
            self._make_tmp_path()

        return result

    def _remote_file_exists(self, path):
        # Forward to target plugin.
        return self._target.exists(path)

    def _compute_environment_string(self, raw_environment_out=None):
        '''
        Builds the environment string to be used when executing the remote task.
        '''

        final_environment = dict()
        if self._task.environment is not None:
            environments = self._task.environment
            if not isinstance(environments, list):
                environments = [environments]

            # The order of environments matters to make sure we merge
            # in the parent's values first so those in the block then
            # task 'win' in precedence
            for environment in environments:
                if environment is None or len(environment) == 0:
                    continue
                temp_environment = self._templar.template(environment)
                if not isinstance(temp_environment, dict):
                    raise AnsibleError("environment must be a dictionary, received %s (%s)" % (temp_environment, type(temp_environment)))
                # very deliberately using update here instead of combine_vars, as
                # these environment settings should not need to merge sub-dicts
                final_environment.update(temp_environment)

        if len(final_environment) > 0:
            final_environment = self._templar.template(final_environment)

        if isinstance(raw_environment_out, dict):
            raw_environment_out.clear()
            raw_environment_out.update(final_environment)

        return self._connection._shell.env_prefix(**final_environment)

    def _early_needs_tmp_path(self):
        '''
        Determines if a tmp path should be created before the action is executed.
        '''

        return getattr(self, 'TRANSFERS_FILES', False)

    def _get_admin_users(self):
        # Forward to connection plugin.
        return self._connection.get_admin_users()

    def is_become_unprivileged(self):
        # Forward to connection plugin.
        return self._connection.is_become_unprivileged()

    def _make_tmp_path(self, remote_user=None):
        '''
        Create and return a temporary path on a remote box.
        '''
        self._connection._shell.tmpdir = self._target.make_tmp_path()
        self._should_cleanup_remote_tmp = True
        return self._connection._shell.tmpdir

    def _should_remove_tmp_path(self, tmp_path):
        '''Determine if temporary path should be deleted or kept by user request/config'''
        return tmp_path and self._cleanup_remote_tmp and not C.DEFAULT_KEEP_REMOTE_FILES and "-tmp-" in tmp_path

    def _remove_tmp_path(self, tmp_path):
        '''Remove a temporary path we created. '''

        if tmp_path is None and self._connection._shell.tmpdir:
            tmp_path = self._connection._shell.tmpdir

        if self._should_remove_tmp_path(tmp_path) and self._target.remove(tmp_path):
            self._connection._shell.tmpdir = None

    def _transfer_file(self, local_path, remote_path):
        self._connection.put_file(local_path, remote_path)
        return remote_path

    def _fixup_perms2(self, remote_paths, remote_user=None, execute=True):
        '''
        Ensure a list of paths created on the target are readable by `remote_user`.
        '''
        if remote_user is None:
            remote_user = self._play_context.remote_user

        self._target.ensure_readable(remote_paths, remote_user, execute)
        return remote_paths

    def _execute_remote_stat(self, path, all_vars, follow, tmp=None, checksum=True):
        '''
        Get information from remote file.
        '''
        if tmp is not None:
            display.warning('_execute_remote_stat no longer honors the tmp parameter. Action'
                            ' plugins should set self._connection._shell.tmpdir to share'
                            ' the tmpdir')
        del tmp  # No longer used

        module_args = dict(
            path=path,
            follow=follow,
            get_checksum=checksum,
            checksum_algo='sha1',
        )
        mystat = self._execute_module(module_name='stat', module_args=module_args, task_vars=all_vars,
                                      wrap_async=False)

        if mystat.get('failed'):
            msg = mystat.get('module_stderr')
            if not msg:
                msg = mystat.get('module_stdout')
            if not msg:
                msg = mystat.get('msg')
            raise AnsibleError('Failed to get information on remote file (%s): %s' % (path, msg))

        if not mystat['stat']['exists']:
            # empty might be matched, 1 should never match, also backwards compatible
            mystat['stat']['checksum'] = '1'

        # happens sometimes when it is a dir and not on bsd
        if 'checksum' not in mystat['stat']:
            mystat['stat']['checksum'] = ''
        elif not isinstance(mystat['stat']['checksum'], string_types):
            raise AnsibleError("Invalid checksum returned by stat: expected a string type but got %s" % type(mystat['stat']['checksum']))

        return mystat['stat']

    def _remote_checksum(self, path, all_vars, follow=False):
        '''
        Produces a remote checksum given a path,
        Returns a number 0-4 for specific errors instead of checksum, also ensures it is different
        0 = unknown error
        1 = file does not exist, this might not be an error
        2 = permissions issue
        3 = its a directory, not a file
        4 = stat module failed, likely due to not finding python
        5 = appropriate json module not found
        '''
        x = "0"  # unknown error has occurred
        try:
            remote_stat = self._execute_remote_stat(path, all_vars, follow=follow)
            if remote_stat['exists'] and remote_stat['isdir']:
                x = "3"  # its a directory not a file
            else:
                x = remote_stat['checksum']  # if 1, file is missing
        except AnsibleError as e:
            errormsg = to_text(e)
            if errormsg.endswith(u'Permission denied'):
                x = "2"  # cannot read file
            elif errormsg.endswith(u'MODULE FAILURE'):
                x = "4"  # python not found or module uncaught exception
            elif 'json' in errormsg:
                x = "5"  # json module needed
        finally:
            return x  # pylint: disable=lost-exception

    def _remote_expand_user(self, path, sudoable=True, pathsep=None):
        ''' takes a remote path and performs tilde/$HOME expansion on the remote host '''
        return self._target.expand_user(path, sudoable=sudoable)

    def _update_module_args(self, module_name, module_args, task_vars):

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
        module_args['_ansible_verbosity'] = display.verbosity

        # give the module information about the ansible version
        module_args['_ansible_version'] = __version__

        # give the module information about its name
        module_args['_ansible_module_name'] = module_name

        # set the syslog facility to be used in the module
        module_args['_ansible_syslog_facility'] = task_vars.get('ansible_syslog_facility', C.DEFAULT_SYSLOG_FACILITY)

        # let module know about filesystems that selinux treats specially
        module_args['_ansible_selinux_special_fs'] = C.DEFAULT_SELINUX_SPECIAL_FS

        # give the module the socket for persistent connections
        module_args['_ansible_socket'] = getattr(self._connection, 'socket_path')
        if not module_args['_ansible_socket']:
            module_args['_ansible_socket'] = task_vars.get('ansible_socket')

        # make sure all commands use the designated shell executable
        module_args['_ansible_shell_executable'] = self._play_context.executable

        # make sure modules are aware if they need to keep the remote files
        module_args['_ansible_keep_remote_files'] = C.DEFAULT_KEEP_REMOTE_FILES

        # make sure all commands use the designated temporary directory if created
        if self._connection.is_become_unprivileged():  # force fallback on remote_tmp as user cannot normally write to dir
            module_args['_ansible_tmpdir'] = None
        else:
            module_args['_ansible_tmpdir'] = self._connection._shell.tmpdir

        # make sure the remote_tmp value is sent through in case modules needs to create their own
        try:
            module_args['_ansible_remote_tmp'] = self._connection._shell.get_option('remote_tmp')
        except KeyError:
            # here for 3rd party shell plugin compatibility in case they do not define the remote_tmp option
            module_args['_ansible_remote_tmp'] = '~/.ansible/tmp'

    def _update_connection_options(self, options, variables=None):
        ''' ensures connections have the appropriate information '''
        update = {}

        if getattr(self.connection, 'glob_option_vars', False):
            # if the connection allows for it, pass any variables matching it.
            if variables is not None:
                for varname in variables:
                    if varname.match('ansible_%s_' % self.connection._load_name):
                        update[varname] = variables[varname]

        # always override existing with options
        update.update(options)
        self.connection.set_options(update)

    def _execute_module(self, module_name=None, module_args=None, tmp=None, task_vars=None, persist_files=False, delete_remote_tmp=None, wrap_async=False):
        '''
        Transfer and run a module along with its arguments.
        '''
        if tmp is not None:
            display.warning('_execute_module no longer honors the tmp parameter. Action plugins'
                            ' should set self._connection._shell.tmpdir to share the tmpdir')
        if delete_remote_tmp is not None:
            display.warning('_execute_module no longer honors the delete_remote_tmp parameter.'
                            ' Action plugins should check self._connection._shell.tmpdir to'
                            ' see if a tmpdir existed before they were called to determine'
                            ' if they are responsible for removing it.')

        if task_vars is None:
            task_vars = dict()
        if module_name is None:
            module_name = self._task.action
        if module_args is None:
            module_args = self._task.args

        self._update_module_args(module_name, module_args, task_vars)

        # parse the main result
        data = self._target.execute_module(
            module_name=module_name,
            module_args=module_args,
            task_vars=task_vars,
            wrap_async=wrap_async,
            async_limit=self._task.async_val
        )

        # NOTE: INTERNAL KEYS ONLY ACCESSIBLE HERE
        # get internal info before cleaning
        if data.pop("_ansible_suppress_tmpdir_delete", False):
            self._cleanup_remote_tmp = False

        if wrap_async:
            # FIXME: for backwards compat, figure out if still makes sense
            data['changed'] = True

        # remove internal keys
        remove_internal_keys(data)

        # pre-split stdout/stderr into lines if needed
        if 'stdout' in data and 'stdout_lines' not in data:
            # if the value is 'False', a default won't catch it.
            txt = data.get('stdout', None) or u''
            data['stdout_lines'] = txt.splitlines()
        if 'stderr' in data and 'stderr_lines' not in data:
            # if the value is 'False', a default won't catch it.
            txt = data.get('stderr', None) or u''
            data['stderr_lines'] = txt.splitlines()

        display.debug("done with _execute_module (%s, %s)" % (module_name, module_args))
        return data

    def _low_level_execute_command(self, cmd, sudoable=True, in_data=None, executable=None, encoding_errors='surrogate_then_replace', chdir=None):
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
        :kwarg chdir: cd into this directory before executing the command.
        :returns:
            Dict with keys:

            * `rc`: return code
            * `stdout`: Decoded standard output
            * `stderr`: Decoded standard error
            * `stdout_lines`: Decoded standard output split on line endings
            * `stderr_lines`: Decoded standard error split on line endings
        '''
        if encoding_errors != 'surrogate_then_replace':
            display.warning('_low_level_execute_command no longer honors the encoding_errors parameter')
        result = self._target.execute_command(
            cmd=cmd,
            sudoable=sudoable,
            in_data=in_data,
            executable=executable,
            chdir=chdir
        )
        result['stdout_lines'] = result['stdout'].splitlines()
        result['stderr_lines'] = result['stderr'].splitlines()
        return result

    def _get_diff_data(self, destination, source, task_vars, source_file=True):

        diff = {}
        display.debug("Going to peek to see if file has changed permissions")
        peek_result = self._execute_module(module_name='file', module_args=dict(path=destination, _diff_peek=True), task_vars=task_vars, persist_files=True)

        if not peek_result.get('failed', False) or peek_result.get('rc', 0) == 0:

            if peek_result.get('state') == 'absent':
                diff['before'] = ''
            elif peek_result.get('appears_binary'):
                diff['dst_binary'] = 1
            elif peek_result.get('size') and C.MAX_FILE_SIZE_FOR_DIFF > 0 and peek_result['size'] > C.MAX_FILE_SIZE_FOR_DIFF:
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
                        with open(source, 'rb') as src:
                            src_contents = src.read()
                    except Exception as e:
                        raise AnsibleError("Unexpected error while reading source (%s) for diff: %s " % (source, str(e)))

                    if b"\x00" in src_contents:
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
                diff["after"] = " [[ Diff output has been hidden because 'no_log: true' was specified for this result ]]\n"

        return diff

    def _find_needle(self, dirname, needle):
        '''
            find a needle in haystack of paths, optionally using 'dirname' as a subdir.
            This will build the ordered list of paths to search and pass them to dwim
            to get back the first existing file found.
        '''

        # dwim already deals with playbook basedirs
        path_stack = self._task.get_search_path()

        # if missing it will return a file not found exception
        return self._loader.path_dwim_relative_stack(path_stack, dirname, needle)
