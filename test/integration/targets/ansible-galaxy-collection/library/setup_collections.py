#!/usr/bin/python

# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: setup_collections
short_description: Set up test collections based on the input
description:
- Builds and publishes a whole bunch of collections used for testing in bulk.
options:
  server:
    description:
    - The Galaxy server to upload the collections to.
    required: yes
    type: str
  token:
    description:
    - The token used to authenticate with the Galaxy server.
    required: yes
    type: str
  collections:
    description:
    - A list of collection details to use for the build.
    required: yes
    type: list
    elements: dict
    options:
      namespace:
        description:
        - The namespace of the collection.
        required: yes
        type: str
      name:
        description:
        - The name of the collection.
        required: yes
        type: str
      version:
        description:
        - The version of the collection.
        type: str
        default: '1.0.0'
      dependencies:
        description:
        - The dependencies of the collection.
        type: dict
        default: '{}'
author:
- Jordan Borean (@jborean93)
'''

EXAMPLES = '''
- name: Build test collections
  setup_collections:
    path: ~/ansible/collections/ansible_collections
    collections:
    - namespace: namespace1
      name: name1
      version: 0.0.1
    - namespace: namespace1
      name: name1
      version: 0.0.2
'''

RETURN = '''
#
'''

import os
import tempfile
import yaml

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes


def run_module():
    module_args = dict(
        server=dict(type='str', required=True),
        token=dict(type='str', required=True),
        collections=dict(
            type='list',
            elements='dict',
            required=True,
            options=dict(
                namespace=dict(type='str', required=True),
                name=dict(type='str', required=True),
                version=dict(type='str', default='1.0.0'),
                dependencies=dict(type='dict', default={}),
                use_symlink=dict(type='bool', default=False),
            ),
        ),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    result = dict(changed=True)

    for idx, collection in enumerate(module.params['collections']):
        collection_dir = os.path.join(module.tmpdir, "%s-%s-%s" % (collection['namespace'], collection['name'],
                                                                   collection['version']))
        b_collection_dir = to_bytes(collection_dir, errors='surrogate_or_strict')
        os.mkdir(b_collection_dir)

        with open(os.path.join(b_collection_dir, b'README.md'), mode='wb') as fd:
            fd.write(b"Collection readme")

        galaxy_meta = {
            'namespace': collection['namespace'],
            'name': collection['name'],
            'version': collection['version'],
            'readme': 'README.md',
            'authors': ['Collection author <name@email.com'],
            'dependencies': collection['dependencies'],
        }
        with open(os.path.join(b_collection_dir, b'galaxy.yml'), mode='wb') as fd:
            fd.write(to_bytes(yaml.safe_dump(galaxy_meta), errors='surrogate_or_strict'))

        with tempfile.NamedTemporaryFile(mode='wb') as temp_fd:
            temp_fd.write(b"data")

            if collection['use_symlink']:
                os.mkdir(os.path.join(b_collection_dir, b'docs'))
                os.mkdir(os.path.join(b_collection_dir, b'plugins'))
                b_target_file = b'RE\xc3\x85DM\xc3\x88.md'
                with open(os.path.join(b_collection_dir, b_target_file), mode='wb') as fd:
                    fd.write(b'data')

                os.symlink(b_target_file, os.path.join(b_collection_dir, b_target_file + b'-link'))
                os.symlink(temp_fd.name, os.path.join(b_collection_dir, b_target_file + b'-outside-link'))
                os.symlink(os.path.join(b'..', b_target_file), os.path.join(b_collection_dir, b'docs', b_target_file))
                os.symlink(os.path.join(b_collection_dir, b_target_file),
                           os.path.join(b_collection_dir, b'plugins', b_target_file))
                os.symlink(b'docs', os.path.join(b_collection_dir, b'docs-link'))

            release_filename = '%s-%s-%s.tar.gz' % (collection['namespace'], collection['name'], collection['version'])
            collection_path = os.path.join(collection_dir, release_filename)
            module.run_command(['ansible-galaxy', 'collection', 'build'], cwd=collection_dir)

        # To save on time, skip the import wait until the last collection is being uploaded.
        publish_args = ['ansible-galaxy', 'collection', 'publish', collection_path, '--server',
                        module.params['server'], '--token', module.params['token']]
        if idx != (len(module.params['collections']) - 1):
            publish_args.append('--no-wait')
        module.run_command(publish_args)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
