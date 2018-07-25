#!/usr/bin/python
#
# Copyright 2016 Red Hat | Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: docker_image

short_description: Manage docker images.

version_added: "1.5"

description:
     - Build, load or pull an image, making the image available for creating containers. Also supports tagging an
       image into a repository and archiving an image to a .tar file.

options:
  archive_path:
    description:
      - Use with state C(present) to archive an image to a .tar file.
    required: false
    version_added: "2.1"
  load_path:
    description:
      - Use with state C(present) to load an image from a .tar file.
    required: false
    version_added: "2.2"
  dockerfile:
    description:
      - Use with state C(present) to provide an alternate name for the Dockerfile to use when building an image.
    required: false
    version_added: "2.0"
  force:
    description:
      - Use with state I(absent) to un-tag and remove all images matching the specified name. Use with state
        C(present) to build, load or pull an image when the image already exists.
    default: false
    required: false
    version_added: "2.1"
    type: bool
  http_timeout:
    description:
      - Timeout for HTTP requests during the image build operation. Provide a positive integer value for the number of
        seconds.
    required: false
    version_added: "2.1"
  name:
    description:
      - "Image name. Name format will be one of: name, repository/name, registry_server:port/name.
        When pushing or pulling an image the name can optionally include the tag by appending ':tag_name'."
    required: true
  path:
    description:
      - Use with state 'present' to build an image. Will be the path to a directory containing the context and
        Dockerfile for building an image.
    aliases:
      - build_path
    required: false
  pull:
    description:
      - When building an image downloads any updates to the FROM image in Dockerfile.
    default: true
    required: false
    version_added: "2.1"
    type: bool
  push:
    description:
      - Push the image to the registry. Specify the registry as part of the I(name) or I(repository) parameter.
    default: false
    required: false
    version_added: "2.2"
    type: bool
  rm:
    description:
      - Remove intermediate containers after build.
    default: true
    required: false
    version_added: "2.1"
    type: bool
  nocache:
    description:
      - Do not use cache when building an image.
    default: false
    required: false
    type: bool
  repository:
    description:
      - Full path to a repository. Use with state C(present) to tag the image into the repository. Expects
        format I(repository:tag). If no tag is provided, will use the value of the C(tag) parameter or I(latest).
    required: false
    version_added: "2.1"
  state:
    description:
      - Make assertions about the state of an image.
      - When C(absent) an image will be removed. Use the force option to un-tag and remove all images
        matching the provided name.
      - When C(present) check if an image exists using the provided name and tag. If the image is not found or the
        force option is used, the image will either be pulled, built or loaded. By default the image will be pulled
        from Docker Hub. To build the image, provide a path value set to a directory containing a context and
        Dockerfile. To load an image, specify load_path to provide a path to an archive file. To tag an image to a
        repository, provide a repository path. If the name contains a repository path, it will be pushed.
      - "NOTE: C(build) is DEPRECATED and will be removed in release 2.3. Specifying C(build) will behave the
         same as C(present)."
    required: false
    default: present
    choices:
      - absent
      - present
      - build
  tag:
    description:
      - Used to select an image when pulling. Will be added to the image when pushing, tagging or building. Defaults to
        I(latest).
      - If C(name) parameter format is I(name:tag), then tag value from C(name) will take precedence.
    default: latest
    required: false
  buildargs:
    description:
      - Provide a dictionary of C(key:value) build arguments that map to Dockerfile ARG directive.
      - Docker expects the value to be a string. For convenience any non-string values will be converted to strings.
      - Requires Docker API >= 1.21 and docker-py >= 1.7.0.
    required: false
    version_added: "2.2"
  container_limits:
    description:
      - A dictionary of limits applied to each container created by the build process.
    required: false
    version_added: "2.1"
    suboptions:
      memory:
        description:
          - Set memory limit for build.
      memswap:
        description:
          - Total memory (memory + swap), -1 to disable swap.
      cpushares:
        description:
          - CPU shares (relative weight).
      cpusetcpus:
        description:
          - CPUs in which to allow execution, e.g., "0-3", "0,1".
  use_tls:
    description:
      - "DEPRECATED. Whether to use tls to connect to the docker server. Set to C(no) when TLS will not be used. Set to
        C(encrypt) to use TLS. And set to C(verify) to use TLS and verify that the server's certificate is valid for the
        server. NOTE: If you specify this option, it will set the value of the tls or tls_verify parameters."
    choices:
      - 'no'
      - 'encrypt'
      - 'verify'
    default: 'no'
    required: false
    version_added: "2.0"

extends_documentation_fragment:
    - docker

