#!/usr/bin/env python

import sys


def main():
    skip = set([
        'test/integration/targets/template/files/foo.dos.txt',
        'test/integration/targets/win_regmerge/templates/win_line_ending.j2',
        'test/integration/targets/win_template/files/foo.dos.txt',
        'test/integration/targets/win_blockinfile/files/default_block_only_crlf.txt',
        'test/integration/targets/win_blockinfile/files/file_with_lines.txt',
        'test/integration/targets/win_blockinfile/files/file_with_lines_after.txt',
        'test/integration/targets/win_blockinfile/files/file_with_lines_before.txt',
        'test/integration/targets/win_blockinfile/files/file_with_lines_bof.txt',
        'test/integration/targets/win_blockinfile/files/file_with_lines_custom_marker.txt',
        'test/integration/targets/win_blockinfile/files/file_with_lines_eof.txt',
        'test/integration/targets/win_blockinfile/files/file_with_lines_inverted_marker.txt',
        'test/integration/targets/win_blockinfile/files/no_trailing_newline.txt',
        'test/integration/targets/win_blockinfile/files/no_trailing_newline_bof.txt',
        'test/integration/targets/win_blockinfile/files/utf_16_after.txt.txt',
        'test/integration/targets/win_blockinfile/files/utf_16_orig.txt.txt',
        'test/integration/targets/win_module_utils/library/legacy_only_new_way_win_line_ending.ps1',
        'test/integration/targets/win_module_utils/library/legacy_only_old_way_win_line_ending.ps1',
        'test/units/modules/network/routeros/fixtures/system_package_print',
    ])

    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        if path in skip:
            continue

        with open(path, 'rb') as path_fd:
            contents = path_fd.read()

        if b'\r' in contents:
            print('%s: use "\\n" for line endings instead of "\\r\\n"' % path)


if __name__ == '__main__':
    main()
