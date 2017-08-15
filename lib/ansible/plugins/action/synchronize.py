# -*- coding: utf-8 -*-

# (c) 2012-2013, Timothy Appnel <tim@appnel.com>
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os.path
from collections import MutableSequence

from ansible import constants as C
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_text
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.playbook.play_context import MAGIC_VARIABLE_MAPPING
from ansible.plugins.action import ActionBase
from ansible.plugins import connection_loader


class ActionModule(ActionBase):

    def _get_absolute_path(self, path):
        original_path = path

        if path.startswith('rsync://'):
            return path

        if self._task._role is not None:
            path = self._loader.path_dwim_relative(self._task._role._role_path, 'files', path)
        else:
            path = self._loader.path_dwim_relative(self._loader.get_basedir(), 'files', path)

        if original_path and original_path[-1] == '/' and path[-1] != '/':
            # make sure the dwim'd path ends in a trailing "/"
            # if the original path did
            path += '/'

        return path

    def _host_is_ipv6_address(self, host):
        return ':' in host

    def _format_rsync_rsh_target(self, host, path, user):
        ''' formats rsync rsh target, escaping ipv6 addresses if needed '''

        user_prefix = ''

        if path.startswith('rsync://'):
            return path

        # If using docker, do not add user information
        if self._remote_transport not in ['docker'] and user:
            user_prefix = '%s@' % (user, )

        if self._host_is_ipv6_address(host):
            return '[%s%s]:%s' % (user_prefix, host, path)
        else:
            return '%s%s:%s' % (user_prefix, host, path)

    def _process_origin(self, host, path, user):

        if host not in C.LOCALHOST:
            return self._format_rsync_rsh_target(host, path, user)

        if ':' not in path and not path.startswith('/'):
            path = self._get_absolute_path(path=path)
        return path

    def _process_remote(self, task_args, host, path, user, port_matches_localhost_port):
        """
        :arg host: hostname for the path
        :arg path: file path
        :arg user: username for the transfer
        :arg port_matches_localhost_port: boolean whether the remote port
            matches the port used by localhost's sshd.  This is used in
            conjunction with seeing whether the host is localhost to know
            if we need to have the module substitute the pathname or if it
            is a different host (for instance, an ssh tunnelled port or an
            alternative ssh port to a vagrant host.)
        """
        transport = self._connection.transport
        # If we're connecting to a remote host or we're delegating to another
        # host or we're connecting to a different ssh instance on the
        # localhost then we have to format the path as a remote rsync path
        if host not in C.LOCALHOST or transport != "local" or \
                (host in C.LOCALHOST and not port_matches_localhost_port):
            # If we're delegating to non-localhost and but the
            # inventory_hostname host is localhost then we need the module to
            # fix up the rsync path to use the controller's public DNS/IP
            # instead of "localhost"
            if port_matches_localhost_port and host in C.LOCALHOST:
                task_args['_substitute_controller'] = True
            return self._format_rsync_rsh_target(host, path, user)

        if ':' not in path and not path.startswith('/'):
            path = self._get_absolute_path(path=path)
        return path

    def _override_module_replaced_vars(self, task_vars):
        """ Some vars are substituted into the modules.  Have to make sure
        that those are correct for localhost when synchronize creates its own
        connection to localhost."""

        # Clear the current definition of these variables as they came from the
        # connection to the remote host
        if 'ansible_syslog_facility' in task_vars:
            del task_vars['ansible_syslog_facility']
        for key in list(task_vars.keys()):
            if key.startswith("ansible_") and key.endswith("_interpreter"):
                del task_vars[key]

        # Add the definitions from localhost
        for host in C.LOCALHOST:
            if host in task_vars['hostvars']:
                localhost = task_vars['hostvars'][host]
                break
        if 'ansible_syslog_facility' in localhost:
            task_vars['ansible_syslog_facility'] = localhost['ansible_syslog_facility']
        for key in localhost:
            if key.startswith("ansible_") and key.endswith("_interpreter"):
                task_vars[key] = localhost[key]

    def run(self, tmp=None, task_vars=None):
        ''' generates params and passes them on to the rsync module '''
        # When modifying this function be aware of the tricky convolutions
        # your thoughts have to go through:
        #
        # In normal ansible, we connect from controller to inventory_hostname
        # (playbook's hosts: field) or controller to delegate_to host and run
        # a module on one of those hosts.
        #
        # So things that are directly related to the core of ansible are in
        # terms of that sort of connection that always originate on the
        # controller.
        #
        # In synchronize we use ansible to connect to either the controller or
        # to the delegate_to host and then run rsync which makes its own
        # connection from controller to inventory_hostname or delegate_to to
        # inventory_hostname.
        #
        # That means synchronize needs to have some knowledge of the
        # controller to inventory_host/delegate host that ansible typically
        # establishes and use those to construct a command line for rsync to
        # connect from the inventory_host to the controller/delegate.  The
        # challenge for coders is remembering which leg of the trip is
        # associated with the conditions that you're checking at any one time.
        if task_vars is None:
            task_vars = dict()

        # We make a copy of the args here because we may fail and be asked to
        # retry. If that happens we don't want to pass the munged args through
        # to our next invocation. Munged args are single use only.
        _tmp_args = self._task.args.copy()

        result = super(ActionModule, self).run(tmp, task_vars)

        # Store remote connection type
        self._remote_transport = self._connection.transport

        # Handle docker connection options
        if self._remote_transport == 'docker':
            self._docker_cmd = self._connection.docker_cmd
            if self._play_context.docker_extra_args:
                self._docker_cmd = "%s %s" % (self._docker_cmd, self._play_context.docker_extra_args)

        # self._connection accounts for delegate_to so
        # remote_transport is the transport ansible thought it would need
        # between the controller and the delegate_to host or the controller
        # and the remote_host if delegate_to isn't set.

        remote_transport = False
        if self._connection.transport != 'local':
            remote_transport = True

        try:
            delegate_to = self._task.delegate_to
        except (AttributeError, KeyError):
            delegate_to = None

        # ssh paramiko docker and local are fully supported transports.  Anything
        # else only works with delegate_to
        if delegate_to is None and self._connection.transport not in ('ssh', 'paramiko', 'local', 'docker'):
            result['failed'] = True
            result['msg'] = ("synchronize uses rsync to function. rsync needs to connect to the remote host via ssh, docker client or a direct filesystem "
                             "copy. This remote host is being accessed via %s instead so it cannot work." % self._connection.transport)
            return result

        use_ssh_args = _tmp_args.pop('use_ssh_args', None)

        # Parameter name needed by the ansible module
        _tmp_args['_local_rsync_path'] = task_vars.get('ansible_rsync_path') or 'rsync'

        # rsync thinks that one end of the connection is localhost and the
        # other is the host we're running the task for  (Note: We use
        # ansible's delegate_to mechanism to determine which host rsync is
        # running on so localhost could be a non-controller machine if
        # delegate_to is used)
        src_host = '127.0.0.1'
        inventory_hostname = task_vars.get('inventory_hostname')
        dest_host_inventory_vars = task_vars['hostvars'].get(inventory_hostname)
        try:
            dest_host = dest_host_inventory_vars['ansible_host']
        except KeyError:
            dest_host = dest_host_inventory_vars.get('ansible_ssh_host', inventory_hostname)

        dest_host_ids = [hostid for hostid in (dest_host_inventory_vars.get('inventory_hostname'),
                                               dest_host_inventory_vars.get('ansible_host'),
                                               dest_host_inventory_vars.get('ansible_ssh_host'))
                         if hostid is not None]

        localhost_ports = set()
        for host in C.LOCALHOST:
            localhost_vars = task_vars['hostvars'].get(host, {})
            for port_var in MAGIC_VARIABLE_MAPPING['port']:
                port = localhost_vars.get(port_var, None)
                if port:
                    break
            else:
                port = C.DEFAULT_REMOTE_PORT
            localhost_ports.add(port)

        # dest_is_local tells us if the host rsync runs on is the same as the
        # host rsync puts the files on.  This is about *rsync's connection*,
        # not about the ansible connection to run the module.
        dest_is_local = False
        if delegate_to is None and remote_transport is False:
            dest_is_local = True
        elif delegate_to is not None and delegate_to in dest_host_ids:
            dest_is_local = True

        # CHECK FOR NON-DEFAULT SSH PORT
        inv_port = task_vars.get('ansible_ssh_port', None) or C.DEFAULT_REMOTE_PORT
        if _tmp_args.get('dest_port', None) is None:
            if inv_port is not None:
                _tmp_args['dest_port'] = inv_port

        # Set use_delegate if we are going to run rsync on a delegated host
        # instead of localhost
        use_delegate = False
        if delegate_to is not None and delegate_to in dest_host_ids:
            # edge case: explicit delegate and dest_host are the same
            # so we run rsync on the remote machine targeting its localhost
            # (itself)
            dest_host = '127.0.0.1'
            use_delegate = True
        elif delegate_to is not None and remote_transport:
            # If we're delegating to a remote host then we need to use the
            # delegate_to settings
            use_delegate = True

        # Delegate to localhost as the source of the rsync unless we've been
        # told (via delegate_to) that a different host is the source of the
        # rsync
        if not use_delegate and remote_transport:
            # Create a connection to localhost to run rsync on
            new_stdin = self._connection._new_stdin

            # Unike port, there can be only one shell
            localhost_shell = None
            for host in C.LOCALHOST:
                localhost_vars = task_vars['hostvars'].get(host, {})
                for shell_var in MAGIC_VARIABLE_MAPPING['shell']:
                    localhost_shell = localhost_vars.get(shell_var, None)
                    if localhost_shell:
                        break
                if localhost_shell:
                    break
            else:
                localhost_shell = os.path.basename(C.DEFAULT_EXECUTABLE)
            self._play_context.shell = localhost_shell

            # Unike port, there can be only one executable
            localhost_executable = None
            for host in C.LOCALHOST:
                localhost_vars = task_vars['hostvars'].get(host, {})
                for executable_var in MAGIC_VARIABLE_MAPPING['executable']:
                    localhost_executable = localhost_vars.get(executable_var, None)
                    if localhost_executable:
                        break
                if localhost_executable:
                    break
            else:
                localhost_executable = C.DEFAULT_EXECUTABLE
            self._play_context.executable = localhost_executable

            new_connection = connection_loader.get('local', self._play_context, new_stdin)
            self._connection = new_connection
            self._override_module_replaced_vars(task_vars)

        # SWITCH SRC AND DEST HOST PER MODE
        if _tmp_args.get('mode', 'push') == 'pull':
            (dest_host, src_host) = (src_host, dest_host)

        # MUNGE SRC AND DEST PER REMOTE_HOST INFO
        src = _tmp_args.get('src', None)
        dest = _tmp_args.get('dest', None)
        if src is None or dest is None:
            return dict(failed=True, msg="synchronize requires both src and dest parameters are set")

        # Determine if we need a user@
        user = None
        if not dest_is_local:
            # Src and dest rsync "path" handling
            if boolean(_tmp_args.get('set_remote_user', 'yes'), strict=False):
                if use_delegate:
                    user = task_vars.get('ansible_delegated_vars', dict()).get('ansible_ssh_user', None)
                    if not user:
                        user = C.DEFAULT_REMOTE_USER

                else:
                    user = task_vars.get('ansible_ssh_user') or self._play_context.remote_user

            # Private key handling
            private_key = self._play_context.private_key_file

            if private_key is not None:
                private_key = os.path.expanduser(private_key)
                _tmp_args['private_key'] = private_key

            # use the mode to define src and dest's url
            if _tmp_args.get('mode', 'push') == 'pull':
                # src is a remote path: <user>@<host>, dest is a local path
                src = self._process_remote(_tmp_args, src_host, src, user, inv_port in localhost_ports)
                dest = self._process_origin(dest_host, dest, user)
            else:
                # src is a local path, dest is a remote path: <user>@<host>
                src = self._process_origin(src_host, src, user)
                dest = self._process_remote(_tmp_args, dest_host, dest, user, inv_port in localhost_ports)
        else:
            # Still need to munge paths (to account for roles) even if we aren't
            # copying files between hosts
            if not src.startswith('/'):
                src = self._get_absolute_path(path=src)
            if not dest.startswith('/'):
                dest = self._get_absolute_path(path=dest)

        _tmp_args['src'] = src
        _tmp_args['dest'] = dest

        # Allow custom rsync path argument
        rsync_path = _tmp_args.get('rsync_path', None)

        # backup original become as we are probably about to unset it
        become = self._play_context.become

        if not dest_is_local:
            # don't escalate for docker. doing --rsync-path with docker exec fails
            # and we can switch directly to the user via docker arguments
            if self._play_context.become and not rsync_path and self._remote_transport != 'docker':
                # If no rsync_path is set, become was originally set, and dest is
                # remote then add privilege escalation here.
                if self._play_context.become_method == 'sudo':
                    rsync_path = 'sudo rsync'
                # TODO: have to add in the rest of the become methods here

            # We cannot use privilege escalation on the machine running the
            # module.  Instead we run it on the machine rsync is connecting
            # to.
            self._play_context.become = False

        _tmp_args['rsync_path'] = rsync_path

        if use_ssh_args:
            ssh_args = [
                getattr(self._play_context, 'ssh_args', ''),
                getattr(self._play_context, 'ssh_common_args', ''),
                getattr(self._play_context, 'ssh_extra_args', ''),
            ]
            _tmp_args['ssh_args'] = ' '.join([a for a in ssh_args if a])

        # If launching synchronize against docker container
        # use rsync_opts to support container to override rsh options
        if self._remote_transport in ['docker']:
            # Replicate what we do in the module argumentspec handling for lists
            if not isinstance(_tmp_args.get('rsync_opts'), MutableSequence):
                tmp_rsync_opts = _tmp_args.get('rsync_opts', [])
                if isinstance(tmp_rsync_opts, string_types):
                    tmp_rsync_opts = tmp_rsync_opts.split(',')
                elif isinstance(tmp_rsync_opts, (int, float)):
                    tmp_rsync_opts = [to_text(tmp_rsync_opts)]
                _tmp_args['rsync_opts'] = tmp_rsync_opts

            if '--blocking-io' not in _tmp_args['rsync_opts']:
                _tmp_args['rsync_opts'].append('--blocking-io')
            if become and self._play_context.become_user:
                _tmp_args['rsync_opts'].append("--rsh=%s exec -u %s -i" % (self._docker_cmd, self._play_context.become_user))
            elif user is not None:
                _tmp_args['rsync_opts'].append("--rsh=%s exec -u %s -i" % (self._docker_cmd, user))
            else:
                _tmp_args['rsync_opts'].append("--rsh=%s exec -i" % self._docker_cmd)

        # run the module and store the result
        result.update(self._execute_module('synchronize', module_args=_tmp_args, task_vars=task_vars))

        if 'SyntaxError' in result.get('exception', result.get('msg', '')):
            # Emit a warning about using python3 because synchronize is
            # somewhat unique in running on localhost
            result['exception'] = result['msg']
            result['msg'] = ('SyntaxError parsing module.  Perhaps invoking "python" on your local (or delegate_to) machine invokes python3. '
                             'You can set ansible_python_interpreter for localhost (or the delegate_to machine) to the location of python2 to fix this')
        return result
