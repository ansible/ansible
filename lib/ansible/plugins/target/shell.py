# Copyright: (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import random
import re
import tempfile
import time

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleConnectionFailure
from ansible.executor.module_common import modify_module
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.json_utils import _filter_non_json_lines
from ansible.module_utils.six import binary_type, text_type, iteritems
from ansible.module_utils.six.moves import shlex_quote
from ansible.parsing.utils.jsonify import jsonify
from ansible.plugins.loader import module_loader
from ansible.plugins.target import TargetBase
from ansible.utils.unsafe_proxy import wrap_var


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class TargetModule(TargetBase):
    '''
    A target plugin implementing high-level actions via file transfer and the
    operating system shell.
    '''
    _used_interpreter = None

    def exists(self, path):
        cmd = self._connection._shell.exists(path)
        result = self.execute_command(cmd=cmd)
        return result['rc'] == 0

    def make_tmp_path(self):
        become_unprivileged = self._connection.is_become_unprivileged()
        try:
            remote_tmp = self._connection._shell.get_option('remote_tmp')
        except AnsibleError:
            remote_tmp = '~/.ansible/tmp'

        # deal with tmpdir creation
        basefile = 'ansible-tmp-%s-%s' % (time.time(), random.randint(0, 2**48))
        # Network connection plugins (network_cli, netconf, etc.) execute on the controller, rather than the remote host.
        # As such, we want to avoid using remote_user for paths  as remote_user may not line up with the local user
        # This is a hack and should be solved by more intelligent handling of remote_tmp in 2.7
        if getattr(self._connection, '_remote_is_local', False):
            tmpdir = C.DEFAULT_LOCAL_TMP
        else:
            tmpdir = self.expand_user(remote_tmp, sudoable=False)
        cmd = self._connection._shell.mkdtemp(basefile=basefile, system=become_unprivileged, tmpdir=tmpdir)
        result = self.execute_command(cmd, sudoable=False)

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
                output = ('Authentication or permission failure. '
                          'In some cases, you may have been able to authenticate and did not have permissions on the target directory. '
                          'Consider changing the remote tmp path in ansible.cfg to a path rooted in "/tmp". '
                          'Failed command was: %s, exited with result %d' % (cmd, result['rc']))
            if 'stdout' in result and result['stdout'] != u'':
                output = output + u", stdout output: %s" % result['stdout']
            if self._play_context.verbosity > 3 and 'stderr' in result and result['stderr'] != u'':
                output += u", stderr output: %s" % result['stderr']
            raise AnsibleConnectionFailure(output)

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

        return rc

    def remove(self, tmp_path):
        cmd = self._connection._shell.remove(tmp_path, recurse=True)
        # If we have gotten here we have a working ssh configuration.
        # If ssh breaks we could leave tmp directories out on the remote system.
        res = self.execute_command(cmd, sudoable=False)

        if res.get('rc', 0) != 0:
            display.warning('Error deleting remote temporary files (rc: %s, stderr: %s})'
                            % (res.get('rc'), res.get('stderr', 'No error string available.')))
            return False

        return True

    def ensure_readable(self, remote_paths, remote_user, execute):
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
           with chown which only works in case the remote_user is
          privileged or the remote systems allows chown calls by unprivileged
          users (e.g. HP-UX)
        * If the chown fails we can set the file to be world readable so that
          the second unprivileged user can read the file.
          Since this could allow other users to get access to private
          information we only do this if ansible is configured with
          "allow_world_readable_tmpfiles" in the ansible.cfg
        """
        if self._connection._shell.SHELL_FAMILY == 'powershell':
            # This won't work on Powershell as-is, so we'll just completely skip until
            # we have a need for it, at which point we'll have to do something different.
            return remote_paths

        if self._connection.is_become_unprivileged():
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

            res = self._remote_set_user_facl(remote_paths, self._play_context.become_user, setfacl_mode)
            if res['rc'] != 0:
                # File system acls failed; let's try to use chown next
                # Set executable bit first as on some systems an
                # unprivileged user can use chown
                if execute:
                    res = self._remote_chmod(remote_paths, 'u+x')
                    if res['rc'] != 0:
                        raise AnsibleError('Failed to set file mode on remote temporary files (rc: {0}, err: {1})'.format(res['rc'], to_native(res['stderr'])))

                res = self._remote_chown(remote_paths, self._play_context.become_user)
                if res['rc'] != 0 and remote_user in self._connection.get_admin_users():
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

    def _remote_chmod(self, paths, mode, sudoable=False):
        '''
        Issue a remote chmod command
        '''
        cmd = self._connection._shell.chmod(paths, mode)
        res = self.execute_command(cmd, sudoable=sudoable)
        return res

    def _remote_chown(self, paths, user, sudoable=False):
        '''
        Issue a remote chown command
        '''
        cmd = self._connection._shell.chown(paths, user)
        res = self.execute_command(cmd, sudoable=sudoable)
        return res

    def _remote_set_user_facl(self, paths, user, mode, sudoable=False):
        '''
        Issue a remote call to setfacl
        '''
        cmd = self._connection._shell.set_user_facl(paths, user, mode)
        res = self.execute_command(cmd, sudoable=sudoable)
        return res

    def _strip_success_message(self, data):
        '''
        Removes the BECOME-SUCCESS message from the data.
        '''
        if data.strip().startswith('BECOME-SUCCESS-'):
            data = re.sub(r'^((\r)?\n)?BECOME-SUCCESS.*(\r)?\n', '', data)
        return data

    def execute_command(self, cmd, sudoable=True, in_data=None, executable=None, chdir=None):
        display.debug("execute_command(): starting")
#        if not cmd:
#            # this can happen with powershell modules when there is no analog to a Windows command (like chmod)
#            display.debug("execute_command(): no command, exiting")
#           return dict(stdout='', stderr='', rc=254)

        if chdir:
            display.debug("execute_command(): changing cwd to %s for this command" % chdir)
            cmd = self._connection._shell.append_command('cd %s' % chdir, cmd)

        allow_same_user = C.BECOME_ALLOW_SAME_USER
        same_user = self._play_context.become_user == self._play_context.remote_user
        if sudoable and self._play_context.become and (allow_same_user or not same_user):
            display.debug("execute_command(): using become for this command")
            if self._connection.transport != 'network_cli' and self._play_context.become_method != 'enable':
                cmd = self._play_context.make_become_cmd(cmd, executable=executable)

        if self._connection.allow_executable:
            if executable is None:
                executable = self._play_context.executable
                # mitigation for SSH race which can drop stdout (https://github.com/ansible/ansible/issues/13876)
                # only applied for the default executable to avoid interfering with the raw action
                cmd = self._connection._shell.append_command(cmd, 'sleep 0')
            if executable:
                cmd = executable + ' -c ' + shlex_quote(cmd)

        display.debug("execute_command(): executing: %s" % (cmd,))

        # Change directory to basedir of task for command execution when connection is local
        if self._connection.transport == 'local':
            cwd = os.getcwd()
            os.chdir(self._loader.get_basedir())
        try:
            rc, stdout, stderr = self._connection.exec_command(cmd, in_data=in_data, sudoable=sudoable)
        finally:
            if self._connection.transport == 'local':
                os.chdir(cwd)

        # stdout and stderr may be either a file-like or a bytes object.
        # Convert either one to a text type
        if isinstance(stdout, binary_type):
            out = to_text(stdout, errors='surrogate_then_replace')
        elif not isinstance(stdout, text_type):
            out = to_text(b''.join(stdout.readlines()), errors='surrogate_then_replace')
        else:
            out = stdout

        if isinstance(stderr, binary_type):
            err = to_text(stderr, errors='surrogate_then_replace')
        elif not isinstance(stderr, text_type):
            err = to_text(b''.join(stderr.readlines()), errors='surrogate_then_replace')
        else:
            err = stderr

        if rc is None:
            rc = 0

        # be sure to remove the BECOME-SUCCESS message now
        out = self._strip_success_message(out)
        display.debug(u"execute_command() done: rc=%d, stdout=%s, stderr=%s" % (rc, out, err))
        return {
            'rc': rc,
            'stdout': out,
            'stderr': err
        }

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
            self._play_context.become_method != 'su',  # su does not work with pipelining,
            # FIXME: we might need to make become_method exclusion a configurable list
        ]:
            if not condition:
                return False

        return True

    def _configure_module(self, name, args, module_env, async_timeout, task_vars=None):
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
                if name in ('stat', 'file', 'copy') and self._task.action != name:
                    name = 'win_%s' % name

                # Remove extra quotes surrounding path parameters before sending to module.
                if name in ('win_stat', 'win_file', 'win_copy', 'slurp') and args and hasattr(self._connection._shell, '_unquote'):
                    for key in ('src', 'dest', 'path'):
                        if key in args:
                            args[key] = self._connection._shell._unquote(args[key])

            module_path = module_loader.find_plugin(name, mod_type)
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
            module_path2 = module_loader.find_plugin(ping_module, self._connection.module_implementation_preferences)
            if module_path2 is not None:
                raise AnsibleError("The module %s was not found in configured module paths" % (name))
            else:
                raise AnsibleError("The module %s was not found in configured module paths. "
                                   "Additionally, core modules are missing. If this is a checkout, "
                                   "run 'git pull --rebase' to correct this problem." % (name))

        (module_data, module_style, module_shebang) = modify_module(name, module_path, args, self._templar,
                                                                    task_vars=task_vars,
                                                                    module_compression=self._play_context.module_compression,
                                                                    async_timeout=async_timeout,
                                                                    become=self._play_context.become,
                                                                    become_method=self._play_context.become_method,
                                                                    become_user=self._play_context.become_user,
                                                                    become_password=self._play_context.become_pass,
                                                                    become_flags=self._play_context.become_flags,
                                                                    environment=module_env)

        return (module_style, module_shebang, module_data, module_path)

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

    def execute_module(self, name, args, env, task_vars, wrap_async, async_timeout):
        tmpdir = self._connection._shell.tmpdir

        # We set the module_style to new here so the remote_tmp is created
        # before the module args are built if remote_tmp is needed (async).
        # If the module_style turns out to not be new and we didn't create the
        # remote tmp here, it will still be created. This must be done before
        # calling self._update_args() so the module wrapper has the
        # correct remote_tmp value set
        if not self._is_pipelining_enabled("new", wrap_async) and tmpdir is None:
            self._make_tmp_path()
            tmpdir = self._connection._shell.tmpdir

        # FUTURE: refactor this along with module build process to better encapsulate "smart wrapper" functionality
        (module_style, shebang, module_data, module_path) = self._configure_module(name=name, args=args, async_timeout=async_timeout, task_vars=task_vars)
        display.vvv("Using module file %s" % module_path)
        if not shebang and module_style != 'binary':
            raise AnsibleError("module (%s) is missing interpreter line" % name)

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
                for k, v in iteritems(args):
                    args_data += '%s=%s ' % (k, shlex_quote(text_type(v)))
                self._transfer_data(args_file_path, args_data)
            elif module_style in ('non_native_want_json', 'binary'):
                self._transfer_data(args_file_path, json.dumps(args))
            display.debug("done transferring module to remote")

        environment_string = self._connection.shell.env_prefix(**env)

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
            (async_module_style, shebang, async_module_data, async_module_path) = self._configure_module(
                name='async_wrapper',
                args=dict(),
                async_timeout=async_timeout,
                module_env=env,
                task_vars=task_vars
            )

            async_module_remote_filename = self._connection._shell.get_remote_filename(async_module_path)
            remote_async_module_path = self._connection._shell.join_path(tmpdir, async_module_remote_filename)
            self._transfer_data(remote_async_module_path, async_module_data)
            remote_files.append(remote_async_module_path)

            async_jid = str(random.randint(0, 999999999999))

            # call the interpreter for async_wrapper directly
            # this permits use of a script for an interpreter on non-Linux platforms
            # TODO: re-implement async_wrapper as a regular module to avoid this special case
            interpreter = shebang.replace('#!', '').strip()
            async_cmd = [interpreter, remote_async_module_path, async_jid, async_timeout, remote_module_path]

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
            else:
                cmd = remote_module_path

            cmd = self._connection._shell.build_module_command(environment_string, shebang, cmd, arg_path=args_file_path).strip()

        # Fix permissions of the tmpdir path and tmpdir files. This should be called after all
        # files have been transferred.
        if remote_files:
            # remove none/empty
            remote_files = [x for x in remote_files if x]
            self._fixup_perms2(remote_files, self._play_context.remote_user)

        # actually execute
        res = self.execute_command(cmd, sudoable=sudoable, in_data=in_data)

        if wrap_async:
            # async_wrapper will clean up its tmpdir on its own so we want the controller side to
            # forget about it now
            self._connection._shell.tmpdir = None

        # parse the main result
        return self._parse_returned_data(res)

    def _parse_returned_data(self, res):
        try:
            filtered_output, warnings = _filter_non_json_lines(res.get('stdout', u''))
            for w in warnings:
                display.warning(w)

            data = json.loads(filtered_output)

            if 'ansible_facts' in data and isinstance(data['ansible_facts'], dict):
                data['ansible_facts'] = wrap_var(data['ansible_facts'])
            data['_ansible_parsed'] = True
        except ValueError:
            # not valid json, lets try to capture error
            data = dict(failed=True, _ansible_parsed=False)
            data['module_stdout'] = res.get('stdout', u'')
            if 'stderr' in res:
                data['module_stderr'] = res['stderr']
                if res['stderr'].startswith(u'Traceback'):
                    data['exception'] = res['stderr']

            # try to figure out if we are missing interpreter
            if self._used_interpreter is not None and '%s: No such file or directory' % self._used_interpreter.lstrip('!#') in data['module_stderr']:
                data['msg'] = "The module failed to execute correctly, you probably need to set the interpreter."
            else:
                data['msg'] = "MODULE FAILURE"

            data['msg'] += '\nSee stdout/stderr for the exact error'

            if 'rc' in res:
                data['rc'] = res['rc']
        return data

    def expand_user(self, path, sudoable=True):
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
            if getattr(self._connection, '_remote_is_local', False):
                pass
            elif sudoable and self._play_context.become and self._play_context.become_user:
                expand_path = '~%s' % self._play_context.become_user
            else:
                # use remote user instead, if none set default to current user
                expand_path = '~%s' % (self._play_context.remote_user or self._connection.default_user or '')

        # use shell to construct appropriate command and execute
        cmd = self._connection._shell.expand_user(expand_path)
        data = self.execute_command(cmd, sudoable=False)

        try:
            initial_fragment = data['stdout'].strip().splitlines()[-1]
        except IndexError:
            initial_fragment = None

        if not initial_fragment:
            # Something went wrong trying to expand the path remotely. Try using pwd, if not, return
            # the original string
            cmd = self._connection._shell.pwd()
            pwd = self.execute_command(cmd, sudoable=False).get('stdout', '').strip()
            if pwd:
                expanded = pwd
            else:
                expanded = path

        elif len(split_path) > 1:
            expanded = self._connection._shell.join_path(initial_fragment, *split_path[1:])
        else:
            expanded = initial_fragment

        return expanded
