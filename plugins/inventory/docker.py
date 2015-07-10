#!/usr/bin/env python

# (c) 2013, Paul Durivage <paul.durivage@gmail.com>
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
#
# Author: Paul Durivage <paul.durivage@gmail.com>
#
# Description:
# This module queries local or remote Docker daemons and generates
# inventory information.
#
# This plugin does not support targeting of specific hosts using the --host
# flag. Instead, it queries the Docker API for each container, running
# or not, and returns this data all once.
#
# The plugin returns the following custom attributes on Docker containers:
#    docker_args
#    docker_config
#    docker_created
#    docker_driver
#    docker_exec_driver
#    docker_host_config
#    docker_hostname_path
#    docker_hosts_path
#    docker_id
#    docker_image
#    docker_name
#    docker_network_settings
#    docker_path
#    docker_resolv_conf_path
#    docker_state
#    docker_volumes
#    docker_volumes_rw
#
# Requirements:
# The docker-py module version >= 0.6.0: https://github.com/dotcloud/docker-py
#
# Notes:
# A config file can be used to configure this inventory module, and there
# are several environment variables that can be set to modify the behavior
# of the plugin at runtime:
#    DOCKER_CONFIG_FILE
#    DOCKER_HOST
#    DOCKER_VERSION
#    DOCKER_TIMEOUT
#    DOCKER_TLS_VERIFY
#    DOCKER_SSL_VERSION
#    DOCKER_ASSERT_HOSTNAME
#    DOCKER_CERT_PATH
#    DOCKER_PRIVATE_SSH_PORT
#    DOCKER_DEFAULT_IP
#
# Environment Variables:
# environment variable: DOCKER_CONFIG_FILE
#     description:
#         - A path to a Docker inventory hosts/defaults file in YAML format
#         - A sample file has been provided, colocated with the inventory
#           file called 'docker.yml'
#     required: false
#     default: Uses docker.docker.Client constructor defaults
# environment variable: DOCKER_HOST
#     description:
#         - The socket on which to connect to a Docker daemon API
#     required: false
#     default: Uses docker.docker.Client constructor defaults
# environment variable: DOCKER_VERSION
#     description:
#         - Version of the Docker API to use
#     default: Uses docker.docker.Client constructor defaults
#     required: false
# environment variable: DOCKER_TIMEOUT
#     description:
#         - Timeout in seconds for connections to Docker daemon API
#     default: Uses docker.docker.Client constructor defaults
#     required: false
# environment variable: DOCKER_TLS_VERIFY
#     description:
#         - Sets client-side TLS certificate verification.
#     default: Uses docker.utils.kwargs_from_env function defaults
#     required: false
# environment variable: DOCKER_SSL_VERSION
#     description:
#         - Sets TLS version used.
#           See: https://docs.python.org/3.4/library/ssl.html#ssl.PROTOCOL_TLSv1
#     default: TLSv1 
#     required: false
# environment variable: DOCKER_ASSERT_HOSTNAME
#     description:
#         - Sets the TLS library server certificate CN assertion behaviour
#         - If True: asserts that the CN equals the hostname in the url 
#           (default value)
#         - If False: no CN assertion takes place
#         - Some string: asserts that the CN matches the given string
#     default: True
#     required: false
# environment variable: DOCKER_CERT_PATH
#     description: 
#         - File system path to the directory holding:
#             - ca.pem (CA certificate)
#             - cert.pem (client certificate)
#             - key.pem (client certificate key)
#     default: Uses docker.utils.kwargs_from_env function defaults
#     required: false
# environment variable: DOCKER_PRIVATE_SSH_PORT
#     description:
#         - The private port (container port) on which SSH is listening
#           for connections
#     default: 22
#     required: false
# environment variable: DOCKER_DEFAULT_IP
#     description:
#         - This environment variable overrides the container SSH connection
#           IP address (aka, 'ansible_ssh_host')
#
#           This option allows one to override the ansible_ssh_host whenever
#           Docker has exercised its default behavior of binding private ports
#           to all interfaces of the Docker host.  This behavior, when dealing
#           with remote Docker hosts, does not allow Ansible to determine
#           a proper host IP address on which to connect via SSH to containers.
#           By default, this inventory module assumes all 0.0.0.0-exposed
#           ports to be bound to localhost:<port>.  To override this
#           behavior, for example, to bind a container's SSH port to the public
#           interface of its host, one must manually set this IP.
#
#           It is preferable to begin to launch Docker containers with
#           ports exposed on publicly accessible IP addresses, particularly
#           if the containers are to be targeted by Ansible for remote
#           configuration, not accessible via localhost SSH connections.
#
#           Docker containers can be explicitly exposed on IP addresses by
#           a) starting the daemon with the --ip argument
#           b) running containers with the -P/--publish ip::containerPort
#              argument
#     default: 127.0.0.1 if port exposed on 0.0.0.0 by Docker
#     required: false
#
# Examples:
#  Use the config file:
#  DOCKER_CONFIG_FILE=./docker.yml docker.py --list
#
#  Connect to docker instance on localhost port 4243
#  DOCKER_HOST=tcp://localhost:4243 docker.py --list
#
#  Any container's ssh port exposed on 0.0.0.0 will mapped to
#  another IP address (where Ansible will attempt to connect via SSH)
#  DOCKER_DEFAULT_IP=1.2.3.4 docker.py --list

