# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os


def get_file_content(path, default=None, strip=True):
    data = default
    if os.path.exists(path) and os.access(path, os.R_OK):
        try:
            try:
                datafile = open(path)
                data = datafile.read()
                if strip:
                    data = data.strip()
                if len(data) == 0:
                    data = default
            finally:
                datafile.close()
        except Exception:
            # ignore errors as some jails/containers might have readable permissions but not allow reads to proc
            # done in 2 blocks for 2.4 compat
            pass
    return data


def get_file_lines(path, strip=True, line_sep=None):
    '''get list of lines from file'''
    data = get_file_content(path, strip=strip)
    if data:
        if line_sep is None:
            ret = data.splitlines()
        else:
            if len(line_sep) == 1:
                ret = data.rstrip(line_sep).split(line_sep)
            else:
                ret = data.split(line_sep)
    else:
        ret = []
    return ret


def get_mount_size(mountpoint):
    mount_size = {}

    try:
        statvfs_result = os.statvfs(mountpoint)
        mount_size['size_total'] = statvfs_result.f_frsize * statvfs_result.f_blocks
        mount_size['size_available'] = statvfs_result.f_frsize * (statvfs_result.f_bavail)

        # Block total/available/used
        mount_size['block_size'] = statvfs_result.f_bsize
        mount_size['block_total'] = statvfs_result.f_blocks
        mount_size['block_available'] = statvfs_result.f_bavail
        mount_size['block_used'] = mount_size['block_total'] - mount_size['block_available']

        # Inode total/available/used
        mount_size['inode_total'] = statvfs_result.f_files
        mount_size['inode_available'] = statvfs_result.f_favail
        mount_size['inode_used'] = mount_size['inode_total'] - mount_size['inode_available']
    except OSError:
        pass

    return mount_size
