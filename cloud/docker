#!/usr/bin/env python
#
# The MIT License (MIT)
#
# Copyright (c) 2013 Cove Schneider
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

DOCUMENTATION = '''
---
module: docker
short_description: manage docker containers
description:
     - Manage the life cycle of docker containers. This module has a dependency on the docker-py python module.
options:
  count:
    description:
      - Set number of containers to run
    required: False
    default: 1
    aliases: []
  image:
    description:
       - Set container image to use
    required: true
    default: null
    aliases: []
  command:
    description:
       - Set command to run in a container on startup
    required: false
    default: null
    aliases: []
  ports:
    description:
      - Set private to public port mapping specification (e.g. ports=22,80 or ports=:8080 maps 8080 directly to host)
    required: false
    default: null
    aliases: []
  volumes:
    description:
      - Set volume(s) to mount on the container
    required: false
    default: null
    aliases: []
  volumes_from:
    description:
      - Set shared volume(s) from another container
    required: false
    default: null
    aliases: []
  memory_limit:
    description:
      - Set RAM allocated to container
    required: false
    default: null
    aliases: []
    default: 256MB
  docker_url:
    description:
      - URL of docker host to issue commands to
    required: false
    default: unix://var/run/docker.sock
    aliases: []
  username:
    description:
      - Set remote API username
    required: false
    default: null
    aliases: []
  password:
    description:
      - Set remote API password
    required: false
    default: null
    aliases: []
  hostname:
    description:
      - Set container hostname
    required: false
    default: null
    aliases: []
  env:
    description:
      - Set environment variables
    required: false
    default: null
    aliases: []
  dns:
    description:
      - Set custom DNS servers for the container
    required: false
    default: null
    aliases: []
  detach:
    description:
      - Enable detached mode on start up, leaves container running in background
    required: false
    default: true
    aliases: []
  state:
    description:
      - Set the state of the container
    required: false
    default: present
    choices: [ "present", "stopped", "absent", "killed", "restarted" ]
    aliases: []
  privileged:
    description:
      - Set whether the container should run in privileged mode
    required: false
    default: false
    aliases: []
  lxc_conf:
    description:
      - LXC config parameters,  e.g. lxc.aa_profile:unconfined
    required: false
    default:
    aliases: []
author: Cove Schneider
'''

try:
    import sys
    import json
    import docker.client
    from requests.exceptions import *
    from urlparse import urlparse
except ImportError, e:
    print "failed=True msg='failed to import python module: %s'" % e
    sys.exit(1)

def _human_to_bytes(number):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

    if isinstance(number, int):
        return number
    if number[-1] == suffixes[0] and number[-2].isdigit():
        return number[:-1]

    i = 1
    for each in suffixes[1:]:
        if number[-len(each):] == suffixes[i]:
            return int(number[:-len(each)]) * (1024 ** i)
        i = i + 1

    print "failed=True msg='Could not convert %s to integer'" % (number)
    sys.exit(1)

def _ansible_facts(container_list):
    return {"DockerContainers": container_list}

