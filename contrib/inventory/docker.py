#!/usr/bin/env python
#
# (c) 2016 Paul Durivage <paul.durivage@gmail.com>
#          Chris Houseknecht <house@redhat.com>
#          James Tanner <jtanner@redhat.com>
#
# This file is part of Ansible.
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
#

DOCUMENTATION = '''

Docker Inventory Script
=======================
The inventory script generates dynamic inventory by making API requests to one or more Docker APIs. It's dynamic
because the inventory is generated at run-time rather than being read from a static file. The script generates the
inventory by connecting to one or many Docker APIs and inspecting the containers it finds at each API. Which APIs the
script contacts can be defined using environment variables or a configuration file.

Requirements
------------

Using the docker modules requires having docker-py <https://docker-py.readthedocs.org/en/stable/>
installed on the host running Ansible. To install docker-py:

   pip install docker-py


Run for Specific Host
---------------------
When run for a specific container using the --host option this script returns the following hostvars:

{
    "ansible_ssh_host": "",
    "ansible_ssh_port": 0,
    "docker_apparmorprofile": "",
    "docker_args": [],
    "docker_config": {
        "AttachStderr": false,
        "AttachStdin": false,
        "AttachStdout": false,
        "Cmd": [
            "/hello"
        ],
        "Domainname": "",
        "Entrypoint": null,
        "Env": null,
        "Hostname": "9f2f80b0a702",
        "Image": "hello-world",
        "Labels": {},
        "OnBuild": null,
        "OpenStdin": false,
        "StdinOnce": false,
        "Tty": false,
        "User": "",
        "Volumes": null,
        "WorkingDir": ""
    },
    "docker_created": "2016-04-18T02:05:59.659599249Z",
    "docker_driver": "aufs",
    "docker_execdriver": "native-0.2",
    "docker_execids": null,
    "docker_graphdriver": {
        "Data": null,
        "Name": "aufs"
    },
    "docker_hostconfig": {
        "Binds": null,
        "BlkioWeight": 0,
        "CapAdd": null,
        "CapDrop": null,
        "CgroupParent": "",
        "ConsoleSize": [
            0,
            0
        ],
        "ContainerIDFile": "",
        "CpuPeriod": 0,
        "CpuQuota": 0,
        "CpuShares": 0,
        "CpusetCpus": "",
        "CpusetMems": "",
        "Devices": null,
        "Dns": null,
        "DnsOptions": null,
        "DnsSearch": null,
        "ExtraHosts": null,
        "GroupAdd": null,
        "IpcMode": "",
        "KernelMemory": 0,
        "Links": null,
        "LogConfig": {
            "Config": {},
            "Type": "json-file"
        },
        "LxcConf": null,
        "Memory": 0,
        "MemoryReservation": 0,
        "MemorySwap": 0,
        "MemorySwappiness": null,
        "NetworkMode": "default",
        "OomKillDisable": false,
        "PidMode": "host",
        "PortBindings": null,
        "Privileged": false,
        "PublishAllPorts": false,
        "ReadonlyRootfs": false,
        "RestartPolicy": {
            "MaximumRetryCount": 0,
            "Name": ""
        },
        "SecurityOpt": [
            "label:disable"
        ],
        "UTSMode": "",
        "Ulimits": null,
        "VolumeDriver": "",
        "VolumesFrom": null
    },
    "docker_hostnamepath": "/mnt/sda1/var/lib/docker/containers/9f2f80b0a702361d1ac432e6af816c19bda46da15c21264fb418c873de635a14/hostname",
    "docker_hostspath": "/mnt/sda1/var/lib/docker/containers/9f2f80b0a702361d1ac432e6af816c19bda46da15c21264fb418c873de635a14/hosts",
    "docker_id": "9f2f80b0a702361d1ac432e6af816c19bda46da15c21264fb418c873de635a14",
    "docker_image": "0a6ba66e537a53a5ea94f7c6a99c534c6adb12e3ed09326d4bf3b38f7c3ba4e7",
    "docker_logpath": "/mnt/sda1/var/lib/docker/containers/9f2f80b0a702361d1ac432e6af816c19bda46da15c21264fb418c873de635a14/9f2f80b0a702361d1ac432e6af816c19bda46da15c21264fb418c873de635a14-json.log",
    "docker_mountlabel": "",
    "docker_mounts": [],
    "docker_name": "/hello-world",
    "docker_networksettings": {
        "Bridge": "",
        "EndpointID": "",
        "Gateway": "",
        "GlobalIPv6Address": "",
        "GlobalIPv6PrefixLen": 0,
        "HairpinMode": false,
        "IPAddress": "",
        "IPPrefixLen": 0,
        "IPv6Gateway": "",
        "LinkLocalIPv6Address": "",
        "LinkLocalIPv6PrefixLen": 0,
        "MacAddress": "",
        "Networks": {
            "bridge": {
                "EndpointID": "",
                "Gateway": "",
                "GlobalIPv6Address": "",
                "GlobalIPv6PrefixLen": 0,
                "IPAddress": "",
                "IPPrefixLen": 0,
                "IPv6Gateway": "",
                "MacAddress": ""
            }
        },
        "Ports": null,
        "SandboxID": "",
        "SandboxKey": "",
        "SecondaryIPAddresses": null,
        "SecondaryIPv6Addresses": null
    },
    "docker_path": "/hello",
    "docker_processlabel": "",
    "docker_resolvconfpath": "/mnt/sda1/var/lib/docker/containers/9f2f80b0a702361d1ac432e6af816c19bda46da15c21264fb418c873de635a14/resolv.conf",
    "docker_restartcount": 0,
    "docker_short_id": "9f2f80b0a7023",
    "docker_state": {
        "Dead": false,
        "Error": "",
        "ExitCode": 0,
        "FinishedAt": "2016-04-18T02:06:00.296619369Z",
        "OOMKilled": false,
        "Paused": false,
        "Pid": 0,
        "Restarting": false,
        "Running": false,
        "StartedAt": "2016-04-18T02:06:00.272065041Z",
        "Status": "exited"
    }
}

Groups
------
When run in --list mode (the default), container instances are grouped by:

 - container id
 - container name
 - container short id
 - image_name  (image_<image name>)
 - docker_host
 - running
 - stopped


Configuration:
--------------
You can control the behavior of the inventory script by passing arguments, defining environment variables, or
creating a configuration file named docker.yml (sample provided in ansible/contrib/inventory). The order of precedence
is command line args, then the docker.yml file and finally environment variables.

Environment variables:
......................

To connect to a single Docker API the following variables can be defined in the environment to control the connection
options. These are the same environment variables used by the Docker modules.

    DOCKER_HOST
        The URL or Unix socket path used to connect to the Docker API. Defaults to unix://var/run/docker.sock.

    DOCKER_API_VERSION:
        The version of the Docker API running on the Docker Host. Defaults to the latest version of the API supported
        by docker-py.

    DOCKER_TIMEOUT:
        The maximum amount of time in seconds to wait on a response fromm the API. Defaults to 60 seconds.

    DOCKER_TLS:
        Secure the connection to the API by using TLS without verifying the authenticity of the Docker host server.
        Defaults to False.

    DOCKER_TLS_VERIFY:
        Secure the connection to the API by using TLS and verifying the authenticity of the Docker host server.
        Default is False

    DOCKER_TLS_HOSTNAME:
        When verifying the authenticity of the Docker Host server, provide the expected name of the server. Defaults
        to localhost.

    DOCKER_CERT_PATH:
        Path to the directory containing the client certificate, client key and CA certificate.

    DOCKER_SSL_VERSION:
        Provide a valid SSL version number. Default value determined by docker-py, which at the time of this writing
        was 1.0

In addition to the connection variables there are a couple variables used to control the execution and output of the
script:

    DOCKER_CONFIG_FILE
        Path to the configuration file. Defaults to ./docker.yml.

    DOCKER_PRIVATE_SSH_PORT:
        The private port (container port) on which SSH is listening for connections. Defaults to 22.

    DOCKER_DEFAULT_IP:
        The IP address to assign to ansible_host when the container's SSH port is mapped to interface '0.0.0.0'.


Configuration File
..................

Using a configuration file provides a means for defining a set of Docker APIs from which to build an inventory.

The default name of the file is derived from the name of the inventory script. By default the script will look for
basename of the script (i.e. docker) with an extension of '.yml'.

You can also override the default name of the script by defining DOCKER_CONFIG_FILE in the environment.

Here's what you can define in docker_inventory.yml:

    defaults
        Defines a default connection. Defaults will be taken from this and applied to any values not provided
        for a host defined in the hosts list.

    hosts
        If you wish to get inventory from more than one Docker host, define a hosts list.

For the default host and each host in the hosts list define the following attributes:

  host:
      description: The URL or Unix socket path used to connect to the Docker API.
      required: yes

  tls:
     description: Connect using TLS without verifying the authenticity of the Docker host server.
     default: false
     required: false

  tls_verify:
     description: Connect using TLS without verifying the authenticity of the Docker host server.
     default: false
     required: false

  cert_path:
     description: Path to the client's TLS certificate file.
     default: null
     required: false

  cacert_path:
     description: Use a CA certificate when performing server verification by providing the path to a CA certificate file.
     default: null
     required: false

  key_path:
     description: Path to the client's TLS key file.
     default: null
     required: false

  version:
     description: The Docker API version.
     required: false
     default: will be supplied by the docker-py module.

  timeout:
     description: The amount of time in seconds to wait on an API response.
     required: false
     default: 60

  default_ip:
     description: The IP address to assign to ansible_host when the container's SSH port is mapped to interface
     '0.0.0.0'.
     required: false
     default: 127.0.0.1

  private_ssh_port:
     description: The port containers use for SSH
     required: false
     default: 22

Examples
--------

# Connect to the Docker API on localhost port 4243 and format the JSON output
DOCKER_HOST=tcp://localhost:4243 ./docker.py --pretty

# Any container's ssh port exposed on 0.0.0.0 will be mapped to
# another IP address (where Ansible will attempt to connect via SSH)
DOCKER_DEFAULT_IP=1.2.3.4 ./docker.py --pretty

# Run as input to a playbook:
ansible-playbook -i ~/projects/ansible/contrib/inventory/docker.py docker_inventory_test.yml

# Simple playbook to invoke with the above example:

    - name: Test docker_inventory
      hosts: all
      connection: local
      gather_facts: no
      tasks:
        - debug: msg="Container - {{ inventory_hostname }}"

'''

