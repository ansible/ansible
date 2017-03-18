#!/usr/bin/python
# This file is part of Ansible
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ecs_ecr_facts
version_added: "2.4"
short_description: Get Elastic Container Registry facts
description:
- Manage Elastic Container Registry facts
options:
    mode:
        description: which facts to fetch.
        choices:
        - list_repositories
        - list_images
        - describe_images
        default: list_repositories
        required: false
    repository_name:
        description:
        - the name of the repository
        - required for C(list_images) and C(describe_images)
        required: false
    image_list:
        description:
        - list of dictionaries containing C(imageDigest) and/or C(imageTag)s with values to match
        - if unspecified, all images in a repository are returned (except those tagged C(latest), apparently)
        required: false
notes:
- there's no way to create or list nondefault registries in any AWS API, though it's implied in the return data. So there's no input for the registry ID.
author:
- tedder (@tedder)
extends_documentation_fragment:
- aws
- ec2
'''

EXAMPLES = '''
- name: list my repositories in a region
  ecs_ecr_facts:
    mode: list_repositories
    region: 'us-west-2'
  register: repolist

- name: list images for a given repository
  ecs_ecr_facts:
    mode: list_images
    repository_name: 'numbers/jenny'
  register: imglist
- name: most recent version number
  debug: var=imglist.image_sorted_by_version[-1].imageTag

- name: get metadata on a specific image
  ecs_ecr_facts:
    mode: describe_images
    repository_name: 'numbers/jenny'
    image_list:
    - imageDigest: "{{imglist.image_sorted_by_version[-1].imageDigest}}"
    register: imgdesc
- name: get the first tag that isn''t "latest"
  debug: msg="{{imgdesc.single_result.imageTags|reject('equalto', 'latest')|first}}"
- name: when was this image pushed?
  debug: msg="{{imgdesc.single_result.imagePushedAt}}"
'''

RETURN = '''
# for list_repositories
repo_by_name:
    description: repositories in a given region
    returned: for mode=list_repositories
    type: dict of repositories, keyed by repository name
    example:
        {
           "numbers/tommy": {
                "createdAt": "2017-02-02T13:21:35-08:00",
                "registryId": "8675309",
                "repositoryArn": "arn:aws:ecr:us-west-2:8675309:repository/numbers/tommy",
                "repositoryName": "numbers/tommy",
                "repositoryUri": "8675309.dkr.ecr.us-west-2.amazonaws.com/numbers/tommy"
            },
            "numbers/jenny": {
                "createdAt": "2016-12-22T15:00:34-08:00",
                "registryId": "8675309",
                "repositoryArn": "arn:aws:ecr:us-west-2:8675309:repository/numbers/jenny",
                "repositoryName": "numbers/jenny",
                "repositoryUri": "8675309.dkr.ecr.us-west-2.amazonaws.com/numbers/jenny"
            }
        }


image_by_digest:
    description: image digests/tags in a dict, keyed by digest (which are sha256 hashes)
    returned: for mode=list_images
    type: dict of images, keyed by digest
    example:
        {
            "sha256:3c10075da9e50f8b89b8b05b287cdd4e920322b6e8876ede6088d0c25e8ad442": {
                "imageDigest": "sha256:3c10075da9e50f8b89b8b05b287cdd4e920322b6e8876ede6088d0c25e8ad442",
                "imageTag": "0.0.2"
            },
            "sha256:c31525b2bbd1bfe6a89811cba8a799edab4ab98038fa4a861da56f5b1de31142": {
                "imageDigest": "sha256:c31525b2bbd1bfe6a89811cba8a799edab4ab98038fa4a861da56f5b1de31142",
                "imageTag": "0.0.3"
            }
        }
valid_image_ids:
    description: image digests/tags in a dict, keyed by tag, excluding any that don't appear to be a version number
    returned: for mode=list_images
    type: dict of images, keyed by tag
    example:
        {
            "0.0.2": {
                "imageDigest": "sha256:3c10075da9e50f8b89b8b05b287cdd4e920322b6e8876ede6088d0c25e8ad4fc",
                "imageTag": "0.0.2"
            },
            "0.0.3": {
                "imageDigest": "sha256:c31525b2bbd1bfe6a89811cba8a799edab4ab98038fa4a861da56f5b1de3113f",
                "imageTag": "0.0.3"
            }
        }
sorted_by_version:
    description: image digests/tags in a list, sorted by LooseVersion. Handy way to get the most recent version
    returned: for mode=list_images
    type: list of dicts of digests/tags
    example:
        [
            {
                "imageDigest": "sha256:3c10075da9e50f8b89b8b05b287cdd4e920322b6e8876ede6088d0c25e8ad442",
                "imageTag": "0.0.2"
            },
            {
                "imageDigest": "sha256:c31525b2bbd1bfe6a89811cba8a799edab4ab98038fa4a861da56f5b1de31142",
                "imageTag": "0.0.3"
            }
        ]


