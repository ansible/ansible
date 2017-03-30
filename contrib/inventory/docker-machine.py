#!/usr/bin/env python

# Copyright (C) 2017 Brice Burgess <nesta@iceburg.net>
#
# This script is free software: you can redistribute it and/or modify
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
# along with it.  If not, see <http://www.gnu.org/licenses/>.

"""
Polls available docker machines and creates Ansible inventory, including
docker engine connection information.

Requires:
  * docker-machine - https://github.com/docker/machine/

Example Usage:
$ ansible -i docker-machine.py machinename -m ping

Example Playbook Usage (demonstrates interfacing with remote docker engine):
- docker_service:
    project_src: "/home/acme/compositions/acme-website"
    state: present
    docker_host: "{{ docker_engine_host }}"
    cacert_path: "{{ docker_engine_tlscacert }}"
    cert_path: "{{ docker_engine_tlscert }}"
    key_path: "{{ docker_engine_tlskey }}"
    tls: yes
  delegate_to: 127.0.0.1

Example Output:
{
  "_meta": {
    "hostvars": {
      "node-a": {
        "ansible_host": "172.16.0.8",
        "ansible_port": 22,
        "ansible_private_key_file": "/home/acme/.docker/machine/machines/node-a/id_rsa",
        "ansible_user": "root",
        "docker_engine_host": "tcp://172.16.0.8:2376",
        "docker_engine_tlscacert": "/home/acme/.docker/machine/machines/node-a/ca.pem",
        "docker_engine_tlscert": "/home/acme/.docker/machine/machines/node-a/cert.pem",
        "docker_engine_tlskey": "/home/acme/.docker/machine/machines/node-a/key.pem"
      },
      "node-b": {
        "ansible_host": "172.16.0.9",
        "ansible_port": 22,
        "ansible_private_key_file": "/home/acme/.docker/machine/machines/node-b/id_rsa",
        "ansible_user": "root",
        "docker_engine_host": "tcp://172.16.0.9:2376",
        "docker_engine_tlscacert": "/home/acme/.docker/machine/machines/node-b/ca.pem",
        "docker_engine_tlscert": "/home/acme/.docker/machine/machines/node-b/cert.pem",
        "docker_engine_tlskey": "/home/acme/.docker/machine/machines/node-b/key.pem"
      }
    }
  },
  "node-a": {
    "hosts": [
      "node-a"
    ]
  },
  "node-b": {
    "hosts": [
      "node-b"
    ]
  }
}
"""

import argparse
import subprocess

try:
    import json
except ImportError:
    import simplejson as json


def dm(*args):
    try:
        return subprocess.check_output(["docker-machine"] + list(args)).strip()
    except:
        sys.stderr.write("docker-machine call failed")
        sys.exit(-1)


class DockerMachineInventory(object):

    def __init__(self):
        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file from available docker-machines')
        parser.add_argument('--pretty', '-p', action='store_true', help='Pretty-print results')
        self.args = parser.parse_args()

        '''build inventory'''
        self.inventory = {"_meta": {"hostvars": {}}}
        for m in dm("ls", "-q").splitlines():
            self.inventory[m] = {"hosts": [m]}
            self.inventory["_meta"]["hostvars"][m] = self.read_machine_vars(m)

        if self.args.pretty:
            print(json.dumps(self.inventory, sort_keys=True, indent=2))
        else:
            print(json.dumps(self.inventory))

    def read_machine_vars(self, m):
        machine_config = json.loads(dm("inspect", m))
        return {
            'ansible_host': machine_config["Driver"]["IPAddress"],
            'ansible_user': machine_config["Driver"].get("SSHUser", "root"),
            'ansible_port': machine_config["Driver"].get("SSHPort", 22),
            'ansible_private_key_file': machine_config["Driver"].get("SSHKeyPath", "%s/machines/%s/id_rsa" % (machine_config["Driver"]["StorePath"], m)),
            'docker_engine_host': "tcp://%s:%d" % (machine_config["Driver"]["IPAddress"], machine_config["Driver"].get("EnginePort", 2376)),
            'docker_engine_tlscacert': "%s/machines/%s/ca.pem" % (machine_config["Driver"]["StorePath"], m),
            'docker_engine_tlscert': "%s/machines/%s/cert.pem" % (machine_config["Driver"]["StorePath"], m),
            'docker_engine_tlskey': "%s/machines/%s/key.pem" % (machine_config["Driver"]["StorePath"], m)
        }

if __name__ == '__main__':
    DockerMachineInventory()
