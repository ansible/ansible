# -*- coding: utf-8 -*-
# Copyright:
#   (c) 2018 Ansible Project
# License: GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division)

__metaclass__ = type

from units.compat.mock import MagicMock
from ansible.module_utils.basic import AnsibleModule
from ansible.modules.files import file
from posix import stat_result
import pytest
import time


test = [  # Access time and modification time are not preserved
    {'path': '/tmp/test',
     'follow': True,
     'timestamps': dict(access_time='now', access_time_format='%Y%m%d%H%M.%S', modification_time='now',
                        modification_time_format='%Y%m%d%H%M.%S')},
    # Access time is preserved
    {'path': '/tmp/test',
     'follow': True,
     'timestamps': dict(access_time='preserve', access_time_format='%Y%m%d%H%M.%S', modification_time='now',
                        modification_time_format='%Y%m%d%H%M.%S')},
    # Modification time is preserved
    {'path': '/tmp/test',
     'follow': True,
     'timestamps': dict(access_time='now', access_time_format='%Y%m%d%H%M.%S', modification_time='preserve',
                        modification_time_format='%Y%m%d%H%M.%S')}]

# Use current time to determine current access and modification time
current_time = time.time()
# Use prev_time to determine previous access and modification times of the file
prev_time = time.time() - 1
# Need stat_result object in order to use st_mtime and st_atime methods in update_timestamp_for_file function
stat_results = stat_result((0, 0, 0, 0, 0, 0, 0, prev_time, prev_time, prev_time))
# Test Results
file_exist = {'changed': True,
              'dest': '/tmp/test',
              'diff':
                  {'after': dict(atime=current_time, mtime=current_time, path='/tmp/test', state='touch'),
                   'before': dict(atime=prev_time, mtime=prev_time, path='/tmp/test', state='file')
                   }
              }

atime_preserve = {'changed': True,
                  'dest': '/tmp/test',
                  'diff':
                      {'after': dict(mtime=current_time, path='/tmp/test', state='touch'),
                       'before': dict(mtime=prev_time, path='/tmp/test', state='file')
                       }
                  }

mtime_preserve = {'changed': True,
                  'dest': '/tmp/test',
                  'diff':
                      {'after': dict(atime=current_time, path='/tmp/test', state='touch'),
                       'before': dict(atime=prev_time, path='/tmp/test', state='file')
                       }
                  }


@pytest.mark.parametrize('path, follow, timestamps', [(test[0]['path'], test[0]['follow'], test[0]['timestamps'])])
def test_execute_touch_check_mode_is_set_file_not_exist(path, follow, timestamps, mocker):
    file.module = MagicMock()
    file.module.check_mode = True
    mocker.patch('ansible.modules.files.file.get_state', return_value='absent')
    assert file.execute_touch(path, follow, timestamps) == {'changed': True, 'dest': '/tmp/test'}


@pytest.mark.parametrize('path, follow, timestamps', [(test[0]['path'], test[0]['follow'], test[0]['timestamps'])])
def test_execute_touch_check_mode_is_set_file_exists(path, follow, timestamps, mocker):
    file.module = MagicMock()
    file.module.check_mode = True
    mocker.patch('ansible.modules.files.file.get_state', return_value='file')
    mocker.patch('time.time', return_value=current_time)
    mocker.patch('os.stat', return_value=stat_results)
    assert file.execute_touch(path, follow, timestamps) == file_exist


@pytest.mark.parametrize('path, follow, timestamps', [(test[0]['path'], test[0]['follow'], test[0]['timestamps'])])
def test_execute_touch_check_mode_is_set_file_exists_atime_and_mtime_preserve(path, follow, timestamps, mocker):
    file.module = MagicMock()
    file.module.check_mode = True
    file.module.params = {'access_time': 'preserve', 'modification_time': 'preserve'}
    mocker.patch('ansible.modules.files.file.get_state', return_value='file')
    assert file.execute_touch(path, follow, timestamps) == {'changed': False, 'dest': '/tmp/test'}


@pytest.mark.parametrize('path, follow, timestamps', [(test[1]['path'], test[1]['follow'], test[1]['timestamps'])])
def test_execute_touch_check_mode_is_set_file_exists_atime_is_preserve(path, follow, timestamps, mocker):
    file.module = MagicMock()
    file.module.check_mode = True
    file.module.params = {'access_time': 'preserve', 'modification_time': None}
    mocker.patch('ansible.modules.files.file.get_state', return_value='file')
    mocker.patch('time.time', return_value=current_time)
    mocker.patch('os.stat', return_value=stat_results)
    assert file.execute_touch(path, follow, timestamps) == atime_preserve


@pytest.mark.parametrize('path, follow, timestamps', [(test[2]['path'], test[2]['follow'], test[2]['timestamps'])])
def test_execute_touch_check_mode_is_set_file_exists_mtime_is_preserve(path, follow, timestamps, mocker):
    file.module = MagicMock()
    file.module.check_mode = True
    file.module.params = {'access_time': None, 'modification_time': 'preserve'}
    mocker.patch('ansible.modules.files.file.get_state', return_value='file')
    mocker.patch('time.time', return_value=current_time)
    mocker.patch('os.stat', return_value=stat_results)
    assert file.execute_touch(path, follow, timestamps) == mtime_preserve
