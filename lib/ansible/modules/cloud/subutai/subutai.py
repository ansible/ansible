#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2018 Fernando H R Silva <liquuid@gmail.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: subutai
short_description: Subutai container module. This modules manage all life cicle of subutai containers.
description:
    - Subutai is a daemon written in Golang whose main task is to receive commands from the Subutai Social
      management server and execute them on Resource Hosts.
      Behind such a seemingly simple task are complex procedures like bidirectional ssl communication, gpg
      message encryption, different health and security checks, etc.

version_added: "2.6"
options:
  name:
    description:
      - Name of container or network.
  network:
    description:
      - Define network operations, like  Configuring network tunnel for containers in subutai, vxlan tunnels,
        and network maps.

        Subutai VXLAN is network layer built on top of P2P swarms and intended to be environment communication
        bridges between physically separate hosts. Each Subutai environment has its own separate VXLAN tunnel
        so all internal network traffic goes through isolated channels, doesn't matter if environment located
        on single peer or distributed between multiple peers.

        The tunnel feature is based on SSH tunnels and works in combination with Subutai Helpers and serves as
        an easy solution for bypassing NATs. In Subutai, tunnels are used to access the SS management server's
        web UI from the Bazaar, and open direct connection to containers, etc. There are two types of channels
        local (default), which is created from destination address to host and global, from destination to
        Subutai Helper node. Tunnels may also be set to be permanent (default) or temporary (ttl in seconds).
        The default destination port is 22.

        Subutai tunnels have a continuous state checking mechanism which keeps opened tunnels alive and closes
        outdated tunnels to keep the system network connections clean. This mechanism may re-create a tunnel if
        it was dropped unintentionally (system reboot, network interruption, etc.), but newly created tunnels
        will have different "entrance" address.
    choices: [ 'tunnel', 'map', 'vxlan', 'proxy' ]
  state:
    description:
      - Indicates the desired container state are installed.
    default: 'present'
    choices: [ 'absent', 'present', 'latest', 'started', 'stopped' ]
  check:
    description:
      - Check for updates without installation.
    type: bool
  source:
    description:
      - Set the source for promoting.
  ipaddr:
    description:
      - IPv4 address, ie 192.168.1.1/24
  vlan:
    description:
      - VLAN tag.
  ttl:
    description:
      - Tunnels may also be set to be permanent or temporary (ttl in seconds).
  globalFlag:
    description:
      - There are two types of channels - local, which is created from destination address to host and global from destination to Subutai Helper node.
    type: bool
  template:
    description:
      - A flag to specify if changes will affect template or a container
    type: bool
  protocol:
    description:
      - Specifies required protocol for mapping and might be http, https, tcp or udp.
    choices: [ 'http', 'https', 'tcp', 'udp' ]
  internal:
    description:
      - Peer's internal socket that should be exposed. Format should be <ip>/<port>
  external:
    description:
      - Optional parameter which shows desired RH socket where internal socket should be mapped.
        If more than one container mapped to one RH port, those containers are being put to the same backend group.
        Allowed port value must be in range of 1000-65535
  domain:
    description:
      - Should be only specified for http and https protocols mapping.
  cert:
    description:
      - Path to SSL pem certificate for https protocol.
  map_policy:
    description:
      - Balancing methods (round-robin by default, least_time, hash, ip_hash).
    choices: [ 'round-robin', 'least_time', 'hash', 'ip_hash' ]
  sslbackend :
    description:
      - SSL backend in https upstream.
  vxlan:
    description:
      - Vxlan name.
  remoteip:
    description:
      - Remote IP address.
  vni:
    description:
      - VXLAN tunnel VNI.
  interface:
    description:
      - Interface name
  hash:
    description:
      - hash
  key:
    description:
      - key
  localPeepIPAddr:
    description:
      - localPeepIPAddr
  portrange :
    description:
      - portrange
  host:
    description:
      - Add host to domain on VLAN.
  proxy_policy:
    description:
      - Set load balance policy (rr|lb|hash).
    choices: [ 'lb', 'rr', 'hash' ]
  file:
    description:
      - Pem certificate file.

author:
  - "Fernando Silva (@liquuid)"
'''

EXAMPLES = '''

- name: run subutai import nginx
  subutai:
    name: nginx
    state: present

- name: run subutai destroy nginx
  subutai:
    name: nginx
    state: absent

- name: run subutai destroy template nginx
  subutai:
    name: nginx
    state: absent
    template: true

- name: upgrade nginx
  subutai:
    name: nginx
    state: latest

