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
module: docker_image_facts

short_description: Inspect docker images

version_added: "2.1.0"

description:
     - Provide one or more image names, and the module will inspect each, returning an array of inspection results.

options:
  name:
    description:
      - An image name or a list of image names. Name format will be name[:tag] or repository/name[:tag], where tag is
        optional. If a tag is not provided, 'latest' will be used.
    required: true

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
     be installed at the same time."
  - "Docker API >= 1.20"

author:
  - Chris Houseknecht (@chouseknecht)

'''

EXAMPLES = '''

- name: Inspect a single image
  docker_image_facts:
    name: pacur/centos-7

- name: Inspect multiple images
  docker_image_facts:
    name:
      - pacur/centos-7
      - sinatra
'''

RETURN = '''
images:
    description: Facts for the selected images.
    returned: always
    type: dict
    sample: [
        {
            "Architecture": "amd64",
            "Author": "",
            "Comment": "",
            "Config": {
                "AttachStderr": false,
                "AttachStdin": false,
                "AttachStdout": false,
                "Cmd": [
                    "/etc/docker/registry/config.yml"
                ],
                "Domainname": "",
                "Entrypoint": [
                    "/bin/registry"
                ],
                "Env": [
                    "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
                ],
                "ExposedPorts": {
                    "5000/tcp": {}
                },
                "Hostname": "e5c68db50333",
                "Image": "c72dce2618dc8f7b794d2b2c2b1e64e0205ead5befc294f8111da23bd6a2c799",
                "Labels": {},
                "OnBuild": [],
                "OpenStdin": false,
                "StdinOnce": false,
                "Tty": false,
                "User": "",
                "Volumes": {
                    "/var/lib/registry": {}
                },
                "WorkingDir": ""
            },
            "Container": "e83a452b8fb89d78a25a6739457050131ca5c863629a47639530d9ad2008d610",
            "ContainerConfig": {
                "AttachStderr": false,
                "AttachStdin": false,
                "AttachStdout": false,
                "Cmd": [
                    "/bin/sh",
                    "-c",
                    '#(nop) CMD ["/etc/docker/registry/config.yml"]'
                ],
                "Domainname": "",
                "Entrypoint": [
                    "/bin/registry"
                ],
                "Env": [
                    "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
                ],
                "ExposedPorts": {
                    "5000/tcp": {}
                },
                "Hostname": "e5c68db50333",
                "Image": "c72dce2618dc8f7b794d2b2c2b1e64e0205ead5befc294f8111da23bd6a2c799",
                "Labels": {},
                "OnBuild": [],
                "OpenStdin": false,
                "StdinOnce": false,
                "Tty": false,
                "User": "",
                "Volumes": {
                    "/var/lib/registry": {}
                },
                "WorkingDir": ""
            },
            "Created": "2016-03-08T21:08:15.399680378Z",
            "DockerVersion": "1.9.1",
            "GraphDriver": {
                "Data": null,
                "Name": "aufs"
            },
            "Id": "53773d8552f07b730f3e19979e32499519807d67b344141d965463a950a66e08",
            "Name": "registry:2",
            "Os": "linux",
            "Parent": "f0b1f729f784b755e7bf9c8c2e65d8a0a35a533769c2588f02895f6781ac0805",
            "RepoDigests": [],
            "RepoTags": [
                "registry:2"
            ],
            "Size": 0,
            "VirtualSize": 165808884
        }
    ]
'''

try:
    from docker import utils
except ImportError:
    # missing docker-py handled in ansible.module_utils.docker_common
    pass

from ansible.module_utils.docker_common import AnsibleDockerClient, DockerBaseClass


class ImageManager(DockerBaseClass):

    def __init__(self, client, results):

        super(ImageManager, self).__init__()

        self.client = client
        self.results = results
        self.name = self.client.module.params.get('name')
        self.log("Gathering facts for images: %s" % (str(self.name)))

        if self.name:
            self.results['images'] = self.get_facts()
        else:
            self.results['images'] = self.get_all_images()

    def fail(self, msg):
        self.client.fail(msg)

    def get_facts(self):
        '''
        Lookup and inspect each image name found in the names parameter.

        :returns array of image dictionaries
        '''

        results = []

        names = self.name
        if not isinstance(names, list):
            names = [names]

        for name in names:
            repository, tag = utils.parse_repository_tag(name)
            if not tag:
                tag = 'latest'
            self.log('Fetching image %s:%s' % (repository, tag))
            image = self.client.find_image(name=repository, tag=tag)
            if image:
                results.append(image)
        return results

    def get_all_images(self):
        results = []
        images = self.client.images()
        for image in images:
            try:
                inspection = self.client.inspect_image(image['Id'])
            except Exception as exc:
                self.fail("Error inspecting image %s - %s" % (image['Id'], str(exc)))
            results.append(inspection)
        return results


def main():
    argument_spec = dict(
        name=dict(type='list'),
    )

    client = AnsibleDockerClient(
        argument_spec=argument_spec
    )

    results = dict(
        changed=False,
        images=[]
    )

    ImageManager(client, results)
    client.module.exit_json(**results)


if __name__ == '__main__':
    main()
