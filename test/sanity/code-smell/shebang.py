#!/usr/bin/env python

import os
import stat
import sys


def main():
    allowed = set([
        b'#!/bin/bash -eu',
        b'#!/bin/bash -eux',
        b'#!/bin/bash',
        b'#!/bin/sh',
        b'#!/usr/bin/env bash',
        b'#!/usr/bin/env fish',
        b'#!/usr/bin/env pwsh',
        b'#!/usr/bin/env python',
        b'#!/usr/bin/make -f',
    ])

    module_shebangs = {
        '': b'#!/usr/bin/python',
        '.py': b'#!/usr/bin/python',
        '.ps1': b'#!powershell',
    }

    skip = set([
        'test/integration/targets/win_module_utils/library/legacy_only_new_way_win_line_ending.ps1',
        'test/integration/targets/win_module_utils/library/legacy_only_old_way_win_line_ending.ps1',
    ])

    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        if path in skip:
            continue

        with open(path, 'rb') as path_fd:
            shebang = path_fd.readline().strip()
            mode = os.stat(path).st_mode
            executable = (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) & mode

            if not shebang or not shebang.startswith(b'#!'):
                if executable:
                    print('%s:%d:%d: file without shebang should not be executable' % (path, 0, 0))

                continue

            is_module = False

            if path.startswith('lib/ansible/modules/'):
                is_module = True
            elif path.startswith('lib/') or path.startswith('test/runner/lib/'):
                if executable:
                    print('%s:%d:%d: should not be executable' % (path, 0, 0))

                if shebang:
                    print('%s:%d:%d: should not have a shebang' % (path, 0, 0))

                continue
            elif path.startswith('test/integration/targets/'):
                dirname = os.path.dirname(path)

                if dirname.endswith('/library') or dirname in (
                    # non-standard module library directories
                    'test/integration/targets/module_precedence/lib_no_extension',
                    'test/integration/targets/module_precedence/lib_with_extension',
                ):
                    is_module = True

            if is_module:
                if executable:
                    print('%s:%d:%d: module should not be executable' % (path, 0, 0))

                ext = os.path.splitext(path)[1]
                expected_shebang = module_shebangs.get(ext)
                expected_ext = ' or '.join(['"%s"' % k for k in module_shebangs])

                if expected_shebang:
                    if shebang == expected_shebang:
                        continue

                    print('%s:%d:%d: expected module shebang "%s" but found: %s' % (path, 1, 1, expected_shebang, shebang))
                else:
                    print('%s:%d:%d: expected module extension %s but found: %s' % (path, 0, 0, expected_ext, ext))
            else:
                if shebang not in allowed:
                    print('%s:%d:%d: unexpected non-module shebang: %s' % (path, 1, 1, shebang))


if __name__ == '__main__':
    main()
