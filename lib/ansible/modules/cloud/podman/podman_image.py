#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
  module: podman_image
  author:
      - Sam Doran (@samdoran)
  version_added: '2.8'
  short_description: Pull images for use by podman
  notes: []
  description:
      - Build, pull, or push images using Podman.
  options:
    name:
      description:
        - Name of the image to pull, push, or delete. It may contain a tag using the format C(image:tag).
      required: True
    executable:
      description:
        - Path to C(podman) executable if it is not in the C($PATH) on the machine running C(podman)
      default: 'podman'
      type: str
    ca_cert_dir:
      description:
        - Path to directory containing TLS certificates and keys to use
      type: 'path'
    tag:
      description:
        - Tag of the image to pull, push, or delete.
      default: "latest"
    pull:
      description: Whether or not to pull the image.
      default: True
    push:
      description: Whether or not to push an image.
      default: False
    path:
      description: Path to directory containing the build file.
    force:
      description:
        - Whether or not to force push or pull an image. When building, force the build even if the image already exists.
    state:
      description:
        - Whether an image should be present, absent, or built.
      default: "present"
      choices:
        - present
        - absent
        - build
    validate_certs:
      description:
        - Require HTTPS and validate certificates when pulling or pushing. Also used during build if a pull or push is necessary.
      default: True
      aliases:
        - tlsverify
        - tls_verify
    password:
      description:
        - Password to use when authenticating to remote registries.
      type: str
    username:
      description:
        - username to use when authenticating to remote registries.
      type: str
    auth_file:
      description:
        - Path to file containing authorization credentials to the remote registry
      aliases:
        - authfile
    build:
      description: Arguments that control image build.
      aliases:
        - build_args
        - buildargs
      suboptions:
        annotation:
          description:
            - Dictionary of key=value pairs to add to the image. Only works with OCI images. Ignored for Docker containers.
          type: str
        force_rm:
          description:
            - Always remove intermediate containers after a build, even if the build is unsuccessful.
          type: bool
          default: False
        format:
          description:
            - Format of the built image.
          choices:
            - docker
            - oci
          default: "oci"
        cache:
          description:
            - Whether or not to use cached layers when building an image
          type: bool
          default: True
        rm:
          description: Remove intermediate containers after a successful build
          type: bool
          default: True
    push_args:
      description: Arguments that control pushing images.
      suboptions:
        compress:
          description:
            - Compress tarball image layers when pushing to a directory using the 'dir' transport.
          type: bool
        format:
          description:
            - Manifest type to use when pushing an image using the 'dir' transport (default is manifest type of source)
          choices:
            - oci
            - v2s1
            - v2s2
        remove_signatures:
          description: Discard any pre-existing signatures in the image
          type: bool
        sign_by:
          description:
            - Path to a key file to use to sign the image.
        dest:
          description: Path or URL where image will be pushed.
        transport:
          description:
            - Transport to use when pushing in image. If no transport is set, will attempt to push to a remote registry.
          choices:
            - dir
            - docker-archive
            - docker-daemon
            - oci-archive
            - ostree
"""

EXAMPLES = """
- name: Pull an image
  podman_image:
    name: quay.io/bitnami/wildfly

- name: Remove an image
  podman_image:
    name: quay.io/bitnami/wildfly
    state: absent

- name: Pull a specific version of an image
  podman_image:
    name: redis
    tag: 4

- name: Build a basic OCI image
  podman_image:
    name: nginx
    path: /path/to/build/dir

- name: Build a basic OCI image with advanced parameters
  podman_image:
    name: nginx
    path: /path/to/build/dir
    build:
      cache: no
      force_rm: yes
      format: oci
      annotation:
        app: nginx
        function: proxy
        info: Load balancer for my cool app

- name: Build a Docker formatted image
  podman_image:
    name: nginx
    path: /path/to/build/dir
    build:
      format: docker

- name: Build and push an image using existing credentials
  podman_image:
    name: nginx
    path: /path/to/build/dir
    push: yes
    push_args:
      dest: quay.io/acme

- name: Build and push an image using an auth file
  podman_image:
    name: nginx
    push: yes
    auth_file: /etc/containers/auth.json
    push_args:
      dest: quay.io/acme

