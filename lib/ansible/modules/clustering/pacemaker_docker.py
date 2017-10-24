#!/usr/bin/python
#coding: utf-8 -*-

# Copyright (c), Chafik Belhaoues  <chafik.bel@gmail.com>, 2017
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: pacemaker_docker
short_description: Manage docker resources in a pacemaker cluster
version_added: "2.4"
author: "Chafik Belhaoues (@africanzoe)"
description:
   - This module can create|delete|manage|unmanage a docker resource within a
     pacemaker cluster using the pacemaker "pcs" cli.
options:
    state:
      description:
        - Indicate desired state of the resource
      choices: ['created', 'deleted', 'managed', 'unamanged']
      required: true
      default: created
    resource:
      description:
        - Specify the name of the resource to be created.
      required: true
      default: None
    docker_name:
      description:
        - Specify the name of the docker to be created, this name will appear
          in "docker ps" command.
      required: true
      default: resource
    group:
      description:
        - Specify the name of the resource group to be created.
      required: false
    after:
      description:
        - Specify the position of the added resource relatively to some resource
          already existing in the group.
      required: false
    before:
      description:
        - Specify the position of the added resource relatively to some resource
          already existing in the group.
      required: false
    image:
      description:
        - Specify the name of the image used to create the docker.
      required: true
    command:
      description:
        - Specify the command to execute inside the container.
          Please consider using docker Entrypoints or CMD instead.
      required: false
    run_opts:
      description:
        - Specify options to be appended to the 'docker run' command which is
          used when creating the container during the start action.
      required: false
    mount_points:
      description:
        - A comma separated list of directories that the container is expecting
          to use. The agent will ensure they exist by running 'mkdir -p'.
      required: false
    monitor_cmd:
      description:
        - Specifiy the full path of a command to launch within the container to
          check the health of the container.
      required: false
    timeout:
      description:
        - Timeout when the module should considered that the action has failed
      required: false
      default: 300
    force_kill:
      description:
        - Specify wether to kill a container immediately rather than waiting
          for it to gracefully shutdown.
      required: false
      default: true
    allow_pull:
      description:
        - Specify wether to allow the image to be pulled from the configured
          docker registry when the image does not exist locally.
      required: false
      default: true
requirements:
    - "python >= 2.6"
'''
EXAMPLES = '''
---
- name: Set cluster Online
  hosts: localhost
  gather_facts: no
  tasks:
    - name: Create Docker resource
      pacemaker_docker:
        resource: "docker-resource-2"
        docker_name: "happy-docker-resource-2"
        image: 'alpine:latest'
        command: "ping myservice.mydomain.com" 
        group: "happy-docker-group"
        run_opts: '-p 80:80'
        before: "docker-resource-1"
        state: created
'''

RETURN = '''
changed:
    description: True if the cluster state has changed
    type: bool
    returned: always
out:
    description: The output of the current state of the cluster. It return a
                 list of the nodes state.
    type: string
    sample: 'out: [["  overcloud-controller-0", " Online"]]}'
    returned: always
rc:
    description: exit code of the module
    type: bool
    returned: always
