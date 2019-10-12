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
  - Since Ansible 2.8, it is recommended to explicitly specify the image's source (I(source) can be C(build),
    C(load), C(pull) or C(local)). This will be required from Ansible 2.12 on.

options:
  source:
    description:
      - "Determines where the module will try to retrieve the image from."
      - "Use C(build) to build the image from a C(Dockerfile). I(build.path) must
         be specified when this value is used."
      - "Use C(load) to load the image from a C(.tar) file. I(load_path) must
         be specified when this value is used."
      - "Use C(pull) to pull the image from a registry."
      - "Use C(local) to make sure that the image is already available on the local
         docker daemon, i.e. do not try to build, pull or load the image."
      - "Before Ansible 2.12, the value of this option will be auto-detected
         to be backwards compatible, but a warning will be issued if it is not
         explicitly specified. From Ansible 2.12 on, auto-detection will be disabled
         and this option will be made mandatory."
    type: str
    choices:
    - build
    - load
    - pull
    - local
    version_added: "2.8"
  build:
    description:
      - "Specifies options used for building images."
    type: dict
    suboptions:
      cache_from:
        description:
          - List of image names to consider as cache source.
        type: list
      dockerfile:
        description:
          - Use with state C(present) and source C(build) to provide an alternate name for the Dockerfile to use when building an image.
          - This can also include a relative path (relative to I(path)).
        type: str
      http_timeout:
        description:
          - Timeout for HTTP requests during the image build operation. Provide a positive integer value for the number of
            seconds.
        type: int
      path:
        description:
          - Use with state 'present' to build an image. Will be the path to a directory containing the context and
            Dockerfile for building an image.
        type: path
        required: yes
      pull:
        description:
          - When building an image downloads any updates to the FROM image in Dockerfile.
          - The default is currently C(yes). This will change to C(no) in Ansible 2.12.
        type: bool
      rm:
        description:
          - Remove intermediate containers after build.
        type: bool
        default: yes
      network:
        description:
          - The network to use for C(RUN) build instructions.
        type: str
      nocache:
        description:
          - Do not use cache when building an image.
        type: bool
        default: no
      args:
        description:
          - Provide a dictionary of C(key:value) build arguments that map to Dockerfile ARG directive.
          - Docker expects the value to be a string. For convenience any non-string values will be converted to strings.
          - Requires Docker API >= 1.21.
        type: dict
      container_limits:
        description:
          - A dictionary of limits applied to each container created by the build process.
        type: dict
        suboptions:
          memory:
            description:
              - Set memory limit for build.
            type: int
          memswap:
            description:
              - Total memory (memory + swap), -1 to disable swap.
            type: int
          cpushares:
            description:
              - CPU shares (relative weight).
            type: int
          cpusetcpus:
            description:
              - CPUs in which to allow execution, e.g., "0-3", "0,1".
            type: str
      use_config_proxy:
        description:
          - If set to C(yes) and a proxy configuration is specified in the docker client configuration
            (by default C($HOME/.docker/config.json)), the corresponding environment variables will
            be set in the container being built.
          - Needs Docker SDK for Python >= 3.7.0.
        type: bool
    version_added: "2.8"
  archive_path:
    description:
      - Use with state C(present) to archive an image to a .tar file.
    type: path
    version_added: "2.1"
  load_path:
    description:
      - Use with state C(present) to load an image from a .tar file.
      - Set I(source) to C(load) if you want to load the image. The option will
        be set automatically before Ansible 2.12 if this option is used (except
        if I(path) is specified as well, in which case building will take precedence).
        From Ansible 2.12 on, you have to set I(source) to C(load).
    type: path
    version_added: "2.2"
  dockerfile:
    description:
      - Use with state C(present) and source C(build) to provide an alternate name for the Dockerfile to use when building an image.
      - This can also include a relative path (relative to I(path)).
      - Please use I(build.dockerfile) instead. This option will be removed in Ansible 2.12.
    type: str
    version_added: "2.0"
  force:
    description:
      - Use with state I(absent) to un-tag and remove all images matching the specified name. Use with state
        C(present) to build, load or pull an image when the image already exists. Also use with state C(present)
        to force tagging an image.
      - Please stop using this option, and use the more specialized force options
        I(force_source), I(force_absent) and I(force_tag) instead.
      - This option will be removed in Ansible 2.12.
    type: bool
    version_added: "2.1"
  force_source:
    description:
      - Use with state C(present) to build, load or pull an image (depending on the
        value of the I(source) option) when the image already exists.
    type: bool
    default: false
    version_added: "2.8"
  force_absent:
    description:
      - Use with state I(absent) to un-tag and remove all images matching the specified name.
    type: bool
    default: false
    version_added: "2.8"
  force_tag:
    description:
      - Use with state C(present) to force tagging an image.
    type: bool
    default: false
    version_added: "2.8"
  http_timeout:
    description:
      - Timeout for HTTP requests during the image build operation. Provide a positive integer value for the number of
        seconds.
      - Please use I(build.http_timeout) instead. This option will be removed in Ansible 2.12.
    type: int
    version_added: "2.1"
  name:
    description:
      - "Image name. Name format will be one of: name, repository/name, registry_server:port/name.
        When pushing or pulling an image the name can optionally include the tag by appending ':tag_name'."
      - Note that image IDs (hashes) are not supported.
    type: str
    required: yes
  path:
    description:
      - Use with state 'present' to build an image. Will be the path to a directory containing the context and
        Dockerfile for building an image.
      - Set I(source) to C(build) if you want to build the image. The option will
        be set automatically before Ansible 2.12 if this option is used. From Ansible 2.12
        on, you have to set I(source) to C(build).
      - Please use I(build.path) instead. This option will be removed in Ansible 2.12.
    type: path
    aliases:
      - build_path
  pull:
    description:
      - When building an image downloads any updates to the FROM image in Dockerfile.
      - Please use I(build.pull) instead. This option will be removed in Ansible 2.12.
      - The default is currently C(yes). This will change to C(no) in Ansible 2.12.
    type: bool
    version_added: "2.1"
  push:
    description:
      - Push the image to the registry. Specify the registry as part of the I(name) or I(repository) parameter.
    type: bool
    default: no
    version_added: "2.2"
  rm:
    description:
      - Remove intermediate containers after build.
      - Please use I(build.rm) instead. This option will be removed in Ansible 2.12.
    type: bool
    default: yes
    version_added: "2.1"
  nocache:
    description:
      - Do not use cache when building an image.
      - Please use I(build.nocache) instead. This option will be removed in Ansible 2.12.
    type: bool
    default: no
  repository:
    description:
      - Full path to a repository. Use with state C(present) to tag the image into the repository. Expects
        format I(repository:tag). If no tag is provided, will use the value of the C(tag) parameter or I(latest).
    type: str
    version_added: "2.1"
  state:
    description:
      - Make assertions about the state of an image.
      - When C(absent) an image will be removed. Use the force option to un-tag and remove all images
        matching the provided name.
      - When C(present) check if an image exists using the provided name and tag. If the image is not found or the
        force option is used, the image will either be pulled, built or loaded, depending on the I(source) option.
      - By default the image will be pulled from Docker Hub, or the registry specified in the image's name. Note that
        this will change in Ansible 2.12, so to make sure that you are pulling, set I(source) to C(pull). To build
        the image, provide a I(path) value set to a directory containing a context and Dockerfile, and set I(source)
        to C(build). To load an image, specify I(load_path) to provide a path to an archive file. To tag an image to
        a repository, provide a I(repository) path. If the name contains a repository path, it will be pushed.
      - "*Note:* C(state=build) is DEPRECATED and will be removed in Ansible 2.11. Specifying C(build) will behave the
         same as C(present)."
    type: str
    default: present
    choices:
      - absent
      - present
      - build
  tag:
    description:
      - Used to select an image when pulling. Will be added to the image when pushing, tagging or building. Defaults to
        I(latest).
      - If I(name) parameter format is I(name:tag), then tag value from I(name) will take precedence.
    type: str
    default: latest
  buildargs:
    description:
      - Provide a dictionary of C(key:value) build arguments that map to Dockerfile ARG directive.
      - Docker expects the value to be a string. For convenience any non-string values will be converted to strings.
      - Requires Docker API >= 1.21.
      - Please use I(build.args) instead. This option will be removed in Ansible 2.12.
    type: dict
    version_added: "2.2"
  container_limits:
    description:
      - A dictionary of limits applied to each container created by the build process.
      - Please use I(build.container_limits) instead. This option will be removed in Ansible 2.12.
    type: dict
    suboptions:
      memory:
        description:
          - Set memory limit for build.
        type: int
      memswap:
        description:
          - Total memory (memory + swap), -1 to disable swap.
        type: int
      cpushares:
        description:
          - CPU shares (relative weight).
        type: int
      cpusetcpus:
        description:
          - CPUs in which to allow execution, e.g., "0-3", "0,1".
        type: str
    version_added: "2.1"
  use_tls:
    description:
      - "DEPRECATED. Whether to use tls to connect to the docker daemon. Set to
        C(encrypt) to use TLS. And set to C(verify) to use TLS and verify that
        the server's certificate is valid for the server."
      - "*Note:* If you specify this option, it will set the value of the I(tls) or
        I(validate_certs) parameters if not set to C(no)."
      - Will be removed in Ansible 2.11.
    type: str
    choices:
      - 'no'
      - 'encrypt'
      - 'verify'
    version_added: "2.0"

