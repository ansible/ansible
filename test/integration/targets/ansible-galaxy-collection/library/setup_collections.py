#!/usr/bin/python

# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

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

import datetime
import os
import subprocess
import tarfile
import tempfile
import yaml

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_bytes
from functools import partial
from multiprocessing import dummy as threading
from multiprocessing import TimeoutError


COLLECTIONS_BUILD_AND_PUBLISH_TIMEOUT = 180


def publish_collection(module, collection):
    namespace = collection['namespace']
    name = collection['name']
    version = collection['version']
    dependencies = collection['dependencies']
    use_symlink = collection['use_symlink']

    result = {}
    collection_dir = os.path.join(module.tmpdir, "%s-%s-%s" % (namespace, name, version))
    b_collection_dir = to_bytes(collection_dir, errors='surrogate_or_strict')
    os.mkdir(b_collection_dir)
    os.mkdir(os.path.join(b_collection_dir, b'meta'))

    with open(os.path.join(b_collection_dir, b'README.md'), mode='wb') as fd:
        fd.write(b"Collection readme")

    galaxy_meta = {
        'namespace': namespace,
        'name': name,
        'version': version,
        'readme': 'README.md',
        'authors': ['Collection author <name@email.com'],
        'dependencies': dependencies,
        'license': ['GPL-3.0-or-later'],
        'repository': 'https://ansible.com/',
    }
    with open(os.path.join(b_collection_dir, b'galaxy.yml'), mode='wb') as fd:
        fd.write(to_bytes(yaml.safe_dump(galaxy_meta), errors='surrogate_or_strict'))
    with open(os.path.join(b_collection_dir, b'meta/runtime.yml'), mode='wb') as fd:
        fd.write(b'requires_ansible: ">=1.0.0"')

    with tempfile.NamedTemporaryFile(mode='wb') as temp_fd:
        temp_fd.write(b"data")

        if use_symlink:
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

        release_filename = '%s-%s-%s.tar.gz' % (namespace, name, version)
        collection_path = os.path.join(collection_dir, release_filename)
        rc, stdout, stderr = module.run_command(['ansible-galaxy', 'collection', 'build'], cwd=collection_dir)
        result['build'] = {
            'rc': rc,
            'stdout': stdout,
            'stderr': stderr,
        }

        if module.params['signature_dir'] is not None:
            # To test user-provided signatures, we need to sign the MANIFEST.json before publishing

            # Extract the tarfile to sign the MANIFEST.json
            with tarfile.open(collection_path, mode='r') as collection_tar:
                # deprecated: description='extractall fallback without filter' python_version='3.11'
                # Replace 'tar_filter' with 'data_filter' and 'filter=tar' with 'filter=data' once Python 3.12 is minimum requirement.
                if hasattr(tarfile, 'tar_filter'):
                    collection_tar.extractall(path=os.path.join(collection_dir, '%s-%s-%s' % (namespace, name, version)), filter='tar')
                else:
                    collection_tar.extractall(path=os.path.join(collection_dir, '%s-%s-%s' % (namespace, name, version)))

            manifest_path = os.path.join(collection_dir, '%s-%s-%s' % (namespace, name, version), 'MANIFEST.json')
            signature_path = os.path.join(module.params['signature_dir'], '%s-%s-%s-MANIFEST.json.asc' % (namespace, name, version))
            sign_manifest(signature_path, manifest_path, module, result)

            # Create the tarfile containing the signed MANIFEST.json
            with tarfile.open(collection_path, "w:gz") as tar:
                tar.add(os.path.join(collection_dir, '%s-%s-%s' % (namespace, name, version)), arcname=os.path.sep)

    publish_args = ['ansible-galaxy', 'collection', 'publish', collection_path, '--server', module.params['server']]
    if module.params['token']:
        publish_args.extend(['--token', module.params['token']])

    rc, stdout, stderr = module.run_command(publish_args)
    result['publish'] = {
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr,
    }

    return result


def sign_manifest(signature_path, manifest_path, module, collection_setup_result):
    collection_setup_result['gpg_detach_sign'] = {'signature_path': signature_path}

    status_fd_read, status_fd_write = os.pipe()
    gpg_cmd = [
        "gpg",
        "--batch",
        "--pinentry-mode",
        "loopback",
        "--yes",
        "--homedir",
        module.params['signature_dir'],
        "--detach-sign",
        "--armor",
        "--output",
        signature_path,
        manifest_path,
    ]
    try:
        p = subprocess.Popen(
            gpg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            pass_fds=(status_fd_write,),
            encoding='utf8',
        )
    except (FileNotFoundError, subprocess.SubprocessError) as err:
        collection_setup_result['gpg_detach_sign']['error'] = "Failed during GnuPG verification with command '{gpg_cmd}': {err}".format(
            gpg_cmd=gpg_cmd, err=err
        )
    else:
        stdout, stderr = p.communicate()
        collection_setup_result['gpg_detach_sign']['stdout'] = stdout
        if stderr:
            error = "Failed during GnuPG verification with command '{gpg_cmd}':\n{stderr}".format(gpg_cmd=gpg_cmd, stderr=stderr)
            collection_setup_result['gpg_detach_sign']['error'] = error
    finally:
        os.close(status_fd_write)


def run_module():
    module_args = dict(
        server=dict(type='str', required=True),
        token=dict(type='str'),
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
        signature_dir=dict(type='path', default=None),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    start = datetime.datetime.now()
    result = dict(changed=True, results=[], start=str(start))

    pool = threading.Pool(4)
    publish_func = partial(publish_collection, module)
    try:
        result['results'] = pool.map_async(
            publish_func, module.params['collections'],
        ).get(timeout=COLLECTIONS_BUILD_AND_PUBLISH_TIMEOUT)
    except TimeoutError as timeout_err:
        module.fail_json(
            'Timed out waiting for collections to be provisioned.',
        )

    failed = bool(sum(
        r['build']['rc'] + r['publish']['rc'] for r in result['results']
    ))

    end = datetime.datetime.now()
    delta = end - start
    module.exit_json(failed=failed, end=str(end), delta=str(delta), **result)


def main():
    run_module()


if __name__ == '__main__':
    main()
