# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os
import tempfile

from ansible.utils.path import cleanup_tmp_file


def test_cleanup_tmp_file_file():
    tmp_fd, tmp = tempfile.mkstemp()
    cleanup_tmp_file(tmp)

    assert not os.path.exists(tmp)


def test_cleanup_tmp_file_dir():
    tmp = tempfile.mkdtemp()
    cleanup_tmp_file(tmp)

    assert not os.path.exists(tmp)


def test_cleanup_tmp_file_nonexistant():
    assert None is cleanup_tmp_file('nope')


def test_cleanup_tmp_file_failure(mocker, capsys):
    tmp = tempfile.mkdtemp()
    rmtree = mocker.patch('shutil.rmtree', side_effect=OSError('test induced failure'))
    cleanup_tmp_file(tmp)
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''
    rmtree.assert_called_once()


def test_cleanup_tmp_file_failure_warning(mocker, capsys):
    tmp = tempfile.mkdtemp()
    rmtree = mocker.patch('shutil.rmtree', side_effect=OSError('test induced failure'))
    cleanup_tmp_file(tmp, warn=True)
    out, err = capsys.readouterr()
    assert out == 'Unable to remove temporary file test induced failure\n'
    assert err == ''
    rmtree.assert_called_once()