- name: Build and push an image using username and password
  podman_image:
    name: nginx
    push: yes
    username: bugs
    password: "{{ vault_registry_password }}"
    push_args:
      dest: quay.io/acme

- name: Build and push an image to multiple registries
  podman_image:
    name: "{{ item }}"
    path: /path/to/build/dir
    push: yes
    auth_file: /etc/containers/auth.json
    loop:
    - quay.io/acme/nginx
    - docker.io/acme/nginx

- name: Build and push an image to multiple registries with separate parameters
  podman_image:
    name: "{{ item.name }}"
    tag: "{{ item.tag }}"
    path: /path/to/build/dir
    push: yes
    auth_file: /etc/containers/auth.json
    push_args:
      dest: "{{ item.dest }}"
    loop:
    - name: nginx
      tag: 4
      dest: docker.io/acme

    - name: nginx
      tag: 3
      dest: docker.io/acme
"""

RETURN = """
  image:
    description:
      - Image inspection results for the image that was pulled, pushed, or built.
    returned: success
    type: dict
    sample: [
      {
        "Annotations": {},
        "Architecture": "amd64",
        "Author": "",
        "Comment": "from Bitnami with love",
        "ContainerConfig": {
          "Cmd": [
            "/run.sh"
          ],
          "Entrypoint": [
            "/app-entrypoint.sh"
          ],
          "Env": [
            "PATH=/opt/bitnami/java/bin:/opt/bitnami/wildfly/bin:/opt/bitnami/nami/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "IMAGE_OS=debian-9",
            "NAMI_VERSION=1.0.0-1",
            "GPG_KEY_SERVERS_LIST=ha.pool.sks-keyservers.net",
            "TINI_VERSION=v0.13.2",
            "TINI_GPG_KEY=595E85A6B1B4779EA4DAAEC70B588DFF0527A9B7",
            "GOSU_VERSION=1.10",
            "GOSU_GPG_KEY=B42F6819007F00F88E364FD4036A9C25BF357DD4",
            "BITNAMI_IMAGE_VERSION=16.0.0-debian-9-r27",
            "BITNAMI_PKG_CHMOD=-R g+rwX",
            "BITNAMI_PKG_EXTRA_DIRS=/home/wildfly",
            "HOME=/",
            "BITNAMI_APP_NAME=wildfly",
            "NAMI_PREFIX=/.nami",
            "WILDFLY_HOME=/home/wildfly",
            "WILDFLY_JAVA_HOME=",
            "WILDFLY_JAVA_OPTS=",
            "WILDFLY_MANAGEMENT_HTTP_PORT_NUMBER=9990",
            "WILDFLY_PASSWORD=bitnami",
            "WILDFLY_PUBLIC_CONSOLE=true",
            "WILDFLY_SERVER_AJP_PORT_NUMBER=8009",
            "WILDFLY_SERVER_HTTP_PORT_NUMBER=8080",
            "WILDFLY_SERVER_INTERFACE=0.0.0.0",
            "WILDFLY_USERNAME=user",
            "WILDFLY_WILDFLY_HOME=/home/wildfly",
            "WILDFLY_WILDFLY_OPTS=-Dwildfly.as.deployment.ondemand=false"
          ],
          "ExposedPorts": {
            "8080/tcp": {},
            "9990/tcp": {}
          },
          "Labels": {
            "maintainer": "Bitnami <containers@bitnami.com>"
          },
          "User": "1001"
        },
        "Created": "2019-04-10T05:48:03.553887623Z",
        "Digest": "sha256:5a8ab28e314c2222de3feaf6dac94a0436a37fc08979d2722c99d2bef2619a9b",
        "GraphDriver": {
          "Data": {
            "LowerDir": "/var/lib/containers/storage/overlay/142c1beadf1bb09fbd929465ec98c9dca3256638220450efb4214727d0d0680e/diff:/var/lib/containers/s",
            "MergedDir": "/var/lib/containers/storage/overlay/9aa10191f5bddb59e28508e721fdeb43505e5b395845fa99723ed787878dbfea/merged",
            "UpperDir": "/var/lib/containers/storage/overlay/9aa10191f5bddb59e28508e721fdeb43505e5b395845fa99723ed787878dbfea/diff",
            "WorkDir": "/var/lib/containers/storage/overlay/9aa10191f5bddb59e28508e721fdeb43505e5b395845fa99723ed787878dbfea/work"
          },
          "Name": "overlay"
        },
        "History": [
          {
            "comment": "from Bitnami with love",
            "created": "2019-04-09T22:27:40.659377677Z"
          },
          {
            "created": "2019-04-09T22:38:53.86336555Z",
            "created_by": "/bin/sh -c #(nop)  LABEL maintainer=Bitnami <containers@bitnami.com>",
            "empty_layer": true
          },
          {
            "created": "2019-04-09T22:38:54.022778765Z",
            "created_by": "/bin/sh -c #(nop)  ENV IMAGE_OS=debian-9",
            "empty_layer": true
          },
        ],
        "Id": "ace34da54e4af2145e1ad277005adb235a214e4dfe1114c2db9ab460b840f785",
        "Labels": {
          "maintainer": "Bitnami <containers@bitnami.com>"
        },
        "ManifestType": "application/vnd.docker.distribution.manifest.v1+prettyjws",
        "Os": "linux",
        "Parent": "",
        "RepoDigests": [
          "quay.io/bitnami/wildfly@sha256:5a8ab28e314c2222de3feaf6dac94a0436a37fc08979d2722c99d2bef2619a9b"
        ],
        "RepoTags": [
          "quay.io/bitnami/wildfly:latest"
        ],
        "RootFS": {
          "Layers": [
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            ""
          ],
          "Type": "layers"
        },
        "Size": 466180019,
        "User": "1001",
        "Version": "18.09.3",
        "VirtualSize": 466180019
      }
    ]
