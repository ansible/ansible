#!/usr/bin/env python

# (c) 2017, Stefan Heitmueller <stefan.heitmueller@gmx.com>
#
# This file is part of Ansible,
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

# Installation
# ------------
#
# pip install docker
#
# curl -L https://gitlab.com/snippets/1661311/raw -o /etc/ansible/docker-swarm-nodes.py && chmod +x /etc/ansible/docker-swarm-nodes.py
#
# create /etc/ansible/docker_swarm_nodes.ini like this:
# ----------------------------------------------------
# [swarm]
#
# docker_host = tcp://my-docker-host:2375
# ----------------------------------------------------
#
# Use it:
# ansible -i /etc/ansible/docker-swarm-nodes.py swarm -m ping
# ansible -i /etc/ansible/docker-swarm-nodes.py manager -m ping
# ansible -i /etc/ansible/docker-swarm-nodes.py worker -m ping
# ansible -i /etc/ansible/docker-swarm-nodes.py single-host-from-swarm -m ping
#

import ConfigParser
import os
import json
import docker


class SwarmNodesInventory(object):

    def __init__(self):
        """ Main execution path """

        # read settings
        self.read_settings()

        # initiate swarm api connection
        self.client = docker.DockerClient(base_url=self.docker_host)

        # build json output for ansible containing hostgroup "swarm"
        self.data = {"swarm": [], "manager": [], "worker": []}
        # get manager nodes
        for self.node in self.client.nodes.list(filters={'role': 'manager'}):
            self.node_hostname = self.client.nodes.get(self.node.id).attrs['Description']['Hostname']
            # append to hostgroup "swarm"
            self.data["swarm"].append(self.node_hostname)
            # append to hostgroup "manager"
            self.data["manager"].append(self.node_hostname)

        # get worker nodes
        for self.node in self.client.nodes.list(filters={'role': 'worker'}):
            self.node_hostname = self.client.nodes.get(self.node.id).attrs['Description']['Hostname']
            # append to hostgroup "swarm"
            self.data["swarm"].append(self.node_hostname)
            # append to hostgroup "worker"
            self.data["worker"].append(self.node_hostname)

        # finally print json
        print(json.dumps(self.data))

    def read_settings(self):
        """ Reads the settings from the docker_swarm_nodes.ini file """

        config = ConfigParser.SafeConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__)) + '/docker_swarm_nodes.ini')

        self.docker_host = config.get('swarm', 'docker_host')

if __name__ == "__main__":
    SwarmNodesInventory()