class AnsibleDocker:
    
    counters = {'created':0, 'started':0, 'stopped':0, 'killed':0, 'removed':0, 'restarted':0, 'pull':0}

    def __init__(self, module):
        self.module = module
    
        # connect to docker server
        docker_url = urlparse(module.params.get('docker_url'))
        self.client = docker.Client(base_url=docker_url.geturl())
    
    def get_summary_counters_msg(self):
        msg = ""
        for k, v in self.counters.iteritems():
            msg = msg + "%s %d " % (k, v)

        return msg
    
    def increment_counter(self, name):
        self.counters[name] = self.counters[name] + 1

    def has_changed(self):
        for k, v in self.counters.iteritems():
            if v > 0:
                return True

        return False

    def get_deployed_containers(self):
        # determine which images/commands are running already
        containers = self.client.containers()
        image      = self.module.params.get('image')
        command    = self.module.params.get('command')
        deployed   = []

        for i in containers:
            if i["Image"].split(":")[0] == image.split(":")[0] and (not command or i["Command"].strip() == command.strip()):
                details = self.client.inspect_container(i['Id'])
                # XXX: some quirk in docker
                if 'ID' in details:
                    details['Id'] = details['ID']
                    del details['ID']
                deployed.append(details)

        return deployed

    def get_running_containers(self):
        running = []
        for i in self.get_deployed_containers():
            if i['State']['Running'] == True:
                running.append(i)

        return running

    def create_containers(self, count=1):
        params = {'image':        self.module.params.get('image'),
                  'command':      self.module.params.get('command'),
                  'volumes_from': self.module.params.get('volumes_from'),
                  'mem_limit':    _human_to_bytes(self.module.params.get('memory_limit')),
                  'environment':  self.module.params.get('env'),
                  'dns':          self.module.params.get('dns'),
                  'hostname':     self.module.params.get('hostname'),
                  'detach':       self.module.params.get('detach'),
                  'privileged':   self.module.params.get('privileged'),
                  }

        if self.module.params.get('ports'):
            params['ports'] = self.module.params.get('ports').split(",")
           
        def do_create(count, params):
            results = []
            for i in range(count):
                result = self.client.create_container(**params)
                self.increment_counter('created')
                results.append(result)

            return results

        try:
            containers = do_create(count, params)
        except:
            self.client.pull(params['image'])
            self.increment_counter('pull')
            containers = do_create(count, params)

        return containers

    def start_containers(self, containers):
        binds = None
        if self.module.params.get('volumes'):
            binds = {}
            vols = self.module.params.get('volumes').split(" ")
            for vol in vols:
                parts = vol.split(":")
                binds[parts[0]] = parts[1]

        lxc_conf = None
        if self.module.params.get('lxc_conf'):
            lxc_conf = []
            options = self.module.params.get('lxc_conf').split(" ")
            for option in options:
                parts = option.split(':')
                lxc_conf.append({"Key": parts[0], "Value": parts[1]})

        for i in containers:
                self.client.start(i['Id'], lxc_conf=lxc_conf, binds=binds)
                self.increment_counter('started')

    def stop_containers(self, containers):
        for i in containers:
            self.client.stop(i['Id'])
            self.increment_counter('stopped')

        return [self.client.wait(i['Id']) for i in containers]

    def remove_containers(self, containers):
        for i in containers:
            self.client.remove_container(i['Id'])
            self.increment_counter('removed')
    
    def kill_containers(self, containers):
        for i in containers:
            self.client.kill(i['Id'])
            self.increment_counter('killed')

    def restart_containers(self, containers):
        for i in containers:
            self.client.restart(i['Id'])
            self.increment_counter('restarted')

def main():
    module = AnsibleModule(
        argument_spec = dict(
            count           = dict(default=1),
            image           = dict(required=True),
            command         = dict(required=False, default=None),
            ports           = dict(required=False, default=None),
            volumes         = dict(default=None),
            volumes_from    = dict(default=None),
            memory_limit    = dict(default=0),
            memory_swap     = dict(default=0),
            docker_url      = dict(default='unix://var/run/docker.sock'),
            user            = dict(default=None),
            password        = dict(),
            email           = dict(),
            hostname        = dict(default=None),
            env             = dict(),
            dns             = dict(),
            detach          = dict(default=True, type='bool'),
            state           = dict(default='present', choices=['absent', 'present', 'stopped', 'killed', 'restarted']),
            debug           = dict(default=False, type='bool'),
            privileged      = dict(default=False, type='bool'),
            lxc_conf        = dict(default=None)
        )
    )

    try:
        docker_client = AnsibleDocker(module)
        state = module.params.get('state')
        count = int(module.params.get('count'))

        if count < 1:
            module.fail_json(msg="Count must be positive number")
    
        running_containers = docker_client.get_running_containers()
        running_count = len(running_containers)
        delta = count - running_count
        deployed_containers = docker_client.get_deployed_containers()
        facts = None
        failed = False
        changed = False

        # start/stop containers
        if state == "present":
    
            # start more containers if we don't have enough
            if delta > 0:
                containers = docker_client.create_containers(delta)
                docker_client.start_containers(containers)
                
            # stop containers if we have too many
            elif delta < 0:
                docker_client.stop_containers(running_containers[0:abs(delta)])
                docker_client.remove_containers(running_containers[0:abs(delta)])
            
            facts = docker_client.get_running_containers()
    
        # stop and remove containers
        elif state == "absent":
            facts = docker_client.stop_containers(deployed_containers)
            docker_client.remove_containers(containers)
    
        # stop containers
        elif state == "stopped":
            facts = docker_client.stop_containers(running_containers)
    
        # kill containers
        elif state == "killed":
            docker_client.kill_containers(running_containers)
    
        # restart containers
        elif state == "restarted":
            docker_client.restart_containers(running_containers)        
    
        msg = "%s container(s) running image %s with command %s" % \
                (docker_client.get_summary_counters_msg(), module.params.get('image'), module.params.get('command'))
        changed = docker_client.has_changed()
    
        module.exit_json(failed=failed, changed=changed, msg=msg, ansible_facts=_ansible_facts(facts))

    except docker.client.APIError as e:
        changed = docker_client.has_changed()
        module.exit_json(failed=True, changed=changed, msg="Docker API error: " + e.explanation)

    except RequestException as e:
        changed = docker_client.has_changed()
        module.exit_json(failed=True, changed=changed, msg=repr(e))
        
# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>

main()
