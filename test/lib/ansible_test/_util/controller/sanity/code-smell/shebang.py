"""Check shebangs, execute bits and byte order marks."""
from __future__ import annotations

import os
import re
import stat
import sys


def main():
    """Main entry point."""
    standard_shebangs = set([
        b'#!/bin/bash -eu',
        b'#!/bin/bash -eux',
        b'#!/bin/sh',
        b'#!/usr/bin/env bash',
        b'#!/usr/bin/env fish',
        b'#!/usr/bin/env pwsh',
        b'#!/usr/bin/env python',
        b'#!/usr/bin/make -f',
    ])

    integration_shebangs = set([
        b'#!/bin/sh',
        b'#!/usr/bin/env bash',
        b'#!/usr/bin/env python',
    ])

    module_shebangs = {
        '': b'#!/usr/bin/python',
        '.py': b'#!/usr/bin/python',
        '.ps1': b'#!powershell',
    }

    # see https://unicode.org/faq/utf_bom.html#bom1
    byte_order_marks = (
        (b'\x00\x00\xFE\xFF', 'UTF-32 (BE)'),
        (b'\xFF\xFE\x00\x00', 'UTF-32 (LE)'),
        (b'\xFE\xFF', 'UTF-16 (BE)'),
        (b'\xFF\xFE', 'UTF-16 (LE)'),
        (b'\xEF\xBB\xBF', 'UTF-8'),
    )

    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        with open(path, 'rb') as path_fd:
            shebang = path_fd.readline().strip()
            mode = os.stat(path).st_mode
            executable = (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) & mode

            if not shebang or not shebang.startswith(b'#!'):
                if executable:
                    print('%s:%d:%d: file without shebang should not be executable' % (path, 0, 0))

                for mark, name in byte_order_marks:
                    if shebang.startswith(mark):
                        print('%s:%d:%d: file starts with a %s byte order mark' % (path, 0, 0, name))
                        break

                continue

            is_module = False
            is_integration = False
            is_role_file = False

            dirname = os.path.dirname(path)

            if path.startswith('lib/ansible/modules/'):
                is_module = True
            elif re.search('^test/support/[^/]+/plugins/modules/', path):
                is_module = True
            elif re.search('^test/support/[^/]+/collections/ansible_collections/[^/]+/[^/]+/plugins/modules/', path):
                is_module = True
            elif path == 'test/lib/ansible_test/_util/target/cli/ansible_test_cli_stub.py':
                pass  # ansible-test entry point must be executable and have a shebang
            elif re.search(r'^lib/ansible/cli/[^/]+\.py', path):
                pass  # cli entry points must be executable and have a shebang
            elif path.startswith('examples/'):
                continue  # examples trigger some false positives due to location
            elif path.startswith('lib/') or path.startswith('test/lib/'):
                if executable:
                    print('%s:%d:%d: should not be executable' % (path, 0, 0))

                if shebang:
                    print('%s:%d:%d: should not have a shebang' % (path, 0, 0))

                continue
            elif re.search('^roles/[^/]+/(?:files|templates)/', path):
                is_role_file = True
            elif re.search('^tests/integration/targets/[^/]+/(?:files|templates)/', path):
                is_role_file = True
            elif path.startswith('test/integration/targets/') or path.startswith('tests/integration/targets/'):
                is_integration = True

                if dirname.endswith('/library') or '/plugins/modules' in dirname or dirname in (
                        # non-standard module library directories
                        'test/integration/targets/module_precedence/lib_no_extension',
                        'test/integration/targets/module_precedence/lib_with_extension',
                ):
                    is_module = True
            elif path.startswith('plugins/modules/'):
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
            elif is_role_file:
                continue
            else:
                if is_integration:
                    allowed = integration_shebangs
                else:
                    allowed = standard_shebangs

                if shebang not in allowed:
                    print('%s:%d:%d: unexpected non-module shebang: %s' % (path, 1, 1, shebang))


if __name__ == '__main__':
    main()