extends_documentation_fragment:
  - docker
  - docker.docker_py_1_documentation

requirements:
  - "L(Docker SDK for Python,https://docker-py.readthedocs.io/en/stable/) >= 1.8.0 (use L(docker-py,https://pypi.org/project/docker-py/) for Python 2.6)"
  - "Docker API >= 1.20"

author:
  - Pavel Antonov (@softzilla)
  - Chris Houseknecht (@chouseknecht)

'''

EXAMPLES = '''

- name: pull an image
  docker_image:
    name: pacur/centos-7
    source: pull

- name: Tag and push to docker hub
  docker_image:
    name: pacur/centos-7:56
    repository: dcoppenhagan/myimage:7.56
    push: yes
    source: local

- name: Tag and push to local registry
  docker_image:
    # Image will be centos:7
    name: centos
    # Will be pushed to localhost:5000/centos:7
    repository: localhost:5000/centos
    tag: 7
    push: yes
    source: local

- name: Add tag latest to image
  docker_image:
    name: myimage:7.1.2
    repository: myimage:latest
    # As 'latest' usually already is present, we need to enable overwriting of existing tags:
    force_tag: yes
    source: local

- name: Remove image
  docker_image:
    state: absent
    name: registry.ansible.com/chouseknecht/sinatra
    tag: v1

