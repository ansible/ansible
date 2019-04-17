# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.module_utils.facts.collector import BaseFactCollector


def is_chroot(module=None):

    is_chroot = None

    if os.environ.get('debian_chroot', False):
        is_chroot = True
    else:
        my_root = os.stat('/')
        try:
            # check if my file system is the root one
            proc_root = os.stat('/proc/1/root/.')
            is_chroot = my_root.st_ino != proc_root.st_ino or my_root.st_dev != proc_root.st_dev
        except Exception:
            # I'm not root or no proc, fallback to checking it is inode #2
            fs_root_ino = 2

            if module is not None:
                stat_path = module.get_bin_path('stat')
                if stat_path:
                    cmd = [stat_path, '-f', '--format=%T', '/']
                    rc, out, err = module.run_command(cmd)
                    if 'btrfs' in out:
                        fs_root_ino = 256

            is_chroot = (my_root.st_ino != fs_root_ino)

    return is_chroot


class ChrootFactCollector(BaseFactCollector):
    name = 'chroot'
    _fact_ids = set(['is_chroot'])

    def collect(self, module=None, collected_facts=None):
        return {'is_chroot': is_chroot(module)}
