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

import StringIO
import json
import os
import random
import sys # FIXME: probably not needed
import tempfile
import time

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.executor.module_common import modify_module
from ansible.parsing.utils.jsonify import jsonify
from ansible.plugins import shell_loader

from ansible.utils.debug import debug

class ActionBase:

    '''
    This class is the base class for all action plugins, and defines
    code common to all actions. The base class handles the connection
    by putting/getting files and executing commands based on the current
    action in use.
    '''

    def __init__(self, task, connection, connection_info, loader, module_loader):
        self._task            = task
        self._connection      = connection
        self._connection_info = connection_info
        self._loader          = loader
        self._module_loader   = module_loader
        self._shell           = self.get_shell()

        self._supports_check_mode = True

    def get_shell(self):

        # FIXME: no more inject, get this from the host variables?
        #default_shell = getattr(self._connection, 'default_shell', '')
        #shell_type = inject.get('ansible_shell_type')
        #if not shell_type:
        #    if default_shell:
        #        shell_type = default_shell
        #    else:
        #        shell_type = os.path.basename(C.DEFAULT_EXECUTABLE)

        shell_type = getattr(self._connection, 'default_shell', '')
        if not shell_type:
            shell_type = os.path.basename(C.DEFAULT_EXECUTABLE)

        shell_plugin = shell_loader.get(shell_type)
        if shell_plugin is None:
            shell_plugin = shell_loader.get('sh')

        return shell_plugin

    def _configure_module(self, module_name, module_args):
        '''
        Handles the loading and templating of the module code through the
        modify_module() function.
        '''

        # Search module path(s) for named module.
        module_suffixes = getattr(self._connection, 'default_suffixes', None)
        module_path = self._module_loader.find_plugin(module_name, module_suffixes, transport=self._connection.get_transport())
        if module_path is None:
            module_path2 = self._module_loader.find_plugin('ping', module_suffixes)
            if module_path2 is not None:
                raise AnsibleError("The module %s was not found in configured module paths" % (module_name))
            else:
                raise AnsibleError("The module %s was not found in configured module paths. " \
                                   "Additionally, core modules are missing. If this is a checkout, " \
                                   "run 'git submodule update --init --recursive' to correct this problem." % (module_name))

        # insert shared code and arguments into the module
        (module_data, module_style, module_shebang) = modify_module(module_path, module_args)

        return (module_style, module_shebang, module_data)

    def _compute_environment_string(self):
        '''
        Builds the environment string to be used when executing the remote task.
        '''

        enviro = {}

        # FIXME: not sure where this comes from, probably task but maybe also the play?
        #if self.environment:
        #    enviro = template.template(self.basedir, self.environment, inject, convert_bare=True)
        #    enviro = utils.safe_eval(enviro)
        #    if type(enviro) != dict:
        #        raise errors.AnsibleError("environment must be a dictionary, received %s" % enviro)

        return self._shell.env_prefix(**enviro)

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
        if not self._connection._has_pipelining or not C.ANSIBLE_SSH_PIPELINING or C.DEFAULT_KEEP_REMOTE_FILES or self._connection_info.su:
            # tmp is necessary to store module source code
            return True
        if not self._connection._has_pipelining:
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

        if (self._connection_info.sudo and self._connection_info.sudo_user != 'root') or (self._connection_info.su and self._connection_info.su_user != 'root'):
            use_system_tmp = True

        tmp_mode = None
        if self._connection_info.remote_user != 'root' or \
           ((self._connection_info.sudo and self._connection_info.sudo_user != 'root') or (self._connection_info.su and self._connection_info.su_user != 'root')):
            tmp_mode = 'a+rx'

        cmd = self._shell.mkdtemp(basefile, use_system_tmp, tmp_mode)
        debug("executing _low_level_execute_command to create the tmp path")
        result = self._low_level_execute_command(cmd, None, sudoable=False)
        debug("done with creation of tmp path")

        # error handling on this seems a little aggressive?
        if result['rc'] != 0:
            if result['rc'] == 5:
                output = 'Authentication failure.'
            elif result['rc'] == 255 and self._connection.get_transport() in ['ssh']:
                # FIXME: more utils.VERBOSITY
                #if utils.VERBOSITY > 3:
                #    output = 'SSH encountered an unknown error. The output was:\n%s' % (result['stdout']+result['stderr'])
                #else:
                #    output = 'SSH encountered an unknown error during the connection. We recommend you re-run the command using -vvvv, which will enable SSH debugging output to help diagnose the issue'
                output = 'SSH encountered an unknown error. The output was:\n%s' % (result['stdout']+result['stderr'])
            elif 'No space left on device' in result['stderr']:
                output = result['stderr']
            else:
                output = 'Authentication or permission failure.  In some cases, you may have been able to authenticate and did not have permissions on the remote directory. Consider changing the remote temp path in ansible.cfg to a path rooted in "/tmp". Failed command was: %s, exited with result %d' % (cmd, result['rc'])
            if 'stdout' in result and result['stdout'] != '':
                output = output + ": %s" % result['stdout']
            raise AnsibleError(output)

        # FIXME: do we still need to do this?
        #rc = self._shell.join_path(utils.last_non_blank_line(result['stdout']).strip(), '')
        rc = self._shell.join_path(result['stdout'].strip(), '').splitlines()[-1]

        # Catch failure conditions, files should never be
        # written to locations in /.
        if rc == '/':
            raise AnsibleError('failed to resolve remote temporary directory from %s: `%s` returned empty string' % (basetmp, cmd))

        return rc

    def _remove_tmp_path(self, tmp_path):
        '''Remove a temporary path we created. '''

        if tmp_path and "-tmp-" in tmp_path:
            cmd = self._shell.remove(tmp_path, recurse=True)
            # If we have gotten here we have a working ssh configuration.
            # If ssh breaks we could leave tmp directories out on the remote system.
            debug("calling _low_level_execute_command to remove the tmp path")
            self._low_level_execute_command(cmd, None, sudoable=False)
            debug("done removing the tmp path")

    def _transfer_data(self, remote_path, data):
        '''
        Copies the module data out to the temporary module path.
        '''

        if type(data) == dict:
            data = jsonify(data)

        afd, afile = tempfile.mkstemp()
        afo = os.fdopen(afd, 'w')
        try:
            # FIXME: is this still necessary?
            #if not isinstance(data, unicode):
            #    #ensure the data is valid UTF-8
            #    data = data.decode('utf-8')
            #else:
            #    data = data.encode('utf-8')
            afo.write(data)
        except Exception, e:
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

        cmd = self._shell.chmod(mode, path)
        debug("calling _low_level_execute_command to chmod the remote path")
        res = self._low_level_execute_command(cmd, tmp, sudoable=sudoable)
        debug("done with chmod call")
        return res

    def _remote_checksum(self, tmp, path):
        '''
        Takes a remote checksum and returns 1 if no file
        '''

        # FIXME: figure out how this will work, probably pulled from the
        #        variable manager data
        #python_interp = inject['hostvars'][inject['inventory_hostname']].get('ansible_python_interpreter', 'python')
        python_interp = 'python'
        cmd = self._shell.checksum(path, python_interp)
        debug("calling _low_level_execute_command to get the remote checksum")
        data = self._low_level_execute_command(cmd, tmp, sudoable=True)
        debug("done getting the remote checksum")
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
            # FIXME: this should probably not print to sys.stderr, but should instead
            #        fail in a more normal way?
            sys.stderr.write("warning: Calculating checksum failed unusually, please report this to the list so it can be fixed\n")
            sys.stderr.write("command: %s\n" % cmd)
            sys.stderr.write("----\n")
            sys.stderr.write("output: %s\n" % data)
            sys.stderr.write("----\n")
            # this will signal that it changed and allow things to keep going
            return "INVALIDCHECKSUM"

    def _remote_expand_user(self, path, tmp):
        ''' takes a remote path and performs tilde expansion on the remote host '''
        if not path.startswith('~'):
            return path

        split_path = path.split(os.path.sep, 1)
        expand_path = split_path[0]
        if expand_path == '~':
            if self._connection_info.sudo and self._connection_info.sudo_user:
                expand_path = '~%s' % self._connection_info.sudo_user
            elif self._connection_info.su and self._connection_info.su_user:
                expand_path = '~%s' % self._connection_info.su_user

        cmd = self._shell.expand_user(expand_path)
        debug("calling _low_level_execute_command to expand the remote user path")
        data = self._low_level_execute_command(cmd, tmp, sudoable=False)
        debug("done expanding the remote user path")
        #initial_fragment = utils.last_non_blank_line(data['stdout'])
        initial_fragment = data['stdout'].strip().splitlines()[-1]

        if not initial_fragment:
            # Something went wrong trying to expand the path remotely.  Return
            # the original string
            return path

        if len(split_path) > 1:
            return self._shell.join_path(initial_fragment, *split_path[1:])
        else:
            return initial_fragment

    def _filter_leading_non_json_lines(self, data):
        '''
        Used to avoid random output from SSH at the top of JSON output, like messages from
        tcagetattr, or where dropbear spews MOTD on every single command (which is nuts).

        need to filter anything which starts not with '{', '[', ', '=' or is an empty line.
        filter only leading lines since multiline JSON is valid.
        '''

        filtered_lines = StringIO.StringIO()
        stop_filtering = False
        for line in data.splitlines():
            if stop_filtering or line.startswith('{') or line.startswith('['):
                stop_filtering = True
                filtered_lines.write(line + '\n')
        return filtered_lines.getvalue()

    def _execute_module(self, module_name=None, module_args=None, tmp=None, persist_files=False, delete_remote_tmp=True):
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
        if self._connection_info.check_mode and not self._task.always_run:
            if not self._supports_check_mode:
                raise AnsibleError("check mode is not supported for this operation")
            module_args['_ansible_check_mode'] = True

        # set no log in the module arguments, if required
        if self._connection_info.no_log:
            module_args['_ansible_no_log'] = True

        debug("in _execute_module (%s, %s)" % (module_name, module_args))

        (module_style, shebang, module_data) = self._configure_module(module_name=module_name, module_args=module_args)
        if not shebang:
            raise AnsibleError("module is missing interpreter line")

        # a remote tmp path may be necessary and not already created
        remote_module_path = None
        if not tmp and self._late_needs_tmp_path(tmp, module_style):
            tmp = self._make_tmp_path()
            remote_module_path = self._shell.join_path(tmp, module_name)

        # FIXME: async stuff here?
        #if (module_style != 'new' or async_jid is not None or not self._connection._has_pipelining or not C.ANSIBLE_SSH_PIPELINING or C.DEFAULT_KEEP_REMOTE_FILES):
        if remote_module_path:
            debug("transfering module to remote")
            self._transfer_data(remote_module_path, module_data)
            debug("done transfering module to remote")

        environment_string = self._compute_environment_string()

        if tmp and "tmp" in tmp and ((self._connection_info.sudo and self._connection_info.sudo_user != 'root') or (self._connection_info.su and self._connection_info.su_user != 'root')):
            # deal with possible umask issues once sudo'ed to other user
            self._remote_chmod(tmp, 'a+r', remote_module_path)

        cmd = ""
        in_data = None

        # FIXME: all of the old-module style and async stuff has been removed from here, and
        #        might need to be re-added (unless we decide to drop support for old-style modules
        #        at this point and rework things to support non-python modules specifically)
        if self._connection._has_pipelining and C.ANSIBLE_SSH_PIPELINING and not C.DEFAULT_KEEP_REMOTE_FILES:
            in_data = module_data
        else:
            if remote_module_path:
                cmd = remote_module_path

        rm_tmp = None
        if tmp and "tmp" in tmp and not C.DEFAULT_KEEP_REMOTE_FILES and not persist_files and delete_remote_tmp:
            if not self._connection_info.sudo or self._connection_info.su or self._connection_info.sudo_user == 'root' or self._connection_info.su_user == 'root':
                # not sudoing or sudoing to root, so can cleanup files in the same step
                rm_tmp = tmp

        cmd = self._shell.build_module_command(environment_string, shebang, cmd, rm_tmp)
        cmd = cmd.strip()

        sudoable = True
        if module_name == "accelerate":
            # always run the accelerate module as the user
            # specified in the play, not the sudo_user
            sudoable = False

        debug("calling _low_level_execute_command() for command %s" % cmd)
        res = self._low_level_execute_command(cmd, tmp, sudoable=sudoable, in_data=in_data)
        debug("_low_level_execute_command returned ok")

        if tmp and "tmp" in tmp and not C.DEFAULT_KEEP_REMOTE_FILES and not persist_files and delete_remote_tmp:
            if (self._connection_info.sudo and self._connection_info.sudo_user != 'root') or (self._connection_info.su and self._connection_info.su_user != 'root'):
            # not sudoing to root, so maybe can't delete files as that other user
            # have to clean up temp files as original user in a second step
                cmd2 = self._shell.remove(tmp, recurse=True)
                self._low_level_execute_command(cmd2, tmp, sudoable=False)

        # FIXME: in error situations, the stdout may not contain valid data, so we
        #        should check for bad rc codes better to catch this here
        if 'stdout' in res and res['stdout'].strip():
            data = json.loads(self._filter_leading_non_json_lines(res['stdout']))
            if 'parsed' in data and data['parsed'] == False:
                data['msg'] += res['stderr']
            # pre-split stdout into lines, if stdout is in the data and there
            # isn't already a stdout_lines value there
            if 'stdout' in data and 'stdout_lines' not in data:
                data['stdout_lines'] = data.get('stdout', '').splitlines()
        else:
            data = dict()

        # store the module invocation details back into the result
        data['invocation'] = dict(
            module_args = module_args,
            module_name = module_name,
        )

        debug("done with _execute_module (%s, %s)" % (module_name, module_args))
        return data

    def _low_level_execute_command(self, cmd, tmp, executable=None, sudoable=True, in_data=None):
        '''
        This is the function which executes the low level shell command, which
        may be commands to create/remove directories for temporary files, or to
        run the module code or python directly when pipelining.
        '''

        debug("in _low_level_execute_command() (%s)" % (cmd,))
        if not cmd:
            # this can happen with powershell modules when there is no analog to a Windows command (like chmod)
            debug("no command, exiting _low_level_execute_command()")
            return dict(stdout='', stderr='')

        if executable is None:
            executable = C.DEFAULT_EXECUTABLE

        prompt      = None
        success_key = None

        if sudoable:
            if self._connection_info.su and self._connection_info.su_user:
                cmd, prompt, success_key = self._connection_info.make_su_cmd(executable, cmd)
            elif self._connection_info.sudo and self._connection_info.sudo_user:
                # FIXME: hard-coded sudo_exe here
                cmd, prompt, success_key = self._connection_info.make_sudo_cmd('/usr/bin/sudo', executable, cmd)

        debug("executing the command %s through the connection" % cmd)
        rc, stdin, stdout, stderr = self._connection.exec_command(cmd, tmp, executable=executable, in_data=in_data)
        debug("command execution done")

        if not isinstance(stdout, basestring):
            out = ''.join(stdout.readlines())
        else:
            out = stdout

        if not isinstance(stderr, basestring):
            err = ''.join(stderr.readlines())
        else:
            err = stderr

        debug("done with _low_level_execute_command() (%s)" % (cmd,))
        if rc is not None:
            return dict(rc=rc, stdout=out, stderr=err)
        else:
            return dict(stdout=out, stderr=err)
