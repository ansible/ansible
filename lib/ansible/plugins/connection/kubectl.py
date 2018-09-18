# Based on the docker connection plugin
#
# Connection plugin for configuring kubernetes containers with kubectl
# (c) 2017, XuXinkun <xuxinkun@gmail.com>
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    author:
        - xuxinkun

    connection: kubectl

    short_description: Execute tasks in pods running on Kubernetes.

    description:
        - Use the kubectl exec command to run tasks in, or put/fetch files to, pods running on the Kubernetes
          container platform.

    version_added: "2.5"

    requirements:
      - kubectl (go binary)

    options:
      kubectl_pod:
        description:
          - Pod name. Required when the host name does not match pod name.
        default: ''
        vars:
          - name: ansible_kubectl_pod
        env:
          - name: K8S_AUTH_POD
      kubectl_container:
        description:
          - Container name. Required when a pod contains more than one container.
        default: ''
        vars:
          - name: ansible_kubectl_container
        env:
          - name: K8S_AUTH_CONTAINER
      kubectl_namespace:
        description:
          - The namespace of the pod
        default: ''
        vars:
          - name: ansible_kubectl_namespace
        env:
          - name: K8S_AUTH_NAMESPACE
      kubectl_extra_args:
        description:
          - Extra arguments to pass to the kubectl command line.
        default: ''
        vars:
          - name: ansible_kubectl_extra_args
        env:
          - name: K8S_AUTH_EXTRA_ARGS
      kubectl_kubeconfig:
        description:
          - Path to a kubectl config file. Defaults to I(~/.kube/conig)
        default: ''
        vars:
          - name: ansible_kubectl_kubeconfig
          - name: ansible_kubectl_config
        env:
          - name: K8S_AUTH_KUBECONFIG
      kubectl_context:
        description:
          - The name of a context found in the K8s config file.
        default: ''
        vars:
          - name: ansible_kubectl_context
        env:
          - name: k8S_AUTH_CONTEXT
      kubectl_host:
        description:
          - URL for accessing the API.
        default: ''
        vars:
          - name: ansible_kubectl_host
          - name: ansible_kubectl_server
        env:
          - name: K8S_AUTH_HOST
          - name: K8S_AUTH_SERVER
      kubectl_username:
        description:
          - Provide a username for authenticating with the API.
        default: ''
        vars:
          - name: ansible_kubectl_username
        env:
          - name: K8S_AUTH_USERNAME
      kubectl_password:
        description:
          - Provide a password for authenticating with the API.
        default: ''
        vars:
          - name: ansible_kubectl_password
        env:
          - name: K8S_AUTH_PASSWORD
      kubectl_token:
        description:
          - API authentication bearer token.
        vars:
          - name: ansible_kubectl_token
          - name: ansible_kubectl_api_key
        env:
          - name: K8S_AUTH_TOKEN
          - name: K8S_AUTH_API_KEY
      kubectl_cert_file:
        description:
          - Path to a certificate used to authenticate with the API.
        default: ''
        vars:
          - name: ansible_kubectl_cert_file
        env:
          - name: K8S_AUTH_CERT_FILE
      kubectl_key_file:
        description:
          - Path to a key file used to authenticate with the API.
        default: ''
        vars:
          - name: ansible_kubectl_key_file
        env:
          - name: K8S_AUTH_KEY_FILE
      kubectl_ssl_ca_cert:
        description:
          - Path to a CA certificate used to authenticate with the API.
        default: ''
        vars:
          - name: ansible_kubectl_cert_file
        env:
          - name: K8S_AUTH_SSL_CA_CERT
      kubectl_verify_ssl:
        description:
          - Whether or not to verify the API server's SSL certificate. Defaults to I(true).
        default: ''
        vars:
          - name: ansible_kubectl_verify_ssl
        env:
          - name: K8s_AUTH_VERIFY_SSL
