#!/usr/bin/env python

# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import tarfile

from ansible.module_utils.common.file import S_IRWXU_RXG_RXO

manifest = {
    'collection_info': {
        'namespace': 'ns',
        'name': '../../../../outside',
        'version': '1.0.0',
        'dependencies': {},
    },
    'file_manifest_file': {
        'name': 'FILES.json',
        'ftype': 'file',
        'chksum_type': 'sha256',
        'chksum_sha256': None,
        'format': 1
    },
    'format': 1,
}

files = {
    'files': [
        {
            'name': '.',
            'ftype': 'dir',
            'chksum_type': None,
            'chksum_sha256': None,
            'format': 1,
        },
    ],
    'format': 1,
}


def add_file(tar_file, filename, b_content):
    tar_info = tarfile.TarInfo(filename)
    tar_info.size = len(b_content)
    tar_info.mode = S_IRWXU_RXG_RXO
    tar_file.addfile(tarinfo=tar_info, fileobj=io.BytesIO(b_content))


collection_tar = os.path.join(sys.argv[1], 'badname-test-1.0.0.tar.gz')
with tarfile.open(collection_tar, mode='w:gz') as tar_file:
    b_files = json.dumps(files).encode('utf-8')
    b_files_hash = hashlib.sha256()
    b_files_hash.update(b_files)
    manifest['file_manifest_file']['chksum_sha256'] = b_files_hash.hexdigest()

    add_file(tar_file, 'MANIFEST.json', json.dumps(manifest).encode('utf-8'))
    add_file(tar_file, 'FILES.json', b_files)