'''

import time

from ansible.module_utils.basic import AnsibleModule


_PCS_CLUSTER_DOWN="Error: cluster is not currently running on this node"

def get_cluster_status(module):
    cmd = "pcs cluster status"
    rc, out, err = module.run_command(cmd)
    if out in _PCS_CLUSTER_DOWN:
        return 'offline'
    else:
        return 'online'

class DockerResource:

    def __init__(self, module):
        self.module = module
        self.changed = False
        self.state = module.params.get('state')
        self.force = module.params.get('force')
        self.resource = module.params.get('resource')
        self.docker_name = module.params.get('docker_name')
        self.group = module.params.get('group')
        self.before = module.params.get('before')
        self.after = module.params.get('after')
        self.image = module.params.get('image')
        self.command = module.params.get('command')
        self.opts = module.params.get('opts')
        self.mount_points = module.params.get('mount_points')
        self.monitor_cmd = module.params.get('monitor_cmd')
        self.timeout = module.params.get('timeout')
        self.force_kill = module.params.get('force_kill')
        self.allow_pull = module.params.get('allow_pull')

    def get_res_status(self):
        cmd = "pcs resource show %s" % self.resource
        rc, out, err = self.module.run_command(cmd)
        status = []

        if rc == 0:
            status.append('present')
            if "is-managed=false" in out:
                status.append('unmanaged')
            else:
                status.append('managed')
        else:
            status.append('absent')

        return status

    def create_res(self):
        opts_list = ""

        if self.opts is not None:
            opts_list += " run_opts='%s'" % self.opts
        if self.group is not None:
            opts_list += " --group %s" % self.group
        if self.before is not None:
            opts_list += " --before %s" % self.before
        if self.after is not None:
            opts_list += " --after %s" % self.after
        if self.mount_points is not None:
            opts_list += " mount_points='%s'" % self.mount_points
        if self.monitor_cmd is not None:
            opts_list += " monitor_cmd='%s'" % self.monitor_cmd
        if self.force_kill is not None:
            opts_list += " force_kill='%s'" % self.force_kill

        if self.docker_name is None:
            docker_name = self.resource
        else:
            docker_name = self.docker_name

        cmd = "pcs resource create %s ocf:heartbeat:docker name=%s image=%s run_cmd='%s' %s" % (self.resource,
            docker_name,
            self.image,
            self.command,
            opts_list,
            )
        rc, out, err = self.module.run_command(cmd)
        
        if rc == 0:
            self.module.exit_json(changed=True, rc=rc, stdout=out, stderr=err)
        elif "already exists" in err:
            self.module.exit_json(changed=False, msg="The resource '%s' already exists" % self.resource)
        else:
            self.module.fail_json(rc=rc, stdout=out, stderr=err)
    
    def delete_res(self):
        res_status = self.get_res_status()
        if "absent" in res_status:
            self.module.exit_json(changed=False, stdout="Resource already absent", stderr=None)

        cmd = "pcs resource delete %s" % self.resource
        rc, out, err = self.module.run_command(cmd)

        if rc == 0:
            self.module.exit_json(changed=True, rc=rc, stdout=out, stderr=err)
        else:
            self.module.fail_json(rc=rc, stdout=out, stderr=err)

    def manage_res(self):
        res_status = self.get_res_status()
        if "absent" in res_status:
            self.module.fail_json(msg="Resource '%s' is not present" % self.resource)

        if self.state == "managed":
            if "unmanaged" not in res_status:
                self.module.exit_json(changed=False, stdout="Resource '%s' is already managed" % self.resource, stderr=None)
            action = "manage"
        else:
            if "unmanaged" in res_status:
                self.module.exit_json(changed=False, stdout="Resource '%s' is already unmanaged" % self.resource, stderr=None)
            action = "unmanage"

        cmd = "pcs resource %s %s" % (action, self.resource)
        rc, out, err = self.module.run_command(cmd)

        if rc == 0:
            self.module.exit_json(changed=True, rc=rc, stdout=out, stderr=err)
        else:
            self.module.fail_json(rc=rc, stdout=out, stderr=err)

    def restart_res(self):
        res_status = self.get_res_status()
        if "absent" in res_status:
            self.module.fail_json(msg="Resource '%s' is not present" % self.resource)

        cmd = "pcs resource restart %s" % self.resource
        rc, out, err = self.module.run_command(cmd)

        if rc == 0:
            self.module.exit_json(changed=True, rc=rc, stdout=out, stderr=err)
        else:
            self.module.fail_json(rc=rc, stdout=out, stderr=err)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=False, choices=['created', 'deleted', 'restarted', 'managed', 'unmanaged'], default="created"),
            resource=dict(required=True, default=None),
            docker_name=dict(required=False, default=None),
            group=dict(required=False, default=None),
            before=dict(required=False, default=None),
            after=dict(required=False, default=None),
            image=dict(required=True, default=None),
            command=dict(required=False, default=None),
            run_opts=dict(required=False, default=None),
            mount_points=dict(required=False, default=None),
            monitor_cmd=dict(required=False, default=None),
            timeout=dict(default=30, type='int'),
            force_kill=dict(required=False, default=True, type='bool'),
            allow_pull=dict(required=False, default=True, type='bool'),
        ),
            supports_check_mode=False,
    )

    cluster_state = get_cluster_status(module)
    # Exit if the cluster is down
    if cluster_state == 'offline':
        module.fail_json(msg="The cluster is either offline or not started on the node")

    docker_resource = DockerResource(module)
    state = module.params.get('state')
    if state == "created":
        docker_resource.create_res()
    elif state == "deleted":
        docker_resource.delete_res()
    elif state == "restarted":
        docker_resource.restart_res()
    else:
        docker_resource.manage_res()
        
if __name__ == '__main__':
    main()