import os
import sys
import json
import argparse

from collections import defaultdict

import yaml

from requests import HTTPError, ConnectionError

# Manipulation of the path is needed because the docker-py
# module is imported by the name docker, and because this file
# is also named docker
for path in [os.getcwd(), '', os.path.dirname(os.path.abspath(__file__))]:
    try:
        del sys.path[sys.path.index(path)]
    except:
        pass

try:
    import docker
except ImportError:
    print('docker-py is required for this module')
    sys.exit(1)


def write_stderr(string):
    sys.stderr.write('%s\n' % string)


def setup():
    config = dict()
    config_file = os.environ.get('DOCKER_CONFIG_FILE')
    if config_file:
        try:
            config_file = os.path.abspath(config_file)
        except Exception as e:
            write_stderr(e)
            sys.exit(1)

        with open(config_file) as f:
            try:
                config = yaml.safe_load(f.read())
            except Exception as e:
                write_stderr(e)
                sys.exit(1)

    # Environment Variables
    env_vars = dict()
    env_ssl_version =  os.environ.get('DOCKER_SSL_VERSION', 'TLSv1')
    env_assert_hostname =  os.environ.get('DOCKER_ASSERT_HOSTNAME', None)
    if isinstance(env_assert_hostname, str):
        if env_assert_hostname.lower() == 'false':
            env_assert_hostname = False
        elif env_assert_hostname.lower() == 'true':
            env_assert_hostname = None
    env_vars['server'] = docker.utils.kwargs_from_env(
        ssl_version=env_ssl_version, assert_hostname=env_assert_hostname)
    env_vars['ssh_port'] = os.environ.get('DOCKER_PRIVATE_SSH_PORT', '22')
    env_vars['default_ip'] = os.environ.get('DOCKER_DEFAULT_IP', '127.0.0.1')
    # Config file defaults
    defaults = dict()
    if config:
        defaults = config.get('defaults', dict())
    # Compatibility with old server configuration
    if defaults:
        if not defaults.get('server'):
            defaults['server'] = dict()
            if defaults.get('host'):
                defaults['server']['base_url'] = defaults.pop('host')
            if defaults.get('version'):
                defaults['server']['version'] = defaults.pop('version')
            if defaults.get('timeout'):
                defaults['server']['timeout'] = defaults.pop('timeout')
            defaults['server']['tls_config'] = 'None'

    hosts = list()

    if config:
        env_server = env_vars.pop('server', dict())
        default_server = defaults.pop('server', dict())
        hosts_list = config.get('hosts', list())
        # Look to the config file's defined hosts
        if hosts_list:
            for host in hosts_list:
                # Compatibility with old server configuration
                if not host.get('server'):
                    host['server'] = dict()
                    if host.get('host'):
                        host['server']['base_url'] = host.pop('host')
                    if host.get('version'):
                        host['server']['version'] = host.pop('version')
                    if host.get('timeout'):
                        host['server']['timeout'] = host.pop('timeout')
                    host['server']['tls_config'] = 'None'
                
                host_server = host.pop('server')

                # Host configuration
                host_config = dict()
                host_config.update(env_vars)
                host_config.update(defaults)
                host_config.update(host)
                # Per-host server connection configuration
                host_config_server = dict()
                host_config_server.update(env_server)
                host_config_server.update(default_server)
                host_config_server.update(host_server)
                host_config['server'] = host_config_server
                hosts.append(host_config)
        # Look to the defaults
        else:
            host_config = dict()
            host_config.update(defaults)
            hosts.append(host_config)
    # Look to the environment
    else:
        host_config = dict()
        host_config.update(env_vars)
        hosts.append(host_config)

    return hosts


