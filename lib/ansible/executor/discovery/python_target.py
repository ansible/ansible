# Copyright: (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# FUTURE: this could be swapped out for our bundled version of distro to move more complete platform
# logic to the targets, so long as we maintain Py2.6 compat and don't need to do any kind of script assembly

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import platform
import io
import os


def read_utf8_file(path, encoding='utf-8'):
    if not os.access(path, os.R_OK):
        return None
    with io.open(path, 'r', encoding=encoding) as fd:
        content = fd.read()

    return content


def get_platform_info():
    result = dict(platform_dist_result=[])

    if hasattr(platform, 'dist'):
        result['platform_dist_result'] = platform.dist()

    osrelease_content = read_utf8_file('/etc/os-release')
    # try to fall back to /usr/lib/os-release
    if not osrelease_content:
        osrelease_content = read_utf8_file('/usr/lib/os-release')

    result['osrelease_content'] = osrelease_content

    return result


def main():
    info = get_platform_info()

    print(json.dumps(info))


if __name__ == '__main__':
    main()