import os
import sys
import json
import argparse
import re
import yaml

from collections import defaultdict
# Manipulation of the path is needed because the docker-py
# module is imported by the name docker, and because this file
# is also named docker
for path in [os.getcwd(), '', os.path.dirname(os.path.abspath(__file__))]:
    try:
        del sys.path[sys.path.index(path)]
    except:
        pass

HAS_DOCKER_PY = True
HAS_DOCKER_ERROR = False

try:
    from docker import Client
    from docker.errors import APIError, TLSParameterError
    from docker.tls import TLSConfig
    from docker.constants import DEFAULT_TIMEOUT_SECONDS, DEFAULT_DOCKER_API_VERSION
except ImportError as exc:
    HAS_DOCKER_ERROR = str(exc)
    HAS_DOCKER_PY = False

DEFAULT_DOCKER_HOST = 'unix://var/run/docker.sock'
DEFAULT_TLS = False
DEFAULT_TLS_VERIFY = False
DEFAULT_IP = '127.0.0.1'
DEFAULT_SSH_PORT = '22'

BOOLEANS_TRUE = ['yes', 'on', '1', 'true', 1, True]
BOOLEANS_FALSE = ['no', 'off', '0', 'false', 0, False]


DOCKER_ENV_ARGS = dict(
    config_file='DOCKER_CONFIG_FILE',
    docker_host='DOCKER_HOST',
    api_version='DOCKER_API_VERSION',
    cert_path='DOCKER_CERT_PATH',
    ssl_version='DOCKER_SSL_VERSION',
    tls='DOCKER_TLS',
    tls_verify='DOCKER_TLS_VERIFY',
    timeout='DOCKER_TIMEOUT',
    private_ssh_port='DOCKER_DEFAULT_SSH_PORT',
    default_ip='DOCKER_DEFAULT_IP',
)