image_details_by_digest:
    description: image details (creation time, size)
    returned: for mode=describe_images
    type: dict of image details, keyed by digest (sha256)
    example:
        {
            "sha256:c31525b2bbd1bfe6a89811cba8a799edab4ab98038fa4a861da56f5b1de31142": {
                "imageDigest": "sha256:c31525b2bbd1bfe6a89811cba8a799edab4ab98038fa4a861da56f5b1de31142",
                "imagePushedAt": "2017-03-13T17:32:34-07:00",
                "imageSizeInBytes": 439173000,
                "imageTags": [
                    "latest",
                    "0.0.3"
                ],
                "registryId": "8675309",
                "repositoryName": "numbers/jenny"
            }
        }


image_details_by_timestamp:
    description: image details (creation time, size), sorted (ascending) by creation time
    returned: for mode=describe_images
    type: list of image details
    example:
        [
            {
                "imageDigest": "sha256:c31525b2bbd1bfe6a89811cba8a799edab4ab98038fa4a861da56f5b1de31142",
                "imagePushedAt": "2017-03-13T17:32:34-07:00",
                "imageSizeInBytes": 439173000,
                "imageTags": [
                    "latest",
                    "0.0.3"
                ],
                "registryId": "8675309",
                "repositoryName": "numbers/jenny"
            }
        ]
single_result:
    description: >
        If only one image was returned (no matter how many were requested), image details for that one image.
        This is a convenience so Ansible plays don't need to check for number of results when one is assumed.
    returned: for mode=describe_images
    type: image details
    example:
        {
            "imageDigest": "sha256:c31525b2bbd1bfe6a89811cba8a799edab4ab98038fa4a861da56f5b1de31142",
            "imagePushedAt": "2017-03-13T17:32:34-07:00",
            "imageSizeInBytes": 439173000,
            "imageTags": [
                "latest",
                "0.0.3"
            ],
            "registryId": "8675309",
            "repositoryName": "numbers/jenny"
        }

'''

import re
from distutils.version import LooseVersion

from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.aws as awsutils

try:
    import boto3

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def list_repositories(ecr):
    ret = {}
    res = ecr.describe_repositories()
    repos = res.get('repositories')

    ret['repo_by_name'] = {v['repositoryName']:v for v in repos}
    return ret

def list_images(ecr, reponame):
    ret = {}
    res = ecr.list_images(repositoryName=reponame)

    # "valid" removes any nonnumbers. This is to remove "latest" but will strip others out.
    ret['image_by_digest'] = {x['imageDigest']:x for x in res.get('imageIds', [])}
    ret['valid_image_ids'] = {x['imageTag']:x for x in res.get('imageIds', []) if re.match(r'^[\.0-9]+$', x.get('imageTag', ''))}
    ret['image_sorted_by_version'] = sorted(ret['valid_image_ids'].values(), key=lambda k: LooseVersion(k['imageTag']))

    return ret

def describe_images(ecr, reponame, image_list=[]):
    ret = {'single_result': None}
    res = ecr.describe_images(
        repositoryName=reponame,
        imageIds=image_list)

    # can't return a list sorted by tag, because there can be > 1 tag for a given image.
    images = res.get('imageDetails', [])
    # not calling this 'image_by_digest' because it's confusing to explain return values
    # that are substantially different depending on mode called.
    ret['image_details_by_digest'] = {v['imageDigest']:v for v in images}
    ret['image_details_by_timestamp'] = sorted(images, key=lambda k: k['imagePushedAt'])

    # if there's only one, make it easy to retrieve
    if len(images) == 1:
        ret['single_result'] = images[0]
    return ret


def main():
    argument_spec = awsutils.common_argument_spec()
    argument_spec.update(dict(
        mode=dict(default='list_repositories', choices=['list_repositories', 'list_images', 'describe_images']),
        repository_name=dict(required=False),
        image_list=dict(required=False, type='list')
    ))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_if=[
                               ['mode', 'list_images', ['repository_name']],
                               ['mode', 'describe_images', ['repository_name', 'image_list']],
                           ])

    awsargs = awsutils.get_module_aws_arguments(module)
    ecr = awsutils.connection(conn_type='client', resource='ecr', **awsargs)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    mode = module.params['mode']

    ret = {}
    if mode == 'list_repositories':
        result = list_repositories(ecr)
        ret.update(result)
        ret['changed'] = ret.get('changed') or result.get('changed') # be pessimistic
        ret['failed'] = ret.get('failed') or result.get('failed') # be pessimistic
    elif mode == 'list_images':
        result = list_images(ecr, module.params['repository_name'])
        ret.update(result)
        ret['changed'] = ret.get('changed') or result.get('changed') # be pessimistic
        ret['failed'] = ret.get('failed') or result.get('failed') # be pessimistic
    elif mode == 'describe_images':
        result = describe_images(ecr, module.params['repository_name'], module.params['image_list'])
        ret.update(result)
        ret['changed'] = ret.get('changed') or result.get('changed') # be pessimistic
        ret['failed'] = ret.get('failed') or result.get('failed') # be pessimistic

    if result.get('failed'):
        module.fail_json(**ret)
    else:
        module.exit_json(**ret)


if __name__ == '__main__':
    main()
