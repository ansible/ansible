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
# flag. Instead, it it queries the Docker API for each container, running
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
# The docker-py module: https://github.com/dotcloud/docker-py
#
# Notes:
# A config file can be used to configure this inventory module, and there
# are several environment variables that can be set to modify the behavior
# of the plugin at runtime:
#    DOCKER_CONFIG_FILE
#    DOCKER_HOST
#    DOCKER_VERSION
#    DOCKER_TIMEOUT
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

from UserDict import UserDict
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


class HostDict(UserDict):
    def __setitem__(self, key, value):
        if value is not None:
            self.data[key] = value

    def update(self, dict=None, **kwargs):
        if dict is None:
            pass
        elif isinstance(dict, UserDict):
            for k, v in dict.data.items():
                self[k] = v
        else:
            for k, v in dict.items():
                self[k] = v
        if len(kwargs):
            for k, v in kwargs.items():
                self[k] = v


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

    # Enviroment Variables
    env_base_url = os.environ.get('DOCKER_HOST')
    env_version = os.environ.get('DOCKER_VERSION')
    env_timeout = os.environ.get('DOCKER_TIMEOUT')
    env_ssh_port = os.environ.get('DOCKER_PRIVATE_SSH_PORT', '22')
    env_default_ip = os.environ.get('DOCKER_DEFAULT_IP', '127.0.0.1')
    # Config file defaults
    defaults = config.get('defaults', dict())
    def_host = defaults.get('host')
    def_version = defaults.get('version')
    def_timeout = defaults.get('timeout')
    def_default_ip = defaults.get('default_ip')
    def_ssh_port = defaults.get('private_ssh_port')

    hosts = list()

    if config:
        hosts_list = config.get('hosts', list())
        # Look to the config file's defined hosts
        if hosts_list:
            for host in hosts_list:
                baseurl = host.get('host') or def_host or env_base_url
                version = host.get('version') or def_version or env_version
                timeout = host.get('timeout') or def_timeout or env_timeout
                default_ip = host.get('default_ip') or def_default_ip or env_default_ip
                ssh_port = host.get('private_ssh_port') or def_ssh_port or env_ssh_port

                hostdict = HostDict(
                    base_url=baseurl,
                    version=version,
                    timeout=timeout,
                    default_ip=default_ip,
                    private_ssh_port=ssh_port,
                )
                hosts.append(hostdict)
        # Look to the defaults
        else:
            hostdict = HostDict(
                base_url=def_host,
                version=def_version,
                timeout=def_timeout,
                default_ip=def_default_ip,
                private_ssh_port=def_ssh_port,
            )
            hosts.append(hostdict)
    # Look to the environment
    else:
        hostdict = HostDict(
            base_url=env_base_url,
            version=env_version,
            timeout=env_timeout,
            default_ip=env_default_ip,
            private_ssh_port=env_ssh_port,
        )
        hosts.append(hostdict)

    return hosts


def list_groups():
    hosts = setup()
    groups = defaultdict(list)
    hostvars = defaultdict(dict)

    for host in hosts:
        ssh_port = host.pop('private_ssh_port', None)
        default_ip = host.pop('default_ip', None)
        hostname = host.get('base_url')

        try:
            client = docker.Client(**host)
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

    groups['docker_hosts'] = [host.get('base_url') for host in hosts]
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


main()
