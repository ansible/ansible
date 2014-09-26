#!/usr/bin/python
#

# (c) 2014, Pavel Antonov <antonov@adwz.ru>
#
# This file is part of Ansible
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

######################################################################

DOCUMENTATION = '''
---
module: docker_image
author: Pavel Antonov
version_added: "1.5"
short_description: manage docker images
description:
     - Create, check and remove docker images
options:
  path:
    description:
       - Path to directory with Dockerfile
    required: false
    default: null
    aliases: []
  name:
    description:
       - Image name to work with
    required: true
    default: null
    aliases: []
  tag:
    description:
       - Image tag to work with
    required: false
    default: "latest"
    aliases: []
  nocache:
    description:
      - Do not use cache with building
    required: false
    default: false
    aliases: []
  docker_url:
    description:
      - URL of docker host to issue commands to
    required: false
    default: unix://var/run/docker.sock
    aliases: []
  state:
    description:
      - Set the state of the image
    required: false
    default: present
    choices: [ "present", "absent", "build" ]
    aliases: []
  timeout:
    description:
      - Set image operation timeout
    required: false
    default: 600
    aliases: []
requirements: [ "docker-py" ]
'''

EXAMPLES = '''
Build docker image if required. Path should contains Dockerfile to build image:

- hosts: web
  sudo: yes
  tasks:
  - name: check or build image
    docker_image: path="/path/to/build/dir" name="my/app" state=present

Build new version of image:

- hosts: web
  sudo: yes
  tasks:
  - name: check or build image
    docker_image: path="/path/to/build/dir" name="my/app" state=build

Remove image from local docker storage:

- hosts: web
  sudo: yes
  tasks:
  - name: remove image
    docker_image: name="my/app" state=absent

'''

try:
    import sys
    import re
    import json
    import docker.client
    from requests.exceptions import *
    from urlparse import urlparse
except ImportError, e:
    print "failed=True msg='failed to import python module: %s'" % e
    sys.exit(1)

try:
    from docker.errors import APIError as DockerAPIError
except ImportError:
    from docker.client import APIError as DockerAPIError

class DockerImageManager:

    def __init__(self, module):
        self.module = module
        self.path = self.module.params.get('path')
        self.name = self.module.params.get('name')
        self.tag = self.module.params.get('tag')
        self.nocache = self.module.params.get('nocache')
        docker_url = urlparse(module.params.get('docker_url'))
        self.client = docker.Client(base_url=docker_url.geturl(), timeout=module.params.get('timeout'))
        self.changed = False
        self.log = []
        self.error_msg = None

    def get_log(self, as_string=True):
        return "".join(self.log) if as_string else self.log

    def build(self):
        stream = self.client.build(self.path, tag=':'.join([self.name, self.tag]), nocache=self.nocache, rm=True, stream=True)
        success_search = r'Successfully built ([0-9a-f]+)'
        image_id = None
        self.changed = True

        for chunk in stream:
            if not chunk:
                continue

            try:
                chunk_json = json.loads(chunk)
            except ValueError:
                continue

            if 'error' in chunk_json:
                self.error_msg = chunk_json['error']
                return None

            if 'stream' in chunk_json:
                output = chunk_json['stream']
                self.log.append(output)
                match = re.search(success_search, output)
                if match:
                    image_id = match.group(1)

        # Just in case we skipped evaluating the JSON returned from build
        # during every iteration, add an error if the image_id was never
        # populated
        if not image_id:
            self.error_msg = 'Unknown error encountered'

        return image_id

    def has_changed(self):
        return self.changed

    def get_images(self):
        filtered_images = []
        images = self.client.images()
        for i in images:
            # Docker-py version >= 0.3 (Docker API >= 1.8)
            if 'RepoTags' in i:
                repotag = ':'.join([self.name, self.tag])
                if not self.name or repotag in i['RepoTags']:
                    filtered_images.append(i)
            # Docker-py version < 0.3 (Docker API < 1.8)
            elif (not self.name or self.name == i['Repository']) and (not self.tag or self.tag == i['Tag']):
                filtered_images.append(i)
        return filtered_images

    def remove_images(self):
        images = self.get_images()
        for i in images:
            try:
                self.client.remove_image(i['Id'])
                self.changed = True
            except DockerAPIError as e:
                # image can be removed by docker if not used
                pass


def main():
    module = AnsibleModule(
        argument_spec = dict(
            path            = dict(required=False, default=None),
            name            = dict(required=True),
            tag             = dict(required=False, default="latest"),
            nocache         = dict(default=False, type='bool'),
            state           = dict(default='present', choices=['absent', 'present', 'build']),
            docker_url      = dict(default='unix://var/run/docker.sock'),
            timeout         = dict(default=600, type='int'),
        )
    )

    try:
        manager = DockerImageManager(module)
        state = module.params.get('state')
        failed = False
        image_id = None
        msg = ''
        do_build = False

        # build image if not exists
        if state == "present":
            images = manager.get_images()
            if len(images) == 0:
                do_build = True
        # build image
        elif state == "build":
            do_build = True
        # remove image or images
        elif state == "absent":
            manager.remove_images()

        if do_build:
            image_id = manager.build()
            if image_id:
                msg = "Image built: %s" % image_id
            else:
                failed = True
                msg = "Error: %s\nLog:%s" % (manager.error_msg, manager.get_log())

        module.exit_json(failed=failed, changed=manager.has_changed(), msg=msg, image_id=image_id)

    except DockerAPIError as e:
        module.exit_json(failed=True, changed=manager.has_changed(), msg="Docker API error: " + e.explanation)

    except RequestException as e:
        module.exit_json(failed=True, changed=manager.has_changed(), msg=repr(e))
        
# import module snippets
from ansible.module_utils.basic import *

main()