def fail(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit(1)


def log(msg, pretty_print=False):
    if pretty_print:
        print(json.dumps(msg, sort_keys=True, indent=2))
    else:
        print(msg + u'\n')


class AnsibleDockerClient(Client):
    def __init__(self, auth_params, debug):

        self.auth_params = auth_params
        self.debug = debug
        self._connect_params = self._get_connect_params()

        try:
            super(AnsibleDockerClient, self).__init__(**self._connect_params)
        except APIError as exc:
            self.fail("Docker API error: %s" % exc)
        except Exception as exc:
            self.fail("Error connecting: %s" % exc)

    def fail(self, msg):
        fail(msg)

    def log(self, msg, pretty_print=False):
        if self.debug:
            log(msg, pretty_print)

    def _get_tls_config(self, **kwargs):
        self.log("get_tls_config:")
        for key in kwargs:
            self.log("  %s: %s" % (key, kwargs[key]))
        try:
            tls_config = TLSConfig(**kwargs)
            return tls_config
        except TLSParameterError as exc:
           self.fail("TLS config error: %s" % exc)

    def _get_connect_params(self):
        auth = self.auth_params

        self.log("auth params:")
        for key in auth:
            self.log("  %s: %s" % (key, auth[key]))

        if auth['tls'] or auth['tls_verify']:
            auth['docker_host'] = auth['docker_host'].replace('tcp://', 'https://')

        if auth['tls'] and auth['cert_path'] and auth['key_path']:
            # TLS with certs and no host verification
            tls_config = self._get_tls_config(client_cert=(auth['cert_path'], auth['key_path']),
                                              verify=False,
                                              ssl_version=auth['ssl_version'])
            return dict(base_url=auth['docker_host'],
                        tls=tls_config,
                        version=auth['api_version'],
                        timeout=auth['timeout'])

        if auth['tls']:
            # TLS with no certs and not host verification
            tls_config = self._get_tls_config(verify=False,
                                              ssl_version=auth['ssl_version'])
            return dict(base_url=auth['docker_host'],
                        tls=tls_config,
                        version=auth['api_version'],
                        timeout=auth['timeout'])

        if auth['tls_verify'] and auth['cert_path'] and auth['key_path']:
            # TLS with certs and host verification
            if auth['cacert_path']:
                tls_config = self._get_tls_config(client_cert=(auth['cert_path'], auth['key_path']),
                                                  ca_cert=auth['cacert_path'],
                                                  verify=True,
                                                  assert_hostname=auth['tls_hostname'],
                                                  ssl_version=auth['ssl_version'])
            else:
                tls_config = self._get_tls_config(client_cert=(auth['cert_path'], auth['key_path']),
                                                  verify=True,
                                                  assert_hostname=auth['tls_hostname'],
                                                  ssl_version=auth['ssl_version'])

            return dict(base_url=auth['docker_host'],
                        tls=tls_config,
                        version=auth['api_version'],
                        timeout=auth['timeout'])

        if auth['tls_verify'] and auth['cacert_path']:
            # TLS with cacert only
            tls_config = self._get_tls_config(ca_cert=auth['cacert_path'],
                                              assert_hostname=auth['tls_hostname'],
                                              verify=True,
                                              ssl_version=auth['ssl_version'])
            return dict(base_url=auth['docker_host'],
                        tls=tls_config,
                        version=auth['api_version'],
                        timeout=auth['timeout'])

        if auth['tls_verify']:
            # TLS with verify and no certs
            tls_config = self._get_tls_config(verify=True,
                                              assert_hostname=auth['tls_hostname'],
                                              ssl_version=auth['ssl_version'])
            return dict(base_url=auth['docker_host'],
                        tls=tls_config,
                        version=auth['api_version'],
                        timeout=auth['timeout'])
        # No TLS
        return dict(base_url=auth['docker_host'],
                    version=auth['api_version'],
                    timeout=auth['timeout'])

    def _handle_ssl_error(self, error):
        match = re.match(r"hostname.*doesn\'t match (\'.*\')", str(error))
        if match:
            msg = "You asked for verification that Docker host name matches %s. The actual hostname is %s. " \
                "Most likely you need to set DOCKER_TLS_HOSTNAME or pass tls_hostname with a value of %s. " \
                "You may also use TLS without verification by setting the tls parameter to true." \
                 % (self.auth_params['tls_hostname'], match.group(1))
            self.fail(msg)
        self.fail("SSL Exception: %s" % (error))


class EnvArgs(object):
    def __init__(self):
        self.config_file = None
        self.docker_host = None
        self.api_version = None
        self.cert_path = None
        self.ssl_version = None
        self.tls = None
        self.tls_verify = None
        self.tls_hostname = None
        self.timeout = None
        self.default_ssh_port = None
        self.default_ip = None


class DockerInventory(object):

    def __init__(self):
        self._args = self._parse_cli_args()
        self._env_args = self._parse_env_args()
        self.groups = defaultdict(list)
        self.hostvars = defaultdict(dict)

    def run(self):
        config_from_file = self._parse_config_file()
        if not config_from_file:
            config_from_file = dict()
        docker_hosts = self.get_hosts(config_from_file)

        for host in docker_hosts:
            client = AnsibleDockerClient(host, self._args.debug)
            self.get_inventory(client, host)

        if not self._args.host:
            self.groups['docker_hosts'] = [host.get('docker_host') for host in docker_hosts]
            self.groups['_meta'] = dict(
                hostvars=self.hostvars
            )
            print(self._json_format_dict(self.groups, pretty_print=self._args.pretty))
        else:
            print(self._json_format_dict(self.hostvars.get(self._args.host, dict()), pretty_print=self._args.pretty))

        sys.exit(0)

    def get_inventory(self, client, host):

        ssh_port = host.get('default_ssh_port')
        default_ip = host.get('default_ip')
        hostname = host.get('docker_host')

        try:
            containers = client.containers(all=True)
        except Exception as exc:
            self.fail("Error fetching containers for host %s - %s" % (hostname, str(exc)))

        for container in containers:
            id = container.get('Id')
            short_id = id[:13]

            try:
                name = container.get('Names', list()).pop(0).lstrip('/')
            except IndexError:
                name = short_id

            if not self._args.host or (self._args.host and self._args.host in [name, id, short_id]):
                try:
                    inspect = client.inspect_container(id)
                except Exception as exc:
                    self.fail("Error inspecting container %s - %s" % (name, str(exc)))

                running = inspect.get('State', dict()).get('Running')

                # Add container to groups
                image_name = inspect.get('Config', dict()).get('Image')
                if image_name:
                    self.groups["image_%s" % (image_name)].append(name)

                self.groups[id].append(name)
                self.groups[name].append(name)
                if short_id not in self.groups:
                    self.groups[short_id].append(name)
                self.groups[hostname].append(name)

                if running is True:
                    self.groups['running'].append(name)
                else:
                    self.groups['stopped'].append(name)

                # Figure ous ssh IP and Port
                try:
                    # Lookup the public facing port Nat'ed to ssh port.
                    port = client.port(container, ssh_port)[0]
                except (IndexError, AttributeError, TypeError):
                    port = dict()

                try:
                    ip = default_ip if port['HostIp'] == '0.0.0.0' else port['HostIp']
                except KeyError:
                    ip = ''

                facts = dict(
                    ansible_ssh_host=ip,
                    ansible_ssh_port=port.get('HostPort', int()),
                    docker_name=name,
                    docker_short_id=short_id
                )

                for key in inspect:
                    fact_key = self._slugify(key)
                    facts[fact_key] = inspect.get(key)

                self.hostvars[name].update(facts)

    def _slugify(self, value):
        return 'docker_%s' % (re.sub('[^\w-]', '_', value).lower().lstrip('_'))

    def get_hosts(self, config):
        '''
        Determine the list of docker hosts we need to talk to.

        :param config: dictionary read from config file. can be empty.
        :return: list of connection dictionaries
        '''
        hosts = list()

        hosts_list = config.get('hosts')
        defaults = config.get('defaults', dict())
        self.log('defaults:')
        self.log(defaults, pretty_print=True)
        def_host = defaults.get('host')
        def_tls = defaults.get('tls')
        def_tls_verify = defaults.get('tls_verify')
        def_tls_hostname = defaults.get('tls_hostname')
        def_ssl_version = defaults.get('ssl_version')
        def_cert_path = defaults.get('cert_path')
        def_cacert_path = defaults.get('cacert_path')
        def_key_path = defaults.get('key_path')
        def_version = defaults.get('version')
        def_timeout = defaults.get('timeout')
        def_ip = defaults.get('default_ip')
        def_ssh_port = defaults.get('private_ssh_port')

        if hosts_list:
            # use hosts from config file
            for host in hosts_list:
                docker_host = host.get('host') or def_host or self._args.docker_host or \
                              self._env_args.docker_host or DEFAULT_DOCKER_HOST
                api_version = host.get('version') or def_version or self._args.api_version or \
                    self._env_args.api_version or DEFAULT_DOCKER_API_VERSION
                tls_hostname = host.get('tls_hostname') or def_tls_hostname or self._args.tls_hostname or \
                    self._env_args.tls_hostname
                tls_verify = host.get('tls_verify') or def_tls_verify or self._args.tls_verify or \
                    self._env_args.tls_verify or DEFAULT_TLS_VERIFY
                tls = host.get('tls') or def_tls or self._args.tls or self._env_args.tls or DEFAULT_TLS
                ssl_version = host.get('ssl_version') or def_ssl_version or self._args.ssl_version or \
                    self._env_args.ssl_version

                cert_path = host.get('cert_path') or def_cert_path or self._args.cert_path or \
                    self._env_args.cert_path
                if cert_path and cert_path == self._env_args.cert_path:
                    cert_path = os.path.join(cert_path, 'cert.pem')

                cacert_path = host.get('cacert_path') or def_cacert_path or self._args.cacert_path or \
                    self._env_args.cert_path
                if cacert_path and cacert_path == self._env_args.cert_path:
                    cacert_path = os.path.join(cacert_path, 'ca.pem')

                key_path = host.get('key_path') or def_key_path or self._args.key_path or \
                    self._env_args.cert_path
                if key_path and key_path == self._env_args.cert_path:
                    key_path = os.path.join(key_path, 'key.pem')

                timeout = host.get('timeout') or def_timeout or self._args.timeout or self._env_args.timeout or \
                    DEFAULT_TIMEOUT_SECONDS
                default_ip = host.get('default_ip') or def_ip or self._args.default_ip_address or \
                    DEFAULT_IP
                default_ssh_port = host.get('private_ssh_port') or def_ssh_port or self._args.private_ssh_port or \
                    DEFAULT_SSH_PORT
                host_dict = dict(
                    docker_host=docker_host,
                    api_version=api_version,
                    tls=tls,
                    tls_verify=tls_verify,
                    tls_hostname=tls_hostname,
                    cert_path=cert_path,
                    cacert_path=cacert_path,
                    key_path=key_path,
                    ssl_version=ssl_version,
                    timeout=timeout,
                    default_ip=default_ip,
                    default_ssh_port=default_ssh_port,
                )
                hosts.append(host_dict)
        else:
            # use default definition
            docker_host = def_host or self._args.docker_host or self._env_args.docker_host or DEFAULT_DOCKER_HOST
            api_version = def_version or self._args.api_version or self._env_args.api_version or \
                DEFAULT_DOCKER_API_VERSION
            tls_hostname = def_tls_hostname or self._args.tls_hostname or self._env_args.tls_hostname
            tls_verify = def_tls_verify or self._args.tls_verify or self._env_args.tls_verify or DEFAULT_TLS_VERIFY
            tls = def_tls or self._args.tls or self._env_args.tls or DEFAULT_TLS
            ssl_version = def_ssl_version or self._args.ssl_version or self._env_args.ssl_version

            cert_path = def_cert_path or self._args.cert_path or self._env_args.cert_path
            if cert_path and cert_path == self._env_args.cert_path:
                    cert_path = os.path.join(cert_path, 'cert.pem')

            cacert_path = def_cacert_path or self._args.cacert_path or self._env_args.cert_path
            if cacert_path and cacert_path == self._env_args.cert_path:
                cacert_path = os.path.join(cacert_path, 'ca.pem')

            key_path = def_key_path or self._args.key_path or self._env_args.cert_path
            if key_path and key_path == self._env_args.cert_path:
                key_path = os.path.join(key_path, 'key.pem')

            timeout = def_timeout or self._args.timeout or self._env_args.timeout or DEFAULT_TIMEOUT_SECONDS
            default_ip = def_ip or self._args.default_ip_address or DEFAULT_IP
            default_ssh_port = def_ssh_port or self._args.private_ssh_port or DEFAULT_SSH_PORT
            host_dict = dict(
                docker_host=docker_host,
                api_version=api_version,
                tls=tls,
                tls_verify=tls_verify,
                tls_hostname=tls_hostname,
                cert_path=cert_path,
                cacert_path=cacert_path,
                key_path=key_path,
                ssl_version=ssl_version,
                timeout=timeout,
                default_ip=default_ip,
                default_ssh_port=default_ssh_port,
            )
            hosts.append(host_dict)
        self.log("hosts: ")
        self.log(hosts, pretty_print=True)
        return hosts

    def _parse_config_file(self):
        config = dict()
        config_path = None

        if self._args.config_file:
            config_path = self._args.config_file
        elif self._env_args.config_file:
            config_path = self._env_args.config_file

        if config_path:
            try:
                config_file = os.path.abspath(config_path)
            except:
                config_file = None

            if config_file and os.path.exists(config_file):
                with open(config_file) as f:
                    try:
                        config = yaml.safe_load(f.read())
                    except Exception as exc:
                        self.fail("Error: parsing %s - %s" % (config_path, str(exc)))
        return config

    def log(self, msg, pretty_print=False):
        if self._args.debug:
            log(msg, pretty_print)

    def fail(self, msg):
        fail(msg)

    def _parse_env_args(self):
        args = EnvArgs()
        for key, value in DOCKER_ENV_ARGS.items():
            if os.environ.get(value):
                val = os.environ.get(value)
                if val in BOOLEANS_TRUE:
                    val = True
                if val in BOOLEANS_FALSE:
                    val = False
                setattr(args, key, val)
        return args

    def _parse_cli_args(self):
        # Parse command line arguments

        basename = os.path.splitext(os.path.basename(__file__))[0]
        default_config = basename + '.yml'

        parser = argparse.ArgumentParser(
                description='Return Ansible inventory for one or more Docker hosts.')
        parser.add_argument('--list', action='store_true', default=True,
                           help='List all containers (default: True)')
        parser.add_argument('--debug', action='store_true', default=False,
                           help='Send debug messages to STDOUT')
        parser.add_argument('--host', action='store',
                            help='Only get information for a specific container.')
        parser.add_argument('--pretty', action='store_true', default=False,
                           help='Pretty print JSON output(default: False)')
        parser.add_argument('--config-file', action='store', default=default_config,
                            help="Name of the config file to use. Default is %s" % (default_config))
        parser.add_argument('--docker-host', action='store', default=None,
                            help="The base url or Unix sock path to connect to the docker daemon. Defaults to %s"
                                  % (DEFAULT_DOCKER_HOST))
        parser.add_argument('--tls-hostname', action='store', default='localhost',
                            help="Host name to expect in TLS certs. Defaults to 'localhost'")
        parser.add_argument('--api-version', action='store', default=None,
                            help="Docker daemon API version. Defaults to %s" % (DEFAULT_DOCKER_API_VERSION))
        parser.add_argument('--timeout', action='store', default=None,
                            help="Docker connection timeout in seconds. Defaults to %s"
                                  % (DEFAULT_TIMEOUT_SECONDS))
        parser.add_argument('--cacert-path', action='store', default=None,
                            help="Path to the TLS certificate authority pem file.")
        parser.add_argument('--cert-path', action='store', default=None,
                            help="Path to the TLS certificate pem file.")
        parser.add_argument('--key-path', action='store', default=None,
                            help="Path to the TLS encryption key pem file.")
        parser.add_argument('--ssl-version', action='store', default=None,
                            help="TLS version number")
        parser.add_argument('--tls', action='store_true', default=None,
                            help="Use TLS. Defaults to %s" % (DEFAULT_TLS))
        parser.add_argument('--tls-verify', action='store_true', default=None,
                            help="Verify TLS certificates. Defaults to %s" % (DEFAULT_TLS_VERIFY))
        parser.add_argument('--private-ssh-port', action='store', default=None,
                            help="Default private container SSH Port. Defaults to %s" % (DEFAULT_SSH_PORT))
        parser.add_argument('--default-ip-address', action='store', default=None,
                            help="Default container SSH IP address. Defaults to %s" % (DEFAULT_IP))
        return parser.parse_args()

    def _json_format_dict(self, data, pretty_print=False):
        # format inventory data for output
        if pretty_print:
            return json.dumps(data, sort_keys=True, indent=4)
        else:
            return json.dumps(data)


def main():

    if not HAS_DOCKER_PY:
        fail("Failed to import docker-py. Try `pip install docker-py` - %s" % (HAS_DOCKER_ERROR))

    DockerInventory().run()

main()