- name: Build an image and push it to a private repo
  docker_image:
    build:
      path: ./sinatra
    name: registry.ansible.com/chouseknecht/sinatra
    tag: v1
    push: yes
    source: build

- name: Archive image
  docker_image:
    name: registry.ansible.com/chouseknecht/sinatra
    tag: v1
    archive_path: my_sinatra.tar
    source: local

- name: Load image from archive and push to a private registry
  docker_image:
    name: localhost:5000/myimages/sinatra
    tag: v1
    push: yes
    load_path: my_sinatra.tar
    source: load

- name: Build image and with build args
  docker_image:
    name: myimage
    build:
      path: /path/to/build/dir
      args:
        log_volume: /var/log/myapp
        listen_port: 8080
    source: build

- name: Build image using cache source
  docker_image:
    name: myimage:latest
    build:
      path: /path/to/build/dir
      # Use as cache source for building myimage
      cache_from:
        - nginx:latest
        - alpine:3.8
    source: build
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
import traceback

from distutils.version import LooseVersion

from ansible.module_utils.docker.common import (
    docker_version,
    AnsibleDockerClient,
    DockerBaseClass,
    is_image_name_id,
    is_valid_tag,
    RequestException,
)
from ansible.module_utils._text import to_native

if docker_version is not None:
    try:
        if LooseVersion(docker_version) >= LooseVersion('2.0.0'):
            from docker.auth import resolve_repository_name
        else:
            from docker.auth.auth import resolve_repository_name
        from docker.utils.utils import parse_repository_tag
        from docker.errors import DockerException
    except ImportError:
        # missing Docker SDK for Python handled in module_utils.docker.common
        pass


