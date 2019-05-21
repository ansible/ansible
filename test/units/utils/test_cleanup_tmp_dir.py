# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division)
__metaclass__ = type

import os
import pytest
import tempfile

from ansible.utils.path import cleanup_tmp_dir


def raise_error():
    raise OSError


def test_cleanup_tmp_dir():
    tmp = tempfile.mkdtemp()
    cleanup_tmp_dir(tmp)

    # Ensure the tmp file was removed
    assert not os.path.exists(tmp)


def test_cleanup_tmp_dir_nonexistant():
    assert None is cleanup_tmp_dir('nope')


def test_cleanup_tmp_dir_failure(mocker):
    tmp = tempfile.mkdtemp()
    with pytest.raises(Exception):
        mocker.patch('shutil.rmtree', side_effect=raise_error())
        cleanup_tmp_dir(tmp)
