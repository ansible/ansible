# (c) 2020, Red Hat, Inc. <support@ansible.com>
#
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import atexit
import cProfile
import functools
import os
import pstats
import shutil
import sys
import tempfile
import time


class CProfileDecorator:

    """
    A wraper for functions to add cProfile output.
    Usage:
        @CProfileDecorator()()
        def whatever():
    """

    def __init__(self):
        self._temp = tempfile.mkdtemp()
        atexit.register(self.print_stats)

    def __call__(self, sort='cumtime', cache=False):
        def closure(func):
            name = getattr(func, '__qualname__', func.__name__)
            name_dir = os.path.join(self._temp, name)
            if cache:
                try:
                    os.makedirs(name_dir)
                except OSError as e:
                    if e.errno != 17:
                        raise
                with open(os.path.join(name_dir, 'config'), 'w+') as f:
                    f.write(sort)
            p = cProfile.Profile()

            @functools.wraps(func)
            def do_profile(*args, **kwargs):
                try:
                    p.enable()
                    result = func(*args, **kwargs)
                    p.disable()
                    return result
                finally:
                    if not cache:
                        p.print_stats(sort=sort)
                    else:
                        p.dump_stats(os.path.join(name_dir, str(time.time())))

            return do_profile
        return closure

    def print_stats(self):
        temp_dir = self._temp
        try:
            keys = os.listdir(self._temp)
        except OSError:
            return
        for key in keys:
            key_dir = os.path.join(temp_dir, key)
            files = os.listdir(key_dir)
            _join = os.path.join
            ps = pstats.Stats(
                *(_join(key_dir, d) for d in files if d != 'config'),
                stream=sys.stderr
            )
            with open(_join(key_dir, 'config')) as f:
                sort = f.read()
            print('%s %s' % (key, '*' * (75 - len(key))))
            ps.sort_stats(sort).print_stats()
        try:
            shutil.rmtree(self._temp)
        except Exception:
            pass


cprofile_func = CProfileDecorator()
