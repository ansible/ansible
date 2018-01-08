# Based on the local connection plugin and methods from the Docker plugin
#
# Connection plugin for kubernetes pods
# (c) 2017, Joseph Callen <jcallen@redhat.com>
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
'''
DOCUMENTATION:
    connection: kubernetes
    short_description: connect via kubernetes api to a pod
    description:
        - This connection plugin allows ansible to communicate to the target pod via kubernetes python client
    author: Joseph Callen
    version_added: 2.4
    options:
        _host:
            description: Hostname/ip to connect to.
            default: inventory_hostname
            host_vars:
                 - ansible_host
                 - ansible_ssh_host
        _password:
            description: Authentication password for the C(remote_user). Can be supplied as CLI option.
            host_vars:
                - ansible_password
                - ansible_ssh_pass
        kubernetes_namespace:
            description: The kubernetes namespace where the pods are located
            host_vars:
                - ansible_kubernetes_namespace
        kubernetes_cluster:
            description:
                - The ip address or DNS name of the kubernetes cluster
            host_vars:
                - ansible_kubernetes_cluster
        kubernetes_config_file
            description:
                - The path and filename of the kubernetes config file that will be used when connecting
                - to the kubernetes cluster
            host_vars:
                - ansible_kubernetes_config_file
        kubernetes_port:
            description: Remote port to connect to.
            type: int
            host_vars:
               - ansible_kubernetes_port
        remote_user:
            description:
                - User name with which to login to the remote server, normally set by the remote_user keyword.
            config:
               - section: defaults
                 key: remote_user
            env_vars:
               - ANSIBLE_REMOTE_USER
            host_vars:
               - ansible_user
'''

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import os
import time
import sys
from ansible.errors import AnsibleError, AnsibleFileNotFound
from ansible.module_utils.six.moves import shlex_quote
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.connection import ConnectionBase, BUFSIZE

# NOTE: This was copied from inventory/docker.py
# Manipulation of the path is needed because the kubernetes
# module is imported by the name kubernetes, and because this file
# is also named kubernetes
for path in [os.getcwd(), '', os.path.dirname(os.path.abspath(__file__))]:
    try:
        del sys.path[sys.path.index(path)]
    except:
        pass
try:
    from kubernetes import config
    from kubernetes.config import ConfigException
    from kubernetes.config.kube_config import KubeConfigLoader
    from kubernetes.client import configuration
    from kubernetes.client.apis import core_v1_api
    from kubernetes.client.rest import ApiException
except ImportError as ie:
    raise AnsibleError("Kubernetes library is not installed: {0}".format(ie.message))

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display

    display = Display()


