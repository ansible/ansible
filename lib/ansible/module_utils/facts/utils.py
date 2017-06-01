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
        except:
            # ignore errors as some jails/containers might have readable permissions but not allow reads to proc
            # done in 2 blocks for 2.4 compat
            pass
    return data


def get_file_lines(path):
    '''get list of lines from file'''
    data = get_file_content(path)
    if data:
        ret = data.splitlines()
    else:
        ret = []
    return ret


def get_mount_size(mountpoint):
    size_total = None
    size_available = None
    try:
        statvfs_result = os.statvfs(mountpoint)
        size_total = statvfs_result.f_frsize * statvfs_result.f_blocks
        size_available = statvfs_result.f_frsize * (statvfs_result.f_bavail)
    except OSError:
        pass

    return size_total, size_available