requirements:
  - "python >= 2.6"
  - "docker-py >= 1.7.0"
  - "Please note that the L(docker-py,https://pypi.org/project/docker-py/) Python
     module has been superseded by L(docker,https://pypi.org/project/docker/)
     (see L(here,https://github.com/docker/docker-py/issues/1310) for details).
     For Python 2.6, C(docker-py) must be used. Otherwise, it is recommended to
     install the C(docker) Python module. Note that both modules should I(not)
     be installed at the same time. Also note that when both modules are installed
     and one of them is uninstalled, the other might no longer function and a
     reinstall of it is required."
  - "Docker API >= 1.20"

author:
  - Pavel Antonov (@softzilla)
  - Chris Houseknecht (@chouseknecht)

'''

EXAMPLES = '''

- name: pull an image
  docker_image:
    name: pacur/centos-7

- name: Tag and push to docker hub
  docker_image:
    name: pacur/centos-7
    repository: dcoppenhagan/myimage
    tag: 7.0
    push: yes

- name: Tag and push to local registry
  docker_image:
     name: centos
     repository: localhost:5000/centos
     tag: 7
     push: yes

- name: Remove image
  docker_image:
    state: absent
    name: registry.ansible.com/chouseknecht/sinatra
    tag: v1

- name: Build an image and push it to a private repo
  docker_image:
    path: ./sinatra
    name: registry.ansible.com/chouseknecht/sinatra
    tag: v1
    push: yes

- name: Archive image
  docker_image:
    name: registry.ansible.com/chouseknecht/sinatra
    tag: v1
    archive_path: my_sinatra.tar

- name: Load image from archive and push to a private registry
  docker_image:
    name: localhost:5000/myimages/sinatra
    tag: v1
    push: yes
    load_path: my_sinatra.tar

- name: Build image and with buildargs
  docker_image:
     path: /path/to/build/dir
     name: myimage
     buildargs:
       log_volume: /var/log/myapp
       listen_port: 8080
'''

RETURN = '''
image:
    description: Image inspection results for the affected image.
    returned: success
    type: dict
    sample: {}
'''
import os
import re

from ansible.module_utils.docker_common import HAS_DOCKER_PY_2, HAS_DOCKER_PY_3, AnsibleDockerClient, DockerBaseClass
from ansible.module_utils._text import to_native

try:
    if HAS_DOCKER_PY_2 or HAS_DOCKER_PY_3:
        from docker.auth import resolve_repository_name
    else:
        from docker.auth.auth import resolve_repository_name
    from docker.utils.utils import parse_repository_tag
except ImportError:
    # missing docker-py handled in docker_common
    pass


class ImageManager(DockerBaseClass):

    def __init__(self, client, results):

        super(ImageManager, self).__init__()

        self.client = client
        self.results = results
        parameters = self.client.module.params
        self.check_mode = self.client.check_mode

        self.archive_path = parameters.get('archive_path')
        self.container_limits = parameters.get('container_limits')
        self.dockerfile = parameters.get('dockerfile')
        self.force = parameters.get('force')
        self.load_path = parameters.get('load_path')
        self.name = parameters.get('name')
        self.nocache = parameters.get('nocache')
        self.path = parameters.get('path')
        self.pull = parameters.get('pull')
        self.repository = parameters.get('repository')
        self.rm = parameters.get('rm')
        self.state = parameters.get('state')
        self.tag = parameters.get('tag')
        self.http_timeout = parameters.get('http_timeout')
        self.push = parameters.get('push')
        self.buildargs = parameters.get('buildargs')

        # If name contains a tag, it takes precedence over tag parameter.
        repo, repo_tag = parse_repository_tag(self.name)
        if repo_tag:
            self.name = repo
            self.tag = repo_tag

        if self.state in ['present', 'build']:
            self.present()
        elif self.state == 'absent':
            self.absent()

    def fail(self, msg):
        self.client.fail(msg)

    def present(self):
        '''
        Handles state = 'present', which includes building, loading or pulling an image,
        depending on user provided parameters.

        :returns None
        '''
        image = self.client.find_image(name=self.name, tag=self.tag)

        if not image or self.force:
            if self.path:
                # Build the image
                if not os.path.isdir(self.path):
                    self.fail("Requested build path %s could not be found or you do not have access." % self.path)
                image_name = self.name
                if self.tag:
                    image_name = "%s:%s" % (self.name, self.tag)
                self.log("Building image %s" % image_name)
                self.results['actions'].append("Built image %s from %s" % (image_name, self.path))
                self.results['changed'] = True
                if not self.check_mode:
                    self.results['image'] = self.build_image()
            elif self.load_path:
                # Load the image from an archive
                if not os.path.isfile(self.load_path):
                    self.fail("Error loading image %s. Specified path %s does not exist." % (self.name,
                                                                                             self.load_path))
                image_name = self.name
                if self.tag:
                    image_name = "%s:%s" % (self.name, self.tag)
                self.results['actions'].append("Loaded image %s from %s" % (image_name, self.load_path))
                self.results['changed'] = True
                if not self.check_mode:
                    self.results['image'] = self.load_image()
            else:
                # pull the image
                self.results['actions'].append('Pulled image %s:%s' % (self.name, self.tag))
                self.results['changed'] = True
                if not self.check_mode:
                    self.results['image'], already_latest = self.client.pull_image(self.name, tag=self.tag)
                    if already_latest:
                        self.results['changed'] = False

        if self.archive_path:
            self.archive_image(self.name, self.tag)

        if self.push and not self.repository:
            self.push_image(self.name, self.tag)
        elif self.repository:
            self.tag_image(self.name, self.tag, self.repository, force=self.force, push=self.push)

    def absent(self):
        '''
        Handles state = 'absent', which removes an image.

        :return None
        '''
        image = self.client.find_image(self.name, self.tag)
        if image:
            name = self.name
            if self.tag:
                name = "%s:%s" % (self.name, self.tag)
            if not self.check_mode:
                try:
                    self.client.remove_image(name, force=self.force)
                except Exception as exc:
                    self.fail("Error removing image %s - %s" % (name, str(exc)))

            self.results['changed'] = True
            self.results['actions'].append("Removed image %s" % (name))
            self.results['image']['state'] = 'Deleted'

    def archive_image(self, name, tag):
        '''
        Archive an image to a .tar file. Called when archive_path is passed.

        :param name - name of the image. Type: str
        :return None
        '''

        if not tag:
            tag = "latest"

        image = self.client.find_image(name=name, tag=tag)
        if not image:
            self.log("archive image: image %s:%s not found" % (name, tag))
            return

        image_name = "%s:%s" % (name, tag)
        self.results['actions'].append('Archived image %s to %s' % (image_name, self.archive_path))
        self.results['changed'] = True
        if not self.check_mode:
            self.log("Getting archive of image %s" % image_name)
            try:
                image = self.client.get_image(image_name)
            except Exception as exc:
                self.fail("Error getting image %s - %s" % (image_name, str(exc)))

            try:
                with open(self.archive_path, 'wb') as fd:
                    if HAS_DOCKER_PY_3:
                        for chunk in image:
                            fd.write(chunk)
                    else:
                        for chunk in image.stream(2048, decode_content=False):
                            fd.write(chunk)
            except Exception as exc:
                self.fail("Error writing image archive %s - %s" % (self.archive_path, str(exc)))

        image = self.client.find_image(name=name, tag=tag)
        if image:
            self.results['image'] = image

    def push_image(self, name, tag=None):
        '''
        If the name of the image contains a repository path, then push the image.

        :param name Name of the image to push.
        :param tag Use a specific tag.
        :return: None
        '''

        repository = name
        if not tag:
            repository, tag = parse_repository_tag(name)
        registry, repo_name = resolve_repository_name(repository)

        self.log("push %s to %s/%s:%s" % (self.name, registry, repo_name, tag))

        if registry:
            self.results['actions'].append("Pushed image %s to %s/%s:%s" % (self.name, registry, repo_name, tag))
            self.results['changed'] = True
            if not self.check_mode:
                status = None
                try:
                    for line in self.client.push(repository, tag=tag, stream=True, decode=True):
                        self.log(line, pretty_print=True)
                        if line.get('errorDetail'):
                            raise Exception(line['errorDetail']['message'])
                        status = line.get('status')
                except Exception as exc:
                    if re.search('unauthorized', str(exc)):
                        if re.search('authentication required', str(exc)):
                            self.fail("Error pushing image %s/%s:%s - %s. Try logging into %s first." %
                                      (registry, repo_name, tag, str(exc), registry))
                        else:
                            self.fail("Error pushing image %s/%s:%s - %s. Does the repository exist?" %
                                      (registry, repo_name, tag, str(exc)))
                    self.fail("Error pushing image %s: %s" % (repository, str(exc)))
                self.results['image'] = self.client.find_image(name=repository, tag=tag)
                if not self.results['image']:
                    self.results['image'] = dict()
                self.results['image']['push_status'] = status

    def tag_image(self, name, tag, repository, force=False, push=False):
        '''
        Tag an image into a repository.

        :param name: name of the image. required.
        :param tag: image tag.
        :param repository: path to the repository. required.
        :param force: bool. force tagging, even it image already exists with the repository path.
        :param push: bool. push the image once it's tagged.
        :return: None
        '''
        repo, repo_tag = parse_repository_tag(repository)
        if not repo_tag:
            repo_tag = "latest"
            if tag:
                repo_tag = tag
        image = self.client.find_image(name=repo, tag=repo_tag)
        found = 'found' if image else 'not found'
        self.log("image %s was %s" % (repo, found))

        if not image or force:
            self.log("tagging %s:%s to %s:%s" % (name, tag, repo, repo_tag))
            self.results['changed'] = True
            self.results['actions'].append("Tagged image %s:%s to %s:%s" % (name, tag, repo, repo_tag))
            if not self.check_mode:
                try:
                    # Finding the image does not always work, especially running a localhost registry. In those
                    # cases, if we don't set force=True, it errors.
                    image_name = name
                    if tag and not re.search(tag, name):
                        image_name = "%s:%s" % (name, tag)
                    tag_status = self.client.tag(image_name, repo, tag=repo_tag, force=True)
                    if not tag_status:
                        raise Exception("Tag operation failed.")
                except Exception as exc:
                    self.fail("Error: failed to tag image - %s" % str(exc))
                self.results['image'] = self.client.find_image(name=repo, tag=repo_tag)
                if push:
                    self.push_image(repo, repo_tag)

    def build_image(self):
        '''
        Build an image

        :return: image dict
        '''
        params = dict(
            path=self.path,
            tag=self.name,
            rm=self.rm,
            nocache=self.nocache,
            timeout=self.http_timeout,
            pull=self.pull,
            forcerm=self.rm,
            dockerfile=self.dockerfile,
            decode=True
        )
        if not HAS_DOCKER_PY_3:
            params['stream'] = True
        build_output = []
        if self.tag:
            params['tag'] = "%s:%s" % (self.name, self.tag)
        if self.container_limits:
            params['container_limits'] = self.container_limits
        if self.buildargs:
            for key, value in self.buildargs.items():
                self.buildargs[key] = to_native(value)
            params['buildargs'] = self.buildargs

        for line in self.client.build(**params):
            # line = json.loads(line)
            self.log(line, pretty_print=True)
            if "stream" in line:
                build_output.append(line["stream"])
            if line.get('error'):
                if line.get('errorDetail'):
                    errorDetail = line.get('errorDetail')
                    self.fail(
                        "Error building %s - code: %s, message: %s, logs: %s" % (
                            self.name,
                            errorDetail.get('code'),
                            errorDetail.get('message'),
                            build_output))
                else:
                    self.fail("Error building %s - message: %s, logs: %s" % (
                        self.name, line.get('error'), build_output))
        return self.client.find_image(name=self.name, tag=self.tag)

    def load_image(self):
        '''
        Load an image from a .tar archive

        :return: image dict
        '''
        try:
            self.log("Opening image %s" % self.load_path)
            image_tar = open(self.load_path, 'rb')
        except Exception as exc:
            self.fail("Error opening image %s - %s" % (self.load_path, str(exc)))

        try:
            self.log("Loading image from %s" % self.load_path)
            self.client.load_image(image_tar)
        except Exception as exc:
            self.fail("Error loading image %s - %s" % (self.name, str(exc)))

        try:
            image_tar.close()
        except Exception as exc:
            self.fail("Error closing image %s - %s" % (self.name, str(exc)))

        return self.client.find_image(self.name, self.tag)


def main():
    argument_spec = dict(
        archive_path=dict(type='path'),
        container_limits=dict(type='dict'),
        dockerfile=dict(type='str'),
        force=dict(type='bool', default=False),
        http_timeout=dict(type='int'),
        load_path=dict(type='path'),
        name=dict(type='str', required=True),
        nocache=dict(type='bool', default=False),
        path=dict(type='path', aliases=['build_path']),
        pull=dict(type='bool', default=True),
        push=dict(type='bool', default=False),
        repository=dict(type='str'),
        rm=dict(type='bool', default=True),
        state=dict(type='str', choices=['absent', 'present', 'build'], default='present'),
        tag=dict(type='str', default='latest'),
        use_tls=dict(type='str', default='no', choices=['no', 'encrypt', 'verify']),
        buildargs=dict(type='dict', default=None),
    )

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    results = dict(
        changed=False,
        actions=[],
        image={}
    )

    ImageManager(client, results)
    client.module.exit_json(**results)


if __name__ == '__main__':
    main()