class ImageManager(DockerBaseClass):

    def __init__(self, client, results):

        super(ImageManager, self).__init__()

        self.client = client
        self.results = results
        parameters = self.client.module.params
        self.check_mode = self.client.check_mode

        self.source = parameters['source']
        build = parameters['build'] or dict()
        self.archive_path = parameters.get('archive_path')
        self.cache_from = build.get('cache_from')
        self.container_limits = build.get('container_limits')
        self.dockerfile = build.get('dockerfile')
        self.force_source = parameters.get('force_source')
        self.force_absent = parameters.get('force_absent')
        self.force_tag = parameters.get('force_tag')
        self.load_path = parameters.get('load_path')
        self.name = parameters.get('name')
        self.network = build.get('network')
        self.nocache = build.get('nocache', False)
        self.build_path = build.get('path')
        self.pull = build.get('pull')
        self.repository = parameters.get('repository')
        self.rm = build.get('rm', True)
        self.state = parameters.get('state')
        self.tag = parameters.get('tag')
        self.http_timeout = build.get('http_timeout')
        self.push = parameters.get('push')
        self.buildargs = build.get('args')
        self.use_config_proxy = build.get('use_config_proxy')

        # If name contains a tag, it takes precedence over tag parameter.
        if not is_image_name_id(self.name):
            repo, repo_tag = parse_repository_tag(self.name)
            if repo_tag:
                self.name = repo
                self.tag = repo_tag

        if self.state == 'present':
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

        if not image or self.force_source:
            if self.source == 'build':
                # Build the image
                if not os.path.isdir(self.build_path):
                    self.fail("Requested build path %s could not be found or you do not have access." % self.build_path)
                image_name = self.name
                if self.tag:
                    image_name = "%s:%s" % (self.name, self.tag)
                self.log("Building image %s" % image_name)
                self.results['actions'].append("Built image %s from %s" % (image_name, self.build_path))
                self.results['changed'] = True
                if not self.check_mode:
                    self.results['image'] = self.build_image()
            elif self.source == 'load':
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
            elif self.source == 'pull':
                # pull the image
                self.results['actions'].append('Pulled image %s:%s' % (self.name, self.tag))
                self.results['changed'] = True
                if not self.check_mode:
                    self.results['image'], dummy = self.client.pull_image(self.name, tag=self.tag)
            elif self.source == 'local':
                if image is None:
                    name = self.name
                    if self.tag:
                        name = "%s:%s" % (self.name, self.tag)
                    self.client.fail('Cannot find the image %s locally.' % name)
            if not self.check_mode and image and image['Id'] == self.results['image']['Id']:
                self.results['changed'] = False

        if self.archive_path:
            self.archive_image(self.name, self.tag)

        if self.push and not self.repository:
            self.push_image(self.name, self.tag)
        elif self.repository:
            self.tag_image(self.name, self.tag, self.repository, push=self.push)

    def absent(self):
        '''
        Handles state = 'absent', which removes an image.

        :return None
        '''
        name = self.name
        if is_image_name_id(name):
            image = self.client.find_image_by_id(name)
        else:
            image = self.client.find_image(name, self.tag)
            if self.tag:
                name = "%s:%s" % (self.name, self.tag)
        if image:
            if not self.check_mode:
                try:
                    self.client.remove_image(name, force=self.force_absent)
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
                    if self.client.docker_py_version >= LooseVersion('3.0.0'):
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
                    changed = False
                    for line in self.client.push(repository, tag=tag, stream=True, decode=True):
                        self.log(line, pretty_print=True)
                        if line.get('errorDetail'):
                            raise Exception(line['errorDetail']['message'])
                        status = line.get('status')
                        if status == 'Pushing':
                            changed = True
                    self.results['changed'] = changed
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

    def tag_image(self, name, tag, repository, push=False):
        '''
        Tag an image into a repository.

        :param name: name of the image. required.
        :param tag: image tag.
        :param repository: path to the repository. required.
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

        if not image or self.force_tag:
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
                if image and image['Id'] == self.results['image']['Id']:
                    self.results['changed'] = False

                if push:
                    self.push_image(repo, repo_tag)

    def build_image(self):
        '''
        Build an image

        :return: image dict
        '''
        params = dict(
            path=self.build_path,
            tag=self.name,
            rm=self.rm,
            nocache=self.nocache,
            timeout=self.http_timeout,
            pull=self.pull,
            forcerm=self.rm,
            dockerfile=self.dockerfile,
            decode=True,
        )
        if self.client.docker_py_version < LooseVersion('3.0.0'):
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
        if self.cache_from:
            params['cache_from'] = self.cache_from
        if self.network:
            params['network_mode'] = self.network
        if self.use_config_proxy:
            params['use_config_proxy'] = self.use_config_proxy
            # Due to a bug in docker-py, it will crash if
            # use_config_proxy is True and buildargs is None
            if 'buildargs' not in params:
                params['buildargs'] = {}

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
        source=dict(type='str', choices=['build', 'load', 'pull', 'local']),
        build=dict(type='dict', suboptions=dict(
            cache_from=dict(type='list', elements='str'),
            container_limits=dict(type='dict', options=dict(
                memory=dict(type='int'),
                memswap=dict(type='int'),
                cpushares=dict(type='int'),
                cpusetcpus=dict(type='str'),
            )),
            dockerfile=dict(type='str'),
            http_timeout=dict(type='int'),
            network=dict(type='str'),
            nocache=dict(type='bool', default=False),
            path=dict(type='path', required=True),
            pull=dict(type='bool'),
            rm=dict(type='bool', default=True),
            args=dict(type='dict'),
            use_config_proxy=dict(type='bool'),
        )),
        archive_path=dict(type='path'),
        container_limits=dict(type='dict', options=dict(
            memory=dict(type='int'),
            memswap=dict(type='int'),
            cpushares=dict(type='int'),
            cpusetcpus=dict(type='str'),
        ), removed_in_version='2.12'),
        dockerfile=dict(type='str', removed_in_version='2.12'),
        force=dict(type='bool', removed_in_version='2.12'),
        force_source=dict(type='bool', default=False),
        force_absent=dict(type='bool', default=False),
        force_tag=dict(type='bool', default=False),
        http_timeout=dict(type='int', removed_in_version='2.12'),
        load_path=dict(type='path'),
        name=dict(type='str', required=True),
        nocache=dict(type='bool', default=False, removed_in_version='2.12'),
        path=dict(type='path', aliases=['build_path'], removed_in_version='2.12'),
        pull=dict(type='bool', removed_in_version='2.12'),
        push=dict(type='bool', default=False),
        repository=dict(type='str'),
        rm=dict(type='bool', default=True, removed_in_version='2.12'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'build']),
        tag=dict(type='str', default='latest'),
        use_tls=dict(type='str', choices=['no', 'encrypt', 'verify'], removed_in_version='2.11'),
        buildargs=dict(type='dict', removed_in_version='2.12'),
    )

    required_if = [
        # ('state', 'present', ['source']),   -- enable in Ansible 2.12.
        # ('source', 'build', ['build']),   -- enable in Ansible 2.12.
        ('source', 'load', ['load_path']),
    ]

    def detect_build_cache_from(client):
        return client.module.params['build'] and client.module.params['build'].get('cache_from') is not None

    def detect_build_network(client):
        return client.module.params['build'] and client.module.params['build'].get('network') is not None

    def detect_use_config_proxy(client):
        return client.module.params['build'] and client.module.params['build'].get('use_config_proxy') is not None

    option_minimal_versions = dict()
    option_minimal_versions["build.cache_from"] = dict(docker_py_version='2.1.0', docker_api_version='1.25', detect_usage=detect_build_cache_from)
    option_minimal_versions["build.network"] = dict(docker_py_version='2.4.0', docker_api_version='1.25', detect_usage=detect_build_network)
    option_minimal_versions["build.use_config_proxy"] = dict(docker_py_version='3.7.0', detect_usage=detect_use_config_proxy)

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        required_if=required_if,
        supports_check_mode=True,
        min_docker_version='1.8.0',
        min_docker_api_version='1.20',
        option_minimal_versions=option_minimal_versions,
    )

    if client.module.params['state'] == 'build':
        client.module.warn('The "build" state has been deprecated for a long time '
                           'and will be removed in Ansible 2.11. Please use '
                           '"present", which has the same meaning as "build".')
        client.module.params['state'] = 'present'
    if client.module.params['use_tls']:
        client.module.warn('The "use_tls" option has been deprecated for a long time '
                           'and will be removed in Ansible 2.11. Please use the'
                           '"tls" and "validate_certs" options instead.')

    if not is_valid_tag(client.module.params['tag'], allow_empty=True):
        client.fail('"{0}" is not a valid docker tag!'.format(client.module.params['tag']))

    build_options = dict(
        container_limits='container_limits',
        dockerfile='dockerfile',
        http_timeout='http_timeout',
        nocache='nocache',
        path='path',
        pull='pull',
        rm='rm',
        buildargs='args',
    )
    for option, build_option in build_options.items():
        default_value = None
        if option in ('rm', ):
            default_value = True
        elif option in ('nocache', ):
            default_value = False
        if client.module.params[option] != default_value:
            if client.module.params['build'] is None:
                client.module.params['build'] = dict()
            if client.module.params['build'].get(build_option, default_value) != default_value:
                client.fail('Cannot specify both %s and build.%s!' % (option, build_option))
            client.module.params['build'][build_option] = client.module.params[option]
            client.module.warn('Please specify build.%s instead of %s. The %s option '
                               'has been renamed and will be removed in Ansible 2.12.' % (build_option, option, option))
    if client.module.params['source'] == 'build':
        if (not client.module.params['build'] or not client.module.params['build'].get('path')):
            client.fail('If "source" is set to "build", the "build.path" option must be specified.')
        if client.module.params['build'].get('pull') is None:
            client.module.warn("The default for build.pull is currently 'yes', but will be changed to 'no' in Ansible 2.12. "
                               "Please set build.pull explicitly to the value you need.")
            client.module.params['build']['pull'] = True  # TODO: change to False in Ansible 2.12

    if client.module.params['state'] == 'present' and client.module.params['source'] is None:
        # Autodetection. To be removed in Ansible 2.12.
        if (client.module.params['build'] or dict()).get('path'):
            client.module.params['source'] = 'build'
        elif client.module.params['load_path']:
            client.module.params['source'] = 'load'
        else:
            client.module.params['source'] = 'pull'
        client.module.warn('The value of the "source" option was determined to be "%s". '
                           'Please set the "source" option explicitly. Autodetection will '
                           'be removed in Ansible 2.12.' % client.module.params['source'])

    if client.module.params['force']:
        client.module.params['force_source'] = True
        client.module.params['force_absent'] = True
        client.module.params['force_tag'] = True
        client.module.warn('The "force" option will be removed in Ansible 2.12. Please '
                           'use the "force_source", "force_absent" or "force_tag" option '
                           'instead, depending on what you want to force.')

    try:
        results = dict(
            changed=False,
            actions=[],
            image={}
        )

        ImageManager(client, results)
        client.module.exit_json(**results)
    except DockerException as e:
        client.fail('An unexpected docker error occurred: {0}'.format(e), exception=traceback.format_exc())
    except RequestException as e:
        client.fail('An unexpected requests error occurred when docker-py tried to talk to the docker daemon: {0}'.format(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
