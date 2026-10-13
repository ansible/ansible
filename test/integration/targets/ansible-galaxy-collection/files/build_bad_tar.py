#!/usr/bin/env python

# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import tarfile
from ansible.module_utils.common.file import S_IRWXU_RXG_RXO

manifest = {
    'collection_info': {
        'namespace': 'suspicious',
        'name': 'test',
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


def calculate_target_filename(symlink_path, linkname):
    """The target is relative to the symlink."""
    symlink_dir = os.path.dirname(symlink_path)
    if symlink_dir:
        # tarfile will extract the linkname as {{ symlink_dir }}/{{ linkname }}, even if linkname is an absolute path
        return "/".join([symlink_dir, linkname])
    return linkname


def add_file(tar_file, filename, b_content, update_files=True, symlink_linkname=None):
    tar_info = tarfile.TarInfo(filename)
    if symlink_linkname is not None:
        add_file(tar_file, calculate_target_filename(filename, symlink_linkname), b"", update_files=False)
        tar_info.type = tarfile.SYMTYPE
        tar_info.linkname = symlink_linkname
    else:
        tar_info.size = len(b_content)
    tar_info.mode = S_IRWXU_RXG_RXO
    tar_file.addfile(tarinfo=tar_info, fileobj=io.BytesIO(b_content))

    if update_files:
        sha256 = hashlib.sha256()
        sha256.update(b_content)

        files['files'].append({
            'name': filename,
            'ftype': 'file',
            'chksum_type': 'sha256',
            'chksum_sha256': sha256.hexdigest() if symlink_linkname is None else None,
            'format': 1
        })


def add_dir(tar_file, dir_name, symlink_linkname=None, update_files=True):
    if symlink_linkname:
        add_dir(tar_file, symlink_linkname, update_files=False)

    tar_info = tarfile.TarInfo(dir_name)

    if symlink_linkname is None:
        tar_info.type = tarfile.DIRTYPE
    else:
        tar_info.type = tarfile.SYMTYPE
        tar_info.linkname = symlink_linkname

    tar_info.mode = 0o777
    tar_file.addfile(tar_info)

    if not update_files:
        return

    files['files'].append({
        'name': dir_name,
        'ftype': 'dir',
        'chksum_type': 'sha256',
        'chksum_sha256': None,
        'format': 1,
    })


parser = argparse.ArgumentParser(description="Test suspiciously crafted collection artifacts.")
parser.add_argument("dest", help="The destination directory for the collection artifact.")

mutually_exclusive_group = parser.add_mutually_exclusive_group()
mutually_exclusive_group.add_argument(
    "--file", help="A file to add to the collection artifact.",
)
mutually_exclusive_group.add_argument(
    "--dir", help="A directory to add to the collection artifact.",
)
mutually_exclusive_group.add_argument(
    "--symlink-linkname", help="Add a symlink linkname to the collection artifact.",
)
parser.add_argument(
    "--symlink", help="The name of the symlink to use with --symlink-linkname. Defaults to 'symlink'.",
)


args = parser.parse_args()

collection_tar = os.path.join(args.dest, 'suspicious-test-1.0.0.tar.gz')
with tarfile.open(collection_tar, mode='w:gz') as tar_file:
    filename = args.file
    dirname = args.dir

    if args.symlink and not args.symlink_linkname:
        parser.error("--symlink and --symlink-linkname must be used together")

    if args.symlink_linkname:
        if args.symlink_linkname.endswith(os.path.sep):
            dirname = args.symlink or "symlink"
        else:
            filename = args.symlink or "symlink"

    if dirname:
        add_dir(tar_file, dirname, symlink_linkname=args.symlink_linkname)
    elif filename:
        add_file(tar_file, filename, b"#!/usr/bin/env bash\necho \"you got pwned\"", symlink_linkname=args.symlink_linkname)

    b_files = json.dumps(files).encode('utf-8')
    b_files_hash = hashlib.sha256()
    b_files_hash.update(b_files)
    manifest['file_manifest_file']['chksum_sha256'] = b_files_hash.hexdigest()
    add_file(tar_file, 'FILES.json', b_files)
    add_file(tar_file, 'MANIFEST.json', json.dumps(manifest).encode('utf-8'))