"""

import json
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.podman.common import run_podman_command


class PodmanImageManager(object):

    def __init__(self, module, results):

        super(PodmanImageManager, self).__init__()

        self.module = module
        self.results = results
        self.name = self.module.params.get('name')
        self.executable = self.module.get_bin_path(module.params.get('executable'), required=True)
        self.tag = self.module.params.get('tag')
        self.pull = self.module.params.get('pull')
        self.push = self.module.params.get('push')
        self.path = self.module.params.get('path')
        self.force = self.module.params.get('force')
        self.state = self.module.params.get('state')
        self.validate_certs = self.module.params.get('validate_certs')
        self.auth_file = self.module.params.get('auth_file')
        self.username = self.module.params.get('username')
        self.password = self.module.params.get('password')
        self.ca_cert_dir = self.module.params.get('ca_cert_dir')
        self.build = self.module.params.get('build')
        self.push_args = self.module.params.get('push_args')

        repo, repo_tag = parse_repository_tag(self.name)
        if repo_tag:
            self.name = repo
            self.tag = repo_tag

        self.image_name = '{name}:{tag}'.format(name=self.name, tag=self.tag)

        if self.state in ['present', 'build']:
            self.present()

        if self.state in ['absent']:
            self.absent()

    def _run(self, args, expected_rc=0, ignore_errors=False):
        return run_podman_command(
            module=self.module,
            executable=self.executable,
            args=args,
            expected_rc=expected_rc,
            ignore_errors=ignore_errors)

    def _get_id_from_output(self, lines, startswith=None, contains=None, split_on=' ', maxsplit=1):
        layer_ids = []
        for line in lines.splitlines():
            if startswith and line.startswith(startswith) or contains and contains in line:
                splitline = line.rsplit(split_on, maxsplit)
                layer_ids.append(splitline[1])

        # Podman 1.4 changed the output to only include the layer id when run in quiet mode
        if not layer_ids:
            layer_ids = lines.splitlines()

        return(layer_ids[-1])

    def present(self):
        image = self.find_image()

        if not image or self.force:
            if self.path:
                # Build the image
                self.results['actions'].append('Built image {image_name} from {path}'.format(image_name=self.image_name, path=self.path))
                self.results['changed'] = True
                if not self.module.check_mode:
                    self.results['image'] = self.build_image()
            else:
                # Pull the image
                self.results['actions'].append('Pulled image {image_name}'.format(image_name=self.image_name))
                self.results['changed'] = True
                if not self.module.check_mode:
                    self.results['image'] = self.pull_image()

        if self.push:
            # Push the image
            if '/' in self.image_name:
                push_format_string = 'Pushed image {image_name}'
            else:
                push_format_string = 'Pushed image {image_name} to {dest}'
            self.results['actions'].append(push_format_string.format(image_name=self.image_name, dest=self.push_args['dest']))
            self.results['changed'] = True
            if not self.module.check_mode:
                self.results['image'] = self.push_image()

    def absent(self):
        image = self.find_image()

        if image:
            self.results['actions'].append('Removed image {name}'.format(name=self.name))
            self.results['changed'] = True
            self.results['image']['state'] = 'Deleted'
            if not self.module.check_mode:
                self.remove_image()

    def find_image(self, image_name=None):
        if image_name is None:
            image_name = self.image_name
        args = ['image', 'ls', image_name, '--format', 'json']
        rc, images, err = self._run(args, ignore_errors=True)
        if len(images) > 0:
            return json.loads(images)
        else:
            return None

    def inspect_image(self, image_name=None):
        if image_name is None:
            image_name = self.image_name
        args = ['inspect', image_name, '--format', 'json']
        rc, image_data, err = self._run(args)
        if len(image_data) > 0:
            return json.loads(image_data)
        else:
            return None

    def pull_image(self, image_name=None):
        if image_name is None:
            image_name = self.image_name

        args = ['pull', image_name, '-q']

        if self.auth_file:
            args.extend(['--authfile', self.auth_file])

        if self.validate_certs:
            args.append('--tls-verify')

        if self.ca_cert_dir:
            args.extend(['--cert-dir', self.ca_cert_dir])

        rc, out, err = self._run(args, ignore_errors=True)
        if rc != 0:
            self.module.fail_json(msg='Failed to pull image {image_name}'.format(image_name=image_name))
        return self.inspect_image(out.strip())

    def build_image(self):
        args = ['build', '-q']
        args.extend(['-t', self.image_name])

        if self.validate_certs:
            args.append('--tls-verify')

        annotation = self.build.get('annotation')
        if annotation:
            for k, v in annotation.items():
                args.extend(['--annotation', '{k}={v}'.format(k=k, v=v)])

        if self.ca_cert_dir:
            args.extend(['--cert-dir', self.ca_cert_dir])

        if self.build.get('force_rm'):
            args.append('--force-rm')

        image_format = self.build.get('format')
        if image_format:
            args.extend(['--format', image_format])

        if not self.build.get('cache'):
            args.append('--no-cache')

        if self.build.get('rm'):
            args.append('--rm')

        volume = self.build.get('volume')
        if volume:
            for v in volume:
                args.extend(['--volume', v])

        if self.auth_file:
            args.extend(['--authfile', self.auth_file])

        if self.username and self.password:
            cred_string = '{user}:{password}'.format(user=self.username, password=self.password)
            args.extend(['--creds', cred_string])

        args.append(self.path)

        rc, out, err = self._run(args, ignore_errors=True)
        if rc != 0:
            self.module.fail_json(msg="Failed to build image {image}: {out} {err}".format(image=self.image_name, out=out, err=err))

        last_id = self._get_id_from_output(out, startswith='-->')
        return self.inspect_image(last_id)

    def push_image(self):
        args = ['push']

        if self.validate_certs:
            args.append('--tls-verify')

        if self.ca_cert_dir:
            args.extend(['--cert-dir', self.ca_cert_dir])

        if self.username and self.password:
            cred_string = '{user}:{password}'.format(user=self.username, password=self.password)
            args.extend(['--creds', cred_string])

        if self.auth_file:
            args.extend(['--authfile', self.auth_file])

        if self.push_args.get('compress'):
            args.append('--compress')

        push_format = self.push_args.get('format')
        if push_format:
            args.extend(['--format', push_format])

        if self.push_args.get('remove_signatures'):
            args.append('--remove-signatures')

        sign_by_key = self.push_args.get('sign_by')
        if sign_by_key:
            args.extend(['--sign-by', sign_by_key])

        args.append(self.image_name)

        # Build the destination argument
        dest = self.push_args.get('dest')
        dest_format_string = '{dest}/{image_name}'
        regexp = re.compile(r'/{name}(:{tag})?'.format(name=self.name, tag=self.tag))
        if not dest:
            if '/' not in self.name:
                self.module.fail_json(msg="'push_args['dest']' is required when pushing images that do not have the remote registry in the image name")

        # If the push destination contains the image name and/or the tag
        # remove it and warn since it's not needed.
        elif regexp.search(dest):
            dest = regexp.sub('', dest)
            self.module.warn("Image name and tag are automatically added to push_args['dest']. Destination changed to {dest}".format(dest=dest))

        if dest and dest.endswith('/'):
            dest = dest[:-1]

        transport = self.push_args.get('transport')
        if transport:
            if not dest:
                self.module.fail_json("'push_args['transport'] requires 'push_args['dest'] but it was not provided.")
            if transport == 'docker':
                dest_format_string = '{transport}://{dest}'
            elif transport == 'ostree':
                dest_format_string = '{transport}:{name}@{dest}'
            else:
                dest_format_string = '{transport}:{dest}'

        dest_string = dest_format_string.format(transport=transport, name=self.name, dest=dest, image_name=self.image_name,)

        # Only append the destination argument if the image name is not a URL
        if '/' not in self.name:
            args.append(dest_string)

        rc, out, err = self._run(args, ignore_errors=True)
        if rc != 0:
            self.module.fail_json(msg="Failed to push image {image_name}: {err}".format(image_name=self.image_name, err=err))
        last_id = self._get_id_from_output(
            out + err, contains=':', split_on=':')

        return self.inspect_image(last_id)

    def remove_image(self, image_name=None):
        if image_name is None:
            image_name = self.image_name

        args = ['rmi', image_name]
        if self.force:
            args.append('--force')
        rc, out, err = self._run(args, ignore_errors=True)
        if rc != 0:
            self.module.fail_json(msg='Failed to remove image {image_name}. {err}'.format(image_name=image_name, err=err))
        return out


def parse_repository_tag(repo_name):
    parts = repo_name.rsplit('@', 1)
    if len(parts) == 2:
        return tuple(parts)
    parts = repo_name.rsplit(':', 1)
    if len(parts) == 2 and '/' not in parts[1]:
        return tuple(parts)
    return repo_name, None


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            tag=dict(type='str', default='latest'),
            pull=dict(type='bool', default=True),
            push=dict(type='bool', default=False),
            path=dict(type='str'),
            force=dict(type='bool', default=False),
            state=dict(type='str', default='present', choices=['absent', 'present', 'build']),
            validate_certs=dict(type='bool', default=True, aliases=['tlsverify', 'tls_verify']),
            executable=dict(type='str', default='podman'),
            auth_file=dict(type='path', aliases=['authfile']),
            username=dict(type='str'),
            password=dict(type='str', no_log=True),
            ca_cert_dir=dict(type='path'),
            build=dict(
                type='dict',
                aliases=['build_args', 'buildargs'],
                default={},
                options=dict(
                    annotation=dict(type='dict'),
                    force_rm=dict(type='bool'),
                    format=dict(
                        type='str',
                        choices=['oci', 'docker'],
                        default='oci'
                    ),
                    cache=dict(type='bool', default=True),
                    rm=dict(type='bool', default=True),
                    volume=dict(type='list'),
                ),
            ),
            push_args=dict(
                type='dict',
                default={},
                options=dict(
                    compress=dict(type='bool'),
                    format=dict(type='str', choices=['oci', 'v2s1', 'v2s2']),
                    remove_signatures=dict(type='bool'),
                    sign_by=dict(type='str'),
                    dest=dict(type='str', aliases=['destination'],),
                    transport=dict(
                        type='str',
                        choices=[
                            'dir',
                            'docker-archive',
                            'docker-daemon',
                            'oci-archive',
                            'ostree',
                        ]
                    ),
                ),
            ),
        ),
        supports_check_mode=True,
        required_together=(
            ['username', 'password'],
        ),
        mutually_exclusive=(
            ['authfile', 'username'],
            ['authfile', 'password'],
        ),
    )

    results = dict(
        changed=False,
        actions=[],
        image={},
    )

    PodmanImageManager(module, results)
    module.exit_json(**results)


if __name__ == '__main__':
    main()