class Connection(ConnectionBase):
    ''' Local based connections '''
    transport = 'kubernetes'
    has_pipelining = False
    active_context = None

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self.remote_user = self._play_context.remote_user
        self.actual_user = None

        # Name of the pod
        self.name = self._play_context.remote_addr

        # Overlapping options with kubectl connection plugin
        self.container = self._play_context.kube_container
        self.namespace = self._play_context.kube_namespace
        self.config_file = self._play_context.kube_config_file

        # Options required for this plugin if not using
        # the existing .kube/config
        self.cluster = self._play_context.kubernetes_cluster
        self.port = self._play_context.kubernetes_port

        self.response = None
        configuration.assert_hostname = False

    def requested_context(self):
        server = "{0}:{1}".format(self.cluster, self.port)
        return "{0}/{1}/{2}".format(
            self.namespace,
            server,
            self.remote_user
        )

    def generate_kubernetes_config(self):

        server = "{0}:{1}".format(self.cluster, self.port)
        context = "{0}/{1}/{2}".format(
            self.namespace,
            server,
            self.remote_user
        )
        users_name = "{0}/{1}".format(
            self.remote_user,
            server
        )

        kubernetes_config = {
            "current-context": context,
            "clusters": [
                {
                    "cluster": {
                        "insecure-skip-tls-verify": "true",
                        "server": "https://{0}".format(server)
                    },
                    "name": server
                }
            ],
            "contexts": [
                {
                    "context": {
                        "cluster": server,
                        "namespace": self.namespace,
                        "user": users_name
                    },
                    "name": context
                }
            ],
            "users": [
                {
                    "name": users_name,
                    "user": {
                        "token": self._play_context.password
                    }
                }
            ]
        }
        return kubernetes_config

    def _connect(self):
        '''
        If inventory variables are not empty in then use KubeConfigLoader.
        If inventory variables are empty use the existing ~/.kube/config
        '''

        try:
            if self.active_context is None:
                if not self._connected:
                    if (self.namespace and
                            self.cluster and
                            self.remote_user and
                            self._play_context.password and
                            self.port):

                        # self.namespace = self._play_context.kubernetes_namespace
                        kubernetes_config = self.generate_kubernetes_config()
                        active_context = self.requested_context()
                        kube_loader = KubeConfigLoader(config_dict=kubernetes_config,
                                                       active_context=active_context)
                        kube_loader.load_and_set()
                    elif self.config_file:
                        config.load_kube_config(config_file=self.config_file)
                        # self.namespace = self._play_context.kubernetes_namespace
                    else:
                        config.load_kube_config()
                        _, self.active_context = config.list_kube_config_contexts()
                        self.namespace = self.active_context['context']['namespace']

                    self.api = core_v1_api.CoreV1Api()
                    self._connected = True
                    display.vvv(u"ESTABLISH CONNECTION FOR USER: {0}".format(self.remote_user), host=self.name)
        except ConfigException as e:
            AnsibleError("Kubernetes Connection Config Error: {0}".format(e.message))
        except ApiException as e:
            AnsibleError("Kubernetes Connection API Error: {0}".format(e.message))
        except Exception as e:
            AnsibleError("Unknown Error: {0}".format(e.message))
        return self

    def exec_command(self, cmd, in_data=None, sudoable=False):
        ''' run a command on a kubernetes pod'''
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)
        stdout = ''
        stderr = ''
        returncode = 0

        local_cmd = [self._play_context.executable, '-c', cmd]
        display.vvv("EXEC {0}".format(to_text(local_cmd)), host=self._play_context.remote_addr)
        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]
        try:
            self.response = self.api.connect_get_namespaced_pod_exec(name=self.name,
                                                                     namespace=self.namespace,
                                                                     command=local_cmd,
                                                                     container=self.container,
                                                                     stderr=True,
                                                                     stdin=True,
                                                                     stdout=True,
                                                                     tty=False,
                                                                     _preload_content=False)
        except ApiException as e:
            AnsibleError("Kubernetes Connection API Error: {0}".format(e.message))
        except Exception as e:
            AnsibleError("Unknown Error: {0}".format(e.message))

        # FIXME: Timeout?
        try:
            while self.response.is_open():
                self.response.update(timeout=2)
                if self.response.peek_stderr():
                    stderr = self.response.read_stderr()
                if self.response.peek_stdout():
                    stdout = self.response.read_stdout()
                    break
                else:
                    time.sleep(2)
        except ApiException as e:
            AnsibleError("Kubernetes Connection API Error: {0}".format(e.message))
        except Exception as e:
            AnsibleError("Unknown Error: {0}".format(e.message))

        return (returncode, stdout, stderr)

    def _prefix_login_path(self, remote_path):
        '''
            NOTE: This method is from the docker connection plugin
            Make sure that we put files into a standard path

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
        '''
            NOTE: This method is a modification from the existing docker.py
            connection plugin.
        '''
        super(Connection, self).put_file(in_path, out_path)
        response = None
        display.vvv("PUT %s TO %s" % (in_path, out_path), host=self._play_context.remote_addr)

        out_path = self._prefix_login_path(out_path)
        if not os.path.exists(to_bytes(in_path, errors='surrogate_or_strict')):
            raise AnsibleFileNotFound(
                "file or module does not exist: %s" % in_path)

        out_path = shlex_quote(out_path)
        exec_command = [
            self._play_context.executable,
            '-c',
            'dd of={0} bs={1}'.format(out_path, BUFSIZE)
        ]

        try:
            with open(to_bytes(in_path, errors='surrogate_or_strict'), 'rb') as in_file:
                display.debug(u"put_file pod_exec: {0}".format(to_text(exec_command)))
                response = self.api.connect_get_namespaced_pod_exec(name=self.name,
                                                                    namespace=self.namespace,
                                                                    command=exec_command,
                                                                    container=self.container,
                                                                    stderr=True,
                                                                    stdin=True,
                                                                    stdout=True,
                                                                    tty=False,
                                                                    _preload_content=False)

                if response.is_open():
                    response.write_stdin(in_file.read())
        except ApiException as e:
            AnsibleError("Kubernetes Connection API Error: {0}".format(e.message))
        except Exception as e:
            AnsibleError("Unknown Error: {0}".format(e.message))
        finally:
            if response is not None:
                response.close()

    def fetch_file(self, in_path, out_path):
        super(Connection, self).fetch_file(in_path, out_path)
        raise AnsibleError("Connection Plugin fetch_file not implemented")

    def close(self):
        ''' terminate the connection'''
        self.response.close()
        self._connected = False