def list_groups():
    hosts = setup()
    groups = defaultdict(list)
    hostvars = defaultdict(dict)

    for host in hosts:
        server = host.get('server', None)
        ssh_port = host.get('private_ssh_port', None)
        default_ip = host.get('default_ip', None)
        hostname = server.get('base_url')

        # Setup tls_config
        if server.has_key('tls_config'):
            tls_config = server.pop('tls_config')
            if isinstance(tls_config,dict):
                try:
                    tls = docker.tls.TLSConfig(**tls_config)
                    server['tls'] = tls
                except TypeError as e:
                    write_stderr("Error parsing host tls_config.")
                    write_stderr(tls_config)
                    write_stderr(e)
                    sys.exit(1)
            else:
                server.pop('tls', None)

        try:
            client = docker.Client(**server)
            containers = client.containers(all=True)
        except (HTTPError, ConnectionError) as e:
            write_stderr(e)
            sys.exit(1)

        for container in containers:
            id = container.get('Id')
            short_id = id[:13]
            try:
                name = container.get('Names', list()).pop(0).lstrip('/')
            except IndexError:
                name = short_id

            if not id:
                continue

            inspect = client.inspect_container(id)
            running = inspect.get('State', dict()).get('Running')

            groups[id].append(name)
            groups[name].append(name)
            if not short_id in groups.keys():
                groups[short_id].append(name)
            groups[hostname].append(name)

            if running is True:
                groups['running'].append(name)
            else:
                groups['stopped'].append(name)

            try:
                port = client.port(container, ssh_port)[0]
            except (IndexError, AttributeError, TypeError):
                port = dict()

            try:
                ip = default_ip if port['HostIp'] == '0.0.0.0' else port['HostIp']
            except KeyError:
                ip = ''

            container_info = dict(
                ansible_ssh_host=ip,
                ansible_ssh_port=port.get('HostPort', int()),
                docker_args=inspect.get('Args'),
                docker_config=inspect.get('Config'),
                docker_created=inspect.get('Created'),
                docker_driver=inspect.get('Driver'),
                docker_exec_driver=inspect.get('ExecDriver'),
                docker_host_config=inspect.get('HostConfig'),
                docker_hostname_path=inspect.get('HostnamePath'),
                docker_hosts_path=inspect.get('HostsPath'),
                docker_id=inspect.get('ID'),
                docker_image=inspect.get('Image'),
                docker_name=name,
                docker_network_settings=inspect.get('NetworkSettings'),
                docker_path=inspect.get('Path'),
                docker_resolv_conf_path=inspect.get('ResolvConfPath'),
                docker_state=inspect.get('State'),
                docker_volumes=inspect.get('Volumes'),
                docker_volumes_rw=inspect.get('VolumesRW'),
            )

            hostvars[name].update(container_info)

    groups['docker_hosts'] = list(set(
        [host.get('server', {}).get('base_url') for host in hosts]))
    groups['_meta'] = dict()
    groups['_meta']['hostvars'] = hostvars
    print json.dumps(groups, sort_keys=True, indent=4)
    sys.exit(0)


def parse_args():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true')
    group.add_argument('--host', action='store_true')
    return parser.parse_args()


def main():
    args = parse_args()
    if args.list:
        list_groups()
    elif args.host:
        write_stderr('This option is not supported.')
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    main()
