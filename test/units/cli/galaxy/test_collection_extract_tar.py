# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.errors import AnsibleError
from ansible.galaxy.collection import _extract_tar_dir


@pytest.fixture
def fake_tar_obj(mocker):
    m_tarfile = mocker.Mock()
    m_tarfile.type = mocker.Mock(return_value=b'99')
    m_tarfile.SYMTYPE = mocker.Mock(return_value=b'22')

    return m_tarfile


def test_extract_tar_member_trailing_sep(mocker):
    m_tarfile = mocker.Mock()
    m_tarfile.getmember = mocker.Mock(side_effect=KeyError)

    with pytest.raises(AnsibleError, match='Unable to extract'):
        _extract_tar_dir(m_tarfile, '/some/dir/', b'/some/dest')

    assert m_tarfile.getmember.call_count == 1


def test_extract_tar_member_no_trailing_sep(mocker):
    m_tarfile = mocker.Mock()
    m_tarfile.getmember = mocker.Mock(side_effect=KeyError)

    with pytest.raises(AnsibleError, match='Unable to extract'):
        _extract_tar_dir(m_tarfile, '/some/dir', b'/some/dest')

    assert m_tarfile.getmember.call_count == 2


def test_extract_tar_dir_exists(mocker, fake_tar_obj):
    mocker.patch('os.makedirs', return_value=None)
    m_makedir = mocker.patch('os.mkdir', return_value=None)
    mocker.patch('os.path.isdir', return_value=True)

    _extract_tar_dir(fake_tar_obj, '/some/dir', b'/some/dest')

    assert not m_makedir.called


def test_extract_tar_dir_does_not_exist(mocker, fake_tar_obj):
    mocker.patch('os.makedirs', return_value=None)
    m_makedir = mocker.patch('os.mkdir', return_value=None)
    mocker.patch('os.path.isdir', return_value=False)

    _extract_tar_dir(fake_tar_obj, '/some/dir', b'/some/dest')

    assert m_makedir.called
    assert m_makedir.call_args[0] == (b'/some/dir', 0o0755)
