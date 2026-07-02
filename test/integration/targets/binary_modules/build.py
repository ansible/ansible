#!/usr/bin/env python
"""
Compile binary modules for this test for access from S3 at:
https://ci-files.testing.ansible.com/test/integration/roles/test_binary_modules/
This avoids a test dependency on go and keeps the binaries out of the git repository.
"""

from __future__ import annotations

import os
import pathlib
import shlex
import subprocess


def main() -> None:
    library = pathlib.Path(__file__).parent / 'library'

    # NOTE: The value of `NAME` must be `ansible_architecture` for the target system, plus any required extension.
    builds = (
        dict(GOOS='linux', GOARCH='amd64', NAME='linux_x86_64'),
        dict(GOOS='linux', GOARCH='arm64', NAME='linux_aarch64'),
        dict(GOOS='windows', GOARCH='amd64', NAME='win32nt_64-bit.exe'),
        dict(GOOS='darwin', GOARCH='amd64', NAME='darwin_x86_64'),
        dict(GOOS='darwin', GOARCH='arm64', NAME='darwin_arm64'),
        dict(GOOS='freebsd', GOARCH='amd64', NAME='freebsd_amd64'),
        dict(GOOS='freebsd', GOARCH='arm64', NAME='freebsd_arm64'),
    )

    for build in builds:
        name = build.pop('NAME')
        cmd = ['go', 'build', '-o', f'helloworld_{name}', 'helloworld.go']
        env = os.environ.copy()
        env.update(build)

        print(f'==> {shlex.join(f"{k}={v}" for k, v in build.items())} {shlex.join(cmd)}')
        subprocess.run(cmd, env=env, cwd=library, check=True, text=True)


if __name__ == '__main__':
    main()