- name: subutai tunnel add 10.10.0.20
  subutai:
    network: tunnel
    state: present
    ipaddr: 10.10.0.20

- name: subutai tunnel add 10.10.0.30:8080 300 -g
  subutai:
    network: tunnel
    state: present
    ipaddr: 10.10.0.30:8080
    ttl: 300
    globalFlag: true

- name: subutai tunnel del 10.10.0.30:8080
  subutai:
    network: tunnel
    state: absent
    ipaddr: 10.10.0.30:8080

- name: subutai tunnel del 10.10.0.20:8080
  subutai:
    network: tunnel
    state: absent
    ipaddr: 10.10.0.20:22

- name: map container's 172.16.31.3 port 3306 to the random port on RH
  subutai:
    network: map
    state: present
    protocol: tcp
    internal: 172.16.31.3:3306

- name: add 172.16.31.4:3306 to the same group
  subutai:
    network: map
    state: present
    protocol: tcp
    internal: 172.16.31.4:3306
    external: 46558

- name: remove container 172.16.31.3 from mapping
  subutai:
    network: map
    state: absent
    protocol: tcp
    internal: 172.16.31.3:3306
    external: 46558

- name: map 172.16.25.12:80 to RH's 8080 with domain name example.com
  subutai:
    network: map
    state: present
    protocol: http
    internal: 172.16.25.12:80
    external: 8080
    domain: example.com

- name: add container to existing example.com domain
  subutai:
    network: map
    state: present
    protocol: http
    internal: 172.16.25.13:80
    external: 8080
    domain: example.com

- name: adding subutai vxlan tunnel
  subutai:
    network: vxlan
    state: present
    vxlan: vxlan1
    remoteip: 10.220.22.2
    vlan: 100
    vni: 12345

- name: removing subutai vxlan tunnel
  subutai:
    network: vxlan
    state: absent
    vxlan: vxlan1

- name: add domain example.com to 100 vlan
  subutai:
    network: proxy
    state: present
    vlan: 100
    domain: example.com

- name: add domain example.com to 100 vlan
  subutai:
    network: proxy
    state: present
    vlan: 100
    host: 10.10.0.20

- name: delete domain example.com
  subutai:
    conetwork: proxy
    state: absent
    vlan: 100
    domain: example.com

- name: delete host 10.10.0.20
  subutai:
    conetwork: proxy
    state: absent
    vlan: 100
    host: 10.10.0.20
'''

RETURN = '''
container:
    description: Container affected.
    type: string
    returned: always
    sample: "apache"
stderr:
    description: Error output from subutai container
    type: string
    returned: success, when need
    sample: "FATA[2018-03-09 00:10:29] Extracting tgz, read /var/lib/lxc: is a directory"