"""

import distutils.spawn
import os
import os.path
import subprocess

import ansible.constants as C
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.errors import AnsibleError, AnsibleFileNotFound
from ansible.module_utils.six.moves import shlex_quote
from ansible.module_utils._text import to_bytes
from ansible.plugins.connection import ConnectionBase, BUFSIZE


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


CONNECTION_TRANSPORT = 'kubectl'

CONNECTION_OPTIONS = {
    'kubectl_container': '-c',
    'kubectl_namespace': '-n',
    'kubectl_kubeconfig': '--kubeconfig',
    'kubectl_context': '--context',
    'kubectl_host': '--server',
    'kubectl_username': '--username',
    'kubectl_password': '--password',
    'kubectl_cert_file': '--client-certificate',
    'kubectl_key_file': '--client-key',
    'kubectl_ssl_ca_cert': '--certificate-authority',
    'kubectl_verify_ssl': '--insecure-skip-tls-verify',
    'kubectl_token': '--token'
}


class Connection(ConnectionBase):
    ''' Local kubectl based connections '''

    transport = CONNECTION_TRANSPORT
    connection_options = CONNECTION_OPTIONS
    documentation = DOCUMENTATION
    has_pipelining = True
    become_methods = frozenset(C.BECOME_METHODS)
    transport_cmd = None

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        # Note: kubectl runs commands as the user that started the container.
        # It is impossible to set the remote user for a kubectl connection.
        cmd_arg = '{0}_command'.format(self.transport)
        if cmd_arg in kwargs:
            self.transport_cmd = kwargs[cmd_arg]
        else:
            self.transport_cmd = distutils.spawn.find_executable(self.transport)
            if not self.transport_cmd:
                raise AnsibleError("{0} command not found in PATH".format(self.transport))

    def _build_exec_cmd(self, cmd):
        """ Build the local kubectl exec command to run cmd on remote_host
        """
        local_cmd = [self.transport_cmd]

        # Build command options based on doc string
        doc_yaml = AnsibleLoader(self.documentation).get_single_data()
        for key in doc_yaml.get('options'):
            if key.endswith('verify_ssl') and self.get_option(key) != '':
                # Translate verify_ssl to skip_verify_ssl, and output as string
                skip_verify_ssl = not self.get_option(key)
                local_cmd.append(u'{0}={1}'.format(self.connection_options[key], str(skip_verify_ssl).lower()))
            elif not key.endswith('container') and self.get_option(key) and self.connection_options.get(key):
                cmd_arg = self.connection_options[key]
                local_cmd += [cmd_arg, self.get_option(key)]

        extra_args_name = u'{0}_extra_args'.format(self.transport)
        if self.get_option(extra_args_name):
            local_cmd += self.get_option(extra_args_name).split(' ')

        pod = self.get_option(u'{0}_pod'.format(self.transport))
        if not pod:
            pod = self._play_context.remote_addr
        # -i is needed to keep stdin open which allows pipelining to work
        local_cmd += ['exec', '-i', pod]

        # if the pod has more than one container, then container is required
        container_arg_name = u'{0}_container'.format(self.transport)
        if self.get_option(container_arg_name):
            local_cmd += ['-c', self.get_option(container_arg_name)]

        local_cmd += ['--'] + cmd

        return local_cmd

    def _connect(self, port=None):
        """ Connect to the container. Nothing to do """
        super(Connection, self)._connect()
        if not self._connected:
            display.vvv(u"ESTABLISH {0} CONNECTION".format(self.transport), host=self._play_context.remote_addr)
            self._connected = True

    def exec_command(self, cmd, in_data=None, sudoable=False):
        """ Run a command in the container """
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        local_cmd = self._build_exec_cmd([self._play_context.executable, '-c', cmd])

        display.vvv("EXEC %s" % (local_cmd,), host=self._play_context.remote_addr)
        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]
        p = subprocess.Popen(local_cmd, shell=False, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = p.communicate(in_data)
        return (p.returncode, stdout, stderr)

    def _prefix_login_path(self, remote_path):
        ''' Make sure that we put files into a standard path

            If a path is relative, then we need to choose where to put it.
            ssh chooses $HOME but we aren't guaranteed that a home dir will
            exist in any given chroot.  So for now we're choosing "/" instead.
            This also happens to be the former default.

            Can revisit using $HOME instead if it's a problem
        '''
        if not remote_path.startswith(os.path.sep):
            remote_path = os.path.join(os.path.sep, remote_path)
        return os.path.normpath(remote_path)

    def put_file(self, in_path, out_path):
        """ Transfer a file from local to the container """
        super(Connection, self).put_file(in_path, out_path)
        display.vvv("PUT %s TO %s" % (in_path, out_path), host=self._play_context.remote_addr)

        out_path = self._prefix_login_path(out_path)
        if not os.path.exists(to_bytes(in_path, errors='surrogate_or_strict')):
            raise AnsibleFileNotFound(
                "file or module does not exist: %s" % in_path)

        out_path = shlex_quote(out_path)
        # kubectl doesn't have native support for copying files into
        # running containers, so we use kubectl exec to implement this
        with open(to_bytes(in_path, errors='surrogate_or_strict'), 'rb') as in_file:
            if not os.fstat(in_file.fileno()).st_size:
                count = ' count=0'
            else:
                count = ''
            args = self._build_exec_cmd([self._play_context.executable, "-c", "dd of=%s bs=%s%s" % (out_path, BUFSIZE, count)])
            args = [to_bytes(i, errors='surrogate_or_strict') for i in args]
            try:
                p = subprocess.Popen(args, stdin=in_file,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError:
                raise AnsibleError("kubectl connection requires dd command in the container to put files")
            stdout, stderr = p.communicate()

            if p.returncode != 0:
                raise AnsibleError("failed to transfer file %s to %s:\n%s\n%s" % (in_path, out_path, stdout, stderr))

    def fetch_file(self, in_path, out_path):
        """ Fetch a file from container to local. """
        super(Connection, self).fetch_file(in_path, out_path)
        display.vvv("FETCH %s TO %s" % (in_path, out_path), host=self._play_context.remote_addr)

        in_path = self._prefix_login_path(in_path)
        out_dir = os.path.dirname(out_path)

        # kubectl doesn't have native support for fetching files from
        # running containers, so we use kubectl exec to implement this
        args = self._build_exec_cmd([self._play_context.executable, "-c", "dd if=%s bs=%s" % (in_path, BUFSIZE)])
        args = [to_bytes(i, errors='surrogate_or_strict') for i in args]
        actual_out_path = os.path.join(out_dir, os.path.basename(in_path))
        with open(to_bytes(actual_out_path, errors='surrogate_or_strict'), 'wb') as out_file:
            try:
                p = subprocess.Popen(args, stdin=subprocess.PIPE,
                                     stdout=out_file, stderr=subprocess.PIPE)
            except OSError:
                raise AnsibleError(
                    "{0} connection requires dd command in the container to fetch files".format(self.transport)
                )
            stdout, stderr = p.communicate()

            if p.returncode != 0:
                raise AnsibleError("failed to fetch file %s to %s:\n%s\n%s" % (in_path, out_path, stdout, stderr))

        if actual_out_path != out_path:
            os.rename(to_bytes(actual_out_path, errors='strict'), to_bytes(out_path, errors='strict'))

    def close(self):
        """ Terminate the connection. Nothing to do for kubectl"""
        super(Connection, self).close()
        self._connected = False
