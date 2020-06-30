# coding: utf-8
# Copyright: (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import base64
import json
import os
import random
import re
import stat
import tempfile
import time
from abc import ABCMeta, abstractmethod

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleConnectionFailure, AnsibleActionSkip, AnsibleActionFail
from ansible.executor.module_common import modify_module
from ansible.executor.interpreter_discovery import discover_interpreter, InterpreterDiscoveryRequiredError
from ansible.module_utils.common._collections_compat import Sequence
from ansible.module_utils.json_utils import _filter_non_json_lines
from ansible.module_utils.six import binary_type, string_types, text_type, iteritems, with_metaclass
from ansible.module_utils.six.moves import shlex_quote
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.parsing.utils.jsonify import jsonify
from ansible.release import __version__
from ansible.utils.display import Display
from ansible.utils.unsafe_proxy import wrap_var, AnsibleUnsafeText
from ansible.vars.clean import remove_internal_keys

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
        self._play_context = play_context
        self._loader = loader
        self._templar = templar
        self._shared_loader_obj = shared_loader_obj
        self._cleanup_remote_tmp = False

        self._supports_check_mode = True
        self._supports_async = False

        # interpreter discovery state
        self._discovered_interpreter_key = None
        self._discovered_interpreter = False
        self._discovery_deprecation_warnings = []
        self._discovery_warnings = []

        # Backwards compat: self._display isn't really needed, just import the global display and use that.
        self._display = display

        self._used_interpreter = None

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

    def cleanup(self, force=False):
        """Method to perform a clean up at the end of an action plugin execution

        By default this is designed to clean up the shell tmpdir, and is toggled based on whether
        async is in use

        Action plugins may override this if they deem necessary, but should still call this method
        via super
        """
        if force or not self._task.async_val:
            self._remove_tmp_path(self._connection._shell.tmpdir)

    def get_plugin_option(self, plugin, option, default=None):
        """Helper to get an option from a plugin without having to use
        the try/except dance everywhere to set a default
        """
        try:
            return plugin.get_option(option)
        except (AttributeError, KeyError):
            return default

    def get_become_option(self, option, default=None):
        return self.get_plugin_option(self._connection.become, option, default=default)

    def get_connection_option(self, option, default=None):
        return self.get_plugin_option(self._connection, option, default=default)

    def get_shell_option(self, option, default=None):
        return self.get_plugin_option(self._connection._shell, option, default=default)

    def _remote_file_exists(self, path):
        cmd = self._connection._shell.exists(path)
        result = self._low_level_execute_command(cmd=cmd, sudoable=True)
        if result['rc'] == 0:
            return True
        return False

    def _configure_module(self, module_name, module_args, task_vars):
        '''
        Handles the loading and templating of the module code through the
        modify_module() function.
        '''
        if self._task.delegate_to:
            use_vars = task_vars.get('ansible_delegated_vars')[self._task.delegate_to]
        else:
            use_vars = task_vars

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

            module_path = self._shared_loader_obj.module_loader.find_plugin(module_name, mod_type, collection_list=self._task.collections)
            if module_path:
                break
        else:  # This is a for-else: http://bit.ly/1ElPkyg
            raise AnsibleError("The module %s was not found in configured module paths" % (module_name))

        # insert shared code and arguments into the module
        final_environment = dict()
        self._compute_environment_string(final_environment)

        become_kwargs = {}
        if self._connection.become:
            become_kwargs['become'] = True
            become_kwargs['become_method'] = self._connection.become.name
            become_kwargs['become_user'] = self._connection.become.get_option('become_user',
                                                                              playcontext=self._play_context)
            become_kwargs['become_password'] = self._connection.become.get_option('become_pass',
                                                                                  playcontext=self._play_context)
            become_kwargs['become_flags'] = self._connection.become.get_option('become_flags',
                                                                               playcontext=self._play_context)

        # modify_module will exit early if interpreter discovery is required; re-run after if necessary
        for dummy in (1, 2):
            try:
                (module_data, module_style, module_shebang) = modify_module(module_name, module_path, module_args, self._templar,
                                                                            task_vars=use_vars,
                                                                            module_compression=self._play_context.module_compression,
                                                                            async_timeout=self._task.async_val,
                                                                            environment=final_environment,
                                                                            **become_kwargs)
                break
            except InterpreterDiscoveryRequiredError as idre:
                self._discovered_interpreter = AnsibleUnsafeText(discover_interpreter(
                    action=self,
                    interpreter_name=idre.interpreter_name,
                    discovery_mode=idre.discovery_mode,
                    task_vars=use_vars))

                # update the local task_vars with the discovered interpreter (which might be None);
                # we'll propagate back to the controller in the task result
                discovered_key = 'discovered_interpreter_%s' % idre.interpreter_name

                # update the local vars copy for the retry
                use_vars['ansible_facts'][discovered_key] = self._discovered_interpreter

                # TODO: this condition prevents 'wrong host' from being updated
                # but in future we would want to be able to update 'delegated host facts'
                # irrespective of task settings
                if not self._task.delegate_to or self._task.delegate_facts:
                    # store in local task_vars facts collection for the retry and any other usages in this worker
                    task_vars['ansible_facts'][discovered_key] = self._discovered_interpreter
                    # preserve this so _execute_module can propagate back to controller as a fact
                    self._discovered_interpreter_key = discovered_key
                else:
                    task_vars['ansible_delegated_vars'][self._task.delegate_to]['ansible_facts'][discovered_key] = self._discovered_interpreter

        return (module_style, module_shebang, module_data, module_path)

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

    def _is_pipelining_enabled(self, module_style, wrap_async=False):
        '''
        Determines if we are required and can do pipelining
        '''

        # any of these require a true
        for condition in [
            self._connection.has_pipelining,
            self._play_context.pipelining or self._connection.always_pipeline_modules,  # pipelining enabled for play or connection requires it (eg winrm)
            module_style == "new",                     # old style modules do not support pipelining
            not C.DEFAULT_KEEP_REMOTE_FILES,           # user wants remote files
            not wrap_async or self._connection.always_pipeline_modules,  # async does not normally support pipelining unless it does (eg winrm)
            (self._connection.become.name if self._connection.become else '') != 'su',  # su does not work with pipelining,
            # FIXME: we might need to make become_method exclusion a configurable list
        ]:
            if not condition:
                return False

        return True

    def _get_admin_users(self):
        '''
        Returns a list of admin users that are configured for the current shell
        plugin
        '''

        return self.get_shell_option('admin_users', ['root'])

    def _get_remote_user(self):
        ''' consistently get the 'remote_user' for the action plugin '''
        # TODO: use 'current user running ansible' as fallback when moving away from play_context
        # pwd.getpwuid(os.getuid()).pw_name
        remote_user = None
        try:
            remote_user = self._connection.get_option('remote_user')
        except KeyError:
            # plugin does not have remote_user option, fallback to default and/play_context
            remote_user = getattr(self._connection, 'default_user', None) or self._play_context.remote_user
        except AttributeError:
            # plugin does not use config system, fallback to old play_context
            remote_user = self._play_context.remote_user
        return remote_user

    def _is_become_unprivileged(self):
        '''
        The user is not the same as the connection user and is not part of the
        shell configured admin users
        '''
        # if we don't use become then we know we aren't switching to a
        # different unprivileged user
        if not self._connection.become:
            return False

        # if we use become and the user is not an admin (or same user) then
        # we need to return become_unprivileged as True
        admin_users = self._get_admin_users()
        remote_user = self._get_remote_user()
        become_user = self.get_become_option('become_user')
        return bool(become_user and become_user not in admin_users + [remote_user])

    def _make_tmp_path(self, remote_user=None):
        '''
        Create and return a temporary path on a remote box.
        '''

        # Network connection plugins (network_cli, netconf, etc.) execute on the controller, rather than the remote host.
        # As such, we want to avoid using remote_user for paths  as remote_user may not line up with the local user
        # This is a hack and should be solved by more intelligent handling of remote_tmp in 2.7
        if getattr(self._connection, '_remote_is_local', False):
            tmpdir = C.DEFAULT_LOCAL_TMP
        else:
            # NOTE: shell plugins should populate this setting anyways, but they dont do remote expansion, which
            # we need for 'non posix' systems like cloud-init and solaris
            tmpdir = self._remote_expand_user(self.get_shell_option('remote_tmp', default='~/.ansible/tmp'), sudoable=False)

        become_unprivileged = self._is_become_unprivileged()
        basefile = self._connection._shell._generate_temp_dir_name()
        cmd = self._connection._shell.mkdtemp(basefile=basefile, system=become_unprivileged, tmpdir=tmpdir)
        result = self._low_level_execute_command(cmd, sudoable=False)

        # error handling on this seems a little aggressive?
        if result['rc'] != 0:
            if result['rc'] == 5:
                output = 'Authentication failure.'
            elif result['rc'] == 255 and self._connection.transport in ('ssh',):

                if self._play_context.verbosity > 3:
                    output = u'SSH encountered an unknown error. The output was:\n%s%s' % (result['stdout'], result['stderr'])
                else:
                    output = (u'SSH encountered an unknown error during the connection. '
                              'We recommend you re-run the command using -vvvv, which will enable SSH debugging output to help diagnose the issue')

            elif u'No space left on device' in result['stderr']:
                output = result['stderr']
            else:
                output = ('Failed to create temporary directory.'
                          'In some cases, you may have been able to authenticate and did not have permissions on the target directory. '
                          'Consider changing the remote tmp path in ansible.cfg to a path rooted in "/tmp", for more error information use -vvv. '
                          'Failed command was: %s, exited with result %d' % (cmd, result['rc']))
            if 'stdout' in result and result['stdout'] != u'':
                output = output + u", stdout output: %s" % result['stdout']
            if self._play_context.verbosity > 3 and 'stderr' in result and result['stderr'] != u'':
                output += u", stderr output: %s" % result['stderr']
            raise AnsibleConnectionFailure(output)
        else:
            self._cleanup_remote_tmp = True

        try:
            stdout_parts = result['stdout'].strip().split('%s=' % basefile, 1)
            rc = self._connection._shell.join_path(stdout_parts[-1], u'').splitlines()[-1]
        except IndexError:
            # stdout was empty or just space, set to / to trigger error in next if
            rc = '/'

        # Catch failure conditions, files should never be
        # written to locations in /.
        if rc == '/':
            raise AnsibleError('failed to resolve remote temporary directory from %s: `%s` returned empty string' % (basefile, cmd))

        self._connection._shell.tmpdir = rc

        return rc

    def _should_remove_tmp_path(self, tmp_path):
        '''Determine if temporary path should be deleted or kept by user request/config'''
        return tmp_path and self._cleanup_remote_tmp and not C.DEFAULT_KEEP_REMOTE_FILES and "-tmp-" in tmp_path

    def _remove_tmp_path(self, tmp_path):
        '''Remove a temporary path we created. '''

        if tmp_path is None and self._connection._shell.tmpdir:
            tmp_path = self._connection._shell.tmpdir

        if self._should_remove_tmp_path(tmp_path):
            cmd = self._connection._shell.remove(tmp_path, recurse=True)
            # If we have gotten here we have a working ssh configuration.
            # If ssh breaks we could leave tmp directories out on the remote system.
            tmp_rm_res = self._low_level_execute_command(cmd, sudoable=False)

            if tmp_rm_res.get('rc', 0) != 0:
                display.warning('Error deleting remote temporary files (rc: %s, stderr: %s})'
                                % (tmp_rm_res.get('rc'), tmp_rm_res.get('stderr', 'No error string available.')))
            else:
                self._connection._shell.tmpdir = None

    def _transfer_file(self, local_path, remote_path):
        """
        Copy a file from the controller to a remote path

        :arg local_path: Path on controller to transfer
        :arg remote_path: Path on the remote system to transfer into

        .. warning::
            * When you use this function you likely want to use use fixup_perms2() on the
              remote_path to make sure that the remote file is readable when the user becomes
              a non-privileged user.
            * If you use fixup_perms2() on the file and copy or move the file into place, you will
              need to then remove filesystem acls on the file once it has been copied into place by
              the module.  See how the copy module implements this for help.
        """
        self._connection.put_file(local_path, remote_path)
        return remote_path

    def _transfer_data(self, remote_path, data):
        '''
        Copies the module data out to the temporary module path.
        '''

        if isinstance(data, dict):
            data = jsonify(data)

        afd, afile = tempfile.mkstemp(dir=C.DEFAULT_LOCAL_TMP)
        afo = os.fdopen(afd, 'wb')
        try:
            data = to_bytes(data, errors='surrogate_or_strict')
            afo.write(data)
        except Exception as e:
            raise AnsibleError("failure writing module data to temporary file for transfer: %s" % to_native(e))

        afo.flush()
        afo.close()

        try:
            self._transfer_file(afile, remote_path)
        finally:
            os.unlink(afile)

        return remote_path

    def _fixup_perms2(self, remote_paths, remote_user=None, execute=True):
        """
        We need the files we upload to be readable (and sometimes executable)
        by the user being sudo'd to but we want to limit other people's access
        (because the files could contain passwords or other private
        information.  We achieve this in one of these ways:

        * If no sudo is performed or the remote_user is sudo'ing to
          themselves, we don't have to change permissions.
        * If the remote_user sudo's to a privileged user (for instance, root),
          we don't have to change permissions
        * If the remote_user sudo's to an unprivileged user then we attempt to
          grant the unprivileged user access via file system acls.
        * If granting file system acls fails we try to change the owner of the
          file with chown which only works in case the remote_user is
          privileged or the remote systems allows chown calls by unprivileged
          users (e.g. HP-UX)
        * If the chown fails we can set the file to be world readable so that
          the second unprivileged user can read the file.
          Since this could allow other users to get access to private
          information we only do this if ansible is configured with
          "allow_world_readable_tmpfiles" in the ansible.cfg
        """
        if remote_user is None:
            remote_user = self._get_remote_user()

        if getattr(self._connection._shell, "_IS_WINDOWS", False):
            # This won't work on Powershell as-is, so we'll just completely skip until
            # we have a need for it, at which point we'll have to do something different.
            return remote_paths

        if self._is_become_unprivileged():
            # Unprivileged user that's different than the ssh user.  Let's get
            # to work!

            # Try to use file system acls to make the files readable for sudo'd
            # user
            if execute:
                chmod_mode = 'rx'
                setfacl_mode = 'r-x'
            else:
                chmod_mode = 'rX'
                # NOTE: this form fails silently on freebsd.  We currently
                # never call _fixup_perms2() with execute=False but if we
                # start to we'll have to fix this.
                setfacl_mode = 'r-X'

            res = self._remote_set_user_facl(remote_paths, self.get_become_option('become_user'), setfacl_mode)
            if res['rc'] != 0:
                # File system acls failed; let's try to use chown next
                # Set executable bit first as on some systems an
                # unprivileged user can use chown
                if execute:
                    res = self._remote_chmod(remote_paths, 'u+x')
                    if res['rc'] != 0:
                        raise AnsibleError('Failed to set file mode on remote temporary files (rc: {0}, err: {1})'.format(res['rc'], to_native(res['stderr'])))

                res = self._remote_chown(remote_paths, self.get_become_option('become_user'))
                if res['rc'] != 0 and remote_user in self._get_admin_users():
                    # chown failed even if remote_user is administrator/root
                    raise AnsibleError('Failed to change ownership of the temporary files Ansible needs to create despite connecting as a privileged user. '
                                       'Unprivileged become user would be unable to read the file.')
                elif res['rc'] != 0:
                    if C.ALLOW_WORLD_READABLE_TMPFILES:
                        # chown and fs acls failed -- do things this insecure
                        # way only if the user opted in in the config file
                        display.warning('Using world-readable permissions for temporary files Ansible needs to create when becoming an unprivileged user. '
                                        'This may be insecure. For information on securing this, see '
                                        'https://docs.ansible.com/ansible/become.html#becoming-an-unprivileged-user')
                        res = self._remote_chmod(remote_paths, 'a+%s' % chmod_mode)
                        if res['rc'] != 0:
                            raise AnsibleError('Failed to set file mode on remote files (rc: {0}, err: {1})'.format(res['rc'], to_native(res['stderr'])))
                    else:
                        raise AnsibleError('Failed to set permissions on the temporary files Ansible needs to create when becoming an unprivileged user '
                                           '(rc: %s, err: %s}). For information on working around this, see '
                                           'https://docs.ansible.com/ansible/become.html#becoming-an-unprivileged-user'
                                           % (res['rc'], to_native(res['stderr'])))
        elif execute:
            # Can't depend on the file being transferred with execute permissions.
            # Only need user perms because no become was used here
            res = self._remote_chmod(remote_paths, 'u+x')
            if res['rc'] != 0:
                raise AnsibleError('Failed to set execute bit on remote files (rc: {0}, err: {1})'.format(res['rc'], to_native(res['stderr'])))

        return remote_paths

    def _remote_chmod(self, paths, mode, sudoable=False):
        '''
        Issue a remote chmod command
        '''
        cmd = self._connection._shell.chmod(paths, mode)
        res = self._low_level_execute_command(cmd, sudoable=sudoable)
        return res

    def _remote_chown(self, paths, user, sudoable=False):
        '''
        Issue a remote chown command
        '''
        cmd = self._connection._shell.chown(paths, user)
        res = self._low_level_execute_command(cmd, sudoable=sudoable)
        return res

    def _remote_set_user_facl(self, paths, user, mode, sudoable=False):
        '''
        Issue a remote call to setfacl
        '''
        cmd = self._connection._shell.set_user_facl(paths, user, mode)
        res = self._low_level_execute_command(cmd, sudoable=sudoable)
        return res

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
            checksum_algorithm='sha1',
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

        # We only expand ~/path and ~username/path
        if not path.startswith('~'):
            return path

        # Per Jborean, we don't have to worry about Windows as we don't have a notion of user's home
        # dir there.
        split_path = path.split(os.path.sep, 1)
        expand_path = split_path[0]

        if expand_path == '~':
            # Network connection plugins (network_cli, netconf, etc.) execute on the controller, rather than the remote host.
            # As such, we want to avoid using remote_user for paths  as remote_user may not line up with the local user
            # This is a hack and should be solved by more intelligent handling of remote_tmp in 2.7
            become_user = self.get_become_option('become_user')
            if getattr(self._connection, '_remote_is_local', False):
                pass
            elif sudoable and self._connection.become and become_user:
                expand_path = '~%s' % become_user
            else:
                # use remote user instead, if none set default to current user
                expand_path = '~%s' % (self._get_remote_user() or '')

        # use shell to construct appropriate command and execute
        cmd = self._connection._shell.expand_user(expand_path)
        data = self._low_level_execute_command(cmd, sudoable=False)

        try:
            initial_fragment = data['stdout'].strip().splitlines()[-1]
        except IndexError:
            initial_fragment = None

        if not initial_fragment:
            # Something went wrong trying to expand the path remotely. Try using pwd, if not, return
            # the original string
            cmd = self._connection._shell.pwd()
            pwd = self._low_level_execute_command(cmd, sudoable=False).get('stdout', '').strip()
            if pwd:
                expanded = pwd
            else:
                expanded = path

        elif len(split_path) > 1:
            expanded = self._connection._shell.join_path(initial_fragment, *split_path[1:])
        else:
            expanded = initial_fragment

        if '..' in os.path.dirname(expanded).split('/'):
            raise AnsibleError("'%s' returned an invalid relative home directory path containing '..'" % self._play_context.remote_addr)

        return expanded

    def _strip_success_message(self, data):
        '''
        Removes the BECOME-SUCCESS message from the data.
        '''
        if data.strip().startswith('BECOME-SUCCESS-'):
            data = re.sub(r'^((\r)?\n)?BECOME-SUCCESS.*(\r)?\n', '', data)
        return data

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

        # what to do when parameter values are converted to strings
        module_args['_ansible_string_conversion_action'] = C.STRING_CONVERSION_ACTION

        # give the module the socket for persistent connections
        module_args['_ansible_socket'] = getattr(self._connection, 'socket_path')
        if not module_args['_ansible_socket']:
            module_args['_ansible_socket'] = task_vars.get('ansible_socket')

        # make sure all commands use the designated shell executable
        module_args['_ansible_shell_executable'] = self._play_context.executable

        # make sure modules are aware if they need to keep the remote files
        module_args['_ansible_keep_remote_files'] = C.DEFAULT_KEEP_REMOTE_FILES

        # make sure all commands use the designated temporary directory if created
        if self._is_become_unprivileged():  # force fallback on remote_tmp as user cannot normally write to dir
            module_args['_ansible_tmpdir'] = None
        else:
            module_args['_ansible_tmpdir'] = self._connection._shell.tmpdir

        # make sure the remote_tmp value is sent through in case modules needs to create their own
        module_args['_ansible_remote_tmp'] = self.get_shell_option('remote_tmp', default='~/.ansible/tmp')

    def _execute_module(self, module_name=None, module_args=None, tmp=None, task_vars=None, persist_files=False, delete_remote_tmp=None, wrap_async=False):
        '''
        Transfer and run a module along with its arguments.
        '''
        if tmp is not None:
            display.warning('_execute_module no longer honors the tmp parameter. Action plugins'
                            ' should set self._connection._shell.tmpdir to share the tmpdir')
        del tmp  # No longer used
        if delete_remote_tmp is not None:
            display.warning('_execute_module no longer honors the delete_remote_tmp parameter.'
                            ' Action plugins should check self._connection._shell.tmpdir to'
                            ' see if a tmpdir existed before they were called to determine'
                            ' if they are responsible for removing it.')
        del delete_remote_tmp  # No longer used

        tmpdir = self._connection._shell.tmpdir

        # We set the module_style to new here so the remote_tmp is created
        # before the module args are built if remote_tmp is needed (async).
        # If the module_style turns out to not be new and we didn't create the
        # remote tmp here, it will still be created. This must be done before
        # calling self._update_module_args() so the module wrapper has the
        # correct remote_tmp value set
        if not self._is_pipelining_enabled("new", wrap_async) and tmpdir is None:
            self._make_tmp_path()
            tmpdir = self._connection._shell.tmpdir

        if task_vars is None:
            task_vars = dict()

        # if a module name was not specified for this execution, use the action from the task
        if module_name is None:
            module_name = self._task.action
        if module_args is None:
            module_args = self._task.args

        self._update_module_args(module_name, module_args, task_vars)

        # FIXME: convert async_wrapper.py to not rely on environment variables
        # make sure we get the right async_dir variable, backwards compatibility
        # means we need to lookup the env value ANSIBLE_ASYNC_DIR first
        remove_async_dir = None
        if wrap_async or self._task.async_val:
            env_async_dir = [e for e in self._task.environment if
                             "ANSIBLE_ASYNC_DIR" in e]
            if len(env_async_dir) > 0:
                msg = "Setting the async dir from the environment keyword " \
                      "ANSIBLE_ASYNC_DIR is deprecated. Set the async_dir " \
                      "shell option instead"
                self._display.deprecated(msg, "2.12")
            else:
                # ANSIBLE_ASYNC_DIR is not set on the task, we get the value
                # from the shell option and temporarily add to the environment
                # list for async_wrapper to pick up
                async_dir = self.get_shell_option('async_dir', default="~/.ansible_async")
                remove_async_dir = len(self._task.environment)
                self._task.environment.append({"ANSIBLE_ASYNC_DIR": async_dir})

        # FUTURE: refactor this along with module build process to better encapsulate "smart wrapper" functionality
        (module_style, shebang, module_data, module_path) = self._configure_module(module_name=module_name, module_args=module_args, task_vars=task_vars)
        display.vvv("Using module file %s" % module_path)
        if not shebang and module_style != 'binary':
            raise AnsibleError("module (%s) is missing interpreter line" % module_name)

        self._used_interpreter = shebang
        remote_module_path = None

        if not self._is_pipelining_enabled(module_style, wrap_async):
            # we might need remote tmp dir
            if tmpdir is None:
                self._make_tmp_path()
                tmpdir = self._connection._shell.tmpdir

            remote_module_filename = self._connection._shell.get_remote_filename(module_path)
            remote_module_path = self._connection._shell.join_path(tmpdir, 'AnsiballZ_%s' % remote_module_filename)

        args_file_path = None
        if module_style in ('old', 'non_native_want_json', 'binary'):
            # we'll also need a tmp file to hold our module arguments
            args_file_path = self._connection._shell.join_path(tmpdir, 'args')

        if remote_module_path or module_style != 'new':
            display.debug("transferring module to remote %s" % remote_module_path)
            if module_style == 'binary':
                self._transfer_file(module_path, remote_module_path)
            else:
                self._transfer_data(remote_module_path, module_data)
            if module_style == 'old':
                # we need to dump the module args to a k=v string in a file on
                # the remote system, which can be read and parsed by the module
                args_data = ""
                for k, v in iteritems(module_args):
                    args_data += '%s=%s ' % (k, shlex_quote(text_type(v)))
                self._transfer_data(args_file_path, args_data)
            elif module_style in ('non_native_want_json', 'binary'):
                self._transfer_data(args_file_path, json.dumps(module_args))
            display.debug("done transferring module to remote")

        environment_string = self._compute_environment_string()

        # remove the ANSIBLE_ASYNC_DIR env entry if we added a temporary one for
        # the async_wrapper task - this is so the async_status plugin doesn't
        # fire a deprecation warning when it runs after this task
        if remove_async_dir is not None:
            del self._task.environment[remove_async_dir]

        remote_files = []
        if tmpdir and remote_module_path:
            remote_files = [tmpdir, remote_module_path]

        if args_file_path:
            remote_files.append(args_file_path)

        sudoable = True
        in_data = None
        cmd = ""

        if wrap_async and not self._connection.always_pipeline_modules:
            # configure, upload, and chmod the async_wrapper module
            (async_module_style, shebang, async_module_data, async_module_path) = self._configure_module(module_name='async_wrapper', module_args=dict(),
                                                                                                         task_vars=task_vars)
            async_module_remote_filename = self._connection._shell.get_remote_filename(async_module_path)
            remote_async_module_path = self._connection._shell.join_path(tmpdir, async_module_remote_filename)
            self._transfer_data(remote_async_module_path, async_module_data)
            remote_files.append(remote_async_module_path)

            async_limit = self._task.async_val
            async_jid = str(random.randint(0, 999999999999))

            # call the interpreter for async_wrapper directly
            # this permits use of a script for an interpreter on non-Linux platforms
            # TODO: re-implement async_wrapper as a regular module to avoid this special case
            interpreter = shebang.replace('#!', '').strip()
            async_cmd = [interpreter, remote_async_module_path, async_jid, async_limit, remote_module_path]

            if environment_string:
                async_cmd.insert(0, environment_string)

            if args_file_path:
                async_cmd.append(args_file_path)
            else:
                # maintain a fixed number of positional parameters for async_wrapper
                async_cmd.append('_')

            if not self._should_remove_tmp_path(tmpdir):
                async_cmd.append("-preserve_tmp")

            cmd = " ".join(to_text(x) for x in async_cmd)

        else:

            if self._is_pipelining_enabled(module_style):
                in_data = module_data
                display.vvv("Pipelining is enabled.")
            else:
                cmd = remote_module_path

            cmd = self._connection._shell.build_module_command(environment_string, shebang, cmd, arg_path=args_file_path).strip()

        # Fix permissions of the tmpdir path and tmpdir files. This should be called after all
        # files have been transferred.
        if remote_files:
            # remove none/empty
            remote_files = [x for x in remote_files if x]
            self._fixup_perms2(remote_files, self._get_remote_user())

        # actually execute
        res = self._low_level_execute_command(cmd, sudoable=sudoable, in_data=in_data)

        # parse the main result
        data = self._parse_returned_data(res)

        # NOTE: INTERNAL KEYS ONLY ACCESSIBLE HERE
        # get internal info before cleaning
        if data.pop("_ansible_suppress_tmpdir_delete", False):
            self._cleanup_remote_tmp = False

        # NOTE: yum returns results .. but that made it 'compatible' with squashing, so we allow mappings, for now
        if 'results' in data and (not isinstance(data['results'], Sequence) or isinstance(data['results'], string_types)):
            data['ansible_module_results'] = data['results']
            del data['results']
            display.warning("Found internal 'results' key in module return, renamed to 'ansible_module_results'.")

        # remove internal keys
        remove_internal_keys(data)

        if wrap_async:
            # async_wrapper will clean up its tmpdir on its own so we want the controller side to
            # forget about it now
            self._connection._shell.tmpdir = None

            # FIXME: for backwards compat, figure out if still makes sense
            data['changed'] = True

        # pre-split stdout/stderr into lines if needed
        if 'stdout' in data and 'stdout_lines' not in data:
            # if the value is 'False', a default won't catch it.
            txt = data.get('stdout', None) or u''
            data['stdout_lines'] = txt.splitlines()
        if 'stderr' in data and 'stderr_lines' not in data:
            # if the value is 'False', a default won't catch it.
            txt = data.get('stderr', None) or u''
            data['stderr_lines'] = txt.splitlines()

        # propagate interpreter discovery results back to the controller
        if self._discovered_interpreter_key:
            if data.get('ansible_facts') is None:
                data['ansible_facts'] = {}

            data['ansible_facts'][self._discovered_interpreter_key] = self._discovered_interpreter

        if self._discovery_warnings:
            if data.get('warnings') is None:
                data['warnings'] = []
            data['warnings'].extend(self._discovery_warnings)

        if self._discovery_deprecation_warnings:
            if data.get('deprecations') is None:
                data['deprecations'] = []
            data['deprecations'].extend(self._discovery_deprecation_warnings)

        # mark the entire module results untrusted as a template right here, since the current action could
        # possibly template one of these values.
        data = wrap_var(data)

        display.debug("done with _execute_module (%s, %s)" % (module_name, module_args))
        return data

    def _parse_returned_data(self, res):
        try:
            filtered_output, warnings = _filter_non_json_lines(res.get('stdout', u''))
            for w in warnings:
                display.warning(w)

            data = json.loads(filtered_output)
            data['_ansible_parsed'] = True
        except ValueError:
            # not valid json, lets try to capture error
            data = dict(failed=True, _ansible_parsed=False)
            data['module_stdout'] = res.get('stdout', u'')
            if 'stderr' in res:
                data['module_stderr'] = res['stderr']
                if res['stderr'].startswith(u'Traceback'):
                    data['exception'] = res['stderr']

            # in some cases a traceback will arrive on stdout instead of stderr, such as when using ssh with -tt
            if 'exception' not in data and data['module_stdout'].startswith(u'Traceback'):
                data['exception'] = data['module_stdout']

            # The default
            data['msg'] = "MODULE FAILURE"

            # try to figure out if we are missing interpreter
            if self._used_interpreter is not None:
                match = re.compile('%s: (?:No such file or directory|not found)' % self._used_interpreter.lstrip('!#'))
                if match.search(data['module_stderr']) or match.search(data['module_stdout']):
                    data['msg'] = "The module failed to execute correctly, you probably need to set the interpreter."

            # always append hint
            data['msg'] += '\nSee stdout/stderr for the exact error'

            if 'rc' in res:
                data['rc'] = res['rc']
        return data

    # FIXME: move to connection base
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
        '''

        display.debug("_low_level_execute_command(): starting")
        # if not cmd:
        #     # this can happen with powershell modules when there is no analog to a Windows command (like chmod)
        #     display.debug("_low_level_execute_command(): no command, exiting")
        #     return dict(stdout='', stderr='', rc=254)

        if chdir:
            display.debug("_low_level_execute_command(): changing cwd to %s for this command" % chdir)
            cmd = self._connection._shell.append_command('cd %s' % chdir, cmd)

        # https://github.com/ansible/ansible/issues/68054
        if executable:
            self._connection._shell.executable = executable

        ruser = self._get_remote_user()
        buser = self.get_become_option('become_user')
        if (sudoable and self._connection.become and  # if sudoable and have become
                self._connection.transport != 'network_cli' and  # if not using network_cli
                (C.BECOME_ALLOW_SAME_USER or (buser != ruser or not any((ruser, buser))))):  # if we allow same user PE or users are different and either is set
            display.debug("_low_level_execute_command(): using become for this command")
            cmd = self._connection.become.build_become_command(cmd, self._connection._shell)

        if self._connection.allow_executable:
            if executable is None:
                executable = self._play_context.executable
                # mitigation for SSH race which can drop stdout (https://github.com/ansible/ansible/issues/13876)
                # only applied for the default executable to avoid interfering with the raw action
                cmd = self._connection._shell.append_command(cmd, 'sleep 0')
            if executable:
                cmd = executable + ' -c ' + shlex_quote(cmd)

        display.debug("_low_level_execute_command(): executing: %s" % (cmd,))

        # Change directory to basedir of task for command execution when connection is local
        if self._connection.transport == 'local':
            self._connection.cwd = to_bytes(self._loader.get_basedir(), errors='surrogate_or_strict')

        rc, stdout, stderr = self._connection.exec_command(cmd, in_data=in_data, sudoable=sudoable)

        # stdout and stderr may be either a file-like or a bytes object.
        # Convert either one to a text type
        if isinstance(stdout, binary_type):
            out = to_text(stdout, errors=encoding_errors)
        elif not isinstance(stdout, text_type):
            out = to_text(b''.join(stdout.readlines()), errors=encoding_errors)
        else:
            out = stdout

        if isinstance(stderr, binary_type):
            err = to_text(stderr, errors=encoding_errors)
        elif not isinstance(stderr, text_type):
            err = to_text(b''.join(stderr.readlines()), errors=encoding_errors)
        else:
            err = stderr

        if rc is None:
            rc = 0

        # be sure to remove the BECOME-SUCCESS message now
        out = self._strip_success_message(out)

        display.debug(u"_low_level_execute_command() done: rc=%d, stdout=%s, stderr=%s" % (rc, out, err))
        return dict(rc=rc, stdout=out, stdout_lines=out.splitlines(), stderr=err, stderr_lines=err.splitlines())

    def _get_diff_data(self, destination, source, task_vars, source_file=True):

        # Note: Since we do not diff the source and destination before we transform from bytes into
        # text the diff between source and destination may not be accurate.  To fix this, we'd need
        # to move the diffing from the callback plugins into here.
        #
        # Example of data which would cause trouble is src_content == b'\xff' and dest_content ==
        # b'\xfe'.  Neither of those are valid utf-8 so both get turned into the replacement
        # character: diff['before'] = u'�' ; diff['after'] = u'�'  When the callback plugin later
        # diffs before and after it shows an empty diff.

        diff = {}
        display.debug("Going to peek to see if file has changed permissions")
        peek_result = self._execute_module(module_name='file', module_args=dict(path=destination, _diff_peek=True), task_vars=task_vars, persist_files=True)

        if peek_result.get('failed', False):
            display.warning(u"Failed to get diff between '%s' and '%s': %s" % (os.path.basename(source), destination, to_text(peek_result.get(u'msg', u''))))
            return diff

        if peek_result.get('rc', 0) == 0:

            if peek_result.get('state') in (None, 'absent'):
                diff['before'] = u''
            elif peek_result.get('appears_binary'):
                diff['dst_binary'] = 1
            elif peek_result.get('size') and C.MAX_FILE_SIZE_FOR_DIFF > 0 and peek_result['size'] > C.MAX_FILE_SIZE_FOR_DIFF:
                diff['dst_larger'] = C.MAX_FILE_SIZE_FOR_DIFF
            else:
                display.debug(u"Slurping the file %s" % source)
                dest_result = self._execute_module(module_name='slurp', module_args=dict(path=destination), task_vars=task_vars, persist_files=True)
                if 'content' in dest_result:
                    dest_contents = dest_result['content']
                    if dest_result['encoding'] == u'base64':
                        dest_contents = base64.b64decode(dest_contents)
                    else:
                        raise AnsibleError("unknown encoding in content option, failed: %s" % to_native(dest_result))
                    diff['before_header'] = destination
                    diff['before'] = to_text(dest_contents)

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
                        raise AnsibleError("Unexpected error while reading source (%s) for diff: %s " % (source, to_native(e)))

                    if b"\x00" in src_contents:
                        diff['src_binary'] = 1
                    else:
                        diff['after_header'] = source
                        diff['after'] = to_text(src_contents)
            else:
                display.debug(u"source of file passed in")
                diff['after_header'] = u'dynamically generated'
                diff['after'] = source

        if self._play_context.no_log:
            if 'before' in diff:
                diff["before"] = u""
            if 'after' in diff:
                diff["after"] = u" [[ Diff output has been hidden because 'no_log: true' was specified for this result ]]\n"

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