'''

import subprocess
from ansible.module_utils.basic import AnsibleModule


class Container():
    def __init__(self):
        # parameters
        self.module_args = dict(
            name=dict(type='str', required=False),
            template=dict(type='bool', required=False),
            network=dict(type='str', choices=[
                         'tunnel', 'map', 'vxlan', 'proxy']),
            source=dict(type='str', required=False),
            check=dict(type='bool', required=False),
            ipaddr=dict(type='str', required=False),
            vlan=dict(type='str', required=False),
            ttl=dict(type='str', required=False),
            globalFlag=dict(type='bool', required=False),
            state=dict(type='str', default='present', choices=[
                       'absent', 'present', 'latest', 'started', 'stopped']),
            protocol=dict(type='str', required=False, choices=[
                          'http', 'https', 'tcp', 'udp']),
            internal=dict(type='str', required=False),
            external=dict(type='str', required=False),
            domain=dict(type='str', required=False),
            cert=dict(type='str', required=False),
            map_policy=dict(type='str', required=False, choices=[
                            'round-robin', 'least_time', 'hash', 'ip_hash']),
            proxy_policy=dict(type='str', required=False,
                              choices=['lb', 'rr', 'hash']),
            sslbackend=dict(type='str', required=False),
            vxlan=dict(type='str', required=False),
            remoteip=dict(type='str', required=False),
            vni=dict(type='str', required=False),
            interface=dict(type='str', required=False),
            hash=dict(type='str', required=False),
            key=dict(type='str', required=False),
            localPeepIPAddr=dict(type='str', required=False),
            portrange=dict(type='str', required=False),
            host=dict(type='str', required=False),
            file=dict(type='str', required=False),

        )

        self.module = AnsibleModule(
            argument_spec=self.module_args,
            supports_check_mode=True,
            required_one_of=[['name', 'network']],
            required_if=[
                ["network", "tunnel", ["ipaddr"]],
                ["network", "map", ["protocol"]],
                ["network", "vxlan", ["vxlan"]],
            ]
        )

        # skell to result
        self.result = self.module.params.copy()
        self.result['changed'] = False
        self.result['message'] = ''

        # check mode, don't made any changes
        if self.module.check_mode:
            self._exit()

        self.args = []

        if self.module.params['check']:
            self.args.append("-c")

        if self.module.params['name']:

            if self.module.params['state'] == 'present':
                self._import()

            if self.module.params['state'] == 'absent':
                if self.module.params['template']:
                    self.args.append("-t")
                self._destroy()

            if self.module.params['state'] == 'latest':
                self._update()

            if self.module.params['state'] == 'started':
                self._start()

            if self.module.params['state'] == 'stopped':
                self._stop()

        if self.module.params['network'] == 'tunnel':
            self._tunnel()

        if self.module.params['network'] == 'map':
            self._map()

        if self.module.params['network'] == 'vxlan':
            self._vxlan()

        if self.module.params['network'] == 'proxy':
            self._proxy()

    def _start(self):
        if self._is_running():
            self.result['changed'] = False
            self._exit()

        # verify if container is already installed
        if not self._is_installed():
            self.result['changed'] = True
            self.result['message'] = 'not installed'

            self._subutai_cmd("import")

            # try start container
            if self._subutai_cmd("start"):
                self._return_fail("Start Error")

            if self._is_running():
                self.result['changed'] = True

        else:

            # try start container
            if self._subutai_cmd("start"):
                self._return_fail("Start Error")

            if self._is_running():
                self.result['changed'] = True

        self._exit()

    def _stop(self):
        # verify if container is already installed
        if not self._is_installed():
            self.result['changed'] = True
            self.result['message'] = 'not installed'

            self._subutai_cmd("import")

            # try stop container
            if self._subutai_cmd("stop"):
                self._return_fail("Stop Error")

            if self._is_running():
                self.result['changed'] = True

        else:
            if not self._is_running():
                self.result['changed'] = False
                self._exit()

            # try start container
            if self._subutai_cmd("stop"):
                self._return_fail("Stop Error")

            if not self._is_running():
                self.result['changed'] = True

        self._exit()

    def _update(self):
        # verify if container is already installed
        if not self._is_installed():
            self.result['changed'] = True
            self.result['message'] = 'not installed'
            self._subutai_cmd("import")
            self._exit()

        else:
            if self._subutai_cmd("start"):
                self._return_fail("Start Error")

            # try update container
            if self._subutai_cmd("update"):
                self._return_fail("Update Error")
            self.result['changed'] = True
            self._exit()

    def _destroy(self):
        if not self._is_installed():
            self.result['changed'] = False
            self._exit()
        else:
            # try destroy container
            out = self._subutai_cmd("destroy")
            if out:
                self._return_fail("Destroy Error: " + str(out))
            self.result['changed'] = True
            self._exit()

    def _import(self):
        # verify if container is already installed
        if self._is_installed():
            self.result['changed'] = False
            self.result['message'] = 'already installed'
        else:
            # try install container
            out = self._subutai_cmd("import")
            if out:
                self._return_fail("Import Error: " + str(out))

            if self._is_installed():
                self.result['changed'] = True

        self._exit()

    def _tunnel(self):
        if self.module.params['ttl']:
            self.args.append(self.module.params['ttl'])

        if self.module.params['globalFlag']:
            self.args.append("-g")

        if self.module.params['state'] == "present":
            if not self._exists_tunnel():
                try:
                    err = subprocess.Popen(
                        ["/usr/bin/subutai", "tunnel", "add", self.module.params['ipaddr']] + self.args, stderr=subprocess.PIPE).stderr.read()
                    if err:
                        self.result['stderr'] = err
                        self._return_fail(err)
                    else:
                        self.result['changed'] = True
                        self._exit()
                except OSError as e:
                    if "[Errno 2] No such file or directory" in str(e):
                        self.result['changed'] = False
                        self._return_fail("Subutai is not installed")
                    else:
                        self.result['changed'] = False
                        self._return_fail("OS Error " + str(e))
            else:
                self.result['changed'] = False
                self.result['stderr'] = "Tunnel already exist"
                self._exit()

        elif self.module.params['state'] == "absent":
            if self._exists_tunnel():
                try:
                    err = subprocess.Popen(
                        ["/usr/bin/subutai", "tunnel", "del", self.module.params['ipaddr']], stderr=subprocess.PIPE).stderr.read()
                    if err:
                        self.result['stderr'] = err
                        self._return_fail(err)
                    else:
                        self.result['changed'] = True
                        self._exit()
                except OSError as e:
                    if "[Errno 2] No such file or directory" in str(e):
                        self.result['changed'] = False
                        self._return_fail("Subutai is not installed")
                    else:
                        self.result['changed'] = False
                        self._return_fail("OS Error " + str(e))
            else:
                self.result['changed'] = False
                self.result['stderr'] = "Tunnel do not exist"
                self._exit()

        else:
            self._return_fail(err)

    def _map(self):
        self.args.append(self.module.params['protocol'])
        if self.module.params['internal']:
            self.args.append("--internal")
            self.args.append(self.module.params['internal'])

        if self.module.params['external']:
            self.args.append("--external")
            self.args.append(self.module.params['external'])

        if self.module.params['domain']:
            self.args.append("--domain")
            self.args.append(self.module.params['domain'])

        if self.module.params['cert']:
            self.args.append("--cert")
            self.args.append(self.module.params['cert'])

        if self.module.params['map_policy']:
            self.args.append("--policy")
            self.args.append(self.module.params['map_policy'])

        if self.module.params['sslbackend']:
            self.args.append("--sslbackend")
            self.args.append(self.module.params['sslbackend'])

        if self.module.params['state'] == 'absent':
            self.args.append("--remove")
        try:
            err = subprocess.Popen(["/usr/bin/subutai", "map", self.module.params['protocol']
                                    ] + self.args, stderr=subprocess.PIPE).stderr.read()
            if err:
                if "already exists" in err:
                    self.result['changed'] = False
                    self._exit()
                else:
                    self.result['stderr'] = err
                    self._return_fail(err)
            else:
                self.result['changed'] = True
                self._exit()
        except OSError as e:
            if "[Errno 2] No such file or directory" in str(e):
                self.result['changed'] = False
                self._return_fail("Subutai is not installed")
            else:
                self.result['changed'] = False
                self._return_fail("OS Error " + str(e))

    def _vxlan(self):

        if self.module.params['remoteip']:
            self.args.append("--remoteip")
            self.args.append(self.module.params['remoteip'])

        if self.module.params['vlan']:
            self.args.append("--vlan")
            self.args.append(self.module.params['vlan'])

        if self.module.params['vni']:
            self.args.append("--vni")
            self.args.append(self.module.params['vni'])

        if self.module.params['state'] == "present":
            try:
                err = subprocess.Popen(
                    ["/usr/bin/subutai", "vxlan", "--create", self.module.params['vxlan']] + self.args, stderr=subprocess.PIPE).stderr.read()
                if err:
                    self.result['stderr'] = err
                    self._return_fail(err)
                else:
                    if self.module.params['vxlan'] in self._exists_vxlan():
                        self.result['changed'] = True
                        self._exit()
                    else:
                        self._return_fail(err)
            except OSError as e:
                if "[Errno 2] No such file or directory" in str(e):
                    self.result['changed'] = False
                    self._return_fail("Subutai is not installed")
                else:
                    self.result['changed'] = False
                    self._return_fail("OS Error " + str(e))

        elif self.module.params['state'] == "absent":
            try:
                err = subprocess.Popen(
                    ["/usr/bin/subutai", "vxlan", "--delete", self.module.params['vxlan']], stderr=subprocess.PIPE).stderr.read()
                if err:
                    self.result['stderr'] = err
                    self._return_fail(err)
                else:
                    if self.module.params['vxlan'] not in self._exists_vxlan():
                        self.result['changed'] = True
                        self._exit()
                    else:
                        self._return_fail(err)
            except OSError as e:
                if "[Errno 2] No such file or directory" in str(e):
                    self.result['changed'] = False
                    self._return_fail("Subutai is not installed")
                else:
                    self.result['changed'] = False
                    self._return_fail("OS Error " + str(e))
        else:
            self._return_fail(err)

    def _proxy(self):
        check_args = []
        if self.module.params['domain']:
            self.args.append("--domain")
            self.args.append(self.module.params['domain'])
            check_args.append("-d")

        if self.module.params['host']:
            self.args.append("--host")
            self.args.append(self.module.params['host'])
            check_args.append("-h")
            check_args.append(self.module.params['host'])

        if self.module.params['proxy_policy']:
            self.args.append("--policy")
            self.args.append(self.module.params['proxy_policy'])

        if self.module.params['file']:
            self.args.append("--file")
            self.args.append(self.module.params['file'])

        if self.module.params['state'] == "present":
            try:
                out = subprocess.Popen(
                    ["/usr/bin/subutai", "proxy", "check", self.module.params['vlan']] + check_args, stdout=subprocess.PIPE).stdout.read()
                if out:
                    self.result['changed'] = False
                    self._exit()
                else:
                    err = subprocess.Popen(
                        ["/usr/bin/subutai", "proxy", "add", self.module.params['vlan']] + self.args, stderr=subprocess.PIPE).stderr.read()
                    if err:
                        self.result['stderr'] = err
                        self._return_fail(err)
                    else:
                        self.result['changed'] = True
                        self._exit()
            except OSError as e:
                if "[Errno 2] No such file or directory" in str(e):
                    self.result['changed'] = False
                    self._return_fail("Subutai is not installed")
                else:
                    self.result['changed'] = False
                    self._return_fail("OS Error " + str(e))

        elif self.module.params['state'] == "absent":
            try:
                err = subprocess.Popen(
                    ["/usr/bin/subutai", "proxy", "del", self.module.params['vlan']] + check_args, stderr=subprocess.PIPE).stderr.read()
                if err:
                    self.result['stderr'] = err
                    self._return_fail(err)
                else:
                    self.result['changed'] = True
                    self.result['message'] = str(self.args)
                    self._exit()
            except OSError as e:
                if "[Errno 2] No such file or directory" in str(e):
                    self.result['changed'] = False
                    self._return_fail("Subutai is not installed")
                else:
                    self.result['changed'] = False
                    self._return_fail("OS Error " + str(e))
        else:
            self._return_fail(err)

    def _exists_vxlan(self):
        try:
            return subprocess.Popen(["/usr/bin/subutai", "vxlan", "-l"], stdout=subprocess.PIPE).stdout.read()
        except OSError as e:
            if "[Errno 2] No such file or directory" in str(e):
                self.result['changed'] = False
                self._return_fail("Subutai is not installed")
            else:
                self.result['changed'] = False
                self._return_fail("OS Error " + str(e))

    def _exit(self):
        self.module.exit_json(**self.result)

    def _return_fail(self, err_msg):
        self.result['stderr'] = err_msg
        self.result['changed'] = False
        self.module.fail_json(msg='[Err] ' + err_msg, **self.result)

    def _is_installed(self):
        try:
            out = subprocess.Popen(
                ["/usr/bin/subutai", "list"], stdout=subprocess.PIPE).stdout.read()
            if self.module.params['name'] + '\n' in out:
                return True
            else:
                return False
        except OSError as e:
            if "[Errno 2] No such file or directory" in str(e):
                self.result['changed'] = False
                self._return_fail("Subutai is not installed")
            else:
                self.result['changed'] = False
                self._return_fail("OS Error " + str(e))

    def _exists_tunnel(self):
        try:
            out = subprocess.Popen(
                ["/usr/bin/subutai", "tunnel", "list"], stdout=subprocess.PIPE).stdout.read()
            if self.module.params['ipaddr'] in out:
                return True
            else:
                return False
        except OSError as e:
            if "[Errno 2] No such file or directory" in str(e):
                self.result['changed'] = False
                self._return_fail("Subutai is not installed")
            else:
                self.result['changed'] = False
                self._return_fail("OS Error " + str(e))

    def _is_running(self):
        try:
            out = subprocess.Popen(
                ["/usr/bin/subutai", "list", "-i", self.module.params['name']], stdout=subprocess.PIPE).stdout.read()
            if bytes("RUNNING") in out:
                return True
            else:
                return False
        except OSError as e:
            if "[Errno 2] No such file or directory" in str(e):
                self.result['changed'] = False
                self._return_fail("Subutai is not installed")
            else:
                self.result['changed'] = False
                self._return_fail("OS Error " + str(e))

    def _subutai_cmd(self, cmd):
        try:
            msg = subprocess.Popen(
                ["/usr/bin/subutai", cmd, self.module.params['name']] + self.args, stderr=subprocess.PIPE).stderr.read()
            return msg
        except OSError as e:
            if "[Errno 2] No such file or directory" in str(e):
                self.result['changed'] = False
                self._return_fail("Subutai is not installed")
            else:
                self.result['changed'] = False
                self._return_fail("OS Error " + str(e))


def main():
    Container()


if __name__ == '__main__':
    main()
