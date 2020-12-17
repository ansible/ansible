#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys
import subprocess


def main():
    paths = sys.argv[1:] or sys.stdin.read().splitlines()

    allowed_extensions = ('.yml', '.yaml')
    config_path = 'changelogs/config.yaml'

    # config must be detected independent of the file list since the file list only contains files under test (changed)
    has_config = os.path.exists(config_path)
    paths_to_check = []
    for path in paths:
        if path == config_path:
            continue

        if path.startswith('changelogs/fragments/.'):
            if path in ('changelogs/fragments/.keep', 'changelogs/fragments/.gitkeep'):
                continue

            print('%s:%d:%d: file must not be a dotfile' % (path, 0, 0))
            continue

        ext = os.path.splitext(path)[1]

        if ext not in allowed_extensions:
            print('%s:%d:%d: extension must be one of: %s' % (path, 0, 0, ', '.join(allowed_extensions)))

        paths_to_check.append(path)

    if not has_config:
        print('changelogs/config.yaml:0:0: config file does not exist')
        return

    if not paths_to_check:
        return

    cmd = [sys.executable, '-m', 'antsibull_changelog', 'lint'] + paths_to_check
    subprocess.call(cmd)  # ignore the return code, rely on the output instead


if __name__ == '__main__':
    main()
